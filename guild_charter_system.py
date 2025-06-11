"""
Guild Charter and Administration System

This module handles internal governance, rules, and justice logic for each guild.
It defines charter structures, policy enforcement, and punishment systems that
apply equally to NPCs and Player Characters.

The system ensures that guilds operate under consistent internal rules and
consequences, creating realistic power dynamics and accountability.
"""

import random
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum

# Avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from npc_profile import NPCProfile
    from guild_event_engine import LocalGuild

class PunishmentType(Enum):
    """Types of punishments available to guilds."""
    WARNING = "warning"
    FINE = "fine"
    DEMOTION = "demotion"
    SUSPENSION = "suspension"
    EXPULSION = "expulsion"
    BLACKLIST = "blacklist"
    COMMUNITY_SERVICE = "community_service"

class AmendmentType(Enum):
    """Types of charter amendments."""
    DOCTRINE_CHANGE = "doctrine_change"
    PROFESSION_UPDATE = "profession_update"
    REQUIREMENT_MODIFICATION = "requirement_modification"
    PUNISHMENT_REVISION = "punishment_revision"
    ECONOMIC_RIGHTS_CHANGE = "economic_rights_change"
    POLITICAL_REALIGNMENT = "political_realignment"

class GuildCharter:
    """
    Defines internal governance, rules, and justice logic for a guild.
    
    This class represents the foundational document that governs guild operations,
    member behavior, and internal justice. All guild actions must align with
    the charter or face consequences.
    """
    
    def __init__(self,
                 guild_id: str,
                 charter_name: str = "Guild Charter",
                 core_doctrine: str = "trade protection and mutual prosperity",
                 accepted_professions: Optional[List[str]] = None,
                 political_alignment: Optional[str] = None,
                 membership_requirements: Optional[Dict[str, Any]] = None,
                 punishment_policy: Optional[Dict[str, str]] = None,
                 promotion_criteria: Optional[Dict[str, Any]] = None,
                 economic_rights: Optional[Dict[str, bool]] = None,
                 is_outlawed: bool = False):
        """
        Initialize a guild charter.
        
        Args:
            guild_id: Unique identifier of the guild this charter governs
            charter_name: Display name of the charter
            core_doctrine: Fundamental principle of the guild
            accepted_professions: List of professions welcomed in the guild
            political_alignment: Faction ID or "neutral"
            membership_requirements: Requirements for joining (skills, loyalty, etc.)
            punishment_policy: Mapping of offenses to punishments
            promotion_criteria: Requirements for rank advancement
            economic_rights: Economic privileges and restrictions
            is_outlawed: Whether the guild is banned regionally/factionally
        """
        self.charter_id = str(uuid.uuid4())
        self.guild_id = guild_id
        self.charter_name = charter_name
        self.core_doctrine = core_doctrine
        self.accepted_professions = accepted_professions or ["merchant", "trader"]
        self.political_alignment = political_alignment
        self.membership_requirements = membership_requirements or self._default_membership_requirements()
        self.punishment_policy = punishment_policy or self._default_punishment_policy()
        self.promotion_criteria = promotion_criteria or self._default_promotion_criteria()
        self.economic_rights = economic_rights or self._default_economic_rights()
        self.is_outlawed = is_outlawed
        
        # Amendment tracking
        self.amendment_history: List[Dict[str, Any]] = []
        self.creation_date = datetime.now()
        self.last_amendment_date = datetime.now()
        
        # Charter validation and enforcement
        self.violation_tolerance = 0.3  # How lenient the guild is (0.0 = strict, 1.0 = lenient)
        self.internal_reputation_impact = 1.0  # How much charter violations affect internal reputation
        
        # Record creation
        self.amendment_history.append({
            'date': self.creation_date,
            'type': 'charter_creation',
            'description': f'Charter "{charter_name}" established',
            'amended_by': 'founding_members',
            'old_value': None,
            'new_value': 'charter_established'
        })
    
    def _default_membership_requirements(self) -> Dict[str, Any]:
        """Generate default membership requirements."""
        return {
            'min_skill_level': 0.4,     # Minimum skill in relevant profession
            'min_reputation': 0.1,      # Minimum local reputation
            'min_loyalty': 0.2,         # Minimum loyalty to settlement/faction
            'max_criminal_record': 2,   # Maximum serious crimes allowed
            'wealth_requirement': 0.0,  # Gold required for membership
            'sponsor_required': False,  # Whether existing member must sponsor
            'probation_period': 30      # Days of probationary membership
        }
    
    def _default_punishment_policy(self) -> Dict[str, str]:
        """Generate default punishment mappings."""
        return {
            'minor_theft': 'warning',
            'major_theft': 'suspension',
            'smuggling': 'expulsion',
            'betrayal_of_secrets': 'expulsion',
            'violence_against_member': 'demotion',
            'violence_against_outsider': 'fine',
            'failure_to_pay_dues': 'warning',
            'persistent_dues_default': 'suspension',
            'violation_of_trade_rules': 'fine',
            'competition_violation': 'demotion',
            'charter_violation': 'warning',
            'repeated_charter_violation': 'expulsion',
            'treason': 'blacklist',
            'desertion_in_crisis': 'expulsion',
            'corruption': 'demotion',
            'insubordination': 'warning'
        }
    
    def _default_promotion_criteria(self) -> Dict[str, Any]:
        """Generate default promotion requirements."""
        return {
            'apprentice_to_journeyman': {
                'min_skill': 0.6,
                'min_loyalty': 0.4,
                'min_reputation': 0.3,
                'time_in_rank': 180,  # days
                'required_projects': 2
            },
            'journeyman_to_master': {
                'min_skill': 0.8,
                'min_loyalty': 0.6,
                'min_reputation': 0.5,
                'time_in_rank': 365,
                'required_projects': 5,
                'sponsor_votes': 2  # Master or higher votes needed
            },
            'master_to_guildmaster': {
                'min_skill': 0.9,
                'min_loyalty': 0.8,
                'min_reputation': 0.7,
                'time_in_rank': 730,
                'required_projects': 10,
                'unanimous_master_vote': True,
                'leadership_experience': True
            }
        }
    
    def _default_economic_rights(self) -> Dict[str, bool]:
        """Generate default economic privileges."""
        return {
            'trade_control': False,     # Can control who trades what
            'tax_privileges': False,    # Reduced tax rates
            'monopoly_rights': False,   # Exclusive trade rights
            'price_setting': False,     # Can set standard prices
            'quality_standards': True,  # Can enforce quality standards
            'apprentice_training': True, # Can train apprentices
            'cross_border_trade': False, # Special trade permissions
            'government_contracts': False # Priority for government work
        }
    
    def get_charter_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the charter.
        
        Returns:
            Dictionary containing charter details
        """
        return {
            'charter_id': self.charter_id,
            'guild_id': self.guild_id,
            'charter_name': self.charter_name,
            'core_doctrine': self.core_doctrine,
            'accepted_professions': self.accepted_professions,
            'political_alignment': self.political_alignment,
            'membership_requirements': self.membership_requirements,
            'punishment_policy': self.punishment_policy,
            'promotion_criteria': self.promotion_criteria,
            'economic_rights': self.economic_rights,
            'is_outlawed': self.is_outlawed,
            'creation_date': self.creation_date.isoformat(),
            'last_amendment_date': self.last_amendment_date.isoformat(),
            'total_amendments': len(self.amendment_history),
            'violation_tolerance': self.violation_tolerance
        }

def evaluate_guild_policy_compliance(npc: 'NPCProfile', guild: 'LocalGuild') -> Optional[str]:
    """
    Check if NPC violates charter terms and return recommended punishment.
    
    Args:
        npc: NPC profile to evaluate
        guild: Local guild with charter
        
    Returns:
        Recommended punishment action if violation detected, None if compliant
    """
    if not hasattr(guild, 'charter') or guild.charter is None:
        return None
    
    charter = guild.charter
    compliance_report = evaluate_member_compliance(npc, charter)
    
    if not compliance_report['overall_compliant']:
        # Determine the most serious violation
        violations = compliance_report['violations']
        if not violations:
            return None
        
        # Find the most severe violation
        severity_order = {'low': 1, 'medium': 2, 'high': 3}
        most_severe = max(violations, key=lambda v: severity_order.get(v['severity'], 1))
        
        # Map violation types to offense categories
        violation_to_offense = {
            'profession_mismatch': 'charter_violation',
            'loyalty_violation': 'betrayal_of_secrets',
            'reputation_violation': 'charter_violation',
            'political_conflict': 'treason'
        }
        
        offense = violation_to_offense.get(most_severe['type'], 'charter_violation')
        
        # Look up punishment in charter policy
        return charter.punishment_policy.get(offense, 'warning')
    
    return None

def evaluate_member_compliance(npc: 'NPCProfile', charter: GuildCharter) -> Dict[str, Any]:
    """
    Evaluate if an NPC complies with charter requirements.
    
    Args:
        npc: NPC profile to evaluate
        charter: Guild charter to check against
        
    Returns:
        Dictionary containing compliance evaluation results
    """
    compliance_report = {
        'npc_id': npc.npc_id,
        'overall_compliant': True,
        'violations': [],
        'warnings': [],
        'compliance_score': 1.0,
        'recommended_action': None
    }
    
    violations = []
    warnings = []
    
    # Check profession alignment
    if hasattr(npc, 'profession') and npc.profession:
        if npc.profession not in charter.accepted_professions and 'any' not in charter.accepted_professions:
            violations.append({
                'type': 'profession_mismatch',
                'description': f'Profession "{npc.profession}" not accepted by guild',
                'severity': 'medium'
            })
    
    # Check loyalty requirements
    guild_loyalty = getattr(npc, 'guild_loyalty_score', 0.0)
    if guild_loyalty < charter.membership_requirements.get('min_loyalty', 0.2):
        if guild_loyalty < charter.membership_requirements['min_loyalty'] - 0.3:
            violations.append({
                'type': 'loyalty_violation',
                'description': f'Guild loyalty ({guild_loyalty:.2f}) severely below requirement',
                'severity': 'high'
            })
        else:
            warnings.append({
                'type': 'low_loyalty',
                'description': f'Guild loyalty ({guild_loyalty:.2f}) below requirement',
                'severity': 'low'
            })
    
    # Check reputation requirements
    local_rep = npc.reputation_local.get(npc.region, 0.0)
    min_rep = charter.membership_requirements.get('min_reputation', 0.1)
    if local_rep < min_rep:
        if local_rep < min_rep - 0.4:
            violations.append({
                'type': 'reputation_violation',
                'description': f'Local reputation ({local_rep:.2f}) severely below requirement',
                'severity': 'high'
            })
        else:
            warnings.append({
                'type': 'low_reputation',
                'description': f'Local reputation ({local_rep:.2f}) below requirement',
                'severity': 'low'
            })
    
    # Check political alignment conflicts  
    if charter.political_alignment and charter.political_alignment != "neutral":
        if npc.faction_affiliation and npc.faction_affiliation != charter.political_alignment:
            # Check if factions are hostile
            violations.append({
                'type': 'political_conflict',
                'description': f'Member affiliated with conflicting faction: {npc.faction_affiliation}',
                'severity': 'high'
            })
    
    # Calculate compliance score
    total_violations = len(violations)
    total_warnings = len(warnings)
    
    if total_violations > 0:
        compliance_report['overall_compliant'] = False
        # Score decreases based on violation severity
        severity_penalties = {'low': 0.1, 'medium': 0.2, 'high': 0.4}
        penalty = sum(severity_penalties.get(v['severity'], 0.2) for v in violations)
        compliance_report['compliance_score'] = max(0.0, 1.0 - penalty)
    else:
        # Minor penalty for warnings
        warning_penalty = total_warnings * 0.05
        compliance_report['compliance_score'] = max(0.5, 1.0 - warning_penalty)
    
    compliance_report['violations'] = violations
    compliance_report['warnings'] = warnings
    
    # Recommend action based on violations
    if total_violations > 0:
        high_severity_violations = [v for v in violations if v['severity'] == 'high']
        if len(high_severity_violations) >= 2:
            compliance_report['recommended_action'] = 'expulsion'
        elif len(high_severity_violations) == 1:
            compliance_report['recommended_action'] = 'suspension'
        else:
            compliance_report['recommended_action'] = 'warning'
    
    return compliance_report

def process_guild_punishment(guild: 'LocalGuild', npc: 'NPCProfile', offense: str) -> Dict[str, Any]:
    """
    Process punishment according to guild charter policy.
    
    Args:
        guild: Local guild administering punishment
        npc: NPC being punished
        offense: Type of offense committed
        
    Returns:
        Dictionary containing punishment details and effects
    """
    if not hasattr(guild, 'charter') or guild.charter is None:
        return {'error': 'Guild has no charter defined'}
    
    charter = guild.charter
    punishment_type = charter.punishment_policy.get(offense, 'warning')
    
    punishment_result = {
        'npc_id': npc.npc_id,
        'guild_id': guild.guild_id,
        'offense': offense,
        'punishment_type': punishment_type,
        'execution_date': datetime.now(),
        'effects': [],
        'success': True
    }
    
    # Execute punishment based on type
    if punishment_type == PunishmentType.WARNING.value:
        # Add warning to NPC's guild history
        warning_record = {
            'date': datetime.now(),
            'type': 'warning',
            'offense': offense,
            'guild_id': guild.guild_id,
            'details': f'Warned for {offense}'
        }
        npc.guild_history.append(warning_record)
        punishment_result['effects'].append('warning_recorded')
    
    elif punishment_type == PunishmentType.FINE.value:
        # Implement fine logic (would need wealth system)
        fine_amount = 50  # Base fine amount
        fine_record = {
            'date': datetime.now(),
            'type': 'fine',
            'offense': offense,
            'guild_id': guild.guild_id,
            'amount': fine_amount,
            'details': f'Fined {fine_amount} gold for {offense}'
        }
        npc.guild_history.append(fine_record)
        punishment_result['effects'].append(f'fined_{fine_amount}_gold')
    
    elif punishment_type == PunishmentType.DEMOTION.value:
        # Demote member if possible
        current_rank = getattr(npc, 'guild_rank', 'apprentice')
        rank_structure = getattr(guild, 'rank_structure', ['apprentice', 'journeyman', 'master', 'guildmaster'])
        
        if current_rank in rank_structure:
            current_index = rank_structure.index(current_rank)
            if current_index > 0:
                new_rank = rank_structure[current_index - 1]
                npc.guild_rank = new_rank
                
                demotion_record = {
                    'date': datetime.now(),
                    'type': 'demotion',
                    'offense': offense,
                    'guild_id': guild.guild_id,
                    'old_rank': current_rank,
                    'new_rank': new_rank,
                    'details': f'Demoted from {current_rank} to {new_rank} for {offense}'
                }
                npc.guild_history.append(demotion_record)
                punishment_result['effects'].append(f'demoted_to_{new_rank}')
        
        # Reduce loyalty as additional consequence
        npc.guild_loyalty_score = max(-1.0, npc.guild_loyalty_score - 0.2)
        punishment_result['effects'].append('loyalty_reduced')
    
    elif punishment_type == PunishmentType.SUSPENSION.value:
        # Temporary suspension from guild activities
        suspension_record = {
            'date': datetime.now(),
            'type': 'suspension',
            'offense': offense,
            'guild_id': guild.guild_id,
            'duration_days': 30,
            'details': f'Suspended for 30 days for {offense}'
        }
        npc.guild_history.append(suspension_record)
        
        # Reduce loyalty and reputation
        npc.guild_loyalty_score = max(-1.0, npc.guild_loyalty_score - 0.3)
        if guild.base_settlement in npc.reputation_local:
            npc.reputation_local[guild.base_settlement] = max(-1.0, 
                npc.reputation_local[guild.base_settlement] - 0.1)
        
        punishment_result['effects'].extend(['suspended_30_days', 'loyalty_reduced', 'reputation_reduced'])
    
    elif punishment_type == PunishmentType.EXPULSION.value:
        # Remove from guild permanently
        npc.guild_membership = None
        npc.guild_rank = None
        npc.guild_loyalty_score = -0.5  # Set to negative but not completely hostile
        
        expulsion_record = {
            'date': datetime.now(),
            'type': 'expulsion',
            'offense': offense,
            'guild_id': guild.guild_id,
            'details': f'Expelled from guild for {offense}'
        }
        npc.guild_history.append(expulsion_record)
        
        # Remove from guild member list
        if hasattr(guild, 'members') and npc.npc_id in guild.members:
            guild.members.remove(npc.npc_id)
            guild.member_count = max(0, guild.member_count - 1)
        
        # Reputation impact in settlement
        if guild.base_settlement in npc.reputation_local:
            npc.reputation_local[guild.base_settlement] = max(-1.0, 
                npc.reputation_local[guild.base_settlement] - 0.2)
        
        punishment_result['effects'].extend(['expelled_from_guild', 'reputation_reduced'])
    
    elif punishment_type == PunishmentType.BLACKLIST.value:
        # Permanent blacklist - cannot join any guild of this type
        npc.guild_membership = None
        npc.guild_rank = None
        npc.guild_loyalty_score = -1.0  # Maximum hostility
        
        blacklist_record = {
            'date': datetime.now(),
            'type': 'blacklist',
            'offense': offense,
            'guild_id': guild.guild_id,
            'guild_type': guild.guild_type.value if hasattr(guild.guild_type, 'value') else str(guild.guild_type),
            'details': f'Blacklisted from all {guild.guild_type} guilds for {offense}'
        }
        npc.guild_history.append(blacklist_record)
        
        # Remove from guild member list
        if hasattr(guild, 'members') and npc.npc_id in guild.members:
            guild.members.remove(npc.npc_id)
            guild.member_count = max(0, guild.member_count - 1)
        
        # Severe reputation impact
        if guild.base_settlement in npc.reputation_local:
            npc.reputation_local[guild.base_settlement] = max(-1.0, 
                npc.reputation_local[guild.base_settlement] - 0.4)
        
        punishment_result['effects'].extend(['blacklisted_permanently', 'severe_reputation_loss'])
    
    elif punishment_type == PunishmentType.COMMUNITY_SERVICE.value:
        # Community service requirement
        service_record = {
            'date': datetime.now(),
            'type': 'community_service',
            'offense': offense,
            'guild_id': guild.guild_id,
            'service_hours': 40,
            'details': f'Assigned 40 hours community service for {offense}'
        }
        npc.guild_history.append(service_record)
        
        # Small loyalty reduction
        npc.guild_loyalty_score = max(-1.0, npc.guild_loyalty_score - 0.1)
        punishment_result['effects'].extend(['community_service_assigned', 'minor_loyalty_reduction'])
    
    # Log the punishment in guild history
    if hasattr(guild, 'historical_events'):
        guild.historical_events.append({
            'date': datetime.now(),
            'type': 'member_punishment',
            'member_id': npc.npc_id,
            'member_name': npc.name,
            'offense': offense,
            'punishment': punishment_type,
            'details': f'{npc.name} punished with {punishment_type} for {offense}'
        })
    
    return punishment_result

def generate_default_charter(guild_id: str, guild_type: str, guild_name: str) -> GuildCharter:
    """
    Generate a default charter for a new guild.
    
    Args:
        guild_id: Unique identifier of the guild
        guild_type: Type of guild (merchants, craftsmen, etc.)
        guild_name: Name of the guild
        
    Returns:
        New GuildCharter instance with appropriate defaults
    """
    # Customize based on guild type
    type_defaults = {
        'merchants': {
            'core_doctrine': 'fair trade and mutual prosperity',
            'accepted_professions': ['merchant', 'trader', 'banker', 'caravan_master'],
            'economic_rights': {
                'trade_control': True,
                'tax_privileges': False,
                'monopoly_rights': False,
                'price_setting': True,
                'quality_standards': True,
                'apprentice_training': True,
                'cross_border_trade': True,
                'government_contracts': False
            }
        },
        'craftsmen': {
            'core_doctrine': 'mastery of craft and protection of trade secrets',
            'accepted_professions': ['blacksmith', 'carpenter', 'mason', 'jeweler', 'tailor'],
            'economic_rights': {
                'trade_control': False,
                'tax_privileges': False,
                'monopoly_rights': True,
                'price_setting': True,
                'quality_standards': True,
                'apprentice_training': True,
                'cross_border_trade': False,
                'government_contracts': True
            }
        },
        'scholars': {
            'core_doctrine': 'pursuit of knowledge and preservation of learning',
            'accepted_professions': ['scribe', 'scholar', 'librarian', 'teacher', 'researcher'],
            'economic_rights': {
                'trade_control': False,
                'tax_privileges': True,
                'monopoly_rights': False,
                'price_setting': False,
                'quality_standards': True,
                'apprentice_training': True,
                'cross_border_trade': False,
                'government_contracts': True
            }
        },
        'warriors': {
            'core_doctrine': 'protection of the innocent and martial excellence',
            'accepted_professions': ['guard', 'soldier', 'mercenary', 'trainer'],
            'economic_rights': {
                'trade_control': False,
                'tax_privileges': False,
                'monopoly_rights': False,
                'price_setting': False,
                'quality_standards': True,
                'apprentice_training': True,
                'cross_border_trade': False,
                'government_contracts': True
            }
        }
    }
    
    defaults = type_defaults.get(guild_type.lower(), type_defaults['merchants'])
    
    return GuildCharter(
        guild_id=guild_id,
        charter_name=f"{guild_name} Charter",
        core_doctrine=defaults['core_doctrine'],
        accepted_professions=defaults['accepted_professions'],
        economic_rights=defaults['economic_rights']
    )

def evaluate_charter_violation_risk(npc: 'NPCProfile', guild: 'LocalGuild') -> float:
    """
    Evaluate the risk of an NPC violating guild charter in the future.
    
    Args:
        npc: NPC profile to evaluate
        guild: Local guild with charter
        
    Returns:
        Risk score from 0.0 (very low risk) to 1.0 (very high risk)
    """
    if not hasattr(guild, 'charter') or guild.charter is None:
        return 0.0
    
    risk_factors = []
    
    # Low loyalty increases violation risk
    loyalty = getattr(npc, 'guild_loyalty_score', 0.0)
    if loyalty < 0.0:
        risk_factors.append(abs(loyalty) * 0.3)
    elif loyalty < 0.3:
        risk_factors.append((0.3 - loyalty) * 0.2)
    
    # Personality traits that increase risk
    risky_traits = ['rebellious', 'greedy', 'impulsive', 'cunning', 'aggressive']
    trait_risk = sum(0.1 for trait in risky_traits if trait in npc.personality_traits)
    if trait_risk > 0:
        risk_factors.append(min(0.4, trait_risk))
    
    # Poor reputation increases risk
    local_rep = npc.reputation_local.get(npc.region, 0.0)
    if local_rep < -0.2:
        risk_factors.append(abs(local_rep) * 0.2)
    
    # Political conflicts increase risk
    if guild.charter.political_alignment and guild.charter.political_alignment != "neutral":
        if npc.faction_affiliation and npc.faction_affiliation != guild.charter.political_alignment:
            risk_factors.append(0.3)
    
    # History of violations increases future risk
    violation_history = [event for event in npc.guild_history 
                        if event.get('type') in ['warning', 'fine', 'demotion', 'suspension']]
    if len(violation_history) > 0:
        history_risk = min(0.4, len(violation_history) * 0.1)
        risk_factors.append(history_risk)
    
    # Calculate total risk
    total_risk = sum(risk_factors)
    return min(1.0, total_risk) 