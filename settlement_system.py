"""
Settlement System for Age of Scribes
=====================================

A comprehensive settlement management system that handles tier-based classification,
population dynamics, enchantment integrity, resource production/consumption,
trade tracking, and settlement evolution/collapse mechanics.

Features:
- Tier-based classification (Hamlet -> Village -> Town -> SmallCity -> LargeCity)
- Dynamic population tracking with growth/decline mechanics
- Enchantment integrity score (0-100) affecting settlement stability
- Resource production and consumption tracking
- Trade import/export management
- Settlement evolution and collapse logic
- Serialization support for persistence
- Modular design for AI simulation integration

Author: Age of Scribes Development Team
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SettlementTier(Enum):
    """Settlement tier classifications with associated thresholds and characteristics."""
    
    HAMLET = {
        'name': 'Hamlet',
        'min_population': 10,
        'max_population': 99,
        'base_enchantment_decay': 0.1,
        'trade_multiplier': 0.5,
        'upgrade_requirements': {
            'population': 80,
            'enchantment_integrity': 70,
            'trade_volume': 50,
            'threat_level': 3
        }
    }
    
    VILLAGE = {
        'name': 'Village',
        'min_population': 100,
        'max_population': 499,
        'base_enchantment_decay': 0.08,
        'trade_multiplier': 0.7,
        'upgrade_requirements': {
            'population': 400,
            'enchantment_integrity': 75,
            'trade_volume': 100,
            'threat_level': 4
        }
    }
    
    TOWN = {
        'name': 'Town',
        'min_population': 500,
        'max_population': 1999,
        'base_enchantment_decay': 0.06,
        'trade_multiplier': 1.0,
        'upgrade_requirements': {
            'population': 1600,
            'enchantment_integrity': 80,
            'trade_volume': 200,
            'threat_level': 5
        }
    }
    
    SMALL_CITY = {
        'name': 'Small City',
        'min_population': 2000,
        'max_population': 9999,
        'base_enchantment_decay': 0.05,
        'trade_multiplier': 1.3,
        'upgrade_requirements': {
            'population': 8000,
            'enchantment_integrity': 85,
            'trade_volume': 500,
            'threat_level': 6
        }
    }
    
    LARGE_CITY = {
        'name': 'Large City',
        'min_population': 10000,
        'max_population': float('inf'),
        'base_enchantment_decay': 0.04,
        'trade_multiplier': 1.5,
        'upgrade_requirements': None  # No further upgrades
    }


class ResourceType(Enum):
    """Types of resources tracked by settlements."""
    FOOD = "food"
    ORE = "ore"
    CLOTH = "cloth"
    WOOD = "wood"
    STONE = "stone"
    TOOLS = "tools"
    LUXURY = "luxury"
    MAGIC_COMPONENTS = "magic_components"


@dataclass
class ResourceData:
    """Tracks production, consumption, and trade for a specific resource."""
    production_base: float = 0.0  # Base production per tick
    consumption_base: float = 0.0  # Base consumption per tick
    stockpile: float = 0.0  # Current stockpile
    import_volume: float = 0.0  # Recent import volume
    export_volume: float = 0.0  # Recent export volume
    production_modifier: float = 1.0  # Multiplier for production efficiency
    
    def get_net_production(self) -> float:
        """Calculate net production after consumption."""
        return (self.production_base * self.production_modifier) - self.consumption_base
    
    def get_trade_balance(self) -> float:
        """Calculate trade balance (exports - imports)."""
        return self.export_volume - self.import_volume


@dataclass
class SettlementMetrics:
    """Tracks key settlement performance metrics over time."""
    population_history: List[int] = field(default_factory=list)
    enchantment_history: List[float] = field(default_factory=list)
    trade_volume_history: List[float] = field(default_factory=list)
    threat_level_history: List[int] = field(default_factory=list)
    
    def add_snapshot(self, population: int, enchantment: float, trade_volume: float, threat_level: int):
        """Add a metrics snapshot."""
        self.population_history.append(population)
        self.enchantment_history.append(enchantment)
        self.trade_volume_history.append(trade_volume)
        self.threat_level_history.append(threat_level)
        
        # Keep only last 30 snapshots
        if len(self.population_history) > 30:
            self.population_history.pop(0)
            self.enchantment_history.pop(0)
            self.trade_volume_history.pop(0)
            self.threat_level_history.pop(0)
    
    def get_population_trend(self) -> float:
        """Get population growth trend (-1.0 to 1.0)."""
        if len(self.population_history) < 2:
            return 0.0
        recent = sum(self.population_history[-5:]) / min(5, len(self.population_history))
        older = sum(self.population_history[:-5]) / max(1, len(self.population_history) - 5)
        return min(1.0, max(-1.0, (recent - older) / max(1, older)))
    
    def get_trade_volume_average(self, periods: int = 10) -> float:
        """Get rolling average of trade volume."""
        if not self.trade_volume_history:
            return 0.0
        recent_data = self.trade_volume_history[-periods:] if len(self.trade_volume_history) >= periods else self.trade_volume_history
        return sum(recent_data) / len(recent_data)


class Settlement:
    """
    Represents a settlement with dynamic population, resources, trade, and evolution mechanics.
    
    The Settlement class handles:
    - Tier-based classification and progression
    - Population dynamics and growth/decline
    - Enchantment integrity affecting settlement stability
    - Resource production, consumption, and stockpiling
    - Trade import/export tracking
    - Settlement evolution and collapse conditions
    """
    
    def __init__(self, 
                 name: str,
                 initial_population: int,
                 tier: SettlementTier = None,
                 location: Tuple[float, float] = (0.0, 0.0),
                 founding_date: Optional[datetime] = None,
                 founding_year: int = 1000,
                 governing_faction_id: Optional[str] = None,
                 settlement_type: Optional[str] = None):
        """
        Initialize a new settlement.
        
        Args:
            name: Settlement name
            initial_population: Starting population
            tier: Settlement tier (auto-determined if None)
            location: Geographic coordinates (x, y)
            founding_date: Date of settlement founding
            founding_year: Year the settlement was founded (game calendar)
            governing_faction_id: Unique identifier for controlling faction
            settlement_type: Political structure type (e.g., "theocracy", "merchant republic")
        """
        self.name = name
        self.population = initial_population
        self.location = location
        self.founding_date = founding_date or datetime.now()
        
        # Determine tier based on population if not specified
        self.tier = tier or self._determine_tier_by_population(initial_population)
        
        # Core settlement attributes
        self.enchantment_integrity = 85.0  # 0-100 scale
        self.threat_level = 1  # 0-10 scale
        self.is_active = True
        self.collapse_reason = None
        
        # Resource management
        self.resources: Dict[ResourceType, ResourceData] = {}
        self._initialize_resources()
        
        # Trade tracking
        self.trade_partners: List[str] = []  # Settlement names
        self.trade_routes_active = 0
        
        # Metrics and history
        self.metrics = SettlementMetrics()
        self.last_update = datetime.now()
        
        # Modular hooks for AI systems
        self.ai_modifiers: Dict[str, float] = {}  # For faction control, etc.
        self.pending_events: List[Dict[str, Any]] = []  # For NPC migration, etc.
        
        # New governance and stability attributes
        self.founding_year = founding_year
        self.governing_faction_id = governing_faction_id
        self.settlement_type = settlement_type
        self.stability_score = 50.0  # 0-100 scale, initialized at moderate stability
        self.reputation: Dict[str, float] = {}  # Maps faction/player IDs to reputation values (-100 to +100)
        
        # Calculate initial stability
        self.calculate_stability()
        
        logger.info(f"Settlement '{name}' founded as {self.tier.value['name']} with {initial_population} population")
    
    def _determine_tier_by_population(self, population: int) -> SettlementTier:
        """Determine settlement tier based on population."""
        for tier in SettlementTier:
            tier_data = tier.value
            if tier_data['min_population'] <= population <= tier_data['max_population']:
                return tier
        return SettlementTier.LARGE_CITY  # Default for very large populations
    
    def _initialize_resources(self):
        """Initialize resource tracking with default values."""
        for resource_type in ResourceType:
            # Set base production/consumption based on settlement tier and resource type
            base_production = self._calculate_base_production(resource_type)
            base_consumption = self._calculate_base_consumption(resource_type)
            
            self.resources[resource_type] = ResourceData(
                production_base=base_production,
                consumption_base=base_consumption,
                stockpile=base_production * 5  # Start with 5 ticks worth of production
            )
    
    def _calculate_base_production(self, resource_type: ResourceType) -> float:
        """Calculate base production for a resource type."""
        # Simple calculation based on population and tier
        tier_multiplier = self.tier.value['trade_multiplier']
        population_factor = self.population / 100.0
        
        # Resource-specific modifiers
        resource_modifiers = {
            ResourceType.FOOD: 1.5,
            ResourceType.ORE: 0.8,
            ResourceType.CLOTH: 1.0,
            ResourceType.WOOD: 1.2,
            ResourceType.STONE: 0.9,
            ResourceType.TOOLS: 0.6,
            ResourceType.LUXURY: 0.3,
            ResourceType.MAGIC_COMPONENTS: 0.2
        }
        
        base = population_factor * tier_multiplier * resource_modifiers.get(resource_type, 1.0)
        return max(0.1, base)  # Minimum production
    
    def _calculate_base_consumption(self, resource_type: ResourceType) -> float:
        """Calculate base consumption for a resource type."""
        population_factor = self.population / 100.0
        
        # Essential resources have higher consumption
        essential_resources = {
            ResourceType.FOOD: 1.8,
            ResourceType.CLOTH: 0.4,
            ResourceType.TOOLS: 0.3,
            ResourceType.WOOD: 0.5
        }
        
        if resource_type in essential_resources:
            return population_factor * essential_resources[resource_type]
        else:
            return population_factor * 0.1  # Minimal consumption for non-essentials
    
    def update_settlement(self, ticks_elapsed: int = 1) -> Dict[str, Any]:
        """
        Update settlement state for the given number of ticks.
        
        Args:
            ticks_elapsed: Number of simulation ticks that have passed
            
        Returns:
            Dictionary containing update results and any significant events
        """
        events = []
        
        for _ in range(ticks_elapsed):
            # Update resources
            self._update_resources()
            
            # Update population
            population_change = self._calculate_population_change()
            old_population = self.population
            self.population = max(0, self.population + population_change)
            
            if population_change != 0:
                events.append({
                    'type': 'population_change',
                    'old_value': old_population,
                    'new_value': self.population,
                    'change': population_change
                })
            
            # Update enchantment integrity
            old_enchantment = self.enchantment_integrity
            self._update_enchantment_integrity()
            
            if abs(self.enchantment_integrity - old_enchantment) > 1.0:
                events.append({
                    'type': 'enchantment_change',
                    'old_value': old_enchantment,
                    'new_value': self.enchantment_integrity,
                    'change': self.enchantment_integrity - old_enchantment
                })
            
            # Check for tier changes
            tier_change = self._evaluate_tier_change()
            if tier_change:
                events.append(tier_change)
            
            # Update stability score
            old_stability = self.stability_score
            self.calculate_stability()
            
            if abs(self.stability_score - old_stability) > 5.0:
                events.append({
                    'type': 'stability_change',
                    'old_value': old_stability,
                    'new_value': self.stability_score,
                    'change': self.stability_score - old_stability
                })
            
            # Check for collapse conditions
            collapse_event = self._check_collapse_conditions()
            if collapse_event:
                events.append(collapse_event)
                break  # Settlement collapsed, stop updates
        
        # Record metrics snapshot
        trade_volume = sum(r.import_volume + r.export_volume for r in self.resources.values())
        self.metrics.add_snapshot(self.population, self.enchantment_integrity, trade_volume, self.threat_level)
        
        self.last_update = datetime.now()
        
        return {
            'settlement_name': self.name,
            'events': events,
            'current_state': self.get_status_summary()
        }
    
    def _update_resources(self):
        """Update resource stockpiles based on production and consumption."""
        for resource_type, resource_data in self.resources.items():
            # Calculate net change
            net_production = resource_data.get_net_production()
            trade_net = resource_data.get_trade_balance()
            
            # Update stockpile
            resource_data.stockpile += net_production + trade_net
            resource_data.stockpile = max(0, resource_data.stockpile)  # Cannot go negative
            
            # Reset trade volumes (they represent per-tick trade)
            resource_data.import_volume = 0
            resource_data.export_volume = 0
    
    def _calculate_population_change(self) -> int:
        """Calculate population change for this tick."""
        # Base growth rate
        tier_data = self.tier.value
        base_growth_rate = 0.01  # 1% per tick base
        
        # Modifiers
        enchantment_modifier = (self.enchantment_integrity / 100.0)
        threat_modifier = max(0.1, 1.0 - (self.threat_level / 10.0))
        
        # Resource availability modifier
        food_data = self.resources[ResourceType.FOOD]
        food_security = min(2.0, food_data.stockpile / max(1, food_data.consumption_base))
        resource_modifier = min(1.5, food_security / 2.0)
        
        # Trade modifier
        trade_volume = sum(r.import_volume + r.export_volume for r in self.resources.values())
        trade_modifier = 1.0 + (trade_volume / 1000.0)  # Small bonus for active trade
        
        # Calculate final change
        total_modifier = enchantment_modifier * threat_modifier * resource_modifier * trade_modifier
        growth_rate = base_growth_rate * total_modifier
        
        # Apply some randomness
        import random
        growth_rate *= random.uniform(0.8, 1.2)
        
        # Calculate population change
        population_change = int(self.population * growth_rate)
        
        # Apply minimum/maximum bounds
        if self.population > tier_data['max_population']:
            population_change = min(population_change, -1)  # Force decline if over capacity
        
        return population_change
    
    def _update_enchantment_integrity(self):
        """Update enchantment integrity based on various factors."""
        tier_data = self.tier.value
        base_decay = tier_data['base_enchantment_decay']
        
        # Threat increases decay
        threat_multiplier = 1.0 + (self.threat_level / 20.0)
        
        # Population stress increases decay
        population_stress = max(0, (self.population - tier_data['min_population']) / 
                               (tier_data['max_population'] - tier_data['min_population']))
        stress_multiplier = 1.0 + (population_stress * 0.5)
        
        # Resource shortages increase decay
        food_shortage = max(0, 1.0 - (self.resources[ResourceType.FOOD].stockpile / 
                                     max(1, self.resources[ResourceType.FOOD].consumption_base)))
        shortage_multiplier = 1.0 + food_shortage
        
        # Apply decay
        total_decay = base_decay * threat_multiplier * stress_multiplier * shortage_multiplier
        
        # Apply AI modifiers
        ai_modifier = self.ai_modifiers.get('enchantment_maintenance', 1.0)
        total_decay *= ai_modifier
        
        self.enchantment_integrity = max(0, self.enchantment_integrity - total_decay)
    
    def _evaluate_tier_change(self) -> Optional[Dict[str, Any]]:
        """Evaluate if settlement should change tiers."""
        current_tier_data = self.tier.value
        
        # Check for upgrade
        upgrade_reqs = current_tier_data.get('upgrade_requirements')
        if upgrade_reqs and self._meets_upgrade_requirements(upgrade_reqs):
            old_tier = self.tier
            self.tier = self._get_next_tier()
            return {
                'type': 'tier_upgrade',
                'old_tier': old_tier.value['name'],
                'new_tier': self.tier.value['name']
            }
        
        # Check for downgrade
        if self._should_downgrade():
            old_tier = self.tier
            self.tier = self._get_previous_tier()
            return {
                'type': 'tier_downgrade',
                'old_tier': old_tier.value['name'],
                'new_tier': self.tier.value['name']
            }
        
        return None
    
    def _meets_upgrade_requirements(self, requirements: Dict[str, Any]) -> bool:
        """Check if settlement meets upgrade requirements."""
        # Population requirement
        if self.population < requirements['population']:
            return False
        
        # Enchantment integrity requirement
        if self.enchantment_integrity < requirements['enchantment_integrity']:
            return False
        
        # Trade volume requirement
        avg_trade_volume = self.metrics.get_trade_volume_average()
        if avg_trade_volume < requirements['trade_volume']:
            return False
        
        # Threat level requirement (must be below threshold)
        if self.threat_level > requirements['threat_level']:
            return False
        
        return True
    
    def _should_downgrade(self) -> bool:
        """Check if settlement should be downgraded."""
        tier_data = self.tier.value
        
        # Population too low
        if self.population < tier_data['min_population'] * 0.7:  # 30% buffer
            return True
        
        # Enchantment integrity too low
        if self.enchantment_integrity < 30:
            return True
        
        # High threat level
        if self.threat_level >= 8:
            return True
        
        return False
    
    def _get_next_tier(self) -> SettlementTier:
        """Get the next tier up from current tier."""
        tier_order = [SettlementTier.HAMLET, SettlementTier.VILLAGE, SettlementTier.TOWN, 
                     SettlementTier.SMALL_CITY, SettlementTier.LARGE_CITY]
        
        current_index = tier_order.index(self.tier)
        return tier_order[min(current_index + 1, len(tier_order) - 1)]
    
    def _get_previous_tier(self) -> SettlementTier:
        """Get the previous tier down from current tier."""
        tier_order = [SettlementTier.HAMLET, SettlementTier.VILLAGE, SettlementTier.TOWN, 
                     SettlementTier.SMALL_CITY, SettlementTier.LARGE_CITY]
        
        current_index = tier_order.index(self.tier)
        return tier_order[max(current_index - 1, 0)]
    
    def _check_collapse_conditions(self) -> Optional[Dict[str, Any]]:
        """Check if settlement should collapse."""
        if not self.is_active:
            return None
        
        collapse_reasons = []
        
        # Population collapse
        if self.population <= 5:
            collapse_reasons.append("population_collapse")
        
        # Enchantment failure
        if self.enchantment_integrity <= 5:
            collapse_reasons.append("enchantment_failure")
        
        # Critical threat level
        if self.threat_level >= 9:
            collapse_reasons.append("overwhelming_threat")
        
        # Resource crisis (prolonged food shortage)
        food_data = self.resources[ResourceType.FOOD]
        if food_data.stockpile <= 0 and food_data.get_net_production() <= 0:
            collapse_reasons.append("starvation")
        
        if collapse_reasons:
            self.is_active = False
            self.collapse_reason = collapse_reasons[0]  # Primary reason
            return {
                'type': 'settlement_collapse',
                'reasons': collapse_reasons,
                'primary_reason': collapse_reasons[0]
            }
        
        return None
    
    def add_trade_transaction(self, resource_type: ResourceType, amount: float, is_import: bool, partner_settlement: str = None):
        """
        Add a trade transaction.
        
        Args:
            resource_type: Type of resource being traded
            amount: Amount of resource (positive value)
            is_import: True for import, False for export
            partner_settlement: Name of trading partner (optional)
        """
        if resource_type not in self.resources:
            return
        
        resource_data = self.resources[resource_type]
        
        if is_import:
            resource_data.import_volume += amount
            resource_data.stockpile += amount
        else:
            resource_data.export_volume += amount
            resource_data.stockpile = max(0, resource_data.stockpile - amount)
        
        if partner_settlement and partner_settlement not in self.trade_partners:
            self.trade_partners.append(partner_settlement)
    
    def set_threat_level(self, new_threat_level: int):
        """Set the settlement's threat level (0-10)."""
        self.threat_level = max(0, min(10, new_threat_level))
        logger.info(f"Settlement '{self.name}' threat level set to {self.threat_level}")
    
    def apply_ai_modifier(self, modifier_name: str, value: float):
        """Apply an AI system modifier to the settlement."""
        self.ai_modifiers[modifier_name] = value
        logger.info(f"Applied AI modifier '{modifier_name}' = {value} to settlement '{self.name}'")
    
    def add_pending_event(self, event_type: str, event_data: Dict[str, Any]):
        """Add a pending event for AI systems to process."""
        event = {
            'type': event_type,
            'timestamp': datetime.now(),
            'data': event_data
        }
        self.pending_events.append(event)
    
    def process_pending_events(self) -> List[Dict[str, Any]]:
        """Process and clear pending events."""
        events = self.pending_events.copy()
        self.pending_events.clear()
        return events
    
    def calculate_stability(self) -> float:
        """
        Calculate and update stability_score using a weighted model.
        
        Stability is calculated based on:
        - Settlement age (older settlements gain passive stability)
        - Enchantment integrity (high integrity boosts stability)
        - Governing faction reputation (if applicable)
        - Placeholders for future modifiers (tax rate, recent events)
        
        Returns:
            Updated stability score (0-100)
        """
        # Base stability from settlement age
        current_year = 1100  # TODO: Should be passed from game calendar system
        settlement_age = max(0, current_year - self.founding_year)
        age_stability = min(30.0, settlement_age * 0.5)  # Max 30 points from age (60+ years)
        
        # Enchantment integrity contribution (0-25 points)
        enchantment_stability = (self.enchantment_integrity / 100.0) * 25.0
        
        # Governing faction reputation contribution (0-20 points)
        faction_stability = 0.0
        if self.governing_faction_id and self.governing_faction_id in self.reputation:
            faction_rep = self.reputation[self.governing_faction_id]
            # Convert reputation (-100 to +100) to stability bonus (0 to 20)
            faction_stability = max(0.0, (faction_rep + 100) / 200.0) * 20.0
        else:
            # Default moderate stability if no governing faction
            faction_stability = 10.0
        
        # Settlement tier stability bonus (larger settlements more stable)
        tier_stability_bonus = {
            'Hamlet': 0.0,
            'Village': 5.0,
            'Town': 10.0,
            'Small City': 15.0,
            'Large City': 20.0
        }
        tier_stability = tier_stability_bonus.get(self.tier.value['name'], 0.0)
        
        # Threat level penalty
        threat_penalty = self.threat_level * 2.0  # Each threat level reduces stability by 2 points
        
        # Population stability (balanced population for tier)
        tier_data = self.tier.value
        optimal_pop = (tier_data['min_population'] + tier_data['max_population']) / 2
        pop_ratio = self.population / optimal_pop
        # Penalty for being too far from optimal (overcrowding or underpopulation)
        pop_stability = 10.0 - abs(1.0 - pop_ratio) * 5.0
        pop_stability = max(0.0, pop_stability)
        
        # Placeholders for future modifiers
        tax_stability = 0.0  # TODO: Implement tax rate effects
        event_stability = 0.0  # TODO: Implement recent events effects
        trade_stability = min(5.0, len(self.trade_partners))  # Small bonus for trade relationships
        
        # Calculate final stability
        total_stability = (
            age_stability +
            enchantment_stability +
            faction_stability +
            tier_stability +
            pop_stability +
            trade_stability +
            tax_stability +
            event_stability -
            threat_penalty
        )
        
        # Clamp to 0-100 range
        self.stability_score = max(0.0, min(100.0, total_stability))
        
        return self.stability_score
    
    def set_reputation(self, faction_or_player_id: str, reputation_value: float):
        """
        Set reputation for a specific faction or player.
        
        Args:
            faction_or_player_id: Unique identifier for the faction or player
            reputation_value: Reputation value (-100 to +100)
        """
        reputation_value = max(-100.0, min(100.0, reputation_value))
        self.reputation[faction_or_player_id] = reputation_value
        logger.info(f"Settlement '{self.name}' reputation with '{faction_or_player_id}' set to {reputation_value}")
    
    def modify_reputation(self, faction_or_player_id: str, reputation_change: float):
        """
        Modify reputation for a specific faction or player.
        
        Args:
            faction_or_player_id: Unique identifier for the faction or player
            reputation_change: Amount to change reputation by (can be negative)
        """
        current_rep = self.reputation.get(faction_or_player_id, 0.0)
        new_rep = max(-100.0, min(100.0, current_rep + reputation_change))
        self.reputation[faction_or_player_id] = new_rep
        logger.info(f"Settlement '{self.name}' reputation with '{faction_or_player_id}' changed by {reputation_change:+.1f} to {new_rep}")
    
    def get_reputation(self, faction_or_player_id: str) -> float:
        """
        Get reputation for a specific faction or player.
        
        Args:
            faction_or_player_id: Unique identifier for the faction or player
            
        Returns:
            Reputation value (-100 to +100), or 0.0 if no reputation exists
        """
        return self.reputation.get(faction_or_player_id, 0.0)
    
    def set_governing_faction(self, faction_id: str, settlement_type: str = None):
        """
        Set the governing faction for this settlement.
        
        Args:
            faction_id: Unique identifier for the governing faction
            settlement_type: Optional political structure type
        """
        self.governing_faction_id = faction_id
        if settlement_type:
            self.settlement_type = settlement_type
        
        # Recalculate stability with new governance
        self.calculate_stability()
        logger.info(f"Settlement '{self.name}' now governed by faction '{faction_id}'" + 
                   (f" as {settlement_type}" if settlement_type else ""))
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a comprehensive status summary of the settlement."""
        trade_volume = sum(r.import_volume + r.export_volume for r in self.resources.values())
        
        return {
            'name': self.name,
            'tier': self.tier.value['name'],
            'population': self.population,
            'enchantment_integrity': round(self.enchantment_integrity, 1),
            'threat_level': self.threat_level,
            'is_active': self.is_active,
            'collapse_reason': self.collapse_reason,
            'trade_volume_current': round(trade_volume, 1),
            'trade_volume_average': round(self.metrics.get_trade_volume_average(), 1),
            'population_trend': round(self.metrics.get_population_trend(), 2),
            'trade_partners_count': len(self.trade_partners),
            'location': self.location,
            'founding_date': self.founding_date.isoformat() if self.founding_date else None,
            'last_update': self.last_update.isoformat(),
            # New governance and stability attributes
            'founding_year': self.founding_year,
            'governing_faction_id': self.governing_faction_id,
            'settlement_type': self.settlement_type,
            'stability_score': round(self.stability_score, 1),
            'reputation_count': len(self.reputation)
        }
    
    def get_resource_summary(self) -> Dict[str, Dict[str, float]]:
        """Get detailed resource information."""
        return {
            resource_type.value: {
                'production': round(resource_data.production_base * resource_data.production_modifier, 2),
                'consumption': round(resource_data.consumption_base, 2),
                'stockpile': round(resource_data.stockpile, 2),
                'net_production': round(resource_data.get_net_production(), 2),
                'recent_imports': round(resource_data.import_volume, 2),
                'recent_exports': round(resource_data.export_volume, 2)
            }
            for resource_type, resource_data in self.resources.items()
        }
    
    def serialize(self) -> Dict[str, Any]:
        """Serialize settlement to dictionary for persistence."""
        return {
            'name': self.name,
            'population': self.population,
            'tier': self.tier.name,
            'location': self.location,
            'founding_date': self.founding_date.isoformat() if self.founding_date else None,
            'enchantment_integrity': self.enchantment_integrity,
            'threat_level': self.threat_level,
            'is_active': self.is_active,
            'collapse_reason': self.collapse_reason,
            'resources': {
                resource_type.value: {
                    'production_base': resource_data.production_base,
                    'consumption_base': resource_data.consumption_base,
                    'stockpile': resource_data.stockpile,
                    'production_modifier': resource_data.production_modifier
                }
                for resource_type, resource_data in self.resources.items()
            },
            'trade_partners': self.trade_partners,
            'trade_routes_active': self.trade_routes_active,
            'ai_modifiers': self.ai_modifiers,
            'metrics': {
                'population_history': self.metrics.population_history,
                'enchantment_history': self.metrics.enchantment_history,
                'trade_volume_history': self.metrics.trade_volume_history,
                'threat_level_history': self.metrics.threat_level_history
            },
            'last_update': self.last_update.isoformat(),
            # New governance and stability attributes
            'founding_year': self.founding_year,
            'governing_faction_id': self.governing_faction_id,
            'settlement_type': self.settlement_type,
            'stability_score': self.stability_score,
            'reputation': self.reputation
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'Settlement':
        """Create settlement from serialized data."""
        settlement = cls(
            name=data['name'],
            initial_population=data['population'],
            tier=SettlementTier[data['tier']],
            location=tuple(data['location']),
            founding_date=datetime.fromisoformat(data['founding_date']) if data['founding_date'] else None,
            founding_year=data.get('founding_year', 1000),
            governing_faction_id=data.get('governing_faction_id'),
            settlement_type=data.get('settlement_type')
        )
        
        # Restore state
        settlement.enchantment_integrity = data['enchantment_integrity']
        settlement.threat_level = data['threat_level']
        settlement.is_active = data['is_active']
        settlement.collapse_reason = data['collapse_reason']
        settlement.trade_partners = data['trade_partners']
        settlement.trade_routes_active = data['trade_routes_active']
        settlement.ai_modifiers = data['ai_modifiers']
        settlement.last_update = datetime.fromisoformat(data['last_update'])
        
        # Restore new governance and stability attributes
        settlement.stability_score = data.get('stability_score', 50.0)
        settlement.reputation = data.get('reputation', {})
        
        # Restore resources
        for resource_name, resource_info in data['resources'].items():
            resource_type = ResourceType(resource_name)
            settlement.resources[resource_type] = ResourceData(
                production_base=resource_info['production_base'],
                consumption_base=resource_info['consumption_base'],
                stockpile=resource_info['stockpile'],
                production_modifier=resource_info['production_modifier']
            )
        
        # Restore metrics
        metrics_data = data['metrics']
        settlement.metrics.population_history = metrics_data['population_history']
        settlement.metrics.enchantment_history = metrics_data['enchantment_history']
        settlement.metrics.trade_volume_history = metrics_data['trade_volume_history']
        settlement.metrics.threat_level_history = metrics_data['threat_level_history']
        
        return settlement


def update_all_settlements(settlements: List['Settlement']) -> None:
    """
    Update all settlements in the simulation for one tick.
    
    This function is designed to be called by the main economic tick system.
    It handles inter-settlement interactions and system-wide effects.
    
    Args:
        settlements: List of Settlement objects to update
    """
    # TODO: Implement system-wide settlement updates
    # This function will be expanded to handle:
    # - Inter-settlement trade negotiations
    # - Regional threat propagation
    # - Migration flows between settlements
    # - Market price fluctuations
    # - Diplomatic relations
    # - Resource scarcity effects
    # - Disease/disaster spread
    # - AI-driven faction activities affecting multiple settlements
    
    logger.info(f"Updating {len(settlements)} settlements (stub implementation)")
    
    for settlement in settlements:
        if settlement.is_active:
            update_result = settlement.update_settlement()
            
            # Log significant events
            for event in update_result['events']:
                if event['type'] in ['tier_upgrade', 'tier_downgrade', 'settlement_collapse']:
                    logger.warning(f"Settlement '{settlement.name}': {event}")


# Example usage and testing
if __name__ == "__main__":
    # Create test settlements
    settlements = [
        Settlement("Riverside Hamlet", 45, location=(10.0, 20.0)),
        Settlement("Millbrook Village", 350, location=(15.0, 18.0)),
        Settlement("Ironhold Town", 1200, location=(12.0, 25.0))
    ]
    
    print("=== Initial Settlement States ===")
    for settlement in settlements:
        print(f"{settlement.name}: {settlement.get_status_summary()}")
    
    print("\n=== Running 5 Simulation Ticks ===")
    for tick in range(5):
        print(f"\n--- Tick {tick + 1} ---")
        update_all_settlements(settlements)
        
        for settlement in settlements:
            status = settlement.get_status_summary()
            print(f"{settlement.name}: Pop={status['population']}, "
                  f"Enchant={status['enchantment_integrity']:.1f}, "
                  f"Tier={status['tier']}")
    
    print("\n=== Final Settlement Resources ===")
    for settlement in settlements:
        print(f"\n{settlement.name} Resources:")
        resources = settlement.get_resource_summary()
        for resource, data in resources.items():
            if data['stockpile'] > 0 or data['net_production'] != 0:
                print(f"  {resource}: Stock={data['stockpile']:.1f}, "
                      f"Net={data['net_production']:.1f}") 