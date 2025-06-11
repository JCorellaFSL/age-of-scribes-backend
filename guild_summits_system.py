"""
Guild Summits System for Age of Scribes
========================================

This module provides a comprehensive system for large, multi-guild diplomatic events
that allow for alliance formation, dispute arbitration, economic collaboration,
and political sabotage. Guild summits are formal diplomatic gatherings where multiple
guilds can negotiate, form alliances, resolve conflicts, and engage in political maneuvering.

Key Features:
- GuildSummit class for managing diplomatic events
- Comprehensive agenda system with voting and decision-making
- PC integration for participation, influence, and sabotage
- Dynamic events including walkouts, coups, and sabotage
- Integration with guild charter, reputation, memory, and rumor systems
- Factional influence and consequences

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
    from guild_facilities_system import GuildFacility


class SummitStatus(Enum):
    """Current status of a guild summit."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    CONCLUDED = "concluded"
    CANCELLED = "cancelled"
    DISRUPTED = "disrupted"


class AgendaItemType(Enum):
    """Types of agenda items that can be discussed at summits."""
    ALLIANCE_FORMATION = "alliance_formation"
    BLACKLIST_REPEAL = "blacklist_repeal"
    JOINT_TRADE_ROUTE = "joint_trade_route"
    WAR_DECLARATION = "war_declaration"
    NON_AGGRESSION_PACT = "non_aggression_pact"
    ECONOMIC_EMBARGO = "economic_embargo"
    TERRITORIAL_AGREEMENT = "territorial_agreement"
    REPARATIONS_DEMAND = "reparations_demand"
    RESOURCE_SHARING = "resource_sharing"
    GUILD_SANCTION = "guild_sanction"
    MONOPOLY_AGREEMENT = "monopoly_agreement"
    SETTLEMENT_STATUS = "settlement_status"


class VoteChoice(Enum):
    """Possible votes on agenda items."""
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"
    WALKOUT = "walkout"
    CONDITIONAL = "conditional"


class GuildSummit:
    """
    Represents a formal diplomatic gathering of multiple guilds.
    
    Guild summits are large-scale events where guilds can form alliances,
    resolve disputes, collaborate economically, and engage in political
    maneuvering. They provide opportunities for both cooperation and sabotage.
    """
    
    def __init__(self,
                 host_guild_id: str,
                 location_id: str,
                 invited_guilds: List[str],
                 agenda: List[str],
                 start_day: int,
                 duration_days: int = 3):
        """
        Initialize a new guild summit.
        
        Args:
            host_guild_id: ID of the guild hosting the summit
            location_id: ID of facility or settlement hosting the event
            invited_guilds: List of guild IDs invited to participate
            agenda: List of agenda items to be discussed
            start_day: Day when the summit begins
            duration_days: How many days the summit will last
        """
        self.summit_id = str(uuid.uuid4())
        self.location_id = location_id
        self.host_guild_id = host_guild_id
        self.invited_guilds = invited_guilds.copy()
        self.attending_guilds: List[str] = []
        self.agenda = agenda.copy()
        self.start_day = start_day
        self.duration_days = duration_days
        self.status = SummitStatus.SCHEDULED.value
        
        # Tracking and outcomes
        self.outcome_log: List[Dict[str, Any]] = []
        self.daily_proceedings: Dict[int, Dict[str, Any]] = {}
        self.participant_actions: Dict[str, List[Dict[str, Any]]] = {}
        self.voting_records: Dict[str, Dict[str, str]] = {}  # agenda_item -> guild_id -> vote
        
        # Dynamic summit characteristics
        self.security_level = "normal"  # "low", "normal", "high", "maximum"
        self.public_visibility = True   # Whether summit details are public knowledge
        self.diplomatic_immunity = True # Whether participants have diplomatic protection
        self.agenda_flexibility = "moderate"  # How easily agenda can be changed
        
        # PC integration
        self.pc_attendance_status: Optional[str] = None  # "representative", "observer", "uninvited"
        self.pc_influence_actions: List[Dict[str, Any]] = []
        self.pc_sabotage_attempts: List[Dict[str, Any]] = []
        
        # Factional involvement
        self.faction_sponsors: Dict[str, str] = {}  # faction_id -> sponsorship_type
        self.faction_observers: List[str] = []
        self.faction_interference: List[Dict[str, Any]] = []
        
        # Settlement and location effects
        self.location_modifiers: Dict[str, float] = {}
        self.local_sentiment: Dict[str, float] = {}  # settlement reactions
        
        # Initialize empty attendance
        self.response_deadline = start_day - 7  # One week to respond
        self.invitation_responses: Dict[str, str] = {}  # guild_id -> "accept"/"decline"/"tentative"
        
        # Record creation
        self.outcome_log.append({
            'day': start_day - 14,  # Two weeks advance notice
            'event': 'summit_scheduled',
            'host_guild': host_guild_id,
            'location': location_id,
            'invited_count': len(invited_guilds),
            'agenda_items': len(agenda),
            'timestamp': datetime.now()
        })
    
    def add_agenda_item(self, item: str, proposer_guild_id: str, priority: str = "normal") -> bool:
        """
        Add a new agenda item to the summit.
        
        Args:
            item: Description of the agenda item
            proposer_guild_id: Guild proposing the item
            priority: Priority level ("urgent", "normal", "low")
            
        Returns:
            True if item was added successfully
        """
        if self.status != SummitStatus.SCHEDULED.value:
            return False
            
        # Check if flexibility allows new items
        flexibility_limits = {
            "rigid": 0,      # No new items
            "limited": 2,    # Max 2 new items
            "moderate": 5,   # Max 5 new items
            "flexible": 10   # Max 10 new items
        }
        
        added_items = len([log for log in self.outcome_log if log.get('event') == 'agenda_item_added'])
        max_additions = flexibility_limits.get(self.agenda_flexibility, 3)
        
        if added_items >= max_additions:
            return False
        
        # Add the item based on priority
        if priority == "urgent":
            self.agenda.insert(0, item)
        elif priority == "high":
            # Insert after any urgent items
            urgent_count = sum(1 for log in self.outcome_log 
                             if log.get('event') == 'agenda_item_added' and log.get('priority') == 'urgent')
            self.agenda.insert(urgent_count, item)
        else:
            self.agenda.append(item)
        
        # Record the addition
        self.outcome_log.append({
            'day': datetime.now().day,  # Placeholder for current day
            'event': 'agenda_item_added',
            'item': item,
            'proposer': proposer_guild_id,
            'priority': priority,
            'timestamp': datetime.now()
        })
        
        return True
    
    def process_invitation_response(self, guild_id: str, response: str, conditions: Optional[List[str]] = None) -> None:
        """
        Process a guild's response to the summit invitation.
        
        Args:
            guild_id: ID of responding guild
            response: "accept", "decline", "tentative"
            conditions: List of conditions for acceptance (if any)
        """
        self.invitation_responses[guild_id] = response
        
        if response == "accept":
            if guild_id not in self.attending_guilds:
                self.attending_guilds.append(guild_id)
        elif response == "decline":
            if guild_id in self.attending_guilds:
                self.attending_guilds.remove(guild_id)
        
        # Record response
        self.outcome_log.append({
            'event': 'invitation_response',
            'guild_id': guild_id,
            'response': response,
            'conditions': conditions or [],
            'timestamp': datetime.now()
        })
    
    def get_voting_power(self, guild_id: str, guilds: List['LocalGuild']) -> float:
        """
        Calculate a guild's voting power at the summit.
        
        Args:
            guild_id: ID of the guild
            guilds: List of all guild objects
            
        Returns:
            Voting power multiplier (base 1.0)
        """
        guild = next((g for g in guilds if g.guild_id == guild_id), None)
        if not guild:
            return 0.0
        
        base_power = 1.0
        
        # Host guild gets bonus voting power
        if guild_id == self.host_guild_id:
            base_power *= 1.2
        
        # Influence affects voting power
        influence_modifier = 0.5 + (guild.influence_score / 100.0)
        
        # Wealth affects voting power
        wealth_modifier = 0.8 + (guild.wealth_level / 200.0)
        
        # Stability affects voting reliability
        stability_modifier = 0.6 + (guild.stability / 150.0)
        
        # Faction alignment can boost or reduce power
        faction_modifier = 1.0
        if guild.faction_alignment in self.faction_sponsors:
            faction_modifier = 1.3
        
        return base_power * influence_modifier * wealth_modifier * stability_modifier * faction_modifier
    
    def evaluate_agenda_item_support(self, 
                                   agenda_item: str, 
                                   guilds: List['LocalGuild']) -> Dict[str, str]:
        """
        Evaluate how each attending guild would vote on an agenda item.
        
        Args:
            agenda_item: The agenda item to evaluate
            guilds: List of all guild objects
            
        Returns:
            Dictionary mapping guild_id to expected vote
        """
        votes = {}
        item_type = self._classify_agenda_item(agenda_item)
        
        for guild_id in self.attending_guilds:
            guild = next((g for g in guilds if g.guild_id == guild_id), None)
            if not guild:
                continue
            
            vote = self._calculate_guild_vote(guild, agenda_item, item_type, guilds)
            votes[guild_id] = vote
        
        return votes
    
    def _classify_agenda_item(self, agenda_item: str) -> str:
        """Classify an agenda item by type."""
        item_lower = agenda_item.lower()
        
        if "alliance" in item_lower or "ally" in item_lower:
            return AgendaItemType.ALLIANCE_FORMATION.value
        elif "blacklist" in item_lower:
            return AgendaItemType.BLACKLIST_REPEAL.value
        elif "trade" in item_lower and "route" in item_lower:
            return AgendaItemType.JOINT_TRADE_ROUTE.value
        elif "war" in item_lower or "declare" in item_lower:
            return AgendaItemType.WAR_DECLARATION.value
        elif "non-aggression" in item_lower or "peace" in item_lower:
            return AgendaItemType.NON_AGGRESSION_PACT.value
        elif "embargo" in item_lower or "boycott" in item_lower:
            return AgendaItemType.ECONOMIC_EMBARGO.value
        elif "territory" in item_lower or "border" in item_lower:
            return AgendaItemType.TERRITORIAL_AGREEMENT.value
        elif "reparation" in item_lower or "compensation" in item_lower:
            return AgendaItemType.REPARATIONS_DEMAND.value
        elif "resource" in item_lower and "shar" in item_lower:
            return AgendaItemType.RESOURCE_SHARING.value
        elif "sanction" in item_lower:
            return AgendaItemType.GUILD_SANCTION.value
        elif "monopoly" in item_lower:
            return AgendaItemType.MONOPOLY_AGREEMENT.value
        elif "settlement" in item_lower:
            return AgendaItemType.SETTLEMENT_STATUS.value
        else:
            return "general"
    
    def _calculate_guild_vote(self, 
                            guild: 'LocalGuild', 
                            agenda_item: str, 
                            item_type: str,
                            guilds: List['LocalGuild']) -> str:
        """Calculate how a guild would vote on an agenda item."""
        
        # Base voting tendencies by guild type
        type_preferences = {
            "merchants": {
                AgendaItemType.JOINT_TRADE_ROUTE.value: 0.8,
                AgendaItemType.ECONOMIC_EMBARGO.value: -0.3,
                AgendaItemType.ALLIANCE_FORMATION.value: 0.6,
                AgendaItemType.WAR_DECLARATION.value: -0.7,
                AgendaItemType.MONOPOLY_AGREEMENT.value: 0.4
            },
            "craftsmen": {
                AgendaItemType.RESOURCE_SHARING.value: 0.7,
                AgendaItemType.MONOPOLY_AGREEMENT.value: -0.4,
                AgendaItemType.ALLIANCE_FORMATION.value: 0.5,
                AgendaItemType.WAR_DECLARATION.value: -0.5
            },
            "scholars": {
                AgendaItemType.ALLIANCE_FORMATION.value: 0.6,
                AgendaItemType.WAR_DECLARATION.value: -0.8,
                AgendaItemType.NON_AGGRESSION_PACT.value: 0.8,
                AgendaItemType.RESOURCE_SHARING.value: 0.6
            },
            "warriors": {
                AgendaItemType.WAR_DECLARATION.value: 0.3,
                AgendaItemType.ALLIANCE_FORMATION.value: 0.7,
                AgendaItemType.TERRITORIAL_AGREEMENT.value: 0.6,
                AgendaItemType.NON_AGGRESSION_PACT.value: -0.2
            }
        }
        
        guild_type_str = guild.guild_type.value if hasattr(guild.guild_type, 'value') else str(guild.guild_type)
        preferences = type_preferences.get(guild_type_str, {})
        base_preference = preferences.get(item_type, 0.0)
        
        # Charter considerations
        charter_modifier = 0.0
        if hasattr(guild, 'charter') and guild.charter:
            # Check if charter allows this type of action
            if item_type == AgendaItemType.WAR_DECLARATION.value:
                if guild.charter.political_alignment == "pacifist":
                    charter_modifier = -0.8
            elif item_type == AgendaItemType.ALLIANCE_FORMATION.value:
                if guild.charter.political_alignment == "isolationist":
                    charter_modifier = -0.6
        
        # Relationship considerations
        relationship_modifier = 0.0
        if "alliance" in agenda_item.lower():
            # Check if we have existing relationships with mentioned guilds
            for other_guild_id in self.attending_guilds:
                if other_guild_id in guild.allied_guilds:
                    relationship_modifier += 0.3
                elif other_guild_id in guild.rival_guilds:
                    relationship_modifier -= 0.5
        
        # Stability and influence effects
        stability_modifier = (guild.stability - 50.0) / 200.0  # -0.25 to +0.25
        influence_modifier = (guild.influence_score - 50.0) / 300.0  # -0.17 to +0.17
        
        # Random factor for unpredictability
        random_modifier = random.uniform(-0.1, 0.1)
        
        # Calculate final score
        total_score = (base_preference + charter_modifier + relationship_modifier + 
                      stability_modifier + influence_modifier + random_modifier)
        
        # Convert score to vote
        if total_score > 0.6:
            return VoteChoice.APPROVE.value
        elif total_score > 0.2:
            return VoteChoice.CONDITIONAL.value
        elif total_score > -0.2:
            return VoteChoice.ABSTAIN.value
        elif total_score > -0.6:
            return VoteChoice.REJECT.value
        else:
            return VoteChoice.WALKOUT.value
    
    def get_summit_summary(self) -> Dict[str, Any]:
        """Get comprehensive summit information."""
        return {
            'summit_id': self.summit_id,
            'host_guild_id': self.host_guild_id,
            'location_id': self.location_id,
            'status': self.status,
            'start_day': self.start_day,
            'duration_days': self.duration_days,
            'invited_count': len(self.invited_guilds),
            'attending_count': len(self.attending_guilds),
            'agenda_items': len(self.agenda),
            'agenda': self.agenda,
            'security_level': self.security_level,
            'public_visibility': self.public_visibility,
            'diplomatic_immunity': self.diplomatic_immunity,
            'pc_attendance': self.pc_attendance_status,
            'faction_involvement': len(self.faction_sponsors) + len(self.faction_observers),
            'total_outcomes': len(self.outcome_log),
            'voting_records': len(self.voting_records),
            'last_update': datetime.now().isoformat()
        }


def schedule_guild_summit(host_guild: 'LocalGuild',
                        invited_guild_ids: List[str],
                        agenda: List[str],
                        start_day: int,
                        duration_days: int = 3,
                        location_override: Optional[str] = None) -> Optional[GuildSummit]:
    """
    Schedule a new guild summit.
    
    Args:
        host_guild: Guild hosting the summit
        invited_guild_ids: List of guild IDs to invite
        agenda: List of agenda items for discussion
        start_day: Day when summit should begin
        duration_days: How many days the summit will last
        location_override: Specific location ID (if not using guild headquarters)
        
    Returns:
        GuildSummit object if successfully scheduled, None otherwise
    """
    
    # Validate host guild has appropriate facilities
    location_id = location_override
    if not location_id:
        # Check if guild has suitable headquarters
        if hasattr(host_guild, 'headquarters') and host_guild.headquarters:
            location_id = host_guild.headquarters
        elif hasattr(host_guild, 'facilities') and host_guild.facilities:
            # Look for a guildhall among facilities
            location_id = host_guild.facilities[0]  # Use first facility as fallback
        else:
            # Use settlement as fallback location
            location_id = host_guild.base_settlement + "_town_hall"
    
    # Validate minimum requirements
    if not invited_guild_ids:
        return None
    
    if not agenda:
        return None
    
    if start_day < 7:  # Need at least a week notice
        return None
    
    # Create the summit
    summit = GuildSummit(
        host_guild_id=host_guild.guild_id,
        location_id=location_id,
        invited_guilds=invited_guild_ids,
        agenda=agenda,
        start_day=start_day,
        duration_days=duration_days
    )
    
    # Set initial location modifiers based on host guild's reputation
    summit.location_modifiers = {
        'reputation_bonus': host_guild.settlement_reputation / 100.0,
        'stability_bonus': host_guild.stability / 100.0,
        'influence_bonus': host_guild.influence_score / 100.0
    }
    
    # Record in host guild's history
    host_guild.historical_events.append({
        'type': 'summit_scheduled',
        'summit_id': summit.summit_id,
        'invited_guilds': len(invited_guild_ids),
        'agenda_items': len(agenda),
        'start_day': start_day,
        'timestamp': datetime.now()
    })
    
    return summit


def process_guild_summit_day(summit: GuildSummit, 
                           day: int, 
                           guilds: List['LocalGuild'],
                           pc_actions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Process a single day of a guild summit.
    
    Args:
        summit: The summit to process
        day: Current day number
        guilds: List of all guild objects
        pc_actions: Optional list of PC actions for this day
        
    Returns:
        Dictionary describing the day's events and outcomes
    """
    
    day_results = {
        'summit_id': summit.summit_id,
        'day': day,
        'day_of_summit': day - summit.start_day + 1,
        'agenda_items_processed': [],
        'votes_cast': {},
        'decisions_made': [],
        'dramatic_events': [],
        'pc_actions_processed': [],
        'faction_interference': [],
        'attendance_changes': []
    }
    
    # Check if summit should be active
    if day < summit.start_day:
        return day_results
    
    if day >= summit.start_day + summit.duration_days:
        if summit.status == SummitStatus.IN_PROGRESS.value:
            summit.status = SummitStatus.CONCLUDED.value
        return day_results
    
    # Start summit if first day
    if day == summit.start_day and summit.status == SummitStatus.SCHEDULED.value:
        summit.status = SummitStatus.IN_PROGRESS.value
        day_results['dramatic_events'].append("Summit officially begins")
    
    # Process PC actions first (they can influence the day)
    if pc_actions:
        for action in pc_actions:
            pc_result = _process_pc_summit_action(summit, action, guilds)
            day_results['pc_actions_processed'].append(pc_result)
            summit.pc_influence_actions.append(pc_result)
    
    # Determine how many agenda items to process today
    summit_day = day - summit.start_day + 1
    items_per_day = max(1, len(summit.agenda) // summit.duration_days)
    
    if summit_day == summit.duration_days:
        # Last day - process remaining items
        start_index = (summit_day - 1) * items_per_day
        items_to_process = summit.agenda[start_index:]
    else:
        start_index = (summit_day - 1) * items_per_day
        end_index = start_index + items_per_day
        items_to_process = summit.agenda[start_index:end_index]
    
    # Process each agenda item
    for agenda_item in items_to_process:
        item_result = _process_agenda_item(summit, agenda_item, guilds)
        day_results['agenda_items_processed'].append(item_result)
        
        # Record votes
        if 'votes' in item_result:
            day_results['votes_cast'][agenda_item] = item_result['votes']
            if agenda_item not in summit.voting_records:
                summit.voting_records[agenda_item] = {}
            summit.voting_records[agenda_item].update(item_result['votes'])
        
        # Record decisions
        if 'decision' in item_result:
            day_results['decisions_made'].append({
                'agenda_item': agenda_item,
                'decision': item_result['decision'],
                'vote_tally': item_result.get('vote_tally', {}),
                'consequences': item_result.get('consequences', [])
            })
        
        # Check for dramatic events
        if item_result.get('walkouts'):
            for guild_id in item_result['walkouts']:
                if guild_id in summit.attending_guilds:
                    summit.attending_guilds.remove(guild_id)
                    day_results['attendance_changes'].append(f"{guild_id} walks out")
                    day_results['dramatic_events'].append(f"Guild {guild_id} storms out of summit")
    
    # Check for faction interference
    faction_events = _process_faction_interference(summit, day, guilds)
    day_results['faction_interference'].extend(faction_events)
    
    # Record daily proceedings
    summit.daily_proceedings[day] = day_results.copy()
    
    # Add to summit outcome log
    summit.outcome_log.append({
        'day': day,
        'event': 'daily_proceedings',
        'items_processed': len(day_results['agenda_items_processed']),
        'decisions_made': len(day_results['decisions_made']),
        'dramatic_events': len(day_results['dramatic_events']),
        'current_attendance': len(summit.attending_guilds),
        'timestamp': datetime.now()
    })
    
    return day_results


def _process_agenda_item(summit: GuildSummit,
                       agenda_item: str,
                       guilds: List['LocalGuild']) -> Dict[str, Any]:
    """Process voting and decision-making for a single agenda item."""
    
    result = {
        'agenda_item': agenda_item,
        'item_type': summit._classify_agenda_item(agenda_item),
        'votes': {},
        'vote_tally': {},
        'decision': 'no_decision',
        'consequences': [],
        'walkouts': []
    }
    
    # Get votes from each attending guild
    for guild_id in summit.attending_guilds:
        guild = next((g for g in guilds if g.guild_id == guild_id), None)
        if not guild:
            continue
        
        vote = summit._calculate_guild_vote(guild, agenda_item, result['item_type'], guilds)
        voting_power = summit.get_voting_power(guild_id, guilds)
        
        result['votes'][guild_id] = {
            'vote': vote,
            'voting_power': voting_power,
            'reasoning': _generate_vote_reasoning(guild, agenda_item, vote)
        }
        
        # Handle walkouts
        if vote == VoteChoice.WALKOUT.value:
            result['walkouts'].append(guild_id)
        
        # Tally weighted votes
        if vote not in result['vote_tally']:
            result['vote_tally'][vote] = 0
        result['vote_tally'][vote] += voting_power
    
    # Determine outcome
    total_voting_power = sum(v['voting_power'] for v in result['votes'].values() if v['vote'] != VoteChoice.WALKOUT.value)
    
    if total_voting_power == 0:
        result['decision'] = 'failed_no_quorum'
    else:
        approve_power = result['vote_tally'].get(VoteChoice.APPROVE.value, 0)
        conditional_power = result['vote_tally'].get(VoteChoice.CONDITIONAL.value, 0)
        
        if approve_power / total_voting_power >= 0.6:
            result['decision'] = 'approved'
        elif (approve_power + conditional_power) / total_voting_power >= 0.5:
            result['decision'] = 'approved_conditional'
        elif result['vote_tally'].get(VoteChoice.REJECT.value, 0) / total_voting_power >= 0.4:
            result['decision'] = 'rejected'
        else:
            result['decision'] = 'tabled'
    
    # Generate consequences based on decision
    result['consequences'] = _generate_agenda_consequences(
        agenda_item, result['decision'], result['votes'], guilds
    )
    
    return result


def _process_pc_summit_action(summit: GuildSummit,
                            action: Dict[str, Any],
                            guilds: List['LocalGuild']) -> Dict[str, Any]:
    """Process a PC action during the summit."""
    
    action_type = action.get('type', 'observe')
    action_result = {
        'action_type': action_type,
        'success': False,
        'consequences': [],
        'discovery_risk': 0.0,
        'reputation_impact': 0.0
    }
    
    if action_type == 'propose_agenda_item':
        # PC proposes new agenda item
        item = action.get('agenda_item', '')
        success = summit.add_agenda_item(item, 'pc_character', action.get('priority', 'normal'))
        action_result['success'] = success
        if success:
            action_result['consequences'].append(f"Added '{item}' to agenda")
        else:
            action_result['consequences'].append("Failed to add agenda item")
    
    elif action_type == 'influence_delegate':
        # PC attempts to influence a guild's voting
        target_guild_id = action.get('target_guild')
        influence_method = action.get('method', 'persuasion')  # persuasion, bribery, intimidation
        
        # Calculate success based on method and PC stats (placeholder)
        base_success = 0.3
        if influence_method == 'bribery':
            base_success = 0.6
            action_result['discovery_risk'] = 0.4
        elif influence_method == 'intimidation':
            base_success = 0.4
            action_result['discovery_risk'] = 0.3
            action_result['reputation_impact'] = -5.0
        
        action_result['success'] = random.random() < base_success
        
        if action_result['success']:
            action_result['consequences'].append(f"Successfully influenced {target_guild_id}")
            # Note: This would modify the guild's voting in the actual implementation
        else:
            action_result['consequences'].append(f"Failed to influence {target_guild_id}")
    
    elif action_type == 'leak_information':
        # PC leaks summit contents to rumor network
        leaked_info = action.get('information', 'general_proceedings')
        action_result['success'] = True
        action_result['discovery_risk'] = 0.2
        action_result['consequences'].append(f"Leaked information about {leaked_info}")
    
    elif action_type == 'sabotage':
        # PC attempts to disrupt the summit
        sabotage_type = action.get('sabotage_type', 'create_confusion')
        action_result['discovery_risk'] = 0.7
        action_result['success'] = random.random() < 0.4
        
        if action_result['success']:
            action_result['consequences'].append(f"Successfully executed {sabotage_type}")
            summit.status = SummitStatus.DISRUPTED.value
        else:
            action_result['consequences'].append(f"Failed sabotage attempt detected")
            action_result['reputation_impact'] = -15.0
    
    # Check for discovery
    if action_result['discovery_risk'] > 0:
        if random.random() < action_result['discovery_risk']:
            action_result['discovered'] = True
            action_result['consequences'].append("Action was discovered by summit security")
            action_result['reputation_impact'] -= 10.0
        else:
            action_result['discovered'] = False
    
    return action_result


def _process_faction_interference(summit: GuildSummit,
                                day: int,
                                guilds: List['LocalGuild']) -> List[Dict[str, Any]]:
    """Process any faction interference in the summit."""
    
    interference_events = []
    
    # Check for faction sponsor actions
    for faction_id, sponsorship_type in summit.faction_sponsors.items():
        if random.random() < 0.3:  # 30% chance of daily interference
            interference_type = random.choice([
                'pressure_delegates',
                'offer_incentives',
                'threaten_consequences',
                'provide_information'
            ])
            
            event = {
                'faction_id': faction_id,
                'interference_type': interference_type,
                'day': day,
                'target_guilds': [],
                'effectiveness': random.uniform(0.2, 0.8)
            }
            
            # Determine target guilds based on faction alignment
            for guild in guilds:
                if guild.guild_id in summit.attending_guilds:
                    if guild.faction_alignment == faction_id:
                        event['target_guilds'].append(guild.guild_id)
                    elif guild.faction_alignment is None and random.random() < 0.3:
                        event['target_guilds'].append(guild.guild_id)
            
            interference_events.append(event)
            summit.faction_interference.append(event)
    
    return interference_events


def _generate_vote_reasoning(guild: 'LocalGuild', agenda_item: str, vote: str) -> str:
    """Generate reasoning for why a guild voted a certain way."""
    
    guild_type = guild.guild_type.value if hasattr(guild.guild_type, 'value') else str(guild.guild_type)
    
    reasoning_templates = {
        VoteChoice.APPROVE.value: [
            f"The {guild_type} guild sees clear benefits in this proposal",
            f"This aligns well with our guild's interests and charter",
            f"Our members strongly support this initiative"
        ],
        VoteChoice.REJECT.value: [
            f"This proposal conflicts with our guild's fundamental values",
            f"We cannot support something that harms our members' interests",
            f"The risks outweigh any potential benefits"
        ],
        VoteChoice.ABSTAIN.value: [
            f"We need more information before making a decision",
            f"This matter doesn't significantly affect our guild",
            f"We prefer to remain neutral on this issue"
        ],
        VoteChoice.CONDITIONAL.value: [
            f"We support this with certain modifications",
            f"This needs additional safeguards before we can fully approve",
            f"We'll agree if our concerns are addressed"
        ],
        VoteChoice.WALKOUT.value: [
            f"This is completely unacceptable to our guild",
            f"We refuse to participate in this farce",
            f"Our honor demands we leave rather than compromise"
        ]
    }
    
    templates = reasoning_templates.get(vote, ["No specific reasoning provided"])
    return random.choice(templates)


def _generate_agenda_consequences(agenda_item: str,
                                decision: str,
                                votes: Dict[str, Dict],
                                guilds: List['LocalGuild']) -> List[str]:
    """Generate consequences based on agenda item decision."""
    
    consequences = []
    
    if decision == 'approved':
        if 'alliance' in agenda_item.lower():
            consequences.append("New alliance formed between participating guilds")
            consequences.append("Trade bonuses established between allied guilds")
            consequences.append("Mutual defense pact activated")
        elif 'trade' in agenda_item.lower():
            consequences.append("Joint trade route established")
            consequences.append("Economic benefits for participating guilds")
        elif 'war' in agenda_item.lower():
            consequences.append("Formal declaration of war issued")
            consequences.append("Military preparations begin")
            consequences.append("Diplomatic relations severed")
    
    elif decision == 'rejected':
        consequences.append("Proposal officially rejected")
        if len([v for v in votes.values() if v['vote'] == VoteChoice.WALKOUT.value]) > 0:
            consequences.append("Strong opposition led to diplomatic walkouts")
    
    elif decision == 'tabled':
        consequences.append("Decision postponed for future consideration")
        consequences.append("Committee formed to study the issue further")
    
    elif decision == 'failed_no_quorum':
        consequences.append("Unable to reach decision due to insufficient participation")
        consequences.append("Summit's legitimacy questioned")
    
    return consequences


def get_summit_quest_opportunities(summit: GuildSummit,
                                 guilds: List['LocalGuild']) -> List[Dict[str, Any]]:
    """
    Generate quest opportunities related to the guild summit.
    
    Args:
        summit: The guild summit
        guilds: List of all guild objects
        
    Returns:
        List of quest opportunities
    """
    
    quests = []
    
    # Pre-summit quests
    if summit.status == SummitStatus.SCHEDULED.value:
        quests.append({
            'quest_type': 'diplomatic_courier',
            'title': 'Summit Preparations',
            'description': f'Deliver invitations and agenda materials for the upcoming guild summit.',
            'objectives': [
                'Deliver invitations to invited guilds',
                'Gather RSVPs and attendance confirmations',
                'Resolve any diplomatic concerns'
            ],
            'rewards': ['diplomatic_reputation', 'guild_connections', 'gold'],
            'difficulty': 'easy'
        })
        
        quests.append({
            'quest_type': 'intelligence_gathering',
            'title': 'Summit Intelligence',
            'description': f'Gather information about guild positions before the summit.',
            'objectives': [
                'Learn guild voting intentions',
                'Discover hidden agendas',
                'Identify potential alliance opportunities'
            ],
            'rewards': ['information', 'influence', 'connections'],
            'difficulty': 'medium'
        })
    
    # During summit quests
    elif summit.status == SummitStatus.IN_PROGRESS.value:
        quests.append({
            'quest_type': 'diplomatic_influence',
            'title': 'Summit Negotiator',
            'description': f'Influence the outcome of key summit votes.',
            'objectives': [
                'Persuade undecided guild delegates',
                'Broker compromise agreements',
                'Prevent diplomatic walkouts'
            ],
            'rewards': ['political_influence', 'guild_favor', 'reputation'],
            'difficulty': 'hard'
        })
        
        if summit.security_level == "low":
            quests.append({
                'quest_type': 'summit_sabotage',
                'title': 'Disrupt the Summit',
                'description': f'Secretly sabotage the summit for a rival faction.',
                'objectives': [
                    'Infiltrate summit security',
                    'Create chaos during key votes',
                    'Frame another guild for the disruption'
                ],
                'rewards': ['faction_favor', 'gold', 'blackmail_material'],
                'difficulty': 'very_hard'
            })
    
    # Post-summit quests
    elif summit.status == SummitStatus.CONCLUDED.value:
        # Check for unresolved tensions
        walkout_guilds = [guild_id for day_log in summit.daily_proceedings.values() 
                         for guild_id in day_log.get('attendance_changes', []) 
                         if 'walks out' in guild_id]
        
        if walkout_guilds:
            quests.append({
                'quest_type': 'diplomatic_reconciliation',
                'title': 'Mend Summit Rifts',
                'description': f'Repair relationships damaged during the summit.',
                'objectives': [
                    'Negotiate with guilds that walked out',
                    'Find common ground for future cooperation',
                    'Prevent escalation to open conflict'
                ],
                'rewards': ['diplomatic_achievement', 'peace_bonus', 'reputation'],
                'difficulty': 'medium'
            })
    
    return quests


def evaluate_summit_impact(summit: GuildSummit,
                         guilds: List['LocalGuild'],
                         settlements: Optional[List] = None) -> Dict[str, Any]:
    """
    Evaluate the overall impact of a guild summit on the game world.
    
    Args:
        summit: The completed summit
        guilds: List of all guild objects
        settlements: Optional list of settlements (for broader impact)
        
    Returns:
        Dictionary describing summit's impact
    """
    
    impact = {
        'summit_id': summit.summit_id,
        'guild_relationships': {},
        'economic_effects': {},
        'political_consequences': {},
        'reputation_changes': {},
        'long_term_effects': [],
        'narrative_outcomes': []
    }
    
    # Analyze relationship changes
    for decision in [log for log in summit.outcome_log if log.get('event') == 'daily_proceedings']:
        # Process alliance formations
        # Process trade agreements
        # Process conflicts
        pass
    
    # Calculate reputation changes
    for guild_id in summit.attending_guilds:
        guild = next((g for g in guilds if g.guild_id == guild_id), None)
        if guild:
            reputation_change = 0.0
            
            # Participation bonus
            reputation_change += 2.0
            
            # Host guild gets extra reputation
            if guild_id == summit.host_guild_id:
                reputation_change += 5.0
            
            # Check for successful diplomacy
            successful_votes = len([vote for votes in summit.voting_records.values() 
                                  for vote in votes.values() if vote == VoteChoice.APPROVE.value])
            reputation_change += successful_votes * 0.5
            
            impact['reputation_changes'][guild_id] = reputation_change
    
    # Generate narrative outcomes
    if len(summit.attending_guilds) >= 5:
        impact['narrative_outcomes'].append("Major diplomatic gathering reshapes regional politics")
    
    if any('war' in item.lower() for item in summit.agenda):
        impact['narrative_outcomes'].append("Summit addressed critical military tensions")
    
    if any('alliance' in item.lower() for item in summit.agenda):
        impact['narrative_outcomes'].append("New alliances forged through diplomatic negotiation")
    
    return impact