"""
Guild Elections and Leadership System for Age of Scribes
========================================================

This module provides a comprehensive system for periodic guild leadership elections,
succession events, and internal power dynamics. The system handles democratic elections,
leadership challenges, impeachment proceedings, and political maneuvering within guilds.

Key Features:
- Periodic election cycles with candidate evaluation
- Weighted voting based on member influence and faction support
- PC integration for candidacy, campaigning, and vote manipulation
- Leadership approval ratings and impeachment mechanisms
- Integration with guild charter, faction, and reputation systems
- Dynamic succession events including coups and power struggles

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
    from guild_event_engine import LocalGuild, GuildType
    from npc_profile import NPCProfile
    from guild_charter_system import GuildCharter


class ElectionType(Enum):
    """Types of leadership elections and succession events."""
    SCHEDULED = "scheduled"
    EMERGENCY = "emergency"
    IMPEACHMENT = "impeachment"
    SUCCESSION = "succession"
    COUP = "coup"
    CHARTER_MANDATE = "charter_mandate"


class CandidateStatus(Enum):
    """Status of election candidates."""
    ELIGIBLE = "eligible"
    NOMINATED = "nominated"
    CAMPAIGNING = "campaigning"
    DISQUALIFIED = "disqualified"
    WITHDRAWN = "withdrawn"


class ElectionOutcome(Enum):
    """Possible outcomes of guild elections."""
    DECISIVE_VICTORY = "decisive_victory"
    NARROW_VICTORY = "narrow_victory"
    CONTESTED_RESULT = "contested_result"
    TIE_BROKEN = "tie_broken"
    NO_CONFIDENCE = "no_confidence"
    ELECTION_DISRUPTED = "election_disrupted"


class GuildElection:
    """
    Represents a guild leadership election event.
    
    Manages the entire election process from candidate nomination through
    vote tallying and result implementation. Handles various election types
    including scheduled elections, emergency leadership changes, and impeachment.
    """
    
    def __init__(self,
                 guild_id: str,
                 election_type: str = ElectionType.SCHEDULED.value,
                 election_day: int = 0,
                 trigger_reason: str = "scheduled_election"):
        """
        Initialize a new guild election.
        
        Args:
            guild_id: ID of the guild holding the election
            election_type: Type of election (scheduled, emergency, etc.)
            election_day: Day when election is held
            trigger_reason: What triggered this election
        """
        self.election_id = str(uuid.uuid4())
        self.guild_id = guild_id
        self.election_type = election_type
        self.election_day = election_day
        self.trigger_reason = trigger_reason
        
        # Candidates and voting
        self.candidates: Dict[str, Dict[str, Any]] = {}  # candidate_id -> candidate_data
        self.voting_results: Dict[str, float] = {}  # candidate_id -> vote_score
        self.voter_turnout: float = 0.0
        self.faction_endorsements: Dict[str, str] = {}  # faction_id -> candidate_id
        
        # Election characteristics
        self.campaign_duration: int = 14  # Days of campaigning before election
        self.voting_method = "weighted_influence"  # How votes are calculated
        self.required_majority: float = 0.5  # Threshold for victory
        self.allow_pc_candidates: bool = True
        
        # Results and consequences
        self.winner_id: Optional[str] = None
        self.outcome_type: str = ElectionOutcome.DECISIVE_VICTORY.value
        self.margin_of_victory: float = 0.0
        self.contested: bool = False
        self.election_events: List[Dict[str, Any]] = []
        
        # Post-election effects
        self.stability_impact: float = 0.0
        self.loyalty_changes: Dict[str, float] = {}  # member_id -> loyalty_change
        self.faction_relationship_changes: Dict[str, float] = {}
        
        # Record creation
        self.election_events.append({
            'day': election_day - self.campaign_duration,
            'event': 'election_scheduled',
            'election_type': election_type,
            'trigger_reason': trigger_reason,
            'timestamp': datetime.now()
        })
    
    def add_candidate(self, 
                     candidate_id: str, 
                     candidate_name: str,
                     is_pc: bool = False,
                     platform: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a candidate to the election.
        
        Args:
            candidate_id: Unique identifier for the candidate
            candidate_name: Display name of the candidate
            is_pc: Whether this is a player character
            platform: Campaign platform and promises
            
        Returns:
            True if candidate was added successfully
        """
        if candidate_id in self.candidates:
            return False
        
        self.candidates[candidate_id] = {
            'name': candidate_name,
            'is_pc': is_pc,
            'status': CandidateStatus.NOMINATED.value,
            'platform': platform or {},
            'campaign_funds': 0.0,
            'endorsements': [],
            'scandals': [],
            'approval_rating': 50.0,
            'faction_support': {},
            'campaign_events': []
        }
        
        self.election_events.append({
            'day': self.election_day - self.campaign_duration,
            'event': 'candidate_nominated',
            'candidate_id': candidate_id,
            'candidate_name': candidate_name,
            'is_pc': is_pc,
            'timestamp': datetime.now()
        })
        
        return True
    
    def process_campaign_day(self, current_day: int, guilds: List['LocalGuild']) -> Dict[str, Any]:
        """
        Process daily campaign activities leading up to election.
        
        Args:
            current_day: Current simulation day
            guilds: List of all guild objects
            
        Returns:
            Dictionary of campaign events and changes
        """
        if current_day < self.election_day - self.campaign_duration:
            return {}
        
        if current_day > self.election_day:
            return {}
        
        campaign_results = {
            'election_id': self.election_id,
            'day': current_day,
            'days_until_election': self.election_day - current_day,
            'candidate_activities': [],
            'faction_moves': [],
            'scandal_events': [],
            'endorsement_changes': []
        }
        
        # Process each candidate's daily campaign activities
        for candidate_id, candidate_data in self.candidates.items():
            if candidate_data['status'] != CandidateStatus.CAMPAIGNING.value:
                continue
            
            daily_activity = self._process_candidate_campaign_day(
                candidate_id, candidate_data, current_day, guilds
            )
            campaign_results['candidate_activities'].append(daily_activity)
        
        # Process faction involvement
        faction_activities = self._process_faction_campaign_involvement(current_day, guilds)
        campaign_results['faction_moves'].extend(faction_activities)
        
        # Random campaign events
        random_events = self._generate_campaign_events(current_day)
        campaign_results['scandal_events'].extend(random_events)
        
        return campaign_results
    
    def _process_candidate_campaign_day(self,
                                      candidate_id: str,
                                      candidate_data: Dict[str, Any],
                                      current_day: int,
                                      guilds: List['LocalGuild']) -> Dict[str, Any]:
        """Process daily campaigning for a single candidate."""
        
        activity = {
            'candidate_id': candidate_id,
            'candidate_name': candidate_data['name'],
            'activities': [],
            'approval_change': 0.0,
            'fund_change': 0.0
        }
        
        # Base campaign activities
        if candidate_data['is_pc']:
            # PC candidates have more control and better base effectiveness
            base_effectiveness = 0.8
            daily_cost = 5.0
        else:
            # NPC candidates have variable effectiveness
            base_effectiveness = random.uniform(0.3, 0.7)
            daily_cost = random.uniform(2.0, 8.0)
        
        # Campaign activities
        activities = random.choices(
            ['public_speech', 'guild_meetings', 'door_to_door', 'faction_negotiations', 'fundraising'],
            weights=[20, 25, 15, 20, 20],
            k=random.randint(1, 3)
        )
        
        for activity_type in activities:
            effectiveness = base_effectiveness * random.uniform(0.7, 1.3)
            
            if activity_type == 'public_speech':
                approval_gain = effectiveness * random.uniform(1.0, 3.0)
                cost = daily_cost * 0.5
                activity['activities'].append(f"Delivered public speech (+{approval_gain:.1f} approval)")
                
            elif activity_type == 'guild_meetings':
                approval_gain = effectiveness * random.uniform(0.5, 2.0)
                cost = daily_cost * 0.3
                activity['activities'].append(f"Attended guild meetings (+{approval_gain:.1f} approval)")
                
            elif activity_type == 'door_to_door':
                approval_gain = effectiveness * random.uniform(0.3, 1.5)
                cost = daily_cost * 0.2
                activity['activities'].append(f"Door-to-door campaigning (+{approval_gain:.1f} approval)")
                
            elif activity_type == 'faction_negotiations':
                # Faction negotiations can gain endorsements
                if random.random() < effectiveness * 0.3:
                    activity['activities'].append("Secured faction endorsement")
                    approval_gain = effectiveness * 2.0
                else:
                    approval_gain = effectiveness * 0.5
                cost = daily_cost * 0.8
                
            elif activity_type == 'fundraising':
                funds_raised = effectiveness * random.uniform(10.0, 50.0)
                candidate_data['campaign_funds'] += funds_raised
                activity['fund_change'] += funds_raised
                activity['activities'].append(f"Fundraising (+{funds_raised:.0f} gold)")
                approval_gain = 0.0  # No direct approval from fundraising
                cost = 0.0
            
            activity['approval_change'] += approval_gain
            candidate_data['approval_rating'] += approval_gain
            candidate_data['campaign_funds'] -= cost
        
        # Record activity
        candidate_data['campaign_events'].append({
            'day': current_day,
            'activities': activity['activities'],
            'approval_change': activity['approval_change'],
            'fund_change': activity['fund_change']
        })
        
        return activity
    
    def _process_faction_campaign_involvement(self,
                                            current_day: int,
                                            guilds: List['LocalGuild']) -> List[Dict[str, Any]]:
        """Process faction involvement in the campaign."""
        faction_activities = []
        
        # Simulate faction endorsements and interference
        if random.random() < 0.2:  # 20% chance daily
            faction_id = f"faction_{random.randint(1, 5)}"
            activity_type = random.choice([
                'endorsement', 'funding', 'opposition', 'information_warfare'
            ])
            
            if activity_type == 'endorsement':
                # Random candidate gets faction endorsement
                candidate_ids = list(self.candidates.keys())
                if candidate_ids:
                    endorsed_candidate = random.choice(candidate_ids)
                    self.faction_endorsements[faction_id] = endorsed_candidate
                    self.candidates[endorsed_candidate]['endorsements'].append(faction_id)
                    
                    faction_activities.append({
                        'type': 'faction_endorsement',
                        'faction_id': faction_id,
                        'candidate_id': endorsed_candidate,
                        'day': current_day
                    })
            
            elif activity_type == 'funding':
                # Faction provides campaign funding
                candidate_ids = list(self.candidates.keys())
                if candidate_ids:
                    funded_candidate = random.choice(candidate_ids)
                    funding_amount = random.uniform(50.0, 200.0)
                    self.candidates[funded_candidate]['campaign_funds'] += funding_amount
                    
                    faction_activities.append({
                        'type': 'faction_funding',
                        'faction_id': faction_id,
                        'candidate_id': funded_candidate,
                        'amount': funding_amount,
                        'day': current_day
                    })
        
        return faction_activities
    
    def _generate_campaign_events(self, current_day: int) -> List[Dict[str, Any]]:
        """Generate random campaign events like scandals."""
        events = []
        
        if random.random() < 0.1:  # 10% chance of scandal
            candidate_ids = list(self.candidates.keys())
            if candidate_ids:
                scandal_candidate = random.choice(candidate_ids)
                scandal_types = [
                    'corruption_allegations', 'personal_misconduct', 'policy_contradiction',
                    'faction_bribery', 'guild_fund_misuse'
                ]
                scandal_type = random.choice(scandal_types)
                
                # Impact on approval rating
                approval_loss = random.uniform(5.0, 15.0)
                self.candidates[scandal_candidate]['approval_rating'] -= approval_loss
                self.candidates[scandal_candidate]['scandals'].append({
                    'type': scandal_type,
                    'day': current_day,
                    'approval_impact': -approval_loss
                })
                
                events.append({
                    'type': 'campaign_scandal',
                    'candidate_id': scandal_candidate,
                    'scandal_type': scandal_type,
                    'approval_impact': -approval_loss,
                    'day': current_day
                })
        
        return events
    
    def conduct_election_voting(self, guild: 'LocalGuild') -> Dict[str, Any]:
        """
        Conduct the actual election voting and determine results.
        
        Args:
            guild: The guild holding the election
            
        Returns:
            Dictionary containing election results and consequences
        """
        if len(self.candidates) == 0:
            return {
                'outcome': ElectionOutcome.NO_CONFIDENCE.value,
                'reason': 'no_candidates'
            }
        
        results = {
            'election_id': self.election_id,
            'guild_id': self.guild_id,
            'election_day': self.election_day,
            'candidate_votes': {},
            'vote_details': {},
            'winner_id': None,
            'outcome': None,
            'margin_of_victory': 0.0,
            'voter_turnout': 0.0,
            'faction_influence': {},
            'post_election_effects': {}
        }
        
        # Calculate voter turnout based on guild stability and election type
        base_turnout = 0.7
        if self.election_type == ElectionType.EMERGENCY.value:
            base_turnout = 0.9
        elif self.election_type == ElectionType.IMPEACHMENT.value:
            base_turnout = 0.85
        
        stability_modifier = guild.stability / 100.0
        turnout = base_turnout * stability_modifier * random.uniform(0.8, 1.2)
        turnout = max(0.3, min(1.0, turnout))
        self.voter_turnout = turnout
        results['voter_turnout'] = turnout
        
        # Calculate votes for each candidate
        total_voting_power = 0.0
        
        for candidate_id, candidate_data in self.candidates.items():
            if candidate_data['status'] not in [CandidateStatus.CAMPAIGNING.value, CandidateStatus.NOMINATED.value]:
                continue
            
            vote_score = self._calculate_candidate_vote_score(candidate_id, candidate_data, guild)
            vote_score *= turnout  # Apply turnout modifier
            
            self.voting_results[candidate_id] = vote_score
            results['candidate_votes'][candidate_id] = vote_score
            total_voting_power += vote_score
            
            results['vote_details'][candidate_id] = {
                'base_appeal': candidate_data['approval_rating'],
                'faction_support': len(candidate_data['endorsements']),
                'campaign_effectiveness': len(candidate_data['campaign_events']),
                'scandal_penalties': len(candidate_data['scandals'])
            }
        
        # Determine winner and outcome
        if total_voting_power == 0:
            results['outcome'] = ElectionOutcome.NO_CONFIDENCE.value
            return results
        
        # Sort candidates by vote score
        sorted_candidates = sorted(
            self.voting_results.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        if len(sorted_candidates) >= 2:
            winner_votes = sorted_candidates[0][1]
            runner_up_votes = sorted_candidates[1][1]
            margin = (winner_votes - runner_up_votes) / total_voting_power
        else:
            margin = 1.0
        
        self.winner_id = sorted_candidates[0][0]
        self.margin_of_victory = margin
        results['winner_id'] = self.winner_id
        results['margin_of_victory'] = margin
        
        # Determine outcome type
        if margin >= 0.3:
            self.outcome_type = ElectionOutcome.DECISIVE_VICTORY.value
        elif margin >= 0.1:
            self.outcome_type = ElectionOutcome.NARROW_VICTORY.value
        elif margin >= 0.05:
            self.outcome_type = ElectionOutcome.CONTESTED_RESULT.value
        else:
            self.outcome_type = ElectionOutcome.TIE_BROKEN.value
            self.contested = True
        
        results['outcome'] = self.outcome_type
        
        # Calculate post-election effects
        results['post_election_effects'] = self._calculate_election_consequences(guild)
        
        return results
    
    def _calculate_candidate_vote_score(self,
                                      candidate_id: str,
                                      candidate_data: Dict[str, Any],
                                      guild: 'LocalGuild') -> float:
        """Calculate the total vote score for a candidate."""
        
        base_score = 10.0  # Base voting power
        
        # Approval rating influence
        approval_modifier = candidate_data['approval_rating'] / 100.0
        base_score *= (0.5 + approval_modifier)
        
        # Campaign effectiveness
        campaign_events = len(candidate_data['campaign_events'])
        campaign_modifier = 1.0 + (campaign_events * 0.1)
        base_score *= campaign_modifier
        
        # Faction endorsements
        endorsement_bonus = len(candidate_data['endorsements']) * 5.0
        base_score += endorsement_bonus
        
        # Guild type preferences
        guild_type_bonus = self._get_guild_type_candidate_bonus(
            candidate_data, guild.guild_type
        )
        base_score += guild_type_bonus
        
        # Scandal penalties
        scandal_penalty = len(candidate_data['scandals']) * 3.0
        base_score -= scandal_penalty
        
        # PC candidate bonus (PCs are more effective campaigners)
        if candidate_data['is_pc']:
            base_score *= 1.2
        
        # Random factor for unpredictability
        random_factor = random.uniform(0.8, 1.2)
        base_score *= random_factor
        
        return max(0.0, base_score)
    
    def _get_guild_type_candidate_bonus(self,
                                      candidate_data: Dict[str, Any],
                                      guild_type: 'GuildType') -> float:
        """Get guild type specific bonuses for candidates."""
        
        platform = candidate_data.get('platform', {})
        guild_type_str = guild_type.value if hasattr(guild_type, 'value') else str(guild_type)
        
        bonuses = {
            'merchants': {
                'trade_expansion': 3.0,
                'economic_growth': 2.5,
                'market_control': 2.0
            },
            'craftsmen': {
                'quality_standards': 3.0,
                'apprentice_programs': 2.5,
                'tool_improvement': 2.0
            },
            'scholars': {
                'knowledge_preservation': 3.0,
                'research_funding': 2.5,
                'library_expansion': 2.0
            },
            'warriors': {
                'defense_improvement': 3.0,
                'training_programs': 2.5,
                'equipment_upgrade': 2.0
            }
        }
        
        guild_bonuses = bonuses.get(guild_type_str, {})
        total_bonus = 0.0
        
        for policy, bonus_value in guild_bonuses.items():
            if policy in platform:
                total_bonus += bonus_value
        
        return total_bonus
    
    def _calculate_election_consequences(self, guild: 'LocalGuild') -> Dict[str, Any]:
        """Calculate the consequences of the election result."""
        
        consequences = {
            'leadership_change': False,
            'stability_impact': 0.0,
            'loyalty_changes': {},
            'faction_relationship_changes': {},
            'guild_policy_changes': [],
            'member_reactions': []
        }
        
        if not self.winner_id:
            # No confidence vote consequences
            consequences['stability_impact'] = -15.0
            consequences['member_reactions'].append("Guild members express no confidence in leadership")
            return consequences
        
        # Leadership change
        if self.winner_id != guild.head_of_guild:
            consequences['leadership_change'] = True
            
            # Update guild leadership
            old_leader = guild.head_of_guild
            guild.head_of_guild = self.winner_id
            guild.leadership_approval_rating = self.candidates[self.winner_id]['approval_rating']
            
            # Record in leadership history
            guild.leadership_history.append({
                'year': self.election_day // 365,
                'day': self.election_day,
                'event': f'election_{self.election_type}',
                'leader_name': self.candidates[self.winner_id]['name'],
                'leader_id': self.winner_id,
                'circumstances': f'{self.outcome_type}_election',
                'term_start': self.election_day,
                'term_end': None,
                'approval_rating': self.candidates[self.winner_id]['approval_rating'],
                'predecessor': old_leader
            })
        
        # Stability impact based on election outcome
        if self.outcome_type == ElectionOutcome.DECISIVE_VICTORY.value:
            consequences['stability_impact'] = 5.0
        elif self.outcome_type == ElectionOutcome.NARROW_VICTORY.value:
            consequences['stability_impact'] = 2.0
        elif self.outcome_type == ElectionOutcome.CONTESTED_RESULT.value:
            consequences['stability_impact'] = -3.0
        elif self.outcome_type == ElectionOutcome.TIE_BROKEN.value:
            consequences['stability_impact'] = -5.0
        
        # Apply stability impact
        guild.stability += consequences['stability_impact']
        guild.stability = max(0.0, min(100.0, guild.stability))
        
        # Policy changes based on winner's platform
        winner_platform = self.candidates[self.winner_id].get('platform', {})
        for policy, value in winner_platform.items():
            consequences['guild_policy_changes'].append({
                'policy': policy,
                'new_value': value,
                'implementation_day': self.election_day + 30
            })
        
        return consequences


def schedule_guild_election(guild: 'LocalGuild', current_day: int) -> Optional[GuildElection]:
    """
    Schedule a guild election based on election cycle or triggering events.
    
    Args:
        guild: Guild to schedule election for
        current_day: Current simulation day
        
    Returns:
        GuildElection object if election is scheduled, None otherwise
    """
    
    # Check if it's time for scheduled election
    if current_day >= guild.next_election_day:
        election = GuildElection(
            guild_id=guild.guild_id,
            election_type=ElectionType.SCHEDULED.value,
            election_day=current_day + 14,  # Two weeks notice
            trigger_reason="election_cycle"
        )
        
        # Update next election date
        guild.next_election_day = current_day + guild.election_cycle_days
        
        # Populate candidates
        _populate_election_candidates(guild, election)
        
        # Record in guild history
        guild.historical_events.append({
            'type': 'election_scheduled',
            'election_id': election.election_id,
            'election_type': election.election_type,
            'election_day': election.election_day,
            'day': current_day,
            'timestamp': datetime.now()
        })
        
        return election
    
    # Check for emergency election triggers
    emergency_triggers = _check_emergency_election_triggers(guild, current_day)
    if emergency_triggers:
        election = GuildElection(
            guild_id=guild.guild_id,
            election_type=emergency_triggers['type'],
            election_day=current_day + emergency_triggers['notice_days'],
            trigger_reason=emergency_triggers['reason']
        )
        
        _populate_election_candidates(guild, election)
        
        guild.historical_events.append({
            'type': 'emergency_election_scheduled',
            'election_id': election.election_id,
            'trigger_reason': emergency_triggers['reason'],
            'election_day': election.election_day,
            'day': current_day,
            'timestamp': datetime.now()
        })
        
        return election
    
    return None


def conduct_guild_election(guild: 'LocalGuild', 
                         election: GuildElection, 
                         current_day: int,
                         pc_actions: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """
    Conduct a guild election if it's election day.
    
    Args:
        guild: Guild holding the election
        election: Election object to conduct
        current_day: Current simulation day
        pc_actions: Optional PC actions affecting the election
        
    Returns:
        Election results if election was conducted, None otherwise
    """
    
    if current_day != election.election_day:
        # Process campaign activities if in campaign period
        if current_day >= election.election_day - election.campaign_duration:
            return election.process_campaign_day(current_day, [guild])
        return None
    
    # Process PC actions before voting
    if pc_actions:
        for action in pc_actions:
            _process_pc_election_action(election, action, guild)
    
    # Conduct the vote
    results = election.conduct_election_voting(guild)
    
    # Apply consequences
    if results.get('post_election_effects'):
        _apply_election_consequences(guild, election, results['post_election_effects'])
    
    # Record in guild history
    guild.historical_events.append({
        'type': 'election_completed',
        'election_id': election.election_id,
        'winner_id': results.get('winner_id'),
        'outcome': results.get('outcome'),
        'margin': results.get('margin_of_victory', 0.0),
        'turnout': results.get('voter_turnout', 0.0),
        'day': current_day,
        'timestamp': datetime.now()
    })
    
    return results


def _populate_election_candidates(guild: 'LocalGuild', election: GuildElection) -> None:
    """Populate election with eligible candidates from guild membership."""
    
    # Clear existing candidates
    guild.leadership_candidate_ids = []
    guild.leadership_preferences = {}
    
    # Get high-ranking guild members as potential candidates
    eligible_members = []
    
    # In a real implementation, this would query the NPC system
    # For now, generate representative candidates
    candidate_count = min(random.randint(2, 5), max(2, guild.member_count // 10))
    
    for i in range(candidate_count):
        candidate_id = f"npc_{guild.guild_id}_{i}"
        candidate_name = f"Candidate {i+1}"
        
        # Generate platform based on guild type
        platform = _generate_candidate_platform(guild.guild_type)
        
        election.add_candidate(candidate_id, candidate_name, False, platform)
        guild.leadership_candidate_ids.append(candidate_id)
        
        # Generate candidate preferences
        guild.leadership_preferences[candidate_id] = {
            'faction_influence': random.uniform(0.2, 0.8),
            'skill_rating': random.uniform(0.3, 0.9),
            'loyalty_score': random.uniform(0.4, 0.95),
            'innovation_focus': random.uniform(0.1, 0.8),
            'traditionalism': random.uniform(0.2, 0.7)
        }
    
    # Set all candidates to campaigning status
    for candidate_data in election.candidates.values():
        candidate_data['status'] = CandidateStatus.CAMPAIGNING.value


def _generate_candidate_platform(guild_type: 'GuildType') -> Dict[str, Any]:
    """Generate a campaign platform based on guild type."""
    
    guild_type_str = guild_type.value if hasattr(guild_type, 'value') else str(guild_type)
    
    platforms = {
        'merchants': [
            'trade_expansion', 'market_diversification', 'economic_growth',
            'caravan_protection', 'foreign_relations', 'price_stability'
        ],
        'craftsmen': [
            'quality_standards', 'apprentice_programs', 'tool_improvement',
            'workshop_expansion', 'skill_development', 'innovation_funding'
        ],
        'scholars': [
            'knowledge_preservation', 'research_funding', 'library_expansion',
            'academic_exchange', 'manuscript_copying', 'educational_outreach'
        ],
        'warriors': [
            'defense_improvement', 'training_programs', 'equipment_upgrade',
            'strategic_alliances', 'veteran_support', 'recruitment_expansion'
        ]
    }
    
    available_policies = platforms.get(guild_type_str, ['general_improvement'])
    selected_policies = random.sample(available_policies, min(3, len(available_policies)))
    
    platform = {}
    for policy in selected_policies:
        platform[policy] = True
    
    return platform


def _check_emergency_election_triggers(guild: 'LocalGuild', current_day: int) -> Optional[Dict[str, Any]]:
    """Check if any conditions trigger an emergency election."""
    
    # Low approval rating
    if guild.leadership_approval_rating < 30.0:
        if random.random() < 0.1:  # 10% chance daily when approval is very low
            return {
                'type': ElectionType.IMPEACHMENT.value,
                'reason': 'low_approval_rating',
                'notice_days': 7
            }
    
    # Guild instability
    if guild.stability < 25.0:
        if random.random() < 0.05:  # 5% chance daily when stability is critical
            return {
                'type': ElectionType.EMERGENCY.value,
                'reason': 'guild_instability',
                'notice_days': 3
            }
    
    # Charter mandate (if charter requires leadership change)
    if hasattr(guild, 'charter') and guild.charter:
        # Check for charter-mandated leadership changes
        # This would be expanded based on charter system integration
        pass
    
    return None


def _process_pc_election_action(election: GuildElection,
                              action: Dict[str, Any],
                              guild: 'LocalGuild') -> Dict[str, Any]:
    """Process a PC action affecting the election."""
    
    action_type = action.get('type', 'observe')
    action_result = {
        'action_type': action_type,
        'success': False,
        'consequences': [],
        'discovery_risk': 0.0
    }
    
    if action_type == 'announce_candidacy':
        # PC announces candidacy
        pc_id = action.get('pc_id', 'pc_character')
        pc_name = action.get('pc_name', 'Player Character')
        platform = action.get('platform', {})
        
        success = election.add_candidate(pc_id, pc_name, True, platform)
        action_result['success'] = success
        
        if success:
            guild.leadership_candidate_ids.append(pc_id)
            action_result['consequences'].append("PC successfully entered election")
        else:
            action_result['consequences'].append("PC candidacy rejected")
    
    elif action_type == 'campaign_activity':
        # PC conducts campaign activity
        activity_type = action.get('activity', 'public_speech')
        target_candidate = action.get('target_candidate', action.get('pc_id'))
        effectiveness = action.get('effectiveness', 0.5)
        
        if target_candidate in election.candidates:
            approval_gain = effectiveness * random.uniform(2.0, 5.0)
            election.candidates[target_candidate]['approval_rating'] += approval_gain
            action_result['success'] = True
            action_result['consequences'].append(f"Campaign activity increased approval by {approval_gain:.1f}")
    
    elif action_type == 'vote_manipulation':
        # PC attempts to manipulate votes
        method = action.get('method', 'persuasion')
        target_voters = action.get('target_voters', 'general')
        
        base_success = {'persuasion': 0.4, 'bribery': 0.7, 'intimidation': 0.5}.get(method, 0.3)
        action_result['discovery_risk'] = {'persuasion': 0.1, 'bribery': 0.6, 'intimidation': 0.4}.get(method, 0.3)
        
        action_result['success'] = random.random() < base_success
        
        if action_result['success']:
            # Add vote manipulation bonus (would affect final vote calculation)
            action_result['consequences'].append(f"Successfully manipulated votes through {method}")
        else:
            action_result['consequences'].append(f"Failed vote manipulation attempt")
    
    elif action_type == 'scandal_investigation':
        # PC investigates or creates scandals
        target_candidate = action.get('target_candidate')
        investigation_skill = action.get('skill_level', 0.5)
        
        if target_candidate and target_candidate in election.candidates:
            if random.random() < investigation_skill:
                # Generate scandal
                scandal_impact = random.uniform(3.0, 10.0)
                election.candidates[target_candidate]['approval_rating'] -= scandal_impact
                election.candidates[target_candidate]['scandals'].append({
                    'type': 'pc_investigation',
                    'day': election.election_day,
                    'approval_impact': -scandal_impact
                })
                
                action_result['success'] = True
                action_result['consequences'].append(f"Uncovered scandal affecting {target_candidate}")
            else:
                action_result['consequences'].append("Investigation found nothing significant")
    
    # Check for discovery
    if action_result['discovery_risk'] > 0:
        if random.random() < action_result['discovery_risk']:
            action_result['discovered'] = True
            action_result['consequences'].append("Action was discovered by guild members")
            # Apply reputation penalties
        else:
            action_result['discovered'] = False
    
    return action_result


def _apply_election_consequences(guild: 'LocalGuild',
                               election: GuildElection,
                               consequences: Dict[str, Any]) -> None:
    """Apply the consequences of an election to the guild."""
    
    # Apply stability changes
    if consequences.get('stability_impact'):
        guild.stability += consequences['stability_impact']
        guild.stability = max(0.0, min(100.0, guild.stability))
    
    # Apply policy changes (would integrate with guild policy system)
    for policy_change in consequences.get('guild_policy_changes', []):
        guild.historical_events.append({
            'type': 'policy_change',
            'policy': policy_change['policy'],
            'new_value': policy_change['new_value'],
            'implementation_day': policy_change['implementation_day'],
            'source': 'election_mandate',
            'timestamp': datetime.now()
        })
    
    # Update approval rating
    if election.winner_id and election.winner_id in election.candidates:
        guild.leadership_approval_rating = election.candidates[election.winner_id]['approval_rating']


def get_election_quest_opportunities(election: GuildElection,
                                   guild: 'LocalGuild') -> List[Dict[str, Any]]:
    """
    Generate quest opportunities related to guild elections.
    
    Args:
        election: The guild election
        guild: The guild holding the election
        
    Returns:
        List of quest opportunities
    """
    
    quests = []
    
    # Pre-election quests
    if election.election_day > datetime.now().day:
        quests.append({
            'quest_type': 'campaign_manager',
            'title': 'Run the Campaign',
            'description': f'Manage a candidate\'s campaign for guild leadership.',
            'objectives': [
                'Organize campaign events',
                'Secure faction endorsements',
                'Counter opponent scandals'
            ],
            'rewards': ['political_influence', 'faction_connections', 'reputation'],
            'difficulty': 'medium'
        })
        
        quests.append({
            'quest_type': 'election_investigation',
            'title': 'Uncover the Truth',
            'description': f'Investigate corruption in the guild election.',
            'objectives': [
                'Gather evidence of vote buying',
                'Expose candidate scandals',
                'Protect electoral integrity'
            ],
            'rewards': ['justice_reputation', 'faction_favor', 'information'],
            'difficulty': 'hard'
        })
    
    # Election day quests
    elif election.election_day == datetime.now().day:
        quests.append({
            'quest_type': 'election_security',
            'title': 'Secure the Vote',
            'description': f'Ensure the guild election proceeds fairly.',
            'objectives': [
                'Prevent vote manipulation',
                'Maintain order during voting',
                'Count votes accurately'
            ],
            'rewards': ['guild_reputation', 'stability_bonus', 'civic_duty'],
            'difficulty': 'medium'
        })
    
    # Post-election quests
    else:
        if election.contested:
            quests.append({
                'quest_type': 'election_dispute',
                'title': 'Resolve the Contest',
                'description': f'Mediate disputes over the election results.',
                'objectives': [
                    'Investigate vote counting irregularities',
                    'Mediate between rival factions',
                    'Restore guild unity'
                ],
                'rewards': ['diplomatic_skills', 'guild_stability', 'peace_bonus'],
                'difficulty': 'hard'
            })
    
    return quests


def evaluate_election_impact(election: GuildElection,
                           guild: 'LocalGuild') -> Dict[str, Any]:
    """
    Evaluate the impact of an election on guild and broader systems.
    
    Args:
        election: The completed election
        guild: The guild that held the election
        
    Returns:
        Dictionary describing election impact
    """
    
    impact = {
        'election_id': election.election_id,
        'guild_id': guild.guild_id,
        'leadership_change': election.winner_id != guild.head_of_guild,
        'stability_impact': election.stability_impact,
        'faction_implications': {},
        'settlement_effects': {},
        'long_term_consequences': [],
        'narrative_outcomes': []
    }
    
    # Faction implications
    winner_endorsements = election.candidates.get(election.winner_id, {}).get('endorsements', [])
    for faction_id in winner_endorsements:
        impact['faction_implications'][faction_id] = 'strengthened_influence'
    
    # Settlement effects
    if election.outcome_type in [ElectionOutcome.CONTESTED_RESULT.value, ElectionOutcome.TIE_BROKEN.value]:
        impact['settlement_effects']['stability'] = -5.0
        impact['settlement_effects']['reputation'] = -2.0
    else:
        impact['settlement_effects']['stability'] = 2.0
        impact['settlement_effects']['reputation'] = 1.0
    
    # Long-term consequences
    if election.margin_of_victory < 0.1:
        impact['long_term_consequences'].append("Ongoing political tensions within guild")
    
    if len(election.candidates) > 4:
        impact['long_term_consequences'].append("Increased political engagement among members")
    
    # Narrative outcomes
    if election.winner_id and election.candidates[election.winner_id]['is_pc']:
        impact['narrative_outcomes'].append("Player character assumes guild leadership")
    
    if election.election_type == ElectionType.IMPEACHMENT.value:
        impact['narrative_outcomes'].append("Leadership crisis resolved through democratic process")
    
    return impact