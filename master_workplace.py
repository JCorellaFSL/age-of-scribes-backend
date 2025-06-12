"""
Master Workplace System for Age of Scribes Social Simulation Engine

This module provides the MasterWorkplace class that manages guild hiring behavior,
economic scaling, and workplace dynamics. It integrates with the guild system to
create realistic employment patterns based on settlement economics, moral profiles,
and labor oversight.

Key Features:
- Economic-based hiring capacity calculation
- Moral profile system affecting hiring decisions
- Labor oversight with abuse detection
- Integration with LocalGuild hiring mechanics
- Dynamic capacity adjustment based on settlement conditions

Author: Age of Scribes Development Team
Version: 0.0.6.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MasterWorkplace:
    """
    Represents a master craftsman's workplace within a guild system.
    
    Manages hiring capacity, employee relationships, and workplace dynamics
    based on economic conditions and moral profiles.
    """
    
    # Core identification
    owner_id: str                                    # NPC ID of the master craftsman
    guild_id: str                                   # Associated guild identifier
    
    # Economic and capacity metrics
    economic_score: float = 0.5                     # Settlement economic factor (0.0-1.0)
    max_journeymen: int = 2                         # Maximum journeymen capacity
    max_apprentices: int = 3                        # Maximum apprentices capacity
    
    # Current employment
    employed_journeymen: List[str] = field(default_factory=list)  # NPC IDs of employed journeymen
    employed_apprentices: List[str] = field(default_factory=list) # NPC IDs of employed apprentices
    
    # Moral and behavioral profile
    moral_profile: Dict[str, float] = field(default_factory=lambda: {
        "bribable": 0.3,      # Susceptibility to corruption (0.0-1.0)
        "rigid": 0.4,         # Adherence to rules and procedures (0.0-1.0)
        "pragmatic": 0.6      # Practical decision-making over idealism (0.0-1.0)
    })
    
    # Labor oversight flags
    labor_flags: Dict[str, bool] = field(default_factory=lambda: {
        "abuse_detected": False,    # Overhiring beyond reasonable capacity
        "favoritism": False,        # Preferential hiring of family/allies
        "audit_risk": False         # High risk of guild oversight intervention
    })
    
    # Internal tracking
    _last_capacity_update: int = 0                  # Day of last capacity calculation
    _guild_saturation_cache: float = 0.0           # Cached guild saturation value
    
    def __post_init__(self):
        """Initialize workplace with validation and setup."""
        self._validate_moral_profile()
        self._initialize_capacity()
        logger.info(f"MasterWorkplace created for owner {self.owner_id} in guild {self.guild_id}")
    
    def _validate_moral_profile(self) -> None:
        """Ensure moral profile values are within valid ranges."""
        for trait, value in self.moral_profile.items():
            if not 0.0 <= value <= 1.0:
                logger.warning(f"Invalid moral profile value for {trait}: {value}. Clamping to valid range.")
                self.moral_profile[trait] = max(0.0, min(1.0, value))
    
    def _initialize_capacity(self) -> None:
        """Set initial hiring capacity based on economic score."""
        base_journeymen = max(1, int(self.economic_score * 4))  # 1-4 journeymen
        base_apprentices = max(2, int(self.economic_score * 6)) # 2-6 apprentices
        
        self.max_journeymen = base_journeymen
        self.max_apprentices = base_apprentices
    
    def update_hiring_capacity(self, settlement: Any, guild_members: Optional[Dict[str, List[str]]] = None) -> None:
        """
        Recalculate hiring capacity based on settlement economics and guild saturation.
        
        Args:
            settlement: Settlement object with economic data
            guild_members: Optional dict of guild member lists by sub-guild
        """
        try:
            # Update economic score from settlement
            self._update_economic_score(settlement)
            
            # Calculate guild saturation if member data provided
            if guild_members:
                self._calculate_guild_saturation(guild_members)
            
            # Recalculate base capacity
            self._recalculate_base_capacity()
            
            # Apply moral profile modifiers
            self._apply_moral_modifiers()
            
            # Apply guild saturation effects
            self._apply_saturation_effects()
            
            logger.debug(f"Updated capacity for {self.owner_id}: {self.max_journeymen}J, {self.max_apprentices}A")
            
        except Exception as e:
            logger.error(f"Error updating hiring capacity for {self.owner_id}: {e}")
    
    def _update_economic_score(self, settlement: Any) -> None:
        """Extract economic score from settlement data."""
        try:
            # Try to get economic prosperity or stability
            if hasattr(settlement, 'economic_prosperity'):
                self.economic_score = max(0.1, min(1.0, settlement.economic_prosperity))
            elif hasattr(settlement, 'stability_score'):
                self.economic_score = max(0.1, min(1.0, settlement.stability_score / 100.0))
            else:
                # Fallback to resource-based calculation
                self.economic_score = self._calculate_resource_based_score(settlement)
                
        except Exception as e:
            logger.warning(f"Could not update economic score: {e}. Using default.")
            self.economic_score = 0.5
    
    def _calculate_resource_based_score(self, settlement: Any) -> float:
        """Calculate economic score based on settlement resources."""
        try:
            if hasattr(settlement, 'resources'):
                total_resources = 0
                resource_count = 0
                
                for resource_data in settlement.resources.values():
                    if hasattr(resource_data, 'stockpile'):
                        total_resources += resource_data.stockpile
                        resource_count += 1
                
                if resource_count > 0:
                    avg_resources = total_resources / resource_count
                    # Normalize to 0.1-1.0 range (assuming 100 is good stockpile)
                    return max(0.1, min(1.0, avg_resources / 100.0))
            
            return 0.5  # Default middle value
            
        except Exception:
            return 0.5
    
    def _calculate_guild_saturation(self, guild_members: Dict[str, List[str]]) -> None:
        """Calculate how saturated the guild is with members."""
        try:
            # Get members in same guild/sub-guild
            same_guild_members = guild_members.get(self.guild_id, [])
            total_members = len(same_guild_members)
            
            # Estimate ideal member count (rough heuristic)
            ideal_members = max(10, int(self.economic_score * 50))
            
            self._guild_saturation_cache = min(2.0, total_members / ideal_members)
            
        except Exception as e:
            logger.warning(f"Could not calculate guild saturation: {e}")
            self._guild_saturation_cache = 1.0
    
    def _recalculate_base_capacity(self) -> None:
        """Recalculate base hiring capacity from economic score."""
        # Economic score affects capacity (0.1-1.0 → 1-5 scale)
        economic_multiplier = 0.5 + (self.economic_score * 4.5)
        
        self.max_journeymen = max(1, int(economic_multiplier * 0.8))  # 1-4 journeymen
        self.max_apprentices = max(2, int(economic_multiplier * 1.2)) # 2-6 apprentices
    
    def _apply_moral_modifiers(self) -> None:
        """Apply moral profile modifiers to hiring capacity."""
        # Pragmatic masters hire more efficiently
        pragmatic_bonus = int(self.moral_profile["pragmatic"] * 2)
        
        # Rigid masters may limit capacity to avoid rule violations
        rigid_penalty = int(self.moral_profile["rigid"] * 1.5)
        
        # Bribable masters might overhire if profitable
        bribable_bonus = int(self.moral_profile["bribable"] * 1.5)
        
        self.max_journeymen += pragmatic_bonus + bribable_bonus - rigid_penalty
        self.max_apprentices += pragmatic_bonus + bribable_bonus - rigid_penalty
        
        # Ensure minimum capacity
        self.max_journeymen = max(1, self.max_journeymen)
        self.max_apprentices = max(1, self.max_apprentices)
    
    def _apply_saturation_effects(self) -> None:
        """Apply guild saturation effects to capacity."""
        if self._guild_saturation_cache > 1.5:
            # Oversaturated guild - reduce capacity
            reduction = int((self._guild_saturation_cache - 1.0) * 2)
            self.max_journeymen = max(1, self.max_journeymen - reduction)
            self.max_apprentices = max(1, self.max_apprentices - reduction)
        elif self._guild_saturation_cache < 0.7:
            # Undersaturated guild - increase capacity
            bonus = int((0.7 - self._guild_saturation_cache) * 3)
            self.max_journeymen += bonus
            self.max_apprentices += bonus
    
    def evaluate_flags(self, npc_relationships: Optional[Dict[str, Any]] = None) -> None:
        """
        Evaluate and set labor oversight flags based on current conditions.
        
        Args:
            npc_relationships: Optional NPC relationship data for favoritism detection
        """
        try:
            self._evaluate_abuse_flag()
            self._evaluate_favoritism_flag(npc_relationships)
            self._evaluate_audit_risk_flag()
            
            logger.debug(f"Flags evaluated for {self.owner_id}: {self.labor_flags}")
            
        except Exception as e:
            logger.error(f"Error evaluating flags for {self.owner_id}: {e}")
    
    def _evaluate_abuse_flag(self) -> None:
        """Check for labor abuse through overhiring."""
        # Calculate expected capacity (base economic capacity)
        expected_journeymen = max(1, int(self.economic_score * 3))
        expected_apprentices = max(2, int(self.economic_score * 4))
        
        # Check if current employment exceeds 150% of expected
        journeymen_overhire = len(self.employed_journeymen) > (expected_journeymen * 1.5)
        apprentice_overhire = len(self.employed_apprentices) > (expected_apprentices * 1.5)
        
        self.labor_flags["abuse_detected"] = journeymen_overhire or apprentice_overhire
    
    def _evaluate_favoritism_flag(self, npc_relationships: Optional[Dict[str, Any]]) -> None:
        """Check for favoritism in hiring practices."""
        if not npc_relationships:
            self.labor_flags["favoritism"] = False
            return
        
        try:
            total_employees = len(self.employed_journeymen) + len(self.employed_apprentices)
            if total_employees == 0:
                self.labor_flags["favoritism"] = False
                return
            
            # Count family members and close allies
            family_and_allies = 0
            
            for employee_id in self.employed_journeymen + self.employed_apprentices:
                if self._is_family_or_ally(employee_id, npc_relationships):
                    family_and_allies += 1
            
            # Flag if >50% are family/allies
            favoritism_ratio = family_and_allies / total_employees
            self.labor_flags["favoritism"] = favoritism_ratio > 0.5
            
        except Exception as e:
            logger.warning(f"Could not evaluate favoritism: {e}")
            self.labor_flags["favoritism"] = False
    
    def _is_family_or_ally(self, employee_id: str, npc_relationships: Dict[str, Any]) -> bool:
        """Check if an employee is family or close ally of the owner."""
        try:
            # Check for family relationship
            owner_relationships = npc_relationships.get(self.owner_id, {})
            employee_trust = owner_relationships.get(employee_id, 0.0)
            
            # High trust (>0.8) indicates family or close ally
            return employee_trust > 0.8
            
        except Exception:
            return False
    
    def _evaluate_audit_risk_flag(self) -> None:
        """Check if workplace is at risk of guild audit."""
        # High bribability + favoritism = audit risk
        high_bribability = self.moral_profile["bribable"] > 0.6
        has_favoritism = self.labor_flags["favoritism"]
        has_abuse = self.labor_flags["abuse_detected"]
        
        self.labor_flags["audit_risk"] = high_bribability and (has_favoritism or has_abuse)
    
    def get_available_positions(self) -> Dict[str, int]:
        """Get number of available positions by type."""
        return {
            "journeymen": max(0, self.max_journeymen - len(self.employed_journeymen)),
            "apprentices": max(0, self.max_apprentices - len(self.employed_apprentices))
        }
    
    def can_hire(self, position_type: str) -> bool:
        """Check if workplace can hire for a specific position type."""
        available = self.get_available_positions()
        return available.get(position_type, 0) > 0
    
    def hire_employee(self, employee_id: str, position_type: str) -> bool:
        """
        Hire an employee to the workplace.
        
        Args:
            employee_id: NPC ID to hire
            position_type: "journeyman" or "apprentice"
            
        Returns:
            bool: True if hiring successful, False otherwise
        """
        try:
            if position_type == "journeyman" and self.can_hire("journeymen"):
                if employee_id not in self.employed_journeymen:
                    self.employed_journeymen.append(employee_id)
                    logger.info(f"Hired journeyman {employee_id} at workplace {self.owner_id}")
                    return True
            elif position_type == "apprentice" and self.can_hire("apprentices"):
                if employee_id not in self.employed_apprentices:
                    self.employed_apprentices.append(employee_id)
                    logger.info(f"Hired apprentice {employee_id} at workplace {self.owner_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error hiring {employee_id} as {position_type}: {e}")
            return False
    
    def fire_employee(self, employee_id: str) -> bool:
        """
        Fire an employee from the workplace.
        
        Args:
            employee_id: NPC ID to fire
            
        Returns:
            bool: True if firing successful, False if employee not found
        """
        try:
            if employee_id in self.employed_journeymen:
                self.employed_journeymen.remove(employee_id)
                logger.info(f"Fired journeyman {employee_id} from workplace {self.owner_id}")
                return True
            elif employee_id in self.employed_apprentices:
                self.employed_apprentices.remove(employee_id)
                logger.info(f"Fired apprentice {employee_id} from workplace {self.owner_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error firing {employee_id}: {e}")
            return False
    
    def get_employment_statistics(self) -> Dict[str, Any]:
        """Get comprehensive employment statistics for the workplace."""
        available = self.get_available_positions()
        
        return {
            "owner_id": self.owner_id,
            "guild_id": self.guild_id,
            "economic_score": self.economic_score,
            "capacity": {
                "max_journeymen": self.max_journeymen,
                "max_apprentices": self.max_apprentices,
                "employed_journeymen": len(self.employed_journeymen),
                "employed_apprentices": len(self.employed_apprentices),
                "available_journeymen": available["journeymen"],
                "available_apprentices": available["apprentices"]
            },
            "utilization": {
                "journeymen_rate": len(self.employed_journeymen) / max(1, self.max_journeymen),
                "apprentice_rate": len(self.employed_apprentices) / max(1, self.max_apprentices),
                "total_rate": (len(self.employed_journeymen) + len(self.employed_apprentices)) / 
                             max(1, self.max_journeymen + self.max_apprentices)
            },
            "moral_profile": self.moral_profile.copy(),
            "labor_flags": self.labor_flags.copy(),
            "guild_saturation": self._guild_saturation_cache
        }
    
    def get_hiring_preference_score(self, candidate_id: str, npc_relationships: Optional[Dict[str, Any]] = None) -> float:
        """
        Calculate hiring preference score for a candidate.
        
        Args:
            candidate_id: NPC ID of hiring candidate
            npc_relationships: Optional relationship data
            
        Returns:
            float: Preference score (0.0-1.0, higher = more preferred)
        """
        try:
            base_score = 0.5  # Neutral starting point
            
            # Relationship bonus
            if npc_relationships:
                owner_relationships = npc_relationships.get(self.owner_id, {})
                relationship_score = owner_relationships.get(candidate_id, 0.0)
                
                # Convert trust (-1 to 1) to preference bonus (-0.3 to +0.3)
                relationship_bonus = relationship_score * 0.3
                base_score += relationship_bonus
            
            # Moral profile modifiers
            if self.moral_profile["bribable"] > 0.7:
                # Highly bribable masters prefer those who might offer benefits
                base_score += random.uniform(0.0, 0.2)
            
            if self.moral_profile["rigid"] > 0.7:
                # Rigid masters prefer predictable, rule-following candidates
                base_score += random.uniform(-0.1, 0.1)  # More neutral
            
            if self.moral_profile["pragmatic"] > 0.7:
                # Pragmatic masters focus on practical value
                base_score += random.uniform(0.0, 0.15)
            
            return max(0.0, min(1.0, base_score))
            
        except Exception as e:
            logger.warning(f"Error calculating preference score: {e}")
            return 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workplace to dictionary for serialization."""
        return {
            "owner_id": self.owner_id,
            "guild_id": self.guild_id,
            "economic_score": self.economic_score,
            "max_journeymen": self.max_journeymen,
            "max_apprentices": self.max_apprentices,
            "employed_journeymen": self.employed_journeymen.copy(),
            "employed_apprentices": self.employed_apprentices.copy(),
            "moral_profile": self.moral_profile.copy(),
            "labor_flags": self.labor_flags.copy(),
            "_guild_saturation_cache": self._guild_saturation_cache,
            "_last_capacity_update": self._last_capacity_update
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MasterWorkplace':
        """Create workplace from dictionary data."""
        workplace = cls(
            owner_id=data["owner_id"],
            guild_id=data["guild_id"],
            economic_score=data.get("economic_score", 0.5),
            max_journeymen=data.get("max_journeymen", 2),
            max_apprentices=data.get("max_apprentices", 3),
            employed_journeymen=data.get("employed_journeymen", []),
            employed_apprentices=data.get("employed_apprentices", []),
            moral_profile=data.get("moral_profile", {}),
            labor_flags=data.get("labor_flags", {})
        )
        
        # Restore cached values
        workplace._guild_saturation_cache = data.get("_guild_saturation_cache", 1.0)
        workplace._last_capacity_update = data.get("_last_capacity_update", 0)
        
        return workplace


class MasterWorkplaceManager:
    """
    Manages multiple MasterWorkplace instances and their interactions.
    
    Provides centralized management for workplace creation, updates,
    and integration with guild systems.
    """
    
    def __init__(self):
        self.workplaces: Dict[str, MasterWorkplace] = {}  # owner_id -> MasterWorkplace
        self.guild_workplaces: Dict[str, List[str]] = {}  # guild_id -> [owner_ids]
        
    def create_workplace(self, owner_id: str, guild_id: str, 
                        economic_score: float = 0.5,
                        moral_profile: Optional[Dict[str, float]] = None) -> MasterWorkplace:
        """Create a new master workplace."""
        if owner_id in self.workplaces:
            logger.warning(f"Workplace already exists for owner {owner_id}")
            return self.workplaces[owner_id]
        
        workplace = MasterWorkplace(
            owner_id=owner_id,
            guild_id=guild_id,
            economic_score=economic_score,
            moral_profile=moral_profile or {}
        )
        
        self.workplaces[owner_id] = workplace
        
        # Track by guild
        if guild_id not in self.guild_workplaces:
            self.guild_workplaces[guild_id] = []
        self.guild_workplaces[guild_id].append(owner_id)
        
        logger.info(f"Created workplace for {owner_id} in guild {guild_id}")
        return workplace
    
    def get_workplace(self, owner_id: str) -> Optional[MasterWorkplace]:
        """Get workplace by owner ID."""
        return self.workplaces.get(owner_id)
    
    def get_guild_workplaces(self, guild_id: str) -> List[MasterWorkplace]:
        """Get all workplaces in a specific guild."""
        owner_ids = self.guild_workplaces.get(guild_id, [])
        return [self.workplaces[owner_id] for owner_id in owner_ids if owner_id in self.workplaces]
    
    def update_all_capacities(self, settlement: Any, guild_members: Optional[Dict[str, List[str]]] = None) -> None:
        """Update hiring capacities for all workplaces."""
        for workplace in self.workplaces.values():
            workplace.update_hiring_capacity(settlement, guild_members)
    
    def evaluate_all_flags(self, npc_relationships: Optional[Dict[str, Any]] = None) -> None:
        """Evaluate labor flags for all workplaces."""
        for workplace in self.workplaces.values():
            workplace.evaluate_flags(npc_relationships)
    
    def get_hiring_opportunities(self, guild_id: Optional[str] = None) -> Dict[str, Dict[str, int]]:
        """Get available hiring opportunities across workplaces."""
        opportunities = {}
        
        workplaces_to_check = (
            self.get_guild_workplaces(guild_id) if guild_id 
            else self.workplaces.values()
        )
        
        for workplace in workplaces_to_check:
            available = workplace.get_available_positions()
            if available["journeymen"] > 0 or available["apprentices"] > 0:
                opportunities[workplace.owner_id] = available
        
        return opportunities
    
    def get_manager_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all managed workplaces."""
        total_workplaces = len(self.workplaces)
        guild_counts = {guild_id: len(owners) for guild_id, owners in self.guild_workplaces.items()}
        
        total_positions = {"journeymen": 0, "apprentices": 0}
        total_employed = {"journeymen": 0, "apprentices": 0}
        flag_counts = {"abuse_detected": 0, "favoritism": 0, "audit_risk": 0}
        
        for workplace in self.workplaces.values():
            stats = workplace.get_employment_statistics()
            
            total_positions["journeymen"] += stats["capacity"]["max_journeymen"]
            total_positions["apprentices"] += stats["capacity"]["max_apprentices"]
            total_employed["journeymen"] += stats["capacity"]["employed_journeymen"]
            total_employed["apprentices"] += stats["capacity"]["employed_apprentices"]
            
            for flag, active in stats["labor_flags"].items():
                if active:
                    flag_counts[flag] += 1
        
        return {
            "total_workplaces": total_workplaces,
            "guild_distribution": guild_counts,
            "employment_capacity": total_positions,
            "current_employment": total_employed,
            "utilization_rates": {
                "journeymen": total_employed["journeymen"] / max(1, total_positions["journeymen"]),
                "apprentices": total_employed["apprentices"] / max(1, total_positions["apprentices"])
            },
            "labor_violations": flag_counts
        }