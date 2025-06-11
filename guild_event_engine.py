#!/usr/bin/env python3
"""
Guild Event Engine - Dynamic Guild Behavior System
=================================================

This module provides emergent behavior for trade guilds, professional organizations,
and merchant collectives, simulating power struggles, monopoly assertions, faction
alignments, and other dynamic guild activities that create narrative opportunities.

Key Features:
- LocalGuild and RegionalGuild classes with evolving behavior
- Dynamic event system for guild conflicts and changes
- Integration with existing faction and settlement systems
- Emergent narrative generation through guild interactions
"""

import uuid
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict
from enum import Enum

# Forward declaration to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from npc_profile import NPCProfile


class GuildType(Enum):
    """Types of guilds with different specializations and behaviors."""
    MERCHANTS = "merchants"
    CRAFTSMEN = "craftsmen"
    SCHOLARS = "scholars"
    WARRIORS = "warriors"
    THIEVES = "thieves"
    MAGES = "mages"


class ConflictStatus(Enum):
    """Current conflict status of a guild."""
    PEACEFUL = "peaceful"
    TENSIONS = "tensions"
    MINOR_DISPUTES = "minor_disputes"
    OPEN_CONFLICT = "open_conflict"
    UNDER_SIEGE = "under_siege"
    DISBANDED = "disbanded"


class GuildEvent:
    """
    Represents a dynamic event affecting guild behavior and influence.
    
    Events drive narrative opportunities and mechanical changes in guild systems.
    """
    
    def __init__(self,
                 event_id: Optional[str] = None,
                 guild_id: str = "",
                 event_type: str = "minor_dispute",
                 severity: float = 0.5,
                 duration: int = 7,
                 start_day: int = 0,
                 affected_regions: Optional[List[str]] = None,
                 faction_implications: Optional[Dict[str, str]] = None):
        """
        Initialize a guild event.
        
        Args:
            event_id: Unique identifier for the event
            guild_id: ID of the primary guild affected
            event_type: Type of event occurring
            severity: Intensity of the event (0.0-1.0)
            duration: Duration in days
            start_day: Day the event started
            affected_regions: List of regions affected by the event
            faction_implications: Faction relationship changes
        """
        self.event_id = event_id or str(uuid.uuid4())
        self.guild_id = guild_id
        self.event_type = event_type
        self.severity = max(0.0, min(1.0, severity))
        self.duration = max(1, duration)
        self.start_day = start_day
        self.affected_regions = affected_regions or []
        self.faction_implications = faction_implications or {}
        
        # Event state tracking
        self.days_remaining = duration
        self.active = True
        self.resolved = False
        self.resolution_outcome = None
        
        # Event metadata
        self.creation_timestamp = datetime.now()
        self.participants = []  # Other guilds involved
        self.narrative_tags = []  # For story generation
    
    def advance_day(self) -> Dict[str, Any]:
        """
        Advance the event by one day and return status update.
        
        Returns:
            Dictionary containing event progress information
        """
        if not self.active:
            return {'status': 'inactive', 'days_remaining': 0}
        
        self.days_remaining -= 1
        
        # Check if event should conclude
        if self.days_remaining <= 0:
            self.active = False
            self.resolved = True
            self.resolution_outcome = self._determine_resolution()
            
            return {
                'status': 'concluded',
                'outcome': self.resolution_outcome,
                'final_severity': self.severity
            }
        
        # Apply daily effects
        daily_effects = self._calculate_daily_effects()
        
        return {
            'status': 'ongoing',
            'days_remaining': self.days_remaining,
            'daily_effects': daily_effects,
            'severity': self.severity
        }
    
    def _determine_resolution(self) -> str:
        """Determine how the event resolves based on type and severity."""
        resolution_outcomes = {
            'power_struggle': ['leadership_change', 'compromise', 'schism', 'status_quo'],
            'monopoly_grab': ['monopoly_established', 'competition_emerges', 'government_intervention', 'market_collapse'],
            'faction_alignment_shift': ['new_alliance', 'neutrality_restored', 'deeper_conflict', 'faction_absorbed'],
            'regional_ban': ['ban_upheld', 'ban_overturned', 'underground_operations', 'guild_relocates'],
            'internal_collapse': ['reorganization', 'complete_dissolution', 'hostile_takeover', 'member_exodus'],
            'guild_war': ['decisive_victory', 'pyrrhic_victory', 'stalemate', 'mutual_destruction'],
            'charter_revoked': ['reinstatement', 'appeal_successful', 'permanent_ban', 'bribery_successful']
        }
        
        possible_outcomes = resolution_outcomes.get(self.event_type, ['status_quo', 'escalation', 'resolution'])
        
        # Weight outcomes based on severity
        if self.severity > 0.8:
            # High severity tends toward dramatic outcomes
            weights = [0.4, 0.2, 0.2, 0.2] if len(possible_outcomes) == 4 else [1.0]
        elif self.severity < 0.3:
            # Low severity tends toward mild outcomes
            weights = [0.2, 0.2, 0.2, 0.4] if len(possible_outcomes) == 4 else [1.0]
        else:
            # Moderate severity, equal weights
            weights = [1.0 / len(possible_outcomes)] * len(possible_outcomes)
        
        return random.choices(possible_outcomes, weights=weights)[0]
    
    def _calculate_daily_effects(self) -> Dict[str, float]:
        """Calculate daily mechanical effects of the ongoing event."""
        effects = {}
        
        # Base effects based on event type
        base_effects = {
            'power_struggle': {'influence_change': -0.5, 'stability_change': -1.0},
            'monopoly_grab': {'influence_change': 1.0, 'trade_efficiency': 0.5},
            'faction_alignment_shift': {'reputation_change': -0.3, 'influence_change': 0.2},
            'regional_ban': {'influence_change': -2.0, 'trade_efficiency': -1.5},
            'internal_collapse': {'influence_change': -1.5, 'stability_change': -2.0},
            'guild_war': {'influence_change': -0.8, 'member_loyalty': -1.0},
            'charter_revoked': {'influence_change': -3.0, 'trade_efficiency': -2.0}
        }
        
        event_effects = base_effects.get(self.event_type, {})
        
        # Scale by severity
        for effect, base_value in event_effects.items():
            effects[effect] = base_value * self.severity
        
        return effects
    
    def get_narrative_description(self) -> str:
        """Generate a narrative description of the event."""
        descriptions = {
            'power_struggle': f"Leadership crisis tears through the guild as rival factions vie for control",
            'monopoly_grab': f"The guild aggressively moves to dominate trade in their specialty",
            'faction_alignment_shift': f"Political winds shift as the guild reconsiders their loyalties",
            'regional_ban': f"Local authorities move to restrict or ban guild operations",
            'internal_collapse': f"Internal strife threatens to tear the guild apart from within",
            'guild_war': f"Open conflict erupts between rival guilds",
            'charter_revoked': f"Government officials formally revoke the guild's operating charter"
        }
        
        base_desc = descriptions.get(self.event_type, "The guild faces uncertain times")
        severity_modifier = "catastrophically" if self.severity > 0.8 else "significantly" if self.severity > 0.5 else "moderately"
        
        return f"{base_desc}, {severity_modifier} disrupting normal operations."


class LocalGuild:
    """
    Represents a local professional guild operating within a single settlement.
    
    Local guilds focus on specific trades or crafts and can evolve into regional
    powers through successful operations and political maneuvering.
    """
    
    def __init__(self,
                 guild_id: Optional[str] = None,
                 name: str = "Unnamed Guild",
                 guild_type: GuildType = GuildType.MERCHANTS,
                 base_settlement: str = "",
                 founding_year: int = 1000,
                 influence_score: float = 50.0,
                 member_count: int = 10,
                 faction_alignment: Optional[str] = None):
        """
        Initialize a local guild.
        
        Args:
            guild_id: Unique identifier
            name: Guild name
            guild_type: Type of guild (merchants, craftsmen, etc.)
            base_settlement: Name of settlement where guild is based
            founding_year: Year the guild was founded
            influence_score: Current influence level (0-100)
            member_count: Number of guild members
            faction_alignment: ID of aligned faction (if any)
        """
        self.guild_id = guild_id or str(uuid.uuid4())
        self.name = name
        self.guild_type = guild_type
        self.base_settlement = base_settlement
        self.founding_year = founding_year
        self.influence_score = max(0.0, min(100.0, influence_score))
        self.member_count = max(1, member_count)
        self.faction_alignment = faction_alignment
        
        # Dynamic state
        self.conflict_status = ConflictStatus.PEACEFUL
        self.stability = 80.0  # Internal stability (0-100)
        self.wealth_level = 50.0  # Guild treasury and resources (0-100)
        self.trade_efficiency = 1.0  # Multiplier for trade operations
        self.monopoly_strength = 0.0  # How close to monopoly (0-100)
        self.member_loyalty = 80.0  # Average loyalty of members (0-100)
        
        # Relationships
        self.rival_guilds: Set[str] = set()
        self.allied_guilds: Set[str] = set()
        self.settlement_reputation = 50.0  # Reputation in base settlement
        self.regional_connections: Dict[str, float] = {}  # Other settlements
        
        # Member management
        self.members: List[str] = []  # List of NPC IDs who are members
        self.rank_structure: List[str] = ["apprentice", "journeyman", "master", "guildmaster"]  # Hierarchy
        self.member_cap: int = 50  # Maximum members this guild can support
        self.skill_threshold: Dict[str, float] = {  # Minimum requirements for joining
            "reputation": 0.0,  # Local reputation requirement
            "loyalty": 0.1,     # Minimum loyalty to community/faction
            "wealth": 0.0       # Economic requirement (if any)
        }
        
        # History and tracking
        self.active_events: List[str] = []  # Active event IDs
        self.historical_events: List[Dict[str, Any]] = []
        self.leadership_history: List[Dict[str, Any]] = []
        self.last_update = datetime.now()
        
        # Guild charter integration
        self.charter: Optional['GuildCharter'] = None  # Will be set after creation
        
        # Guild Facilities & Holdings integration
        self.facilities: List[str] = []  # List of facility IDs owned by this guild
        self.headquarters: Optional[str] = None  # Primary facility ID (typically guildhall)
        
        # Guild Elections & Leadership integration
        self.election_cycle_days: int = 365  # Default annual elections
        self.next_election_day: int = founding_year * 365 + 365  # Next election date
        self.leadership_candidate_ids: List[str] = []  # Current election candidates
        self.leadership_preferences: Dict[str, Dict[str, float]] = {}  # candidate -> preferences
        self.head_of_guild: Optional[str] = None  # Current leader NPC ID
        self.leadership_approval_rating: float = 80.0  # Current leader approval (0-100)
        
        # Add founding leadership
        founding_leader = self._generate_leader_name()
        self.leadership_history.append({
            'year': founding_year,
            'event': 'guild_founded',
            'leader_name': founding_leader,
            'leader_id': None,  # Placeholder for NPC system integration
            'circumstances': 'founding',
            'term_start': founding_year * 365,
            'term_end': None,
            'approval_rating': 80.0
        })
    
    def _generate_leader_name(self) -> str:
        """Generate a random leader name."""
        first_names = ['Aldric', 'Betha', 'Caelum', 'Dara', 'Edric', 'Freya', 'Gareth', 'Hilda', 'Ivan', 'Jora']
        surnames = ['Goldweaver', 'Ironhand', 'Quicksilver', 'Stormwright', 'Brightforge', 'Shadowmere', 'Fairwind', 'Stronghammer']
        return f"{random.choice(first_names)} {random.choice(surnames)}"
    
    def calculate_influence_volatility(self) -> float:
        """
        Calculate how volatile the guild's influence score is.
        
        Returns:
            Volatility factor (higher = more likely to have events)
        """
        base_volatility = 0.1
        
        # Conflict status increases volatility
        conflict_multipliers = {
            ConflictStatus.PEACEFUL: 1.0,
            ConflictStatus.TENSIONS: 1.3,
            ConflictStatus.MINOR_DISPUTES: 1.6,
            ConflictStatus.OPEN_CONFLICT: 2.0,
            ConflictStatus.UNDER_SIEGE: 2.5,
            ConflictStatus.DISBANDED: 0.0
        }
        
        conflict_factor = conflict_multipliers[self.conflict_status]
        
        # Low stability increases volatility
        stability_factor = 2.0 - (self.stability / 100.0)
        
        # High monopoly strength increases volatility (attracts attention)
        monopoly_factor = 1.0 + (self.monopoly_strength / 200.0)
        
        # Faction alignment can increase volatility
        faction_factor = 1.2 if self.faction_alignment else 1.0
        
        return base_volatility * conflict_factor * stability_factor * monopoly_factor * faction_factor
    
    def update_daily_state(self, current_day: int) -> Dict[str, Any]:
        """
        Update guild state for daily tick.
        
        Args:
            current_day: Current simulation day
            
        Returns:
            Dictionary of changes and events
        """
        changes = {
            'guild_id': self.guild_id,
            'day': current_day,
            'influence_change': 0.0,
            'stability_change': 0.0,
            'member_changes': 0,
            'new_relationships': [],
            'status_changes': []
        }
        
        # Natural influence drift based on current status
        influence_drift = self._calculate_daily_influence_drift()
        self.influence_score = max(0.0, min(100.0, self.influence_score + influence_drift))
        changes['influence_change'] = influence_drift
        
        # Stability adjustments
        stability_change = self._calculate_daily_stability_change()
        self.stability = max(0.0, min(100.0, self.stability + stability_change))
        changes['stability_change'] = stability_change
        
        # Member count fluctuations
        member_change = self._calculate_member_change()
        self.member_count = max(1, self.member_count + member_change)
        changes['member_changes'] = member_change
        
        # Check for status changes
        new_status = self._evaluate_conflict_status_change()
        if new_status != self.conflict_status:
            changes['status_changes'].append({
                'old_status': self.conflict_status.value,
                'new_status': new_status.value,
                'reason': 'daily_evaluation'
            })
            self.conflict_status = new_status
        
        self.last_update = datetime.now()
        return changes
    
    def _calculate_daily_influence_drift(self) -> float:
        """Calculate daily influence score change."""
        # Base drift toward 50 (equilibrium)
        base_drift = (50.0 - self.influence_score) * 0.01
        
        # Modify based on current status
        status_modifiers = {
            ConflictStatus.PEACEFUL: 0.1,
            ConflictStatus.TENSIONS: 0.0,
            ConflictStatus.MINOR_DISPUTES: -0.2,
            ConflictStatus.OPEN_CONFLICT: -0.5,
            ConflictStatus.UNDER_SIEGE: -1.0,
            ConflictStatus.DISBANDED: -2.0
        }
        
        status_modifier = status_modifiers[self.conflict_status]
        
        # Random daily variance
        random_variance = random.uniform(-0.5, 0.5)
        
        return base_drift + status_modifier + random_variance
    
    def _calculate_daily_stability_change(self) -> float:
        """Calculate daily stability change."""
        # High member loyalty improves stability
        loyalty_effect = (self.member_loyalty - 50.0) * 0.02
        
        # Wealth affects stability
        wealth_effect = (self.wealth_level - 50.0) * 0.01
        
        # Conflict reduces stability
        conflict_penalties = {
            ConflictStatus.PEACEFUL: 0.0,
            ConflictStatus.TENSIONS: -0.1,
            ConflictStatus.MINOR_DISPUTES: -0.3,
            ConflictStatus.OPEN_CONFLICT: -0.8,
            ConflictStatus.UNDER_SIEGE: -1.5,
            ConflictStatus.DISBANDED: -5.0
        }
        
        conflict_penalty = conflict_penalties[self.conflict_status]
        
        # Natural stability drift toward 80
        stability_drift = (80.0 - self.stability) * 0.005
        
        return loyalty_effect + wealth_effect + conflict_penalty + stability_drift
    
    def _calculate_member_change(self) -> int:
        """Calculate daily member count change."""
        # Base chance of member change
        if random.random() > 0.9:  # 10% chance daily
            # Determine if gain or loss
            if self.stability > 70 and self.influence_score > 60:
                # Growing guild
                return random.randint(1, 3)
            elif self.stability < 30 or self.conflict_status in [ConflictStatus.OPEN_CONFLICT, ConflictStatus.UNDER_SIEGE]:
                # Declining guild
                return -random.randint(1, 2)
            else:
                # Stable guild, minor fluctuations
                return random.choice([-1, 0, 0, 1])
        
        return 0
    
    def _evaluate_conflict_status_change(self) -> ConflictStatus:
        """Evaluate if conflict status should change."""
        current_status = self.conflict_status
        
        # Disbandment check
        if self.member_count <= 0 or self.influence_score <= 5:
            return ConflictStatus.DISBANDED
        
        # Improvement conditions
        if current_status in [ConflictStatus.UNDER_SIEGE, ConflictStatus.OPEN_CONFLICT]:
            if self.stability > 70 and random.random() < 0.1:  # 10% chance to improve
                return ConflictStatus.MINOR_DISPUTES
        elif current_status == ConflictStatus.MINOR_DISPUTES:
            if self.stability > 80 and random.random() < 0.15:
                return ConflictStatus.TENSIONS
        elif current_status == ConflictStatus.TENSIONS:
            if self.stability > 85 and random.random() < 0.2:
                return ConflictStatus.PEACEFUL
        
        # Degradation conditions
        if current_status == ConflictStatus.PEACEFUL:
            if self.stability < 50 and random.random() < 0.05:
                return ConflictStatus.TENSIONS
        elif current_status == ConflictStatus.TENSIONS:
            if self.stability < 40 and random.random() < 0.08:
                return ConflictStatus.MINOR_DISPUTES
        elif current_status == ConflictStatus.MINOR_DISPUTES:
            if self.stability < 30 and random.random() < 0.1:
                return ConflictStatus.OPEN_CONFLICT
        elif current_status == ConflictStatus.OPEN_CONFLICT:
            if self.stability < 20 and random.random() < 0.15:
                return ConflictStatus.UNDER_SIEGE
        
        return current_status
    
    def apply_event_effects(self, event: GuildEvent, daily_effects: Dict[str, float]) -> None:
        """
        Apply the effects of an active guild event.
        
        Args:
            event: The active guild event
            daily_effects: Daily effects to apply
        """
        # Apply influence changes
        if 'influence_change' in daily_effects:
            self.influence_score = max(0.0, min(100.0, 
                self.influence_score + daily_effects['influence_change']))
        
        # Apply stability changes
        if 'stability_change' in daily_effects:
            self.stability = max(0.0, min(100.0, 
                self.stability + daily_effects['stability_change']))
        
        # Apply trade efficiency changes
        if 'trade_efficiency' in daily_effects:
            self.trade_efficiency = max(0.1, min(2.0, 
                self.trade_efficiency + daily_effects['trade_efficiency'] * 0.1))
        
        # Apply reputation changes
        if 'reputation_change' in daily_effects:
            self.settlement_reputation = max(0.0, min(100.0, 
                self.settlement_reputation + daily_effects['reputation_change']))
        
        # Apply member loyalty changes
        if 'member_loyalty' in daily_effects:
            self.member_loyalty = max(0.0, min(100.0, 
                self.member_loyalty + daily_effects['member_loyalty']))
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive guild summary."""
        return {
            'guild_id': self.guild_id,
            'name': self.name,
            'type': self.guild_type.value,
            'base_settlement': self.base_settlement,
            'founding_year': self.founding_year,
            'age_years': datetime.now().year - self.founding_year,
            'influence_score': round(self.influence_score, 1),
            'member_count': self.member_count,
            'conflict_status': self.conflict_status.value,
            'stability': round(self.stability, 1),
            'wealth_level': round(self.wealth_level, 1),
            'trade_efficiency': round(self.trade_efficiency, 2),
            'monopoly_strength': round(self.monopoly_strength, 1),
            'member_loyalty': round(self.member_loyalty, 1),
            'settlement_reputation': round(self.settlement_reputation, 1),
            'faction_alignment': self.faction_alignment,
            'active_events_count': len(self.active_events),
            'rival_guilds_count': len(self.rival_guilds),
            'allied_guilds_count': len(self.allied_guilds),
            'last_update': self.last_update.isoformat()
        }
    
    def accept_member(self, npc_id: str) -> bool:
        """
        Accept a new member into the guild.
        
        Args:
            npc_id: ID of the NPC to accept
            
        Returns:
            True if member was accepted, False otherwise
        """
        if len(self.members) >= self.member_cap:
            return False
        
        if npc_id in self.members:
            return False  # Already a member
        
        # Add member to guild
        self.members.append(npc_id)
        self.member_count = len(self.members)
        
        # Record membership change in history
        self.historical_events.append({
            'type': 'member_joined',
            'npc_id': npc_id,
            'rank': 'apprentice',  # Starting rank
            'timestamp': datetime.now(),
            'circumstances': 'accepted_application'
        })
        
        return True
    
    def evaluate_member_promotion(self, npc_id: str, npc_loyalty: float, 
                                 npc_reputation: float, current_rank: str) -> Optional[str]:
        """
        Evaluate if a member should be promoted.
        
        Args:
            npc_id: ID of the NPC to evaluate
            npc_loyalty: NPC's loyalty to the guild (-1.0 to 1.0)
            npc_reputation: NPC's local reputation (-1.0 to 1.0)
            current_rank: Current rank of the NPC
            
        Returns:
            New rank if promotion warranted, None otherwise
        """
        if npc_id not in self.members:
            return None
        
        if current_rank not in self.rank_structure:
            return None
        
        current_rank_index = self.rank_structure.index(current_rank)
        if current_rank_index >= len(self.rank_structure) - 1:
            return None  # Already at highest rank
        
        # Promotion requirements
        promotion_requirements = {
            'apprentice': {'loyalty': 0.3, 'reputation': 0.1, 'time_served': 30},
            'journeyman': {'loyalty': 0.5, 'reputation': 0.3, 'time_served': 90},
            'master': {'loyalty': 0.7, 'reputation': 0.5, 'time_served': 180}
        }
        
        requirements = promotion_requirements.get(current_rank)
        if not requirements:
            return None
        
        # Check loyalty requirement
        if npc_loyalty < requirements['loyalty']:
            return None
        
        # Check reputation requirement
        if npc_reputation < requirements['reputation']:
            return None
        
        # In a full implementation, would check time_served from guild_history
        # For now, assume time requirements are met
        
        next_rank = self.rank_structure[current_rank_index + 1]
        
        # Record promotion in history
        self.historical_events.append({
            'type': 'member_promoted',
            'npc_id': npc_id,
            'old_rank': current_rank,
            'new_rank': next_rank,
            'timestamp': datetime.now(),
            'loyalty_score': npc_loyalty,
            'reputation_score': npc_reputation
        })
        
        return next_rank
    
    def remove_member(self, npc_id: str, reason: str) -> None:
        """
        Remove a member from the guild.
        
        Args:
            npc_id: ID of the NPC to remove
            reason: Reason for removal (e.g., "expelled", "resigned", "died")
        """
        if npc_id in self.members:
            self.members.remove(npc_id)
            self.member_count = len(self.members)
            
            # Record removal in history
            self.historical_events.append({
                'type': 'member_removed',
                'npc_id': npc_id,
                'reason': reason,
                'timestamp': datetime.now()
            })
            
            # Adjust member loyalty if this was an expulsion
            if reason in ['expelled', 'banished']:
                self.member_loyalty = max(0.0, self.member_loyalty - 5.0)
                self.stability = max(0.0, self.stability - 2.0)
    
    def evaluate_member_requirements(self, npc_reputation: float, npc_loyalty: float, 
                                   npc_wealth: float = 0.0) -> bool:
        """
        Check if an NPC meets the requirements to join this guild.
        
        Args:
            npc_reputation: NPC's local reputation (-1.0 to 1.0)
            npc_loyalty: NPC's loyalty to community/faction (-1.0 to 1.0)
            npc_wealth: NPC's wealth level (0.0 to 1.0)
            
        Returns:
            True if requirements are met
        """
        if len(self.members) >= self.member_cap:
            return False
        
        # Check reputation requirement
        if npc_reputation < self.skill_threshold['reputation']:
            return False
        
        # Check loyalty requirement
        if npc_loyalty < self.skill_threshold['loyalty']:
            return False
        
        # Check wealth requirement
        if npc_wealth < self.skill_threshold['wealth']:
            return False
        
        return True
    
    def get_member_by_rank(self, rank: str) -> List[str]:
        """
        Get all members of a specific rank.
        
        Args:
            rank: Rank to search for
            
        Returns:
            List of NPC IDs with that rank
        """
        # In a full implementation, would track individual member ranks
        # For now, return empty list as placeholder
        return []
    
    def apply_policy(self, policy_key: str, value: Any) -> None:
        """
        Apply a charter policy to the guild.
        
        Args:
            policy_key: Key of the policy to apply
            value: Value to set for the policy
        """
        if self.charter is None:
            return
        
        # Apply policy based on key
        if policy_key == 'violation_tolerance':
            self.charter.violation_tolerance = max(0.0, min(1.0, float(value)))
        elif policy_key == 'internal_reputation_impact':
            self.charter.internal_reputation_impact = max(0.0, float(value))
        elif policy_key == 'outlaw_status':
            self.charter.is_outlawed = bool(value)
        elif policy_key.startswith('membership_'):
            # Update membership requirements
            req_key = policy_key.replace('membership_', '')
            if req_key in self.charter.membership_requirements:
                self.charter.membership_requirements[req_key] = value
        elif policy_key.startswith('punishment_'):
            # Update punishment policy
            offense = policy_key.replace('punishment_', '')
            if isinstance(value, str):
                self.charter.punishment_policy[offense] = value
        elif policy_key.startswith('economic_'):
            # Update economic rights
            right_key = policy_key.replace('economic_', '')
            if right_key in self.charter.economic_rights:
                self.charter.economic_rights[right_key] = bool(value)
    
    def enforce_punishment(self, npc: 'NPCProfile', offense: str) -> None:
        """
        Enforce punishment on an NPC according to charter policy.
        
        Args:
            npc: NPC to punish
            offense: Type of offense committed
        """
        if self.charter is None:
            return
        
        # Import punishment function to avoid circular imports
        from guild_charter_system import process_guild_punishment
        
        # Process the punishment
        punishment_result = process_guild_punishment(self, npc, offense)
        
        # Log the punishment event in guild history
        if punishment_result.get('success', False):
            self.historical_events.append({
                'date': datetime.now(),
                'type': 'charter_enforcement',
                'member_id': npc.npc_id,
                'member_name': npc.name,
                'offense': offense,
                'punishment': punishment_result.get('punishment_type', 'unknown'),
                'effects': punishment_result.get('effects', []),
                'details': f'Charter enforcement: {npc.name} punished for {offense}'
            })


class RegionalGuild:
    """
    Represents a guild with influence across multiple settlements and regions.
    
    Regional guilds are evolved forms of local guilds that have expanded their
    reach and political influence beyond their founding settlement.
    """
    
    def __init__(self,
                 guild_id: Optional[str] = None,
                 name: str = "Regional Guild",
                 guild_type: GuildType = GuildType.MERCHANTS,
                 headquarters: str = "",
                 regional_influence: Optional[Dict[str, float]] = None,
                 chapter_guilds: Optional[Set[str]] = None):
        """
        Initialize a regional guild.
        
        Args:
            guild_id: Unique identifier
            name: Guild name
            guild_type: Type of guild
            headquarters: Primary settlement
            regional_influence: Influence per region
            chapter_guilds: IDs of local guilds under this organization
        """
        self.guild_id = guild_id or str(uuid.uuid4())
        self.name = name
        self.guild_type = guild_type
        self.headquarters = headquarters
        self.regional_influence = regional_influence or {}
        self.chapter_guilds = chapter_guilds or set()
        
        # Enhanced attributes for regional operations
        self.total_members = 0
        self.political_power = 50.0  # 0-100
        self.economic_control = 30.0  # 0-100, control over regional economy
        self.unity_score = 75.0  # How unified the regional chapters are
        
        # Regional guild specific attributes
        self.trade_routes_controlled: Set[str] = set()
        self.government_connections: Dict[str, float] = {}  # settlement -> influence
        self.inter_guild_treaties: Dict[str, str] = {}  # guild_id -> treaty_type
        
        # Organizational structure
        self.leadership_council: List[str] = []  # Leader names
        self.succession_policy = "elected"  # elected, hereditary, appointed
        self.decision_making = "council"  # council, autocratic, democratic
        
        self.last_update = datetime.now()
    
    def calculate_total_influence(self) -> float:
        """Calculate total influence across all regions."""
        return sum(self.regional_influence.values())
    
    def add_chapter_guild(self, local_guild: LocalGuild) -> bool:
        """
        Add a local guild as a chapter.
        
        Args:
            local_guild: Local guild to add as chapter
            
        Returns:
            True if successfully added
        """
        if local_guild.guild_id not in self.chapter_guilds:
            self.chapter_guilds.add(local_guild.guild_id)
            
            # Add regional influence for the local guild's region
            region = local_guild.base_settlement
            if region not in self.regional_influence:
                self.regional_influence[region] = 0.0
            
            # Influence increases based on local guild's power
            influence_boost = local_guild.influence_score * 0.3
            self.regional_influence[region] += influence_boost
            
            # Update total member count
            self.total_members += local_guild.member_count
            
            return True
        
        return False
    
    def remove_chapter_guild(self, guild_id: str, reason: str = "disbanded") -> bool:
        """
        Remove a chapter guild.
        
        Args:
            guild_id: ID of guild to remove
            reason: Reason for removal
            
        Returns:
            True if successfully removed
        """
        if guild_id in self.chapter_guilds:
            self.chapter_guilds.remove(guild_id)
            
            # Record the removal in history
            self.historical_events.append({
                'type': 'chapter_removed',
                'guild_id': guild_id,
                'reason': reason,
                'timestamp': datetime.now()
            })
            
            return True
        
        return False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive regional guild summary."""
        return {
            'guild_id': self.guild_id,
            'name': self.name,
            'type': self.guild_type.value,
            'headquarters': self.headquarters,
            'total_influence': round(self.calculate_total_influence(), 1),
            'regions_count': len(self.regional_influence),
            'chapter_guilds_count': len(self.chapter_guilds),
            'total_members': self.total_members,
            'political_power': round(self.political_power, 1),
            'economic_control': round(self.economic_control, 1),
            'unity_score': round(self.unity_score, 1),
            'trade_routes_controlled': len(self.trade_routes_controlled),
            'government_connections': len(self.government_connections),
            'leadership_council_size': len(self.leadership_council),
            'succession_policy': self.succession_policy,
            'decision_making': self.decision_making,
            'last_update': self.last_update.isoformat()
        }


def generate_guild_events(guilds: List[LocalGuild], current_day: int) -> List[GuildEvent]:
    """
    Generate dynamic guild events based on current guild states.
    
    Args:
        guilds: List of local guilds to consider for events
        current_day: Current simulation day
        
    Returns:
        List of new guild events
    """
    new_events = []
    
    for guild in guilds:
        if guild.conflict_status == ConflictStatus.DISBANDED:
            continue
        
        # Calculate event probability
        base_probability = 0.02  # 2% base daily chance
        volatility = guild.calculate_influence_volatility()
        event_probability = base_probability * volatility
        
        if random.random() < event_probability:
            event = _generate_specific_guild_event(guild, current_day)
            if event:
                new_events.append(event)
    
    # Generate inter-guild events
    if len(guilds) > 1:
        inter_guild_events = _generate_inter_guild_events(guilds, current_day)
        new_events.extend(inter_guild_events)
    
    return new_events


def _generate_specific_guild_event(guild: LocalGuild, current_day: int) -> Optional[GuildEvent]:
    """Generate a specific event for a guild based on its current state."""
    
    # Event probabilities based on guild state
    event_weights = {}
    
    # Power struggle more likely with low stability
    if guild.stability < 50:
        event_weights['power_struggle'] = 30
    
    # Monopoly grab more likely with high influence
    if guild.influence_score > 70:
        event_weights['monopoly_grab'] = 25
    
    # Faction alignment shift if factionally aligned
    if guild.faction_alignment:
        event_weights['faction_alignment_shift'] = 20
    
    # Regional ban more likely if low reputation
    if guild.settlement_reputation < 30:
        event_weights['regional_ban'] = 35
    
    # Internal collapse more likely with very low stability
    if guild.stability < 30:
        event_weights['internal_collapse'] = 40
    
    # Charter revoked if multiple problems
    if guild.settlement_reputation < 40 and guild.stability < 40:
        event_weights['charter_revoked'] = 30
    
    # Default events always possible
    event_weights.update({
        'minor_dispute': 10,
        'trade_expansion': 15,
        'leadership_challenge': 12,
        'member_recruitment': 8
    })
    
    if not event_weights:
        return None
    
    # Select event type
    event_types = list(event_weights.keys())
    weights = list(event_weights.values())
    selected_event = random.choices(event_types, weights=weights)[0]
    
    # Generate event parameters
    severity = _calculate_event_severity(guild, selected_event)
    duration = _calculate_event_duration(selected_event, severity)
    affected_regions = [guild.base_settlement]
    
    # Add faction implications if relevant
    faction_implications = {}
    if selected_event == 'faction_alignment_shift' and guild.faction_alignment:
        faction_implications[guild.faction_alignment] = "strained"
    
    return GuildEvent(
        guild_id=guild.guild_id,
        event_type=selected_event,
        severity=severity,
        duration=duration,
        start_day=current_day,
        affected_regions=affected_regions,
        faction_implications=faction_implications
    )


def _generate_inter_guild_events(guilds: List[LocalGuild], current_day: int) -> List[GuildEvent]:
    """Generate events that involve multiple guilds."""
    inter_events = []
    
    # Check for guild wars between rivals
    for guild in guilds:
        for rival_id in guild.rival_guilds:
            rival_guild = next((g for g in guilds if g.guild_id == rival_id), None)
            if rival_guild and random.random() < 0.005:  # 0.5% daily chance
                # Create guild war event
                war_event = GuildEvent(
                    guild_id=guild.guild_id,
                    event_type='guild_war',
                    severity=random.uniform(0.6, 0.9),
                    duration=random.randint(14, 60),
                    start_day=current_day,
                    affected_regions=[guild.base_settlement, rival_guild.base_settlement]
                )
                war_event.participants = [rival_id]
                inter_events.append(war_event)
    
    # Check for alliance formations
    if len(guilds) > 2 and random.random() < 0.01:  # 1% daily chance
        potential_allies = random.sample(guilds, 2)
        if potential_allies[0].guild_id not in potential_allies[1].rival_guilds:
            alliance_event = GuildEvent(
                guild_id=potential_allies[0].guild_id,
                event_type='alliance_formation',
                severity=random.uniform(0.3, 0.7),
                duration=random.randint(7, 21),
                start_day=current_day,
                affected_regions=[g.base_settlement for g in potential_allies]
            )
            alliance_event.participants = [potential_allies[1].guild_id]
            inter_events.append(alliance_event)
    
    return inter_events


def _calculate_event_severity(guild: LocalGuild, event_type: str) -> float:
    """Calculate event severity based on guild state and event type."""
    base_severity = random.uniform(0.3, 0.8)
    
    # Modify based on guild state
    if guild.stability < 30:
        base_severity *= 1.3
    elif guild.stability > 80:
        base_severity *= 0.7
    
    if guild.conflict_status in [ConflictStatus.OPEN_CONFLICT, ConflictStatus.UNDER_SIEGE]:
        base_severity *= 1.4
    
    # Event-specific modifiers
    severity_modifiers = {
        'power_struggle': 1.2,
        'internal_collapse': 1.5,
        'guild_war': 1.3,
        'charter_revoked': 1.4,
        'minor_dispute': 0.6,
        'trade_expansion': 0.5
    }
    
    modifier = severity_modifiers.get(event_type, 1.0)
    return max(0.1, min(1.0, base_severity * modifier))


def _calculate_event_duration(event_type: str, severity: float) -> int:
    """Calculate event duration based on type and severity."""
    base_durations = {
        'power_struggle': 14,
        'monopoly_grab': 21,
        'faction_alignment_shift': 10,
        'regional_ban': 30,
        'internal_collapse': 45,
        'guild_war': 60,
        'charter_revoked': 90,
        'minor_dispute': 7,
        'trade_expansion': 14,
        'leadership_challenge': 10,
        'member_recruitment': 5,
        'alliance_formation': 14
    }
    
    base_duration = base_durations.get(event_type, 14)
    severity_modifier = 0.5 + severity  # 0.5 to 1.5 multiplier
    
    return max(1, int(base_duration * severity_modifier))


def apply_guild_events(events: List[GuildEvent], 
                      guilds: List[LocalGuild], 
                      settlements: Optional[List] = None,
                      factions: Optional[List] = None,
                      current_day: int = 0) -> Dict[str, Any]:
    """
    Apply active guild events to guilds and related systems.
    
    Args:
        events: List of active guild events
        guilds: List of local guilds
        settlements: List of settlements (optional integration)
        factions: List of factions (optional integration)
        current_day: Current simulation day
        
    Returns:
        Dictionary containing application results and updates
    """
    application_results = {
        'events_processed': 0,
        'events_concluded': 0,
        'guild_changes': {},
        'settlement_effects': {},
        'faction_effects': {},
        'narrative_events': []
    }
    
    # Create guild lookup for efficiency
    guild_lookup = {guild.guild_id: guild for guild in guilds}
    
    for event in events:
        if not event.active:
            continue
        
        # Advance event by one day
        event_progress = event.advance_day()
        application_results['events_processed'] += 1
        
        # Find affected guild
        affected_guild = guild_lookup.get(event.guild_id)
        if not affected_guild:
            continue
        
        # Apply daily effects to guild
        if 'daily_effects' in event_progress:
            daily_effects = event_progress['daily_effects']
            affected_guild.apply_event_effects(event, daily_effects)
            
            # Track changes
            if event.guild_id not in application_results['guild_changes']:
                application_results['guild_changes'][event.guild_id] = []
            
            application_results['guild_changes'][event.guild_id].append({
                'event_id': event.event_id,
                'effects': daily_effects,
                'day': current_day
            })
        
        # Handle event conclusion
        if event_progress['status'] == 'concluded':
            application_results['events_concluded'] += 1
            
            # Apply resolution effects
            _apply_event_resolution(event, affected_guild, event_progress['outcome'])
            
            # Generate narrative
            narrative = {
                'event_id': event.event_id,
                'guild_name': affected_guild.name,
                'event_type': event.event_type,
                'outcome': event_progress['outcome'],
                'description': event.get_narrative_description(),
                'severity': event.severity,
                'day': current_day
            }
            application_results['narrative_events'].append(narrative)
        
        # Apply effects to settlements if provided
        if settlements and event.affected_regions:
            settlement_effects = _apply_settlement_effects(event, settlements, affected_guild)
            application_results['settlement_effects'].update(settlement_effects)
        
        # Apply effects to factions if provided
        if factions and event.faction_implications:
            faction_effects = _apply_faction_effects(event, factions, affected_guild)
            application_results['faction_effects'].update(faction_effects)
    
    return application_results


def _apply_event_resolution(event: GuildEvent, guild: LocalGuild, outcome: str) -> None:
    """Apply the final resolution effects of a concluded event."""
    resolution_effects = {
        'leadership_change': {'stability': 10, 'influence': -5},
        'compromise': {'stability': 5, 'influence': 2},
        'schism': {'stability': -20, 'member_count': -0.3},
        'monopoly_established': {'influence': 15, 'monopoly_strength': 30},
        'competition_emerges': {'influence': -5, 'monopoly_strength': -10},
        'new_alliance': {'influence': 8, 'stability': 5},
        'ban_upheld': {'influence': -25, 'trade_efficiency': -0.5},
        'complete_dissolution': {'influence': -50, 'stability': -50},
        'decisive_victory': {'influence': 20, 'wealth_level': 10},
        'mutual_destruction': {'influence': -15, 'stability': -15}
    }
    
    effects = resolution_effects.get(outcome, {})
    
    for effect, value in effects.items():
        if effect == 'stability':
            guild.stability = max(0, min(100, guild.stability + value))
        elif effect == 'influence':
            guild.influence_score = max(0, min(100, guild.influence_score + value))
        elif effect == 'member_count':
            if value < 0:  # Percentage loss
                guild.member_count = max(1, int(guild.member_count * (1 + value)))
            else:  # Absolute gain
                guild.member_count += int(value)
        elif effect == 'monopoly_strength':
            guild.monopoly_strength = max(0, min(100, guild.monopoly_strength + value))
        elif effect == 'wealth_level':
            guild.wealth_level = max(0, min(100, guild.wealth_level + value))
        elif effect == 'trade_efficiency':
            guild.trade_efficiency = max(0.1, min(2.0, guild.trade_efficiency + value))
    
    # Record in guild history
    guild.historical_events.append({
        'event_id': event.event_id,
        'event_type': event.event_type,
        'outcome': outcome,
        'severity': event.severity,
        'resolution_day': datetime.now(),
        'effects_applied': effects
    })


def _apply_settlement_effects(event: GuildEvent, settlements: List, guild: LocalGuild) -> Dict[str, Any]:
    """Apply guild event effects to settlements."""
    effects = {}
    
    for settlement in settlements:
        if hasattr(settlement, 'name') and settlement.name in event.affected_regions:
            # Example effects - would integrate with actual settlement system
            if event.event_type == 'monopoly_grab':
                # Monopoly affects trade efficiency
                effects[settlement.name] = {'trade_modifier': 0.1 if event.severity > 0.5 else -0.05}
            elif event.event_type == 'guild_war':
                # Guild wars disrupt local trade
                effects[settlement.name] = {'stability_modifier': -event.severity * 5}
            elif event.event_type == 'charter_revoked':
                # Revoked charters reduce economic activity
                effects[settlement.name] = {'economic_activity': -event.severity * 10}
    
    return effects


def _apply_faction_effects(event: GuildEvent, factions: List, guild: LocalGuild) -> Dict[str, Any]:
    """Apply guild event effects to factions."""
    effects = {}
    
    for faction_id, relationship in event.faction_implications.items():
        # Find faction in list (would integrate with actual faction system)
        for faction in factions:
            if hasattr(faction, 'faction_id') and faction.faction_id == faction_id:
                if relationship == 'strained':
                    effects[faction_id] = {'reputation_change': -event.severity * 10}
                elif relationship == 'allied':
                    effects[faction_id] = {'reputation_change': event.severity * 5}
                elif relationship == 'hostile':
                    effects[faction_id] = {'reputation_change': -event.severity * 20}
                break
    
    return effects


# Test harness and examples
if __name__ == "__main__":
    print("=== Guild Event Engine Test Harness ===\n")
    
    # Create sample guilds
    merchants_guild = LocalGuild(
        name="Goldport Merchants Collective",
        guild_type=GuildType.MERCHANTS,
        base_settlement="Goldport",
        founding_year=1150,
        influence_score=75.0,
        member_count=45,
        faction_alignment="merchant_faction"
    )
    
    craftsmen_guild = LocalGuild(
        name="Ironhold Smiths Brotherhood",
        guild_type=GuildType.CRAFTSMEN,
        base_settlement="Ironhold",
        founding_year=1140,
        influence_score=65.0,
        member_count=32
    )
    
    # Set up some rivalry
    merchants_guild.rival_guilds.add(craftsmen_guild.guild_id)
    craftsmen_guild.rival_guilds.add(merchants_guild.guild_id)
    
    guilds = [merchants_guild, craftsmen_guild]
    
    # Test event generation
    print("1. Testing event generation...")
    for day in range(1, 31):  # Simulate 30 days
        new_events = generate_guild_events(guilds, day)
        
        if new_events:
            print(f"Day {day}: {len(new_events)} events generated")
            for event in new_events:
                print(f"  - {event.event_type} affecting {event.guild_id} (severity: {event.severity:.2f})")
        
        # Apply events
        all_events = new_events  # In real usage, would maintain active events list
        if all_events:
            results = apply_guild_events(all_events, guilds, current_day=day)
            if results['narrative_events']:
                for narrative in results['narrative_events']:
                    print(f"  RESOLVED: {narrative['description']}")
        
        # Update guilds
        for guild in guilds:
            changes = guild.update_daily_state(day)
            if abs(changes['influence_change']) > 1.0:
                print(f"  {guild.name} influence: {changes['influence_change']:+.1f}")
    
    print(f"\n2. Final guild states:")
    for guild in guilds:
        summary = guild.get_summary()
        print(f"{summary['name']}:")
        print(f"  Influence: {summary['influence_score']}")
        print(f"  Status: {summary['conflict_status']}")
        print(f"  Members: {summary['member_count']}")
        print(f"  Stability: {summary['stability']}")
        print() 