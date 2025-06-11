"""
Guild Facilities & Holdings System for Age of Scribes
=====================================================

This module provides a comprehensive system for guild-controlled physical buildings
and operational sites. Guilds can construct, upgrade, and benefit from facilities
that provide economic bonuses, defensive value, and influence within settlements.

Key Features:
- GuildFacility class with location, status, and benefit tracking
- Construction and management functions
- Damage and capture mechanics during conflicts
- Settlement and guild integration for economic benefits
- PC interaction capabilities and quest generation
- Deep integration with existing guild, settlement, and faction systems

Author: Age of Scribes Development Team
"""

import uuid
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum

# Forward declarations for type checking
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from guild_event_engine import LocalGuild
    from settlement_system import Settlement
    from npc_profile import NPCProfile


class FacilityType(Enum):
    """Types of guild facilities with different purposes and benefits."""
    GUILDHALL = "guildhall"
    WORKSHOP = "workshop"
    WAREHOUSE = "warehouse"
    MARKET_STALL = "market_stall"
    TRAINING_GROUND = "training_ground"
    SHRINE = "shrine"
    SAFEHOUSE = "safehouse"
    ACADEMY = "academy"
    FORGE = "forge"
    SCRIPTORIUM = "scriptorium"


class FacilityStatus(Enum):
    """Current operational status of a facility."""
    ACTIVE = "active"
    DAMAGED = "damaged"
    ABANDONED = "abandoned"
    UNDER_SIEGE = "under_siege"
    CAPTURED = "captured"
    UNDER_CONSTRUCTION = "under_construction"
    RENOVATING = "renovating"


class GuildFacility:
    """
    Represents a physical building or facility controlled by a guild.
    
    Facilities provide various benefits to their owning guild including economic
    bonuses, defensive capabilities, reputation improvements, and special features
    that can be used for quests, training, and guild operations.
    """
    
    def __init__(self,
                 name: str,
                 facility_type: str,
                 location: Tuple[float, float],
                 owning_guild_id: str,
                 settlement_id: Optional[str] = None,
                 construction_year: int = 1000):
        """
        Initialize a new guild facility.
        
        Args:
            name: Display name of the facility
            facility_type: Type of facility (from FacilityType enum)
            location: World coordinates (x, y)
            owning_guild_id: ID of the guild that owns this facility
            settlement_id: ID of settlement containing this facility
            construction_year: Year when construction was completed
        """
        self.facility_id = str(uuid.uuid4())
        self.name = name
        self.location = location
        self.settlement_id = settlement_id
        self.facility_type = facility_type
        self.owning_guild_id = owning_guild_id
        self.status = FacilityStatus.ACTIVE.value
        self.construction_year = construction_year
        
        # Get template for this facility type
        template = self._get_facility_template()
        
        # Base attributes from template
        self.reputation_bonus = template["reputation_bonus"]
        self.economic_bonus = template["economic_bonus"].copy()
        self.defensive_value = template["defensive_value"]
        self.special_features = template["special_features"].copy()
        
        # Operational attributes
        self.condition = 100.0              # 0-100, affects efficiency
        self.current_capacity = 0           # Current occupants/workers
        self.max_capacity = template["max_capacity"]
        self.maintenance_cost = template["maintenance_cost"]
        self.accumulated_maintenance_debt = 0.0
        
        # History and tracking
        self.construction_events: List[Dict[str, Any]] = []
        self.operational_history: List[Dict[str, Any]] = []
        self.damage_events: List[Dict[str, Any]] = []
        self.occupants: List[str] = []      # NPC IDs currently using facility
        self.last_update = datetime.now()
        
        # Upgrades and modifications
        self.upgrades_installed: List[str] = []
        self.planned_upgrades: List[str] = []
        
        # Record construction
        self.construction_events.append({
            'event_type': 'construction_completed',
            'year': construction_year,
            'guild_id': owning_guild_id,
            'cost': template["base_cost"],
            'timestamp': datetime.now()
        })
    
    def _get_facility_template(self) -> Dict[str, Any]:
        """Get the template configuration for this facility type."""
        templates = {
            FacilityType.GUILDHALL.value: {
                "base_cost": 500.0,
                "construction_time": 60,
                "maintenance_cost": 5.0,
                "reputation_bonus": 10.0,
                "economic_bonus": {"administration": 0.15, "recruitment": 0.2},
                "defensive_value": 25.0,
                "max_capacity": 50,
                "special_features": ["meeting_hall", "guild_records", "ceremonial_chamber"]
            },
            FacilityType.WORKSHOP.value: {
                "base_cost": 200.0,
                "construction_time": 30,
                "maintenance_cost": 2.0,
                "reputation_bonus": 5.0,
                "economic_bonus": {"crafting": 0.25, "production_efficiency": 0.15},
                "defensive_value": 5.0,
                "max_capacity": 15,
                "special_features": ["specialized_tools", "materials_storage"]
            },
            FacilityType.WAREHOUSE.value: {
                "base_cost": 300.0,
                "construction_time": 45,
                "maintenance_cost": 3.0,
                "reputation_bonus": 3.0,
                "economic_bonus": {"storage_capacity": 0.4, "trade_efficiency": 0.1},
                "defensive_value": 15.0,
                "max_capacity": 5,
                "special_features": ["secure_storage", "loading_dock"]
            },
            FacilityType.MARKET_STALL.value: {
                "base_cost": 100.0,
                "construction_time": 14,
                "maintenance_cost": 1.0,
                "reputation_bonus": 2.0,
                "economic_bonus": {"trade_volume": 0.15, "customer_relations": 0.1},
                "defensive_value": 2.0,
                "max_capacity": 3,
                "special_features": ["display_area", "cash_box"]
            },
            FacilityType.TRAINING_GROUND.value: {
                "base_cost": 250.0,
                "construction_time": 40,
                "maintenance_cost": 2.5,
                "reputation_bonus": 7.0,
                "economic_bonus": {"training_efficiency": 0.3, "skill_development": 0.2},
                "defensive_value": 20.0,
                "max_capacity": 20,
                "special_features": ["practice_weapons", "obstacle_course"]
            },
            FacilityType.ACADEMY.value: {
                "base_cost": 800.0,
                "construction_time": 90,
                "maintenance_cost": 8.0,
                "reputation_bonus": 15.0,
                "economic_bonus": {"education": 0.4, "research": 0.25, "knowledge_preservation": 0.3},
                "defensive_value": 10.0,
                "max_capacity": 100,
                "special_features": ["library", "lecture_halls", "laboratories"]
            },
            FacilityType.FORGE.value: {
                "base_cost": 350.0,
                "construction_time": 50,
                "maintenance_cost": 4.0,
                "reputation_bonus": 6.0,
                "economic_bonus": {"metalworking": 0.35, "weapon_crafting": 0.25},
                "defensive_value": 8.0,
                "max_capacity": 12,
                "special_features": ["master_anvil", "quenching_pools", "bellows_system"]
            },
            FacilityType.SCRIPTORIUM.value: {
                "base_cost": 400.0,
                "construction_time": 55,
                "maintenance_cost": 3.5,
                "reputation_bonus": 8.0,
                "economic_bonus": {"scholarly_work": 0.3, "record_keeping": 0.2, "magical_scribing": 0.15},
                "defensive_value": 5.0,
                "max_capacity": 25,
                "special_features": ["rare_inks", "binding_equipment", "illumination_station"]
            }
        }
        
        return templates.get(self.facility_type, {
            "base_cost": 100.0,
            "construction_time": 20,
            "maintenance_cost": 1.0,
            "reputation_bonus": 1.0,
            "economic_bonus": {},
            "defensive_value": 0.0,
            "max_capacity": 10,
            "special_features": []
        })
    
    def calculate_effective_bonuses(self) -> Dict[str, float]:
        """
        Calculate current effective bonuses considering condition and status.
        
        Returns:
            Dictionary of bonus categories and their effective values
        """
        if self.status not in [FacilityStatus.ACTIVE.value, FacilityStatus.RENOVATING.value]:
            return {}  # No bonuses if not operational
        
        # Base efficiency from condition
        condition_multiplier = self.condition / 100.0
        
        # Status modifiers
        status_multipliers = {
            FacilityStatus.ACTIVE.value: 1.0,
            FacilityStatus.DAMAGED.value: 0.5,
            FacilityStatus.RENOVATING.value: 0.3,
            FacilityStatus.UNDER_SIEGE.value: 0.1,
            FacilityStatus.CAPTURED.value: 0.0,
            FacilityStatus.ABANDONED.value: 0.0
        }
        
        status_multiplier = status_multipliers.get(self.status, 0.0)
        
        # Calculate effective bonuses
        effective_bonuses = {}
        for bonus_type, base_value in self.economic_bonus.items():
            effective_value = base_value * condition_multiplier * status_multiplier
            if effective_value > 0:
                effective_bonuses[bonus_type] = effective_value
        
        return effective_bonuses
    
    def apply_damage(self, damage_amount: float, damage_source: str, attacker_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Apply damage to the facility.
        
        Args:
            damage_amount: Amount of damage (0-100)
            damage_source: Source of damage (e.g., "siege", "fire", "neglect")
            attacker_id: ID of attacking faction/guild if applicable
            
        Returns:
            Dictionary describing damage results
        """
        old_condition = self.condition
        old_status = self.status
        
        self.condition = max(0.0, self.condition - damage_amount)
        
        # Update status based on condition
        if self.condition <= 0:
            self.status = FacilityStatus.ABANDONED.value
        elif self.condition <= 25:
            self.status = FacilityStatus.DAMAGED.value
        elif self.status == FacilityStatus.DAMAGED.value and self.condition > 50:
            self.status = FacilityStatus.ACTIVE.value
        
        # Record damage event
        damage_event = {
            'timestamp': datetime.now(),
            'damage_amount': damage_amount,
            'damage_source': damage_source,
            'attacker_id': attacker_id,
            'condition_before': old_condition,
            'condition_after': self.condition,
            'status_before': old_status,
            'status_after': self.status
        }
        self.damage_events.append(damage_event)
        
        # Determine consequences
        consequences = []
        if old_status != self.status:
            consequences.append(f"status_changed_to_{self.status}")
        
        if self.status == FacilityStatus.ABANDONED.value:
            consequences.extend(["facility_abandoned", "all_bonuses_lost"])
            self.occupants.clear()  # Everyone evacuates
        elif self.status == FacilityStatus.DAMAGED.value:
            consequences.append("reduced_efficiency")
            # Some occupants may flee
            if len(self.occupants) > 0:
                flee_count = min(len(self.occupants), max(1, int(damage_amount / 20)))
                for _ in range(flee_count):
                    if self.occupants:
                        self.occupants.pop()
                if flee_count > 0:
                    consequences.append(f"{flee_count}_occupants_fled")
        
        return {
            'facility_id': self.facility_id,
            'damage_applied': damage_amount,
            'condition_change': self.condition - old_condition,
            'new_condition': self.condition,
            'status_change': old_status != self.status,
            'new_status': self.status,
            'consequences': consequences,
            'damage_event': damage_event
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive facility information."""
        return {
            'facility_id': self.facility_id,
            'name': self.name,
            'facility_type': self.facility_type,
            'owning_guild_id': self.owning_guild_id,
            'settlement_id': self.settlement_id,
            'location': self.location,
            'status': self.status,
            'condition': round(self.condition, 1),
            'construction_year': self.construction_year,
            'reputation_bonus': round(self.reputation_bonus, 1),
            'economic_bonus': self.economic_bonus,
            'effective_bonuses': self.calculate_effective_bonuses(),
            'defensive_value': self.defensive_value,
            'special_features': self.special_features,
            'current_capacity': self.current_capacity,
            'max_capacity': self.max_capacity,
            'occupant_count': len(self.occupants),
            'maintenance_cost': self.maintenance_cost,
            'maintenance_debt': round(self.accumulated_maintenance_debt, 2),
            'upgrades_installed': self.upgrades_installed,
            'last_update': self.last_update.isoformat()
        }


def construct_guild_facility(guild: 'LocalGuild', 
                           facility_type: str, 
                           name: str,
                           location: Tuple[float, float], 
                           settlement: 'Settlement', 
                           year: int) -> GuildFacility:
    """
    Construct a new guild facility.
    
    Args:
        guild: Guild that will own the facility
        facility_type: Type of facility to construct
        name: Name for the new facility
        location: World coordinates for facility placement
        settlement: Settlement where facility will be built
        year: Current game year
        
    Returns:
        Newly constructed GuildFacility object
    """
    # Create the facility
    facility = GuildFacility(
        name=name,
        facility_type=facility_type,
        location=location,
        owning_guild_id=guild.guild_id,
        settlement_id=settlement.name,  # Using settlement name as ID
        construction_year=year
    )
    
    # Add facility to guild's holdings
    if not hasattr(guild, 'facilities'):
        guild.facilities = []
    guild.facilities.append(facility.facility_id)
    
    # Set as headquarters if it's the first guildhall
    if facility_type == FacilityType.GUILDHALL.value:
        if not hasattr(guild, 'headquarters') or guild.headquarters is None:
            guild.headquarters = facility.facility_id
    
    # Apply settlement benefits
    settlement.modify_reputation(guild.guild_id, facility.reputation_bonus)
    
    # Record construction in guild history
    guild.historical_events.append({
        'type': 'facility_constructed',
        'facility_id': facility.facility_id,
        'facility_name': name,
        'facility_type': facility_type,
        'settlement': settlement.name,
        'year': year,
        'timestamp': datetime.now()
    })
    
    return facility


def damage_or_capture_facility(facility: GuildFacility, 
                             by_faction_or_guild: str,
                             action_type: str = "damage",
                             damage_amount: float = 50.0) -> Dict[str, Any]:
    """
    Damage or capture a guild facility during conflicts.
    
    Args:
        facility: Facility to affect
        by_faction_or_guild: ID of attacking faction or guild
        action_type: "damage", "capture", or "siege"
        damage_amount: Amount of damage to apply (for damage/siege actions)
        
    Returns:
        Dictionary describing the action results and consequences
    """
    results = {
        'facility_id': facility.facility_id,
        'action_type': action_type,
        'attacker_id': by_faction_or_guild,
        'consequences': [],
        'guild_effects': {},
        'settlement_effects': {}
    }
    
    if action_type == "damage":
        # Apply damage to facility
        damage_result = facility.apply_damage(
            damage_amount=damage_amount,
            damage_source="hostile_action",
            attacker_id=by_faction_or_guild
        )
        results.update(damage_result)
        results['consequences'].extend(damage_result['consequences'])
        
    elif action_type == "capture":
        # Change ownership to attacking faction/guild
        facility.owning_guild_id = by_faction_or_guild
        results['consequences'].append("facility_captured")
        results['new_owner'] = by_faction_or_guild
        
    elif action_type == "siege":
        # Set facility under siege and apply moderate damage
        facility.status = FacilityStatus.UNDER_SIEGE.value
        damage_result = facility.apply_damage(
            damage_amount=damage_amount * 0.5,  # Reduced damage during siege
            damage_source="siege",
            attacker_id=by_faction_or_guild
        )
        results.update(damage_result)
        results['consequences'].append("facility_under_siege")
    
    # Guild consequences
    owning_guild_effects = {
        'reputation_loss': -10.0,
        'member_loyalty_loss': -5.0,
        'stability_loss': -8.0
    }
    
    if action_type == "capture":
        owning_guild_effects['reputation_loss'] = -20.0
        owning_guild_effects['member_loyalty_loss'] = -10.0
        owning_guild_effects['facility_lost'] = facility.facility_id
    
    results['guild_effects'] = owning_guild_effects
    
    # Settlement consequences
    settlement_effects = {
        'stability_loss': -3.0,
        'reputation_change': {facility.owning_guild_id: -5.0}
    }
    
    if action_type == "capture":
        settlement_effects['stability_loss'] = -8.0
        settlement_effects['new_guild_presence'] = by_faction_or_guild
    
    results['settlement_effects'] = settlement_effects
    
    # Record diplomatic consequences
    if action_type in ["damage", "capture"]:
        results['consequences'].append(f"diplomatic_incident_with_{by_faction_or_guild}")
    
    return results


def evaluate_facility_impact(settlement: 'Settlement', guild: 'LocalGuild') -> Dict[str, float]:
    """
    Calculate cumulative impact of all guild facilities in a settlement.
    
    Args:
        settlement: Settlement to evaluate
        guild: Guild whose facilities to assess
        
    Returns:
        Dictionary of cumulative bonuses and impacts
    """
    if not hasattr(guild, 'facilities') or not guild.facilities:
        return {}
    
    cumulative_bonuses = {
        'reputation_bonus': 0.0,
        'economic_multipliers': {},
        'defensive_value': 0.0,
        'settlement_capacity_bonus': 0,
        'trade_efficiency': 0.0,
        'recruitment_bonus': 0.0
    }
    
    # Apply guild stability cap
    stability_multiplier = min(1.0, guild.stability / 80.0)
    
    # Sample bonuses based on guild type and size
    base_facilities = max(1, guild.member_count // 10)  # Assume 1 facility per 10 members
    
    # Guild type specific bonuses
    guild_type_bonuses = {
        'merchants': {'trade_efficiency': 0.15, 'economic_multipliers': {'commerce': 0.2}},
        'craftsmen': {'economic_multipliers': {'production': 0.25, 'quality': 0.15}},
        'scholars': {'economic_multipliers': {'education': 0.3, 'research': 0.2}},
        'warriors': {'defensive_value': 20.0, 'recruitment_bonus': 0.2}
    }
    
    guild_type_str = guild.guild_type.value if hasattr(guild.guild_type, 'value') else str(guild.guild_type)
    type_bonuses = guild_type_bonuses.get(guild_type_str, {})
    
    # Apply bonuses with stability multiplier
    for bonus_type, base_value in type_bonuses.items():
        if bonus_type == 'economic_multipliers':
            cumulative_bonuses['economic_multipliers'].update({
                k: v * stability_multiplier * base_facilities
                for k, v in base_value.items()
            })
        else:
            cumulative_bonuses[bonus_type] = base_value * stability_multiplier * base_facilities
    
    # Base reputation bonus
    cumulative_bonuses['reputation_bonus'] = guild.settlement_reputation * 0.1 * stability_multiplier
    
    # Settlement capacity bonus (facilities allow more NPCs)
    cumulative_bonuses['settlement_capacity_bonus'] = base_facilities * 5
    
    return cumulative_bonuses


def get_facility_quest_opportunities(facility: GuildFacility) -> List[Dict[str, Any]]:
    """
    Generate potential quest opportunities related to a facility.
    
    Args:
        facility: Facility to generate quests for
        
    Returns:
        List of quest opportunity dictionaries
    """
    quest_opportunities = []
    
    # Condition-based quests
    if facility.condition < 50:
        quest_opportunities.append({
            'quest_type': 'facility_repair',
            'title': f"Repair the {facility.name}",
            'description': f"The {facility.name} has fallen into disrepair and needs restoration.",
            'objectives': [
                'Gather repair materials',
                'Hire skilled workers',
                'Complete facility repairs'
            ],
            'rewards': ['guild_reputation', 'facility_upgrade'],
            'difficulty': 'medium'
        })
    
    # Status-based quests
    if facility.status == FacilityStatus.UNDER_SIEGE.value:
        quest_opportunities.append({
            'quest_type': 'break_siege',
            'title': f"Break the Siege of {facility.name}",
            'description': f"Enemy forces have besieged the {facility.name}. Drive them off!",
            'objectives': [
                'Gather allies or mercenaries',
                'Assault the besieging forces',
                'Secure the facility'
            ],
            'rewards': ['hero_reputation', 'guild_favor', 'loot'],
            'difficulty': 'hard'
        })
    
    # Special feature quests
    if 'library' in facility.special_features:
        quest_opportunities.append({
            'quest_type': 'secret_knowledge',
            'title': f"Secrets of the {facility.name}",
            'description': f"Ancient knowledge lies hidden within the {facility.name}.",
            'objectives': [
                'Gain access to restricted areas',
                'Decode ancient texts',
                'Uncover the hidden secret'
            ],
            'rewards': ['ancient_knowledge', 'magical_item', 'skill_advancement'],
            'difficulty': 'hard'
        })
    
    # Capacity-based quests
    if facility.current_capacity < facility.max_capacity * 0.5:
        quest_opportunities.append({
            'quest_type': 'recruitment_drive',
            'title': f"Staff the {facility.name}",
            'description': f"The {facility.name} needs more workers to operate at full capacity.",
            'objectives': [
                'Recruit qualified NPCs',
                'Convince them to join the facility',
                'Train new workers'
            ],
            'rewards': ['facility_efficiency', 'guild_connections'],
            'difficulty': 'easy'
        })
    
    return quest_opportunities 