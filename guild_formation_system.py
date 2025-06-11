"""
Guild Formation and Splintering System

This module handles the dynamic creation of new guilds through NPC and Player Character
initiative, including legal guild formation, underground organizations, and guild
splintering events. All characters follow the same rules and requirements.

The system ensures that guild formation is earned through gameplay, not handed out
through menus or special treatment. Players must navigate the same political,
economic, and social challenges as NPCs.
"""

import random
import uuid
from typing import Dict, List, Optional, Any, Union, Set
from datetime import datetime, timedelta
from enum import Enum

# Avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from npc_profile import NPCProfile
    from guild_event_engine import LocalGuild, GuildType
    from settlement_system import Settlement

class GuildFormationType(Enum):
    """Types of guild formation attempts."""
    LEGAL_FORMATION = "legal_formation"
    SPLINTER_GROUP = "splinter_group"
    UNDERGROUND_GUILD = "underground_guild"
    RIVAL_ORGANIZATION = "rival_organization"
    PROFESSIONAL_ASSOCIATION = "professional_association"

class FormationStatus(Enum):
    """Status of guild formation proposals."""
    PROPOSAL = "proposal"
    GATHERING_SUPPORT = "gathering_support"
    LEGAL_REVIEW = "legal_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDERGROUND = "underground"
    FAILED = "failed"

class PlayerProfile:
    """Minimal player profile interface for type checking."""
    def __init__(self, player_id: str, reputation_local: Dict[str, float] = None,
                 guild_membership: Optional[str] = None, wealth_level: float = 0.0):
        self.player_id = player_id
        self.reputation_local = reputation_local or {}
        self.guild_membership = guild_membership
        self.wealth_level = wealth_level
        self.skills = {}
        self.social_connections = []

class GuildFormationProposal:
    """
    Represents a proposal to form a new guild.
    
    This class tracks all aspects of guild formation attempts, whether initiated
    by NPCs or Player Characters, ensuring equal treatment and realistic challenges.
    """
    
    def __init__(self,
                 proposal_id: Optional[str] = None,
                 initiator_id: str = "",
                 proposed_guild_name: str = "",
                 guild_type: str = "MERCHANTS",
                 formation_type: GuildFormationType = GuildFormationType.LEGAL_FORMATION,
                 target_settlement: str = "",
                 is_player_initiated: bool = False):
        """
        Initialize a guild formation proposal.
        
        Args:
            proposal_id: Unique identifier for this proposal
            initiator_id: ID of the NPC or Player initiating formation
            proposed_guild_name: Name for the new guild
            guild_type: Type of guild to be formed
            formation_type: Legal vs underground vs splinter formation
            target_settlement: Settlement where guild will be based
            is_player_initiated: True if Player Character created this proposal
        """
        self.proposal_id = proposal_id or str(uuid.uuid4())
        self.initiator_id = initiator_id
        self.proposed_guild_name = proposed_guild_name
        self.guild_type = guild_type
        self.formation_type = formation_type
        self.target_settlement = target_settlement
        self.is_player_initiated = is_player_initiated
        
        # Formation tracking
        self.status = FormationStatus.PROPOSAL
        self.creation_date = datetime.now()
        self.support_deadline = datetime.now() + timedelta(days=90)
        
        # Support and opposition
        self.supporting_members: List[str] = []  # NPC IDs who support formation
        self.required_support_count: int = 5  # Minimum members needed
        self.opposing_factions: List[str] = []  # Faction IDs opposing formation
        self.rival_guilds: List[str] = []  # Guild IDs threatened by formation
        
        # Requirements and modifiers
        self.skill_requirement: float = 0.6  # Minimum skill level in relevant field
        self.reputation_requirement: float = 0.3  # Minimum local reputation
        self.wealth_requirement: float = 1000.0  # Startup capital needed
        self.pc_support_modifier: float = 0.0  # Additional influence if PC has backing
        
        # Formation challenges
        self.legal_obstacles: List[str] = []  # Legal barriers to overcome
        self.political_complications: List[str] = []  # Political issues
        self.economic_barriers: List[str] = []  # Economic challenges
        
        # Progress tracking
        self.support_gained: float = 0.0  # Progress toward member recruitment
        self.legal_progress: float = 0.0  # Progress through legal approval
        self.funding_secured: float = 0.0  # Amount of startup capital raised
        
        # Results
        self.failure_reasons: List[str] = []
        self.success_factors: List[str] = []
        self.formed_guild_id: Optional[str] = None
    
    def add_supporting_member(self, member_id: str, influence_weight: float = 1.0) -> bool:
        """
        Add a supporting member to the guild formation effort.
        
        Args:
            member_id: ID of the NPC supporting formation
            influence_weight: How much influence this member brings
            
        Returns:
            True if member was successfully added
        """
        if member_id not in self.supporting_members:
            self.supporting_members.append(member_id)
            self.support_gained += influence_weight
            return True
        return False
    
    def calculate_formation_probability(self) -> float:
        """
        Calculate the probability of successful guild formation.
        
        Returns:
            Probability value between 0.0 and 1.0
        """
        base_probability = 0.3
        
        # Support factor
        if len(self.supporting_members) >= self.required_support_count:
            support_factor = min(0.4, len(self.supporting_members) / self.required_support_count * 0.4)
        else:
            support_factor = -0.3  # Penalty for insufficient support
        
        # Legal status factor
        if self.formation_type == GuildFormationType.LEGAL_FORMATION:
            legal_factor = 0.2 - (len(self.legal_obstacles) * 0.1)
        elif self.formation_type == GuildFormationType.UNDERGROUND_GUILD:
            legal_factor = -0.1  # Underground is riskier but possible
        else:
            legal_factor = 0.0
        
        # Opposition factor
        opposition_factor = -(len(self.opposing_factions) * 0.1 + len(self.rival_guilds) * 0.15)
        
        # Player support modifier (if applicable)
        player_factor = self.pc_support_modifier if self.is_player_initiated else 0.0
        
        # Economic factor
        economic_factor = min(0.2, self.funding_secured / self.wealth_requirement * 0.2)
        
        total_probability = base_probability + support_factor + legal_factor + opposition_factor + player_factor + economic_factor
        return max(0.0, min(1.0, total_probability))
    
    def advance_formation_process(self, days_passed: int = 1) -> Dict[str, Any]:
        """
        Advance the guild formation process by the specified number of days.
        
        Args:
            days_passed: Number of days to simulate
            
        Returns:
            Dictionary containing process updates and events
        """
        changes = {
            'proposal_id': self.proposal_id,
            'days_advanced': days_passed,
            'status_changes': [],
            'new_supporters': [],
            'new_obstacles': [],
            'events': []
        }
        
        # Check if proposal has expired
        if datetime.now() > self.support_deadline and self.status == FormationStatus.GATHERING_SUPPORT:
            if len(self.supporting_members) < self.required_support_count:
                self.status = FormationStatus.FAILED
                self.failure_reasons.append("insufficient_support_deadline_exceeded")
                changes['status_changes'].append({'old': 'gathering_support', 'new': 'failed', 'reason': 'deadline'})
                return changes
        
        # Process based on current status
        if self.status == FormationStatus.PROPOSAL:
            self._process_proposal_phase(changes, days_passed)
        elif self.status == FormationStatus.GATHERING_SUPPORT:
            self._process_support_gathering(changes, days_passed)
        elif self.status == FormationStatus.LEGAL_REVIEW:
            self._process_legal_review(changes, days_passed)
        
        return changes
    
    def _process_proposal_phase(self, changes: Dict[str, Any], days_passed: int) -> None:
        """Process the initial proposal phase."""
        # Automatically move to support gathering if initiator meets basic requirements
        if self.support_gained > 0 or len(self.supporting_members) > 0:
            self.status = FormationStatus.GATHERING_SUPPORT
            changes['status_changes'].append({'old': 'proposal', 'new': 'gathering_support'})
            changes['events'].append(f"Guild formation proposal for {self.proposed_guild_name} enters support gathering phase")
    
    def _process_support_gathering(self, changes: Dict[str, Any], days_passed: int) -> None:
        """Process the support gathering phase."""
        # Random chance of gaining or losing support
        for _ in range(days_passed):
            if random.random() < 0.1:  # 10% chance per day of support change
                if random.random() < 0.7:  # 70% chance of gaining support
                    new_supporter = f"npc_{random.randint(1000, 9999)}"
                    if self.add_supporting_member(new_supporter, random.uniform(0.5, 1.5)):
                        changes['new_supporters'].append(new_supporter)
                        changes['events'].append(f"New supporter joins {self.proposed_guild_name} formation effort")
                else:
                    # Chance of new obstacles
                    obstacles = ["political_pressure", "economic_concerns", "rival_interference", "legal_complications"]
                    new_obstacle = random.choice(obstacles)
                    if new_obstacle not in self.legal_obstacles:
                        self.legal_obstacles.append(new_obstacle)
                        changes['new_obstacles'].append(new_obstacle)
                        changes['events'].append(f"New obstacle {new_obstacle} emerges for {self.proposed_guild_name}")
        
        # Check if ready for legal review
        if len(self.supporting_members) >= self.required_support_count:
            if self.formation_type == GuildFormationType.LEGAL_FORMATION:
                self.status = FormationStatus.LEGAL_REVIEW
                changes['status_changes'].append({'old': 'gathering_support', 'new': 'legal_review'})
            else:
                # Underground guilds skip legal review
                self.status = FormationStatus.UNDERGROUND
                changes['status_changes'].append({'old': 'gathering_support', 'new': 'underground'})
    
    def _process_legal_review(self, changes: Dict[str, Any], days_passed: int) -> None:
        """Process the legal review phase."""
        # Advance legal progress
        daily_legal_progress = 0.1 - (len(self.legal_obstacles) * 0.02)
        self.legal_progress = min(1.0, self.legal_progress + (daily_legal_progress * days_passed))
        
        # Check for approval or rejection
        if self.legal_progress >= 1.0:
            formation_probability = self.calculate_formation_probability()
            if random.random() < formation_probability:
                self.status = FormationStatus.APPROVED
                changes['status_changes'].append({'old': 'legal_review', 'new': 'approved'})
                changes['events'].append(f"Guild formation for {self.proposed_guild_name} has been approved!")
            else:
                self.status = FormationStatus.REJECTED
                self.failure_reasons.append("legal_review_failed")
                changes['status_changes'].append({'old': 'legal_review', 'new': 'rejected'})
                changes['events'].append(f"Guild formation for {self.proposed_guild_name} has been rejected")

def evaluate_guild_formation_opportunity(actor: Union['NPCProfile', PlayerProfile], 
                                       guilds: List['LocalGuild'], 
                                       context: Dict[str, Any]) -> Optional[GuildFormationProposal]:
    """
    Evaluate whether an NPC or Player Character can initiate guild formation.
    
    This function applies the same criteria to both NPCs and PCs, ensuring equal
    treatment and realistic requirements for guild formation attempts.
    
    Args:
        actor: NPCProfile or PlayerProfile attempting formation
        guilds: List of existing guilds in the area
        context: Additional context (settlement, faction relationships, etc.)
        
    Returns:
        GuildFormationProposal if formation is possible, None otherwise
    """
    # Determine if this is a player character
    is_player = isinstance(actor, PlayerProfile)
    actor_id = actor.player_id if is_player else actor.npc_id
    
    # Check basic eligibility
    eligibility_check = _check_formation_eligibility(actor, guilds, context)
    if not eligibility_check['eligible']:
        return None
    
    # Determine formation type based on circumstances
    formation_type = _determine_formation_type(actor, guilds, context)
    
    # Create guild formation proposal
    proposal = GuildFormationProposal(
        initiator_id=actor_id,
        proposed_guild_name=_generate_guild_name(actor, eligibility_check['profession']),
        guild_type=eligibility_check['profession'],
        formation_type=formation_type,
        target_settlement=context.get('settlement_name', 'Unknown'),
        is_player_initiated=is_player
    )
    
    # Set requirements based on formation type and actor capabilities
    _configure_formation_requirements(proposal, actor, guilds, context)
    
    # Calculate initial support and obstacles
    _assess_formation_challenges(proposal, actor, guilds, context)
    
    # Add PC-specific modifiers if applicable
    if is_player:
        proposal.pc_support_modifier = _calculate_pc_support_modifier(actor, context)
    
    return proposal

def _check_formation_eligibility(actor: Union['NPCProfile', PlayerProfile], 
                               guilds: List['LocalGuild'], 
                               context: Dict[str, Any]) -> Dict[str, Any]:
    """Check if actor meets basic eligibility requirements for guild formation."""
    result = {'eligible': False, 'profession': None, 'reasons': []}
    
    # Determine actor's profession/skill area
    if hasattr(actor, 'personality_traits'):  # NPCProfile
        profession = _determine_npc_profession(actor)
        reputation = actor.reputation_local.get(context.get('settlement_name', ''), 0.0)
        current_guild = actor.guild_membership
        loyalty = getattr(actor, 'guild_loyalty_score', 0.0)
    else:  # PlayerProfile
        profession = _determine_player_profession(actor)
        reputation = actor.reputation_local.get(context.get('settlement_name', ''), 0.0)
        current_guild = actor.guild_membership
        loyalty = 0.0  # Players don't have guild loyalty score
    
    if not profession:
        result['reasons'].append('no_relevant_profession')
        return result
    
    # Check skill requirements
    skill_level = actor.skills.get(profession.lower(), 0.0)
    if skill_level < 0.6:
        result['reasons'].append('insufficient_skill')
        return result
    
    # Check reputation requirements
    if reputation < 0.2:
        result['reasons'].append('poor_reputation')
        return result
    
    # Check guild status - must be unaffiliated OR disloyal
    if current_guild:
        if loyalty > 0.3:  # Still loyal to current guild
            result['reasons'].append('loyal_to_current_guild')
            return result
    
    # Check motivations (for NPCs)
    if hasattr(actor, 'personality_traits'):
        motivation_check = _check_formation_motivations(actor)
        if not motivation_check:
            result['reasons'].append('insufficient_motivation')
            return result
    
    # Check if similar guild already exists and is thriving
    existing_guild = _find_similar_guild(profession, guilds)
    if existing_guild and existing_guild.influence_score > 70 and existing_guild.member_count > 40:
        result['reasons'].append('market_saturated')
        return result
    
    result['eligible'] = True
    result['profession'] = profession
    return result

def _determine_formation_type(actor: Union['NPCProfile', PlayerProfile], 
                            guilds: List['LocalGuild'], 
                            context: Dict[str, Any]) -> GuildFormationType:
    """Determine what type of guild formation this should be."""
    # Check if actor is blacklisted or has criminal background
    reputation = actor.reputation_local.get(context.get('settlement_name', ''), 0.0)
    
    if reputation < -0.5:
        return GuildFormationType.UNDERGROUND_GUILD
    
    # Check if this is a splinter from existing guild
    if hasattr(actor, 'guild_membership') and actor.guild_membership:
        loyalty = getattr(actor, 'guild_loyalty_score', 0.0)
        if loyalty < -0.3:
            return GuildFormationType.SPLINTER_GROUP
    
    # Check if rival guilds would oppose
    existing_guilds = [g for g in guilds if g.guild_type.name == _determine_npc_profession(actor)]
    if len(existing_guilds) > 0:
        return GuildFormationType.RIVAL_ORGANIZATION
    
    return GuildFormationType.LEGAL_FORMATION

def _determine_npc_profession(npc: 'NPCProfile') -> Optional[str]:
    """Determine NPC's primary profession based on traits and faction."""
    if npc.faction_affiliation:
        faction_mapping = {
            "merchants_guild": "MERCHANTS",
            "city_guard": "WARRIORS",
            "temple_order": "SCHOLARS",
            "thieves_guild": "THIEVES"
        }
        if npc.faction_affiliation in faction_mapping:
            return faction_mapping[npc.faction_affiliation]
    
    # Infer from personality traits
    if "scholarly" in npc.personality_traits:
        return "SCHOLARS"
    elif "cunning" in npc.personality_traits and "secretive" in npc.personality_traits:
        return "THIEVES"
    elif "pragmatic" in npc.personality_traits and "diplomatic" in npc.personality_traits:
        return "MERCHANTS"
    elif "aggressive" in npc.personality_traits and "loyal" in npc.personality_traits:
        return "WARRIORS"
    
    return "CRAFTSMEN"  # Default profession

def _determine_player_profession(player: PlayerProfile) -> Optional[str]:
    """Determine player's primary profession based on skills."""
    if not player.skills:
        return None
    
    # Find highest skill
    max_skill = max(player.skills.values())
    if max_skill < 0.6:
        return None
    
    highest_skills = [skill for skill, level in player.skills.items() if level == max_skill]
    
    # Map skills to guild types
    skill_mapping = {
        "trading": "MERCHANTS",
        "commerce": "MERCHANTS",
        "crafting": "CRAFTSMEN",
        "smithing": "CRAFTSMEN",
        "scholarship": "SCHOLARS",
        "research": "SCHOLARS",
        "combat": "WARRIORS",
        "security": "WARRIORS",
        "stealth": "THIEVES",
        "lockpicking": "THIEVES",
        "magic": "MAGES",
        "spellcasting": "MAGES"
    }
    
    for skill in highest_skills:
        if skill.lower() in skill_mapping:
            return skill_mapping[skill.lower()]
    
    return "CRAFTSMEN"  # Default

def _check_formation_motivations(npc: 'NPCProfile') -> bool:
    """Check if NPC has appropriate motivations for guild formation."""
    motivating_traits = ["pragmatic", "cunning", "ambitious", "leader", "visionary"]
    demotivating_traits = ["cautious", "loyal", "submissive", "follower"]
    
    motivation_score = 0
    for trait in npc.personality_traits:
        if trait in motivating_traits:
            motivation_score += 1
        elif trait in demotivating_traits:
            motivation_score -= 1
    
    # Check belief system
    if hasattr(npc, 'belief_system'):
        if npc.belief_system.get('power', 0.5) > 0.6:
            motivation_score += 1
        if npc.belief_system.get('freedom', 0.5) > 0.6:
            motivation_score += 1
        if npc.belief_system.get('authority', 0.5) > 0.7:
            motivation_score -= 1
    
    return motivation_score >= 1

def _find_similar_guild(profession: str, guilds: List['LocalGuild']) -> Optional['LocalGuild']:
    """Find existing guild of the same profession."""
    for guild in guilds:
        if guild.guild_type.name == profession:
            return guild
    return None

def _generate_guild_name(actor: Union['NPCProfile', PlayerProfile], profession: str) -> str:
    """Generate an appropriate guild name."""
    actor_name = actor.name if hasattr(actor, 'name') else f"Player_{actor.player_id[:8]}"
    
    profession_names = {
        "MERCHANTS": ["Trading Company", "Commerce Guild", "Merchant Collective"],
        "CRAFTSMEN": ["Artisan Brotherhood", "Craft Guild", "Makers Union"],
        "SCHOLARS": ["Academy", "Research Society", "Learning Circle"],
        "WARRIORS": ["Guard Company", "Protection Guild", "Security Brotherhood"],
        "THIEVES": ["Shadow Network", "Silent Brotherhood", "Underground Alliance"],
        "MAGES": ["Arcane Circle", "Mystic Society", "Magical Academy"]
    }
    
    base_names = profession_names.get(profession, ["Professional Guild"])
    base_name = random.choice(base_names)
    
    # Add actor's influence to name if they're well-known
    if hasattr(actor, 'reputation_local'):
        max_rep = max(actor.reputation_local.values()) if actor.reputation_local else 0.0
        if max_rep > 0.6:
            return f"{actor_name}'s {base_name}"
    
    # Generate location-based or descriptive name
    descriptors = ["New", "Independent", "Free", "United", "Progressive", "Reformed"]
    return f"{random.choice(descriptors)} {base_name}"

def _configure_formation_requirements(proposal: GuildFormationProposal, 
                                    actor: Union['NPCProfile', PlayerProfile],
                                    guilds: List['LocalGuild'], 
                                    context: Dict[str, Any]) -> None:
    """Configure formation requirements based on circumstances."""
    # Base requirements
    proposal.required_support_count = 5
    proposal.wealth_requirement = 1000.0
    proposal.reputation_requirement = 0.3
    
    # Adjust based on formation type
    if proposal.formation_type == GuildFormationType.UNDERGROUND_GUILD:
        proposal.required_support_count = 3  # Easier to find fellow outcasts
        proposal.wealth_requirement = 500.0   # Lower capital requirements
        proposal.reputation_requirement = -0.5  # Actually benefits from poor reputation
    elif proposal.formation_type == GuildFormationType.SPLINTER_GROUP:
        proposal.required_support_count = 8   # Need significant exodus
        proposal.wealth_requirement = 1500.0  # Higher due to opposition
    elif proposal.formation_type == GuildFormationType.RIVAL_ORGANIZATION:
        proposal.required_support_count = 10  # Must overcome existing competition
        proposal.wealth_requirement = 2000.0  # Expensive to compete
    
    # Adjust based on settlement size
    settlement_population = context.get('settlement_population', 1000)
    if settlement_population < 500:
        proposal.required_support_count = max(3, proposal.required_support_count - 2)
    elif settlement_population > 5000:
        proposal.required_support_count += 3

def _assess_formation_challenges(proposal: GuildFormationProposal, 
                               actor: Union['NPCProfile', PlayerProfile],
                               guilds: List['LocalGuild'], 
                               context: Dict[str, Any]) -> None:
    """Assess potential challenges and opposition to guild formation."""
    # Check for rival guild opposition
    for guild in guilds:
        if guild.guild_type.name == proposal.guild_type:
            proposal.rival_guilds.append(guild.guild_id)
            if guild.influence_score > 60:
                proposal.legal_obstacles.append(f"opposition_from_{guild.name}")
    
    # Check faction relationships
    if hasattr(actor, 'faction_affiliation') and actor.faction_affiliation:
        # Former faction members may face opposition
        if hasattr(actor, 'guild_loyalty_score') and actor.guild_loyalty_score < -0.3:
            proposal.political_complications.append("former_faction_opposition")
    
    # Economic barriers based on settlement wealth
    settlement_wealth = context.get('settlement_wealth_level', 50)
    if settlement_wealth < 40:
        proposal.economic_barriers.append("limited_local_capital")
        proposal.wealth_requirement *= 1.5
    
    # Legal obstacles for underground formation
    if proposal.formation_type == GuildFormationType.UNDERGROUND_GUILD:
        proposal.legal_obstacles.extend(["operating_without_charter", "regulatory_evasion"])
    
    # Initial support based on actor's reputation and connections
    reputation = actor.reputation_local.get(context.get('settlement_name', ''), 0.0)
    initial_support = max(1, int(reputation * 5))  # 1-5 initial supporters
    proposal.support_gained = initial_support
    
    # Add some initial supporters for viable proposals
    for i in range(initial_support):
        supporter_id = f"initial_supporter_{i}_{proposal.proposal_id[:8]}"
        proposal.supporting_members.append(supporter_id)

def _calculate_pc_support_modifier(player: PlayerProfile, context: Dict[str, Any]) -> float:
    """Calculate additional support modifier for player characters."""
    modifier = 0.0
    
    # Wealth influence
    if player.wealth_level > 5000:
        modifier += 0.2
    elif player.wealth_level > 2000:
        modifier += 0.1
    
    # Reputation influence
    max_reputation = max(player.reputation_local.values()) if player.reputation_local else 0.0
    if max_reputation > 0.7:
        modifier += 0.2
    elif max_reputation > 0.4:
        modifier += 0.1
    
    # Social connections
    connection_count = len(getattr(player, 'social_connections', []))
    if connection_count > 10:
        modifier += 0.1
    elif connection_count > 5:
        modifier += 0.05
    
    return min(0.3, modifier)  # Cap at 0.3 to prevent overwhelming advantage

def process_guild_splintering(parent_guild: 'LocalGuild', 
                            splintering_members: List[str],
                            splinter_leader: str,
                            formation_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process the formation of a splinter guild from an existing organization.
    
    Args:
        parent_guild: The guild being split from
        splintering_members: List of member IDs joining the splinter
        splinter_leader: ID of the leader organizing the split
        formation_context: Additional context for the split
        
    Returns:
        Dictionary containing results of the splintering process
    """
    from guild_event_engine import LocalGuild, GuildType
    
    result = {
        'success': False,
        'parent_guild_id': parent_guild.guild_id,
        'splinter_guild_id': None,
        'members_transferred': [],
        'parent_guild_effects': {},
        'narrative_events': []
    }
    
    # Validate splintering conditions
    if len(splintering_members) < 3:
        result['failure_reason'] = 'insufficient_splinter_membership'
        return result
    
    if len(splintering_members) > len(parent_guild.members) * 0.6:
        # If majority is leaving, this becomes a takeover, not a split
        result['failure_reason'] = 'majority_exodus_triggers_dissolution'
        return result
    
    # Create new splinter guild
    splinter_guild = LocalGuild(
        name=f"Reformed {parent_guild.name}",
        guild_type=parent_guild.guild_type,
        base_settlement=parent_guild.base_settlement,
        founding_year=datetime.now().year,
        influence_score=parent_guild.influence_score * 0.4,  # Start with less influence
        member_count=len(splintering_members),
        faction_alignment=None  # Splinters start neutral
    )
    
    # Transfer members to splinter guild
    for member_id in splintering_members:
        if member_id in parent_guild.members:
            parent_guild.remove_member(member_id, "joined_splinter_guild")
            splinter_guild.accept_member(member_id)
            result['members_transferred'].append(member_id)
    
    # Apply effects to parent guild
    parent_guild.stability = max(20.0, parent_guild.stability - 30.0)
    parent_guild.member_loyalty = max(40.0, parent_guild.member_loyalty - 20.0)
    parent_guild.influence_score = max(20.0, parent_guild.influence_score - 15.0)
    
    # Set up rivalry between parent and splinter
    parent_guild.rival_guilds.add(splinter_guild.guild_id)
    splinter_guild.rival_guilds.add(parent_guild.guild_id)
    
    result['success'] = True
    result['splinter_guild_id'] = splinter_guild.guild_id
    result['parent_guild_effects'] = {
        'stability_loss': 30.0,
        'loyalty_loss': 20.0,
        'influence_loss': 15.0,
        'new_rival': splinter_guild.guild_id
    }
    
    result['narrative_events'].extend([
        f"Major schism splits the {parent_guild.name}",
        f"{len(splintering_members)} members leave to form {splinter_guild.name}",
        f"Rivalry established between parent and splinter organizations",
        f"Political tensions rise as former colleagues become competitors"
    ])
    
    return result

def evaluate_rogue_guild_formation(actor: Union['NPCProfile', PlayerProfile],
                                 context: Dict[str, Any]) -> Optional[GuildFormationProposal]:
    """
    Evaluate possibility of forming illegal or underground guild organizations.
    
    This function handles cases where characters are blacklisted from legal
    guild formation but may still attempt to create underground networks.
    """
    # Check if actor is blacklisted or criminal
    is_player = isinstance(actor, PlayerProfile)
    actor_reputation = actor.reputation_local.get(context.get('settlement_name', ''), 0.0)
    
    if actor_reputation > -0.3:
        return None  # Not sufficiently outcast for rogue formation
    
    # Check if region permits outlaw behavior
    settlement_law_enforcement = context.get('law_enforcement_strength', 70)
    if settlement_law_enforcement > 80:
        return None  # Too much enforcement for underground activity
    
    # Create underground guild proposal
    rogue_proposal = GuildFormationProposal(
        initiator_id=actor.player_id if is_player else actor.npc_id,
        proposed_guild_name=f"Shadow {_determine_player_profession(actor) if is_player else _determine_npc_profession(actor)} Network",
        guild_type=_determine_player_profession(actor) if is_player else _determine_npc_profession(actor),
        formation_type=GuildFormationType.UNDERGROUND_GUILD,
        target_settlement=context.get('settlement_name', 'Unknown'),
        is_player_initiated=is_player
    )
    
    # Configure for underground operation
    rogue_proposal.required_support_count = 3
    rogue_proposal.wealth_requirement = 300.0  # Lower barrier to entry
    rogue_proposal.reputation_requirement = -0.5  # Actually requires poor reputation
    
    # Add underground-specific challenges
    rogue_proposal.legal_obstacles.extend([
        "operating_outside_law",
        "avoiding_detection",
        "securing_safe_locations",
        "finding_trustworthy_members"
    ])
    
    # Find potential criminal contacts
    criminal_network_size = max(1, int(abs(actor_reputation) * 5))
    for i in range(criminal_network_size):
        criminal_contact = f"underground_contact_{i}_{rogue_proposal.proposal_id[:8]}"
        rogue_proposal.supporting_members.append(criminal_contact)
    
    rogue_proposal.support_gained = criminal_network_size
    
    return rogue_proposal

# Example usage and testing
if __name__ == "__main__":
    print("=== Guild Formation System Test ===\n")
    
    # Create mock player profile
    player = PlayerProfile(
        player_id="player_001",
        reputation_local={"Millhaven": 0.6},
        wealth_level=3000.0
    )
    player.skills = {"trading": 0.8, "diplomacy": 0.6}
    player.social_connections = [f"contact_{i}" for i in range(8)]
    
    # Test formation opportunity evaluation
    context = {
        'settlement_name': 'Millhaven',
        'settlement_population': 2000,
        'settlement_wealth_level': 60,
        'law_enforcement_strength': 65
    }
    
    guilds = []  # Mock empty guild list
    
    # Test player guild formation
    proposal = evaluate_guild_formation_opportunity(player, guilds, context)
    if proposal:
        print(f"Player guild formation proposal created:")
        print(f"  Guild Name: {proposal.proposed_guild_name}")
        print(f"  Type: {proposal.guild_type}")
        print(f"  Formation Type: {proposal.formation_type.value}")
        print(f"  Required Support: {proposal.required_support_count}")
        print(f"  Initial Support: {len(proposal.supporting_members)}")
        print(f"  PC Support Modifier: {proposal.pc_support_modifier}")
        print(f"  Formation Probability: {proposal.calculate_formation_probability():.2%}")
    else:
        print("Player not eligible for guild formation")
    
    print("\nGuild Formation System ready for integration!") 