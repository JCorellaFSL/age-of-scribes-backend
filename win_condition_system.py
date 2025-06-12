#!/usr/bin/env python3
"""
Win Condition System for Age of Scribes
=======================================

This module provides a flexible framework for defining and tracking win/loss
conditions in simulations. Supports economic, political, social, and temporal
victory conditions with customizable parameters.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum


class ConditionType(Enum):
    """Types of win conditions."""
    ECONOMIC = "economic"
    POLITICAL = "political" 
    SOCIAL = "social"
    SURVIVAL = "survival"
    TEMPORAL = "temporal"
    CUSTOM = "custom"


class ConditionStatus(Enum):
    """Status of a win condition."""
    ACTIVE = "active"
    ACHIEVED = "achieved"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class WinCondition:
    """Defines a single win condition."""
    condition_id: str
    name: str
    description: str
    condition_type: ConditionType
    
    # Target criteria
    target_value: Union[int, float, str, Dict[str, Any]]
    comparison_operator: str  # ">=", "<=", "==", "!=", ">", "<", "contains", "all", "any"
    
    # Optional constraints
    time_limit_days: Optional[int] = None
    required_factions: Optional[List[str]] = None
    required_settlements: Optional[List[str]] = None
    
    # State tracking
    status: ConditionStatus = ConditionStatus.ACTIVE
    current_value: Union[int, float, str, Dict[str, Any]] = 0
    progress_percentage: float = 0.0
    
    # Metadata
    created_day: int = 0
    achieved_day: Optional[int] = None
    priority: int = 1  # Higher = more important
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['condition_type'] = self.condition_type.value
        result['status'] = self.status.value
        return result


class WinConditionEvaluator:
    """Handles evaluation of win conditions against simulation state."""
    
    def __init__(self):
        """Initialize the evaluator."""
        self.logger = logging.getLogger(__name__)
        
        # Built-in evaluation functions
        self.evaluators = {
            "settlement_population": self._evaluate_settlement_population,
            "faction_influence": self._evaluate_faction_influence,
            "total_wealth": self._evaluate_total_wealth,
            "settlements_controlled": self._evaluate_settlements_controlled,
            "npcs_alive": self._evaluate_npcs_alive,
            "reputation_score": self._evaluate_reputation_score,
            "justice_cases_resolved": self._evaluate_justice_cases,
            "guild_members": self._evaluate_guild_members,
            "resource_stockpile": self._evaluate_resource_stockpile,
            "time_survived": self._evaluate_time_survived
        }
    
    def evaluate_condition(self, 
                          condition: WinCondition,
                          world_state: Dict[str, Any],
                          current_day: int) -> bool:
        """
        Evaluate a single win condition against current world state.
        
        Args:
            condition: The win condition to evaluate
            world_state: Current simulation world state
            current_day: Current simulation day
            
        Returns:
            True if condition is met, False otherwise
        """
        # Check time limit first
        if condition.time_limit_days:
            days_elapsed = current_day - condition.created_day
            if days_elapsed >= condition.time_limit_days:
                condition.status = ConditionStatus.EXPIRED
                return False
        
        # Get evaluation function
        evaluator_key = condition.condition_id.split('_')[0] + '_' + condition.condition_id.split('_')[1]
        if evaluator_key not in self.evaluators:
            # Try full condition_id as evaluator key
            evaluator_key = condition.condition_id
        
        if evaluator_key in self.evaluators:
            try:
                result = self.evaluators[evaluator_key](condition, world_state)
                if result:
                    condition.status = ConditionStatus.ACHIEVED
                    condition.achieved_day = current_day
                return result
            except Exception as e:
                self.logger.error(f"Error evaluating condition {condition.condition_id}: {e}")
                return False
        else:
            self.logger.warning(f"No evaluator found for condition: {condition.condition_id}")
            return False
    
    def _compare_values(self, 
                       current: Union[int, float],
                       target: Union[int, float],
                       operator: str) -> bool:
        """Compare two values using the specified operator."""
        operators = {
            ">=": lambda c, t: c >= t,
            "<=": lambda c, t: c <= t,
            "==": lambda c, t: c == t,
            "!=": lambda c, t: c != t,
            ">": lambda c, t: c > t,
            "<": lambda c, t: c < t
        }
        
        if operator in operators:
            return operators[operator](current, target)
        else:
            self.logger.warning(f"Unknown comparison operator: {operator}")
            return False
    
    def _evaluate_settlement_population(self, 
                                      condition: WinCondition,
                                      world_state: Dict[str, Any]) -> bool:
        """Evaluate settlement population conditions."""
        settlements = world_state.get('settlements', [])
        
        if condition.required_settlements:
            # Check specific settlements
            total_population = 0
            for settlement in settlements:
                if settlement['name'] in condition.required_settlements:
                    total_population += settlement.get('population', 0)
            condition.current_value = total_population
        else:
            # Check all settlements
            condition.current_value = sum(s.get('population', 0) for s in settlements)
        
        # Calculate progress
        if isinstance(condition.target_value, (int, float)) and condition.target_value > 0:
            condition.progress_percentage = min(100.0, 
                (condition.current_value / condition.target_value) * 100.0)
        
        return self._compare_values(condition.current_value, condition.target_value, 
                                  condition.comparison_operator)
    
    def _evaluate_faction_influence(self, 
                                  condition: WinCondition,
                                  world_state: Dict[str, Any]) -> bool:
        """Evaluate faction influence conditions."""
        factions = world_state.get('factions', [])
        
        if condition.required_factions:
            # Check specific faction influence
            total_influence = 0
            for faction in factions:
                if faction['name'] in condition.required_factions:
                    total_influence += faction.get('influence', 0)
            condition.current_value = total_influence
        else:
            # Check highest faction influence
            condition.current_value = max((f.get('influence', 0) for f in factions), default=0)
        
        # Calculate progress
        if isinstance(condition.target_value, (int, float)) and condition.target_value > 0:
            condition.progress_percentage = min(100.0, 
                (condition.current_value / condition.target_value) * 100.0)
        
        return self._compare_values(condition.current_value, condition.target_value,
                                  condition.comparison_operator)
    
    def _evaluate_total_wealth(self, 
                             condition: WinCondition,
                             world_state: Dict[str, Any]) -> bool:
        """Evaluate total wealth conditions."""
        settlements = world_state.get('settlements', [])
        
        # Sum up all resources as wealth indicator
        total_wealth = 0
        for settlement in settlements:
            resources = settlement.get('resources', {})
            for resource_name, resource_data in resources.items():
                if isinstance(resource_data, dict):
                    stockpile = resource_data.get('stockpile', 0)
                    # Simple wealth calculation - could be made more sophisticated
                    wealth_multiplier = {"food": 1, "ore": 2, "cloth": 3, "tools": 4, 
                                       "luxury": 10, "magic_components": 20}.get(resource_name, 1)
                    total_wealth += stockpile * wealth_multiplier
        
        condition.current_value = total_wealth
        
        # Calculate progress
        if isinstance(condition.target_value, (int, float)) and condition.target_value > 0:
            condition.progress_percentage = min(100.0, 
                (condition.current_value / condition.target_value) * 100.0)
        
        return self._compare_values(condition.current_value, condition.target_value,
                                  condition.comparison_operator)
    
    def _evaluate_settlements_controlled(self, 
                                       condition: WinCondition,
                                       world_state: Dict[str, Any]) -> bool:
        """Evaluate settlements controlled conditions."""
        settlements = world_state.get('settlements', [])
        
        if condition.required_factions:
            # Count settlements controlled by specific factions
            controlled_count = 0
            for settlement in settlements:
                governing_faction = settlement.get('governing_faction')
                if governing_faction in condition.required_factions:
                    controlled_count += 1
            condition.current_value = controlled_count
        else:
            # Total active settlements
            condition.current_value = len([s for s in settlements if s.get('is_active', True)])
        
        # Calculate progress
        if isinstance(condition.target_value, (int, float)) and condition.target_value > 0:
            condition.progress_percentage = min(100.0, 
                (condition.current_value / condition.target_value) * 100.0)
        
        return self._compare_values(condition.current_value, condition.target_value,
                                  condition.comparison_operator)
    
    def _evaluate_npcs_alive(self, 
                           condition: WinCondition,
                           world_state: Dict[str, Any]) -> bool:
        """Evaluate NPC survival conditions."""
        npcs = world_state.get('npcs', [])
        condition.current_value = len([npc for npc in npcs if npc.get('is_active', True)])
        
        # Calculate progress
        if isinstance(condition.target_value, (int, float)) and condition.target_value > 0:
            condition.progress_percentage = min(100.0, 
                (condition.current_value / condition.target_value) * 100.0)
        
        return self._compare_values(condition.current_value, condition.target_value,
                                  condition.comparison_operator)
    
    def _evaluate_reputation_score(self, 
                                 condition: WinCondition,
                                 world_state: Dict[str, Any]) -> bool:
        """Evaluate reputation score conditions."""
        # This would need integration with reputation system
        # For now, return a placeholder
        condition.current_value = 0
        return False
    
    def _evaluate_justice_cases(self, 
                              condition: WinCondition,
                              world_state: Dict[str, Any]) -> bool:
        """Evaluate justice system conditions."""
        justice_stats = world_state.get('justice', {})
        condition.current_value = justice_stats.get('total_cases', 0)
        
        # Calculate progress
        if isinstance(condition.target_value, (int, float)) and condition.target_value > 0:
            condition.progress_percentage = min(100.0, 
                (condition.current_value / condition.target_value) * 100.0)
        
        return self._compare_values(condition.current_value, condition.target_value,
                                  condition.comparison_operator)
    
    def _evaluate_guild_members(self, 
                              condition: WinCondition,
                              world_state: Dict[str, Any]) -> bool:
        """Evaluate guild membership conditions."""
        # Placeholder for guild system integration
        condition.current_value = 0
        return False
    
    def _evaluate_resource_stockpile(self, 
                                   condition: WinCondition,
                                   world_state: Dict[str, Any]) -> bool:
        """Evaluate resource stockpile conditions."""
        settlements = world_state.get('settlements', [])
        
        # Target should specify resource type
        if isinstance(condition.target_value, dict):
            resource_type = condition.target_value.get('resource_type', 'food')
            target_amount = condition.target_value.get('amount', 100)
        else:
            resource_type = 'food'
            target_amount = condition.target_value
        
        total_stockpile = 0
        for settlement in settlements:
            resources = settlement.get('resources', {})
            if resource_type in resources:
                resource_data = resources[resource_type]
                if isinstance(resource_data, dict):
                    total_stockpile += resource_data.get('stockpile', 0)
        
        condition.current_value = total_stockpile
        
        # Calculate progress
        if target_amount > 0:
            condition.progress_percentage = min(100.0, 
                (condition.current_value / target_amount) * 100.0)
        
        return self._compare_values(condition.current_value, target_amount,
                                  condition.comparison_operator)
    
    def _evaluate_time_survived(self, 
                              condition: WinCondition,
                              world_state: Dict[str, Any]) -> bool:
        """Evaluate time survival conditions."""
        # This would be handled at the manager level with current_day
        return False


class WinConditionManager:
    """Manages all win conditions for a simulation."""
    
    def __init__(self):
        """Initialize the win condition manager."""
        self.conditions: Dict[str, WinCondition] = {}
        self.evaluator = WinConditionEvaluator()
        self.logger = logging.getLogger(__name__)
        
        # Tracking
        self.achieved_conditions: List[WinCondition] = []
        self.failed_conditions: List[WinCondition] = []
        
    def add_condition(self, condition: WinCondition, current_day: int = 0) -> bool:
        """Add a new win condition."""
        try:
            condition.created_day = current_day
            self.conditions[condition.condition_id] = condition
            self.logger.info(f"Added win condition: {condition.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add condition {condition.condition_id}: {e}")
            return False
    
    def remove_condition(self, condition_id: str) -> bool:
        """Remove a win condition."""
        if condition_id in self.conditions:
            del self.conditions[condition_id]
            self.logger.info(f"Removed win condition: {condition_id}")
            return True
        return False
    
    def evaluate_all_conditions(self, 
                               world_state: Dict[str, Any],
                               current_day: int) -> Dict[str, Any]:
        """
        Evaluate all active win conditions.
        
        Returns:
            Dictionary with evaluation results and game state
        """
        results = {
            "conditions_evaluated": 0,
            "conditions_achieved": 0,
            "conditions_failed": 0,
            "conditions_expired": 0,
            "game_won": False,
            "game_lost": False,
            "active_conditions": [],
            "achieved_conditions": [],
            "failed_conditions": []
        }
        
        for condition in list(self.conditions.values()):
            if condition.status != ConditionStatus.ACTIVE:
                continue
                
            results["conditions_evaluated"] += 1
            
            # Evaluate condition
            achieved = self.evaluator.evaluate_condition(condition, world_state, current_day)
            
            if condition.status == ConditionStatus.ACHIEVED:
                results["conditions_achieved"] += 1
                self.achieved_conditions.append(condition)
                results["achieved_conditions"].append(condition.to_dict())
                
                # Check if this is a winning condition
                if condition.condition_type in [ConditionType.ECONOMIC, ConditionType.POLITICAL, 
                                              ConditionType.SOCIAL] and condition.priority >= 5:
                    results["game_won"] = True
                    
            elif condition.status == ConditionStatus.FAILED:
                results["conditions_failed"] += 1
                self.failed_conditions.append(condition)
                results["failed_conditions"].append(condition.to_dict())
                
                # Check if this is a losing condition
                if condition.condition_type == ConditionType.SURVIVAL and condition.priority >= 5:
                    results["game_lost"] = True
                    
            elif condition.status == ConditionStatus.EXPIRED:
                results["conditions_expired"] += 1
                results["failed_conditions"].append(condition.to_dict())
                
            else:
                # Still active
                results["active_conditions"].append(condition.to_dict())
        
        return results
    
    def get_condition_summary(self) -> Dict[str, Any]:
        """Get summary of all conditions."""
        active = [c for c in self.conditions.values() if c.status == ConditionStatus.ACTIVE]
        achieved = [c for c in self.conditions.values() if c.status == ConditionStatus.ACHIEVED]
        failed = [c for c in self.conditions.values() if c.status == ConditionStatus.FAILED]
        expired = [c for c in self.conditions.values() if c.status == ConditionStatus.EXPIRED]
        
        return {
            "total_conditions": len(self.conditions),
            "active_conditions": len(active),
            "achieved_conditions": len(achieved),
            "failed_conditions": len(failed),
            "expired_conditions": len(expired),
            "conditions": {
                "active": [c.to_dict() for c in active],
                "achieved": [c.to_dict() for c in achieved],
                "failed": [c.to_dict() for c in failed],
                "expired": [c.to_dict() for c in expired]
            }
        }
    
    def create_standard_scenarios(self) -> Dict[str, List[WinCondition]]:
        """Create standard win condition scenarios."""
        scenarios = {}
        
        # Economic Victory Scenario
        scenarios["economic_dominance"] = [
            WinCondition(
                condition_id="settlement_population_5000",
                name="Population Growth",
                description="Achieve a total population of 5000 across all settlements",
                condition_type=ConditionType.ECONOMIC,
                target_value=5000,
                comparison_operator=">=",
                priority=5
            ),
            WinCondition(
                condition_id="total_wealth_50000",
                name="Economic Prosperity",
                description="Accumulate wealth worth 50,000 resource points",
                condition_type=ConditionType.ECONOMIC,
                target_value=50000,
                comparison_operator=">=",
                priority=6
            )
        ]
        
        # Political Victory Scenario
        scenarios["political_conquest"] = [
            WinCondition(
                condition_id="settlements_controlled_5",
                name="Territorial Control",
                description="Control at least 5 settlements",
                condition_type=ConditionType.POLITICAL,
                target_value=5,
                comparison_operator=">=",
                priority=5
            ),
            WinCondition(
                condition_id="faction_influence_80",
                name="Political Dominance",
                description="Achieve faction influence of 80 or higher",
                condition_type=ConditionType.POLITICAL,
                target_value=80,
                comparison_operator=">=",
                priority=6
            )
        ]
        
        # Survival Scenario
        scenarios["survival_challenge"] = [
            WinCondition(
                condition_id="time_survived_100",
                name="Century of Survival",
                description="Survive for 100 simulation days",
                condition_type=ConditionType.TEMPORAL,
                target_value=100,
                comparison_operator=">=",
                time_limit_days=100,
                priority=5
            ),
            WinCondition(
                condition_id="npcs_alive_10",
                name="Population Survival",
                description="Keep at least 10 NPCs alive",
                condition_type=ConditionType.SURVIVAL,
                target_value=10,
                comparison_operator=">=",
                priority=8  # High priority loss condition
            )
        ]
        
        return scenarios
    
    def load_scenario(self, scenario_name: str, current_day: int = 0) -> bool:
        """Load a predefined scenario."""
        scenarios = self.create_standard_scenarios()
        
        if scenario_name not in scenarios:
            self.logger.error(f"Unknown scenario: {scenario_name}")
            return False
        
        # Clear existing conditions
        self.conditions.clear()
        self.achieved_conditions.clear()
        self.failed_conditions.clear()
        
        # Add scenario conditions
        for condition in scenarios[scenario_name]:
            self.add_condition(condition, current_day)
        
        self.logger.info(f"Loaded scenario '{scenario_name}' with {len(scenarios[scenario_name])} conditions")
        return True
    
    def export_conditions(self) -> str:
        """Export all conditions to JSON."""
        conditions_data = {
            "conditions": [c.to_dict() for c in self.conditions.values()],
            "achieved": [c.to_dict() for c in self.achieved_conditions],
            "failed": [c.to_dict() for c in self.failed_conditions]
        }
        return json.dumps(conditions_data, indent=2, default=str)
    
    def import_conditions(self, json_data: str, current_day: int = 0) -> bool:
        """Import conditions from JSON."""
        try:
            data = json.loads(json_data)
            
            # Clear existing
            self.conditions.clear()
            
            # Import conditions
            for cond_data in data.get("conditions", []):
                condition = WinCondition(
                    condition_id=cond_data["condition_id"],
                    name=cond_data["name"],
                    description=cond_data["description"],
                    condition_type=ConditionType(cond_data["condition_type"]),
                    target_value=cond_data["target_value"],
                    comparison_operator=cond_data["comparison_operator"],
                    time_limit_days=cond_data.get("time_limit_days"),
                    required_factions=cond_data.get("required_factions"),
                    required_settlements=cond_data.get("required_settlements"),
                    status=ConditionStatus(cond_data["status"]),
                    current_value=cond_data.get("current_value", 0),
                    progress_percentage=cond_data.get("progress_percentage", 0.0),
                    created_day=cond_data.get("created_day", current_day),
                    achieved_day=cond_data.get("achieved_day"),
                    priority=cond_data.get("priority", 1)
                )
                self.conditions[condition.condition_id] = condition
                
            self.logger.info(f"Imported {len(self.conditions)} win conditions")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import conditions: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    print("=== Win Condition System Test ===")
    
    # Create manager
    win_manager = WinConditionManager()
    
    # Load economic scenario
    print("Loading economic dominance scenario...")
    win_manager.load_scenario("economic_dominance")
    
    # Create mock world state
    mock_world_state = {
        "settlements": [
            {
                "name": "Riverside",
                "population": 2000,
                "is_active": True,
                "resources": {
                    "food": {"stockpile": 500},
                    "ore": {"stockpile": 200},
                    "luxury": {"stockpile": 50}
                }
            },
            {
                "name": "Millbrook", 
                "population": 1500,
                "is_active": True,
                "resources": {
                    "food": {"stockpile": 300},
                    "tools": {"stockpile": 100}
                }
            }
        ],
        "factions": [
            {"name": "Merchants Guild", "influence": 75},
            {"name": "City Watch", "influence": 60}
        ],
        "npcs": [
            {"id": "npc1", "is_active": True},
            {"id": "npc2", "is_active": True},
            {"id": "npc3", "is_active": False}
        ],
        "justice": {"total_cases": 15}
    }
    
    # Evaluate conditions
    print("\nEvaluating conditions on day 50...")
    results = win_manager.evaluate_all_conditions(mock_world_state, 50)
    
    print(f"Conditions evaluated: {results['conditions_evaluated']}")
    print(f"Conditions achieved: {results['conditions_achieved']}")
    print(f"Game won: {results['game_won']}")
    
    # Show active conditions with progress
    print("\nActive conditions:")
    for condition in results['active_conditions']:
        print(f"  {condition['name']}: {condition['progress_percentage']:.1f}% "
              f"({condition['current_value']}/{condition['target_value']})")
    
    # Test survival scenario
    print("\n" + "="*50)
    print("Testing survival scenario...")
    win_manager.load_scenario("survival_challenge")
    
    # Simulate low population crisis
    crisis_state = mock_world_state.copy()
    crisis_state['npcs'] = [{"id": "npc1", "is_active": True}]  # Only 1 survivor
    
    results = win_manager.evaluate_all_conditions(crisis_state, 75)
    print(f"Game lost due to population crisis: {results['game_lost']}")
    
    # Export conditions
    print("\nExporting conditions...")
    exported = win_manager.export_conditions()
    print(f"Export size: {len(exported)} characters")
    
    print("\nWin Condition System test complete!")