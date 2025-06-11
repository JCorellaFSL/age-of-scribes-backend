"""
NPC-Guild Integration System

This module handles the complex interactions between NPCs and guilds, including
membership evaluation, career transitions, loyalty tracking, and player character
interactions with guild systems.

The system ensures that guild membership feels organic and realistic, with NPCs
making decisions based on their personality, motivations, and circumstances.
"""

import random
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum

# Avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from npc_profile import NPCProfile
    from guild_event_engine import LocalGuild
    from settlement_system import Settlement

class CareerType(Enum):
    """NPC career types that may be eligible for guild membership."""
    MERCHANT = "merchant"
    CRAFTSMAN = "craftsman"
    SCHOLAR = "scholar"
    GUARD = "guard"
    THIEF = "thief"
    MAGE = "mage"
    FARMER = "farmer"
    LABORER = "laborer"
    NOBLE = "noble"
    CLERGY = "clergy"

class GuildEligibility(Enum):
    """Eligibility status for guild membership."""
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    REJECTED = "rejected"
    BANNED = "banned"
    ALREADY_MEMBER = "already_member"

# Career to Guild Type mappings
CAREER_GUILD_MAPPING = {
    CareerType.MERCHANT: "MERCHANTS",
    CareerType.CRAFTSMAN: "CRAFTSMEN", 
    CareerType.SCHOLAR: "SCHOLARS",
    CareerType.GUARD: "WARRIORS",
    CareerType.THIEF: "THIEVES",
    CareerType.MAGE: "MAGES"
}

def evaluate_guild_affiliation(npc: 'NPCProfile', guilds: List['LocalGuild'], 
                             settlement: 'Settlement', current_day: int = 0) -> Dict[str, Any]:
    """
    Evaluate and potentially change an NPC's guild affiliation.
    
    This function handles the core logic for NPC-guild interactions:
    - Joining guilds for eligible careers
    - Evaluating loyalty and potential defection
    - Processing promotions and demotions
    - Managing guild transitions
    
    Args:
        npc: NPCProfile to evaluate
        guilds: List of available local guilds
        settlement: Settlement where evaluation takes place
        current_day: Current simulation day
        
    Returns:
        Dictionary containing changes made and reasons
    """
    changes = {
        'npc_id': npc.npc_id,
        'day': current_day,
        'guild_changes': [],
        'loyalty_changes': [],
        'rank_changes': [],
        'career_impacts': [],
        'narrative_events': []
    }
    
    # Get NPC's current career (would need career system integration)
    npc_career = _determine_npc_career(npc)
    
    if npc.guild_membership is None:
        # NPC has no guild - evaluate joining
        _evaluate_guild_joining(npc, guilds, settlement, npc_career, changes)
    else:
        # NPC is already a member - evaluate continued membership
        current_guild = _find_guild_by_id(npc.guild_membership, guilds)
        if current_guild:
            _evaluate_existing_membership(npc, current_guild, settlement, changes, current_day)
    
    return changes

def _determine_npc_career(npc: 'NPCProfile') -> Optional[CareerType]:
    """
    Determine NPC's primary career based on profile attributes.
    
    In a full implementation, this would integrate with a career system.
    For now, we'll use personality traits and faction affiliation to infer career.
    """
    # Use faction affiliation as career indicator
    faction_career_mapping = {
        "merchants_guild": CareerType.MERCHANT,
        "city_guard": CareerType.GUARD,
        "temple_order": CareerType.CLERGY,
        "thieves_guild": CareerType.THIEF
    }
    
    if npc.faction_affiliation in faction_career_mapping:
        return faction_career_mapping[npc.faction_affiliation]
    
    # Infer from personality traits
    if "scholarly" in npc.personality_traits:
        return CareerType.SCHOLAR
    elif "cunning" in npc.personality_traits and "secretive" in npc.personality_traits:
        return CareerType.THIEF
    elif "pragmatic" in npc.personality_traits and "diplomatic" in npc.personality_traits:
        return CareerType.MERCHANT
    elif "aggressive" in npc.personality_traits and "loyal" in npc.personality_traits:
        return CareerType.GUARD
    else:
        # Default to laborer for unspecified careers
        return CareerType.LABORER

def _evaluate_guild_joining(npc: 'NPCProfile', guilds: List['LocalGuild'], 
                          settlement: 'Settlement', npc_career: Optional[CareerType],
                          changes: Dict[str, Any]) -> None:
    """Evaluate if an NPC should join a guild."""
    if not npc_career or npc_career not in CAREER_GUILD_MAPPING:
        return  # Career not eligible for guild membership
    
    # Find matching guilds
    target_guild_type = CAREER_GUILD_MAPPING[npc_career]
    eligible_guilds = [g for g in guilds if g.guild_type.name == target_guild_type]
    
    if not eligible_guilds:
        return  # No appropriate guild exists
    
    # Choose the most suitable guild (highest reputation, best alignment)
    best_guild = _select_best_guild_match(npc, eligible_guilds, settlement)
    
    if not best_guild:
        return
    
    # Evaluate NPC's motivation to join
    join_motivation = _calculate_join_motivation(npc, best_guild, settlement)
    
    if join_motivation > 0.4:  # Threshold for joining
        # Check if guild will accept the NPC
        npc_reputation = npc.reputation_local.get(settlement.name, 0.0)
        npc_loyalty = _calculate_community_loyalty(npc, settlement)
        
        if best_guild.evaluate_member_requirements(npc_reputation, npc_loyalty):
            # Attempt to join
            if best_guild.accept_member(npc.npc_id):
                _process_guild_joining(npc, best_guild, changes, join_motivation)

def _select_best_guild_match(npc: 'NPCProfile', guilds: List['LocalGuild'], 
                           settlement: 'Settlement') -> Optional['LocalGuild']:
    """Select the best guild match for an NPC."""
    if not guilds:
        return None
    
    best_guild = None
    best_score = -1.0
    
    for guild in guilds:
        score = 0.0
        
        # Reputation factor
        if guild.settlement_reputation > 50:
            score += (guild.settlement_reputation - 50) / 100.0
        
        # Faction alignment
        if npc.faction_affiliation == guild.faction_alignment:
            score += 0.3
        elif guild.faction_alignment is None:
            score += 0.1  # Neutral guilds are generally acceptable
        
        # Guild stability
        score += guild.stability / 200.0  # 0-0.5 range
        
        # Size considerations (some NPCs prefer smaller, more intimate guilds)
        if "cautious" in npc.personality_traits and guild.member_count < 20:
            score += 0.2
        elif "social" in npc.personality_traits and guild.member_count > 30:
            score += 0.2
        
        if score > best_score:
            best_score = score
            best_guild = guild
    
    return best_guild

def _calculate_join_motivation(npc: 'NPCProfile', guild: 'LocalGuild', 
                             settlement: 'Settlement') -> float:
    """Calculate how motivated an NPC is to join a specific guild."""
    motivation = 0.5  # Base motivation
    
    # Personality-based motivations
    trait_motivations = {
        # Traits that favor guild membership
        "loyal": 0.3,
        "pragmatic": 0.2,
        "diplomatic": 0.2,
        "cautious": 0.1,
        "generous": 0.1,
        
        # Traits that resist guild membership
        "rebellious": -0.4,
        "impulsive": -0.2,
        "cynical": -0.1,
        "secretive": -0.1
    }
    
    for trait in npc.personality_traits:
        if trait in trait_motivations:
            motivation += trait_motivations[trait]
    
    # Belief system influence
    if npc.belief_system.get("authority", 0.5) > 0.6:
        motivation += 0.2  # Respects authority structures
    
    if npc.belief_system.get("freedom", 0.5) > 0.7:
        motivation -= 0.3  # Values personal freedom
    
    # Economic motivations (guild membership can provide stability)
    if "greedy" in npc.personality_traits or "pragmatic" in npc.personality_traits:
        if guild.wealth_level > 60:
            motivation += 0.2
    
    # Social motivations
    if len(npc.social_circle) < 3:  # Lonely NPCs may seek community
        motivation += 0.2
    
    # Guild-specific factors
    if guild.influence_score > 70:
        motivation += 0.1  # Powerful guilds are attractive
    
    if guild.conflict_status.name != "PEACEFUL":
        motivation -= 0.2  # Avoid troubled guilds
    
    return max(0.0, min(1.0, motivation))

def _calculate_community_loyalty(npc: 'NPCProfile', settlement: 'Settlement') -> float:
    """Calculate NPC's loyalty to their community."""
    base_loyalty = 0.5
    
    # Reputation influences loyalty
    reputation = npc.reputation_local.get(settlement.name, 0.0)
    base_loyalty += reputation * 0.3
    
    # Personality influences
    if "loyal" in npc.personality_traits:
        base_loyalty += 0.3
    if "rebellious" in npc.personality_traits:
        base_loyalty -= 0.4
    
    # Belief in law and authority
    if npc.belief_system.get("law", 0.5) > 0.6:
        base_loyalty += 0.2
    
    return max(-1.0, min(1.0, base_loyalty))

def _process_guild_joining(npc: 'NPCProfile', guild: 'LocalGuild', 
                         changes: Dict[str, Any], motivation: float) -> None:
    """Process the actual guild joining."""
    # Update NPC profile
    npc.guild_membership = guild.guild_id
    npc.guild_rank = "apprentice"
    npc.guild_loyalty_score = min(0.8, motivation)  # Initial loyalty based on motivation
    
    # Add to guild history
    npc.guild_history.append({
        'event': 'joined_guild',
        'guild_id': guild.guild_id,
        'guild_name': guild.name,
        'rank': 'apprentice',
        'timestamp': datetime.now(),
        'motivation_score': motivation
    })
    
    # Record changes
    changes['guild_changes'].append({
        'action': 'joined',
        'guild_id': guild.guild_id,
        'guild_name': guild.name,
        'rank': 'apprentice',
        'motivation': motivation
    })
    
    changes['narrative_events'].append(
        f"{npc.name} has joined the {guild.name} as an apprentice, "
        f"seeking {'security and belonging' if motivation > 0.6 else 'professional advancement'}."
    )

def _evaluate_existing_membership(npc: 'NPCProfile', guild: 'LocalGuild', 
                                settlement: 'Settlement', changes: Dict[str, Any],
                                current_day: int) -> None:
    """Evaluate an existing guild member's status."""
    # Check for promotion eligibility
    reputation = npc.reputation_local.get(settlement.name, 0.0)
    new_rank = guild.evaluate_member_promotion(
        npc.npc_id, npc.guild_loyalty_score, reputation, npc.guild_rank
    )
    
    if new_rank:
        _process_promotion(npc, guild, new_rank, changes)
    
    # Evaluate loyalty changes
    _evaluate_loyalty_changes(npc, guild, settlement, changes, current_day)
    
    # Check for potential defection or expulsion
    if npc.guild_loyalty_score < -0.5:
        _evaluate_guild_departure(npc, guild, changes, "low_loyalty")
    
    # Guild may expel members with very poor reputation
    if reputation < -0.7:
        _evaluate_guild_departure(npc, guild, changes, "poor_reputation")

def _process_promotion(npc: 'NPCProfile', guild: 'LocalGuild', 
                     new_rank: str, changes: Dict[str, Any]) -> None:
    """Process a guild rank promotion."""
    old_rank = npc.guild_rank
    npc.guild_rank = new_rank
    
    # Boost loyalty from promotion
    npc.guild_loyalty_score = min(1.0, npc.guild_loyalty_score + 0.2)
    
    # Add to history
    npc.guild_history.append({
        'event': 'promoted',
        'guild_id': guild.guild_id,
        'old_rank': old_rank,
        'new_rank': new_rank,
        'timestamp': datetime.now()
    })
    
    # Record changes
    changes['rank_changes'].append({
        'action': 'promoted',
        'old_rank': old_rank,
        'new_rank': new_rank,
        'guild_name': guild.name
    })
    
    changes['narrative_events'].append(
        f"{npc.name} has been promoted from {old_rank} to {new_rank} "
        f"in the {guild.name}, recognizing their dedication and skill."
    )

def _evaluate_loyalty_changes(npc: 'NPCProfile', guild: 'LocalGuild', 
                            settlement: 'Settlement', changes: Dict[str, Any],
                            current_day: int) -> None:
    """Evaluate daily loyalty changes for guild member."""
    loyalty_change = 0.0
    
    # Guild performance affects loyalty
    if guild.stability > 80:
        loyalty_change += 0.01
    elif guild.stability < 40:
        loyalty_change -= 0.02
    
    # Conflict status affects loyalty
    if guild.conflict_status.name == "OPEN_CONFLICT":
        loyalty_change -= 0.03
    elif guild.conflict_status.name == "UNDER_SIEGE":
        loyalty_change -= 0.05
    
    # Personal reputation affects loyalty to organization
    reputation = npc.reputation_local.get(settlement.name, 0.0)
    if reputation < -0.3:
        loyalty_change -= 0.01  # Personal shame affects guild loyalty
    
    # Personality-based loyalty drift
    if "loyal" in npc.personality_traits:
        loyalty_change += 0.005  # Naturally loyal people become more devoted
    elif "rebellious" in npc.personality_traits:
        loyalty_change -= 0.01  # Rebels eventually chafe under structure
    
    # Apply loyalty change
    if abs(loyalty_change) > 0.001:  # Only record significant changes
        old_loyalty = npc.guild_loyalty_score
        npc.guild_loyalty_score = max(-1.0, min(1.0, npc.guild_loyalty_score + loyalty_change))
        
        changes['loyalty_changes'].append({
            'old_loyalty': old_loyalty,
            'new_loyalty': npc.guild_loyalty_score,
            'change': loyalty_change,
            'factors': _get_loyalty_change_factors(guild, reputation, npc)
        })

def _get_loyalty_change_factors(guild: 'LocalGuild', reputation: float, 
                              npc: 'NPCProfile') -> List[str]:
    """Get descriptive factors affecting loyalty change."""
    factors = []
    
    if guild.stability > 80:
        factors.append("guild_prosperity")
    elif guild.stability < 40:
        factors.append("guild_instability")
    
    if guild.conflict_status.name in ["OPEN_CONFLICT", "UNDER_SIEGE"]:
        factors.append("guild_under_attack")
    
    if reputation < -0.3:
        factors.append("personal_shame")
    
    if "loyal" in npc.personality_traits:
        factors.append("naturally_loyal")
    elif "rebellious" in npc.personality_traits:
        factors.append("rebellious_nature")
    
    return factors

def _evaluate_guild_departure(npc: 'NPCProfile', guild: 'LocalGuild', 
                            changes: Dict[str, Any], reason: str) -> None:
    """Evaluate if an NPC should leave their guild."""
    departure_probability = 0.0
    
    if reason == "low_loyalty":
        departure_probability = abs(npc.guild_loyalty_score) * 0.3
    elif reason == "poor_reputation":
        departure_probability = 0.7  # Guild likely to expel
    
    # Personality affects likelihood to leave vs stay and fight
    if "rebellious" in npc.personality_traits:
        departure_probability += 0.2
    elif "loyal" in npc.personality_traits:
        departure_probability -= 0.3
    
    if random.random() < departure_probability:
        _process_guild_departure(npc, guild, changes, reason)

def _process_guild_departure(npc: 'NPCProfile', guild: 'LocalGuild', 
                           changes: Dict[str, Any], reason: str) -> None:
    """Process an NPC leaving their guild."""
    # Determine if this is voluntary resignation or expulsion
    is_expelled = reason in ["poor_reputation", "disciplinary_action"]
    action = "expelled" if is_expelled else "resigned"
    
    # Remove from guild
    guild.remove_member(npc.npc_id, action)
    
    # Update NPC profile
    old_guild_id = npc.guild_membership
    old_rank = npc.guild_rank
    
    npc.guild_membership = None
    npc.guild_rank = None
    npc.guild_loyalty_score = 0.0
    
    # Add to history
    npc.guild_history.append({
        'event': action,
        'guild_id': old_guild_id,
        'guild_name': guild.name,
        'rank': old_rank,
        'reason': reason,
        'timestamp': datetime.now()
    })
    
    # Record changes
    changes['guild_changes'].append({
        'action': action,
        'guild_id': old_guild_id,
        'guild_name': guild.name,
        'rank': old_rank,
        'reason': reason
    })
    
    # Narrative based on departure type
    if is_expelled:
        changes['narrative_events'].append(
            f"{npc.name} has been expelled from the {guild.name} "
            f"due to {'poor reputation' if reason == 'poor_reputation' else 'disciplinary issues'}."
        )
    else:
        changes['narrative_events'].append(
            f"{npc.name} has resigned from the {guild.name}, "
            f"citing {'personal conflicts' if reason == 'low_loyalty' else 'changing circumstances'}."
        )

def _find_guild_by_id(guild_id: str, guilds: List['LocalGuild']) -> Optional['LocalGuild']:
    """Find a guild by its ID."""
    for guild in guilds:
        if guild.guild_id == guild_id:
            return guild
    return None

def evaluate_player_guild_application(player_id: str, guild: 'LocalGuild', 
                                    player_reputation: float, player_wealth: float,
                                    application_method: str = "formal") -> Dict[str, Any]:
    """
    Evaluate a player character's application to join a guild.
    
    Unlike NPCs, player characters do not receive automatic acceptance
    and must navigate the guild's requirements and politics.
    
    Args:
        player_id: Player character ID
        guild: Guild to apply to
        player_reputation: Player's reputation in the settlement
        player_wealth: Player's wealth level
        application_method: How they're applying ("formal", "informal", "bribery", "coercion")
        
    Returns:
        Dictionary containing application result and requirements
    """
    result = {
        'player_id': player_id,
        'guild_id': guild.guild_id,
        'guild_name': guild.name,
        'application_method': application_method,
        'accepted': False,
        'requirements_met': [],
        'requirements_failed': [],
        'special_conditions': [],
        'narrative_response': ""
    }
    
    # Check basic requirements
    if len(guild.members) >= guild.member_cap:
        result['requirements_failed'].append("guild_at_capacity")
        result['narrative_response'] = f"The {guild.name} is currently at full capacity and not accepting new members."
        return result
    
    # Reputation check
    if player_reputation >= guild.skill_threshold['reputation']:
        result['requirements_met'].append("reputation_sufficient")
    else:
        result['requirements_failed'].append("reputation_insufficient")
    
    # Wealth check (if applicable)
    if player_wealth >= guild.skill_threshold['wealth']:
        result['requirements_met'].append("wealth_sufficient")
    else:
        result['requirements_failed'].append("wealth_insufficient")
    
    # Handle different application methods
    if application_method == "formal":
        # Standard application process
        if not result['requirements_failed']:
            result['accepted'] = True
            result['narrative_response'] = f"The {guild.name} formally accepts your application. Welcome, apprentice."
        else:
            result['narrative_response'] = f"The {guild.name} must respectfully decline your application at this time."
    
    elif application_method == "bribery":
        # Bribery can overcome some requirements but affects guild relationships
        bribe_effectiveness = min(0.8, player_wealth)
        if bribe_effectiveness > 0.5:
            result['accepted'] = True
            result['special_conditions'].append("joined_through_bribery")
            result['narrative_response'] = f"Your generous 'donation' has convinced the {guild.name} to overlook certain... formalities."
            # Reduce initial loyalty due to corrupt entry
        else:
            result['requirements_failed'].append("insufficient_bribe")
            result['narrative_response'] = f"The {guild.name} is offended by your crude attempt at bribery."
    
    elif application_method == "coercion":
        # Coercion is dangerous and can backfire
        if player_reputation > 0.5:  # Need good reputation to make threats credible
            result['accepted'] = True
            result['special_conditions'].append("joined_through_coercion")
            result['narrative_response'] = f"The {guild.name} reluctantly accepts you, though you sense their fear and resentment."
        else:
            result['requirements_failed'].append("threats_ineffective")
            result['narrative_response'] = f"The {guild.name} laughs off your empty threats and bars you from their premises."
    
    return result

def check_guild_job_availability(npc: 'NPCProfile', job_type: str, 
                                guilds: List['LocalGuild']) -> Dict[str, Any]:
    """
    Check if guild membership affects NPC job availability.
    
    Guild membership can provide exclusive access to certain jobs
    or block access to others based on guild politics.
    """
    result = {
        'npc_id': npc.npc_id,
        'job_type': job_type,
        'access_granted': True,
        'modifiers': [],
        'restrictions': [],
        'guild_benefits': []
    }
    
    if npc.guild_membership:
        guild = _find_guild_by_id(npc.guild_membership, guilds)
        if guild:
            # Guild members get priority for related jobs
            if _is_job_related_to_guild(job_type, guild.guild_type.value):
                result['modifiers'].append('guild_priority')
                result['guild_benefits'].append(f"Priority access through {guild.name} membership")
            
            # High-ranking members get additional benefits
            if npc.guild_rank in ['master', 'guildmaster']:
                result['modifiers'].append('senior_member_bonus')
                result['guild_benefits'].append("Senior guild rank provides professional reputation")
            
            # Guild conflicts can restrict certain jobs
            for rival_guild_id in guild.rival_guilds:
                rival_guild = _find_guild_by_id(rival_guild_id, guilds)
                if rival_guild and _is_job_related_to_guild(job_type, rival_guild.guild_type.value):
                    result['restrictions'].append(f"rival_guild_conflict_{rival_guild.name}")
    
    return result

def _is_job_related_to_guild(job_type: str, guild_type: str) -> bool:
    """Check if a job type is related to a guild type."""
    job_guild_relationships = {
        "merchant": ["merchants"],
        "craft": ["craftsmen"],
        "guard": ["warriors"],
        "research": ["scholars"],
        "magical": ["mages"],
        "criminal": ["thieves"]
    }
    
    related_guilds = job_guild_relationships.get(job_type, [])
    return guild_type in related_guilds

def simulate_guild_conspiracy(conspirators: List['NPCProfile'], 
                            target_guild: 'LocalGuild') -> Dict[str, Any]:
    """
    Simulate NPCs conspiring to form a splinter guild or take over existing leadership.
    
    This represents the organic formation of guild schisms and power struggles.
    """
    conspiracy = {
        'conspirators': [npc.npc_id for npc in conspirators],
        'target_guild': target_guild.guild_id,
        'conspiracy_type': 'unknown',
        'success_probability': 0.0,
        'requirements_met': [],
        'challenges': [],
        'potential_outcomes': []
    }
    
    # Determine conspiracy type based on conspirators' status
    members_in_guild = sum(1 for npc in conspirators if npc.guild_membership == target_guild.guild_id)
    outsiders = len(conspirators) - members_in_guild
    
    if members_in_guild > len(conspirators) * 0.6:
        conspiracy['conspiracy_type'] = 'internal_takeover'
    elif outsiders > members_in_guild:
        conspiracy['conspiracy_type'] = 'hostile_takeover'
    else:
        conspiracy['conspiracy_type'] = 'splinter_formation'
    
    # Calculate success probability
    base_probability = 0.3
    
    # Leader quality matters
    leader_qualities = []
    for npc in conspirators:
        if 'cunning' in npc.personality_traits:
            leader_qualities.append('cunning')
        if 'diplomatic' in npc.personality_traits:
            leader_qualities.append('diplomatic')
        if npc.guild_rank in ['master', 'guildmaster']:
            leader_qualities.append('senior_rank')
    
    if 'cunning' in leader_qualities:
        base_probability += 0.2
    if 'diplomatic' in leader_qualities:
        base_probability += 0.1
    if 'senior_rank' in leader_qualities:
        base_probability += 0.3
    
    # Guild stability affects success
    if target_guild.stability < 50:
        base_probability += 0.2
        conspiracy['requirements_met'].append('target_guild_unstable')
    
    # Guild loyalty affects internal conspiracies
    if target_guild.member_loyalty < 60:
        base_probability += 0.1
        conspiracy['requirements_met'].append('low_member_loyalty')
    
    conspiracy['success_probability'] = min(0.9, base_probability)
    
    # Define potential outcomes
    if conspiracy['conspiracy_type'] == 'internal_takeover':
        conspiracy['potential_outcomes'] = [
            'leadership_change',
            'policy_reform',
            'conspiracy_exposed',
            'guild_split'
        ]
    elif conspiracy['conspiracy_type'] == 'splinter_formation':
        conspiracy['potential_outcomes'] = [
            'new_guild_formed',
            'mass_resignation',
            'failed_recruitment',
            'compromise_reached'
        ]
    
    return conspiracy

# Testing and example usage
if __name__ == "__main__":
    print("=== NPC-Guild Integration System Test ===\n")
    
    # This would normally integrate with the full system
    # For now, we'll create mock examples to show functionality
    
    print("System ready for integration with NPC profiles and guild systems.")
    print("Key functions implemented:")
    print("- evaluate_guild_affiliation()")
    print("- evaluate_player_guild_application()")
    print("- check_guild_job_availability()")
    print("- simulate_guild_conspiracy()") 