"""
Economy Tick System for Age of Scribes
======================================

Daily economic cycle simulation system that orchestrates settlement economies,
resource flows, trade dynamics, and population changes across the simulation.

Features:
- Daily economic processing for all settlements
- Resource production/consumption fluctuation simulation
- Trade volume tracking and rolling averages
- Population dynamics based on stability and growth rates
- Enchantment integrity effects on production
- Settlement evolution and collapse evaluation
- Modular architecture for future faction/caravan integration

Author: Age of Scribes Development Team
"""

from typing import List, Dict, Tuple, Optional, Any
import random
import logging
from datetime import datetime, timedelta
from settlement_system import Settlement, ResourceType, ResourceData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EconomyTickSystem:
    """
    Manages daily economic cycles across all settlements in the simulation.
    
    This system orchestrates resource production, consumption, trade flows,
    population dynamics, and settlement evolution on a daily basis.
    """
    
    def __init__(self, current_day: int = 1, season_modifier: float = 1.0):
        """
        Initialize the economy tick system.
        
        Args:
            current_day: Current simulation day
            season_modifier: Seasonal effect modifier (0.5-1.5)
        """
        self.current_day = current_day
        self.season_modifier = season_modifier
        self.daily_logs: List[Dict[str, Any]] = []
        
        # Economic constants
        self.base_production_variance = 0.05  # ±5% daily variance
        self.enchantment_production_bonus = (0.10, 0.30)  # 10-30% bonus range
        self.trade_volume_history_limit = 30  # Days of trade history
        
        # Integration hooks for future systems
        self.faction_controllers: Dict[str, Any] = {}  # Placeholder for faction system
        self.caravan_routes: List[Dict[str, Any]] = []  # Placeholder for caravan system
        self.market_prices: Dict[str, float] = {}  # Placeholder for market system
        
        logger.info(f"Economy Tick System initialized for day {current_day}")
    
    def economy_tick(self, settlements: List[Settlement]) -> None:
        """
        Execute daily economic cycle for all settlements.
        
        Args:
            settlements: List of active settlements to process
        """
        logger.info(f"=== ECONOMY TICK - Day {self.current_day} ===")
        
        tick_summary = {
            'day': self.current_day,
            'settlements_processed': 0,
            'total_population': 0,
            'total_trade_volume': 0.0,
            'settlements_evolved': 0,
            'settlements_collapsed': 0,
            'stability_changes': 0,
            'start_time': datetime.now()
        }
        
        for settlement in settlements:
            if settlement.is_active:
                daily_result = self._process_settlement_daily_cycle(settlement)
                
                # Update tick summary
                tick_summary['settlements_processed'] += 1
                tick_summary['total_population'] += settlement.population
                tick_summary['total_trade_volume'] += daily_result.get('trade_volume', 0.0)
                
                if daily_result.get('evolved', False):
                    tick_summary['settlements_evolved'] += 1
                if daily_result.get('collapsed', False):
                    tick_summary['settlements_collapsed'] += 1
                if daily_result.get('stability_changed', False):
                    tick_summary['stability_changes'] += 1
        
        # Process inter-settlement economics
        self._process_inter_settlement_trade(settlements)
        self._process_faction_economic_effects(settlements)
        self._process_caravan_routes(settlements)
        
        # Finalize tick
        tick_summary['end_time'] = datetime.now()
        tick_summary['processing_time_ms'] = (
            tick_summary['end_time'] - tick_summary['start_time']
        ).total_seconds() * 1000
        
        self.daily_logs.append(tick_summary)
        self.current_day += 1
        
        # Keep only last 30 days of logs
        if len(self.daily_logs) > 30:
            self.daily_logs.pop(0)
        
        logger.info(
            f"Economy tick complete: {tick_summary['settlements_processed']} settlements, "
            f"{tick_summary['total_population']} total population, "
            f"{tick_summary['processing_time_ms']:.1f}ms"
        )
    
    def _process_settlement_daily_cycle(self, settlement: Settlement) -> Dict[str, Any]:
        """
        Process daily economic cycle for a single settlement.
        
        Args:
            settlement: Settlement to process
            
        Returns:
            Dictionary containing daily processing results
        """
        daily_result = {
            'settlement_name': settlement.name,
            'trade_volume': 0.0,
            'population_change': 0,
            'stability_changed': False,
            'evolved': False,
            'collapsed': False,
            'resource_changes': {}
        }
        
        # 1. Update trade volume rolling average
        current_trade_volume = self._calculate_current_trade_volume(settlement)
        self._update_trade_volume_rolling(settlement, current_trade_volume)
        daily_result['trade_volume'] = current_trade_volume
        
        # 2. Adjust population based on growth rate and stability
        population_change = self._calculate_population_adjustment(settlement)
        old_population = settlement.population
        settlement.population = max(1, settlement.population + population_change)
        daily_result['population_change'] = settlement.population - old_population
        
        # 3. Recalculate stability score
        old_stability = settlement.stability_score
        settlement.calculate_stability()
        daily_result['stability_changed'] = abs(settlement.stability_score - old_stability) > 1.0
        
        # 4. Adjust enchantment integrity
        self._adjust_enchantment_integrity(settlement, current_trade_volume)
        
        # 5. Recalculate resources with daily variation
        resource_changes = self._process_daily_resource_cycle(settlement)
        daily_result['resource_changes'] = resource_changes
        
        # 6. Attempt evolution
        if self._evaluate_settlement_evolution(settlement):
            daily_result['evolved'] = True
            logger.info(f"Settlement '{settlement.name}' evolved to {settlement.tier.value['name']}")
        
        # 7. Attempt collapse evaluation
        if self._evaluate_settlement_collapse(settlement):
            daily_result['collapsed'] = True
            logger.warning(f"Settlement '{settlement.name}' collapsed: {settlement.collapse_reason}")
        
        return daily_result
    
    def _calculate_current_trade_volume(self, settlement: Settlement) -> float:
        """Calculate current day's total trade volume."""
        trade_volume = 0.0
        for resource_data in settlement.resources.values():
            trade_volume += resource_data.import_volume + resource_data.export_volume
        return trade_volume
    
    def _update_trade_volume_rolling(self, settlement: Settlement, volume: float):
        """Update settlement's rolling trade volume history."""
        # Add current volume to history
        settlement.metrics.trade_volume_history.append(volume)
        
        # Maintain history limit
        if len(settlement.metrics.trade_volume_history) > self.trade_volume_history_limit:
            settlement.metrics.trade_volume_history.pop(0)
    
    def _calculate_population_adjustment(self, settlement: Settlement) -> int:
        """
        Calculate daily population change based on growth rate and stability.
        
        Args:
            settlement: Settlement to calculate for
            
        Returns:
            Population change (can be negative)
        """
        # Base growth rate (daily)
        base_daily_growth_rate = 0.001  # 0.1% per day base
        
        # Stability modifier (0.5x to 1.5x based on stability)
        stability_modifier = 0.5 + (settlement.stability_score / 100.0)
        
        # Tier modifier (larger settlements grow slower per capita)
        tier_modifiers = {
            'Hamlet': 1.2,
            'Village': 1.0,
            'Town': 0.8,
            'Small City': 0.6,
            'Large City': 0.4
        }
        tier_modifier = tier_modifiers.get(settlement.tier.value['name'], 1.0)
        
        # Resource availability modifier
        food_data = settlement.resources.get(ResourceType.FOOD)
        if food_data:
            food_ratio = food_data.stockpile / max(1, food_data.consumption_base)
            food_modifier = min(1.5, max(0.3, food_ratio / 2.0))
        else:
            food_modifier = 1.0
        
        # Calculate final growth
        total_modifier = stability_modifier * tier_modifier * food_modifier * self.season_modifier
        daily_growth_rate = base_daily_growth_rate * total_modifier
        
        # Apply random variance
        daily_growth_rate *= random.uniform(0.8, 1.2)
        
        # Calculate population change
        population_change = int(settlement.population * daily_growth_rate)
        
        # Ensure minimum change when conditions are very poor
        if total_modifier < 0.7 and population_change >= 0:
            population_change = random.choice([-1, 0])
        
        return population_change
    
    def _adjust_enchantment_integrity(self, settlement: Settlement, trade_volume: float):
        """
        Adjust enchantment integrity based on daily factors.
        
        Args:
            settlement: Settlement to adjust
            trade_volume: Current day's trade volume
        """
        # Base daily decay
        tier_data = settlement.tier.value
        base_decay = tier_data['base_enchantment_decay'] * 0.1  # Daily rate
        
        # Trade volume bonus (active trade helps maintain enchantment)
        trade_bonus = min(0.05, trade_volume / 1000.0)
        
        # Random daily fluctuation
        random_fluctuation = random.uniform(-0.1, 0.1)
        
        # Population stress factor
        optimal_pop = (tier_data['min_population'] + tier_data['max_population']) / 2
        stress_factor = abs(settlement.population - optimal_pop) / optimal_pop * 0.05
        
        # Calculate net change
        net_change = -base_decay + trade_bonus + random_fluctuation - stress_factor
        
        # Apply change
        settlement.enchantment_integrity = max(0, min(100, 
            settlement.enchantment_integrity + net_change))
    
    def _process_daily_resource_cycle(self, settlement: Settlement) -> Dict[str, Dict[str, float]]:
        """
        Process daily resource production and consumption with variations.
        
        Args:
            settlement: Settlement to process
            
        Returns:
            Dictionary of resource changes
        """
        resource_changes = {}
        
        # Get enchantment production bonus
        enchantment_bonus = self._calculate_enchantment_production_bonus(
            settlement.enchantment_integrity)
        
        for resource_type, resource_data in settlement.resources.items():
            # Calculate daily production with variance
            base_production = resource_data.production_base
            daily_variance = random.uniform(
                1.0 - self.base_production_variance,
                1.0 + self.base_production_variance
            )
            
            # Apply enchantment bonus
            production_modifier = daily_variance * enchantment_bonus * self.season_modifier
            
            # Calculate actual production and consumption
            daily_production = base_production * production_modifier
            daily_consumption = resource_data.consumption_base
            
            # Net change
            net_change = daily_production - daily_consumption
            
            # Update stockpile
            old_stockpile = resource_data.stockpile
            resource_data.stockpile = max(0, resource_data.stockpile + net_change)
            
            # Reset daily trade volumes
            resource_data.import_volume = 0
            resource_data.export_volume = 0
            
            # Record changes
            resource_changes[resource_type.value] = {
                'production': daily_production,
                'consumption': daily_consumption,
                'net_change': net_change,
                'old_stockpile': old_stockpile,
                'new_stockpile': resource_data.stockpile,
                'variance_applied': daily_variance,
                'enchantment_bonus': enchantment_bonus
            }
        
        return resource_changes
    
    def _calculate_enchantment_production_bonus(self, enchantment_integrity: float) -> float:
        """
        Calculate production bonus from enchantment integrity.
        
        Args:
            enchantment_integrity: Current enchantment level (0-100)
            
        Returns:
            Production multiplier (1.0 to 1.3)
        """
        if enchantment_integrity <= 0:
            return 0.8  # Penalty for no enchantment
        
        # Linear scaling from 10% to 30% bonus
        bonus_range = self.enchantment_production_bonus[1] - self.enchantment_production_bonus[0]
        bonus = self.enchantment_production_bonus[0] + (enchantment_integrity / 100.0) * bonus_range
        
        return 1.0 + bonus
    
    def _evaluate_settlement_evolution(self, settlement: Settlement) -> bool:
        """
        Evaluate if settlement should evolve to next tier.
        
        Args:
            settlement: Settlement to evaluate
            
        Returns:
            True if settlement evolved
        """
        tier_data = settlement.tier.value
        upgrade_requirements = tier_data.get('upgrade_requirements')
        
        if not upgrade_requirements:
            return False  # No further upgrades available
        
        # Check all upgrade requirements
        requirements_met = (
            settlement.population >= upgrade_requirements['population'] and
            settlement.enchantment_integrity >= upgrade_requirements['enchantment_integrity'] and
            settlement.threat_level <= upgrade_requirements['threat_level'] and
            settlement.metrics.get_trade_volume_average() >= upgrade_requirements['trade_volume']
        )
        
        if requirements_met:
            # Evolve settlement
            old_tier = settlement.tier
            settlement.tier = settlement._get_next_tier()
            
            # Recalculate stability with new tier
            settlement.calculate_stability()
            
            return True
        
        return False
    
    def _evaluate_settlement_collapse(self, settlement: Settlement) -> bool:
        """
        Evaluate if settlement should collapse.
        
        Args:
            settlement: Settlement to evaluate
            
        Returns:
            True if settlement collapsed
        """
        collapse_reasons = []
        
        # Population collapse
        if settlement.population <= 5:
            collapse_reasons.append("population_collapse")
        
        # Enchantment failure
        if settlement.enchantment_integrity <= 5:
            collapse_reasons.append("enchantment_failure")
        
        # Resource crisis
        food_data = settlement.resources.get(ResourceType.FOOD)
        if food_data and food_data.stockpile <= 0 and food_data.get_net_production() <= 0:
            collapse_reasons.append("starvation")
        
        # Stability crisis
        if settlement.stability_score <= 10:
            collapse_reasons.append("stability_collapse")
        
        # Critical threat level
        if settlement.threat_level >= 9:
            collapse_reasons.append("overwhelming_threat")
        
        if collapse_reasons:
            settlement.is_active = False
            settlement.collapse_reason = collapse_reasons[0]  # Primary reason
            return True
        
        return False
    
    def _process_inter_settlement_trade(self, settlements: List[Settlement]):
        """
        Process trade flows between settlements.
        
        Args:
            settlements: List of all settlements
        """
        # TODO: Implement inter-settlement trade logic
        # This is a placeholder for future trade route and market systems
        active_settlements = [s for s in settlements if s.is_active]
        
        if len(active_settlements) > 1:
            # Simulate basic trade flows
            for i, settlement_a in enumerate(active_settlements):
                for settlement_b in active_settlements[i+1:]:
                    self._simulate_bilateral_trade(settlement_a, settlement_b)
    
    def _simulate_bilateral_trade(self, settlement_a: Settlement, settlement_b: Settlement):
        """
        Simulate trade between two settlements.
        
        Args:
            settlement_a: First settlement
            settlement_b: Second settlement
        """
        # Simple trade simulation - exchange surplus for deficit
        trade_volume = 0.0
        
        for resource_type in ResourceType:
            resource_a = settlement_a.resources.get(resource_type)
            resource_b = settlement_b.resources.get(resource_type)
            
            if not (resource_a and resource_b):
                continue
            
            # Calculate surplus/deficit
            surplus_a = resource_a.stockpile - resource_a.consumption_base * 5  # 5 days buffer
            surplus_b = resource_b.stockpile - resource_b.consumption_base * 5
            
            # Trade if one has surplus and other has deficit
            if surplus_a > 10 and surplus_b < -5:
                trade_amount = min(surplus_a * 0.1, abs(surplus_b) * 0.5)
                settlement_a.add_trade_transaction(resource_type, trade_amount, False, settlement_b.name)
                settlement_b.add_trade_transaction(resource_type, trade_amount, True, settlement_a.name)
                trade_volume += trade_amount
            elif surplus_b > 10 and surplus_a < -5:
                trade_amount = min(surplus_b * 0.1, abs(surplus_a) * 0.5)
                settlement_b.add_trade_transaction(resource_type, trade_amount, False, settlement_a.name)
                settlement_a.add_trade_transaction(resource_type, trade_amount, True, settlement_b.name)
                trade_volume += trade_amount
        
        if trade_volume > 0:
            logger.debug(f"Trade between {settlement_a.name} and {settlement_b.name}: {trade_volume:.1f} units")
    
    def _process_faction_economic_effects(self, settlements: List[Settlement]):
        """
        Process faction-based economic effects on settlements.
        
        Args:
            settlements: List of all settlements
        """
        # TODO: Integrate with faction system
        # Placeholder for faction economic influences
        for settlement in settlements:
            if settlement.is_active and settlement.governing_faction_id:
                # Apply faction-specific economic bonuses/penalties
                faction_id = settlement.governing_faction_id
                
                # Example faction effects (placeholders)
                if 'merchant' in faction_id.lower():
                    # Merchant factions boost trade
                    trade_bonus = 1.1
                    for resource_data in settlement.resources.values():
                        resource_data.production_modifier = max(
                            resource_data.production_modifier, trade_bonus)
                elif 'military' in faction_id.lower():
                    # Military factions reduce enchantment decay
                    settlement.enchantment_integrity = min(100, 
                        settlement.enchantment_integrity + 0.1)
    
    def _process_caravan_routes(self, settlements: List[Settlement]):
        """
        Process caravan route effects on settlements.
        
        Args:
            settlements: List of all settlements
        """
        # TODO: Implement caravan system integration
        # Placeholder for caravan route processing
        pass
    
    def get_economy_summary(self) -> Dict[str, Any]:
        """Get summary of recent economic activity."""
        if not self.daily_logs:
            return {'status': 'no_data'}
        
        recent_logs = self.daily_logs[-7:]  # Last 7 days
        
        return {
            'current_day': self.current_day,
            'days_simulated': len(self.daily_logs),
            'recent_activity': {
                'avg_settlements_processed': sum(log['settlements_processed'] for log in recent_logs) / len(recent_logs),
                'avg_total_population': sum(log['total_population'] for log in recent_logs) / len(recent_logs),
                'avg_trade_volume': sum(log['total_trade_volume'] for log in recent_logs) / len(recent_logs),
                'total_evolutions': sum(log['settlements_evolved'] for log in recent_logs),
                'total_collapses': sum(log['settlements_collapsed'] for log in recent_logs),
                'avg_processing_time_ms': sum(log['processing_time_ms'] for log in recent_logs) / len(recent_logs)
            }
        }


# Convenience function for single-call economy tick
def economy_tick(settlements: List[Settlement]) -> None:
    """
    Execute daily economic cycle for all settlements.
    
    This is a convenience function that creates a temporary EconomyTickSystem
    and executes one tick. For persistent simulation, use EconomyTickSystem directly.
    
    Args:
        settlements: List of Settlement objects to process
    """
    tick_system = EconomyTickSystem()
    tick_system.economy_tick(settlements)


# Example usage and testing
if __name__ == "__main__":
    from settlement_system import Settlement, SettlementTier
    
    # Create test settlements
    settlements = [
        Settlement("Riverside Hamlet", 45, location=(10.0, 20.0), founding_year=1000),
        Settlement("Millbrook Village", 350, SettlementTier.VILLAGE, (15.0, 18.0), founding_year=980),
        Settlement("Ironhold Town", 1200, location=(12.0, 25.0), founding_year=960),
        Settlement("Goldspire City", 5500, location=(20.0, 30.0), founding_year=920)
    ]
    
    # Set up some initial conditions
    settlements[1].set_governing_faction('merchant_guild', 'merchant republic')
    settlements[1].set_reputation('merchant_guild', 80.0)
    settlements[2].set_governing_faction('miners_union', 'guild confederation')
    settlements[2].set_reputation('miners_union', 60.0)
    
    print("=== Economy Tick System Test ===")
    print(f"Initial settlements: {len(settlements)}")
    
    # Create persistent economy system
    economy_system = EconomyTickSystem(current_day=1)
    
    # Run 10 days of simulation
    for day in range(10):
        print(f"\n--- Day {day + 1} ---")
        economy_system.economy_tick(settlements)
        
        # Show status every few days
        if (day + 1) % 3 == 0:
            for settlement in settlements:
                if settlement.is_active:
                    status = settlement.get_status_summary()
                    print(f"{settlement.name}: Pop={status['population']}, "
                          f"Stability={status['stability_score']:.1f}, "
                          f"Enchant={status['enchantment_integrity']:.1f}")
    
    # Show final summary
    print("\n=== Final Economy Summary ===")
    summary = economy_system.get_economy_summary()
    print(f"Days simulated: {summary['days_simulated']}")
    print(f"Average processing time: {summary['recent_activity']['avg_processing_time_ms']:.1f}ms")
    print(f"Total evolutions: {summary['recent_activity']['total_evolutions']}")
    print(f"Total collapses: {summary['recent_activity']['total_collapses']}") 