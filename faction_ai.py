#!/usr/bin/env python3
"""
Faction AI Controller

Provides autonomous behavior for factions, enabling them to evolve
their ideologies, goals, and internal structure over time based on
pressures, events, and changing circumstances.
"""

import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

# Import faction system
from faction_generator import Faction


class FactionAIController:
    """
    Autonomous AI controller for faction behavior and evolution.
    
    Manages faction decision-making, ideology shifts, goal adjustments,
    and internal events based on pressures and circumstances.
    """
    
    def __init__(self, faction_ref: Faction):
        """
        Initialize faction AI controller.
        
        Args:
            faction_ref: Reference to the Faction object to control
        """
        self.faction_ref = faction_ref
        self.internal_pressure = 0.0  # 0.0 to 1.0 - instability/tension
        self.external_pressure = 0.0  # 0.0 to 1.0 - external threats
        self.evolution_log: List[Dict[str, Any]] = []
        
        # AI state tracking
        self.last_evaluation = datetime.now()
        self.pressure_history: List[Tuple[float, float]] = []  # (internal, external) over time
        self.recent_events: List[str] = []  # Recent significant events
        self.leadership_stability = 1.0  # 0.0 to 1.0
        self.member_satisfaction = 0.7  # 0.0 to 1.0
        
        # AI parameters
        self.ideology_change_rate = 0.05  # Max change per tick
        self.pressure_decay_rate = 0.02   # How fast pressure naturally decreases
        self.event_probability_base = 0.1  # Base chance of internal events
        
        # Initialize baseline satisfaction based on faction type
        self._initialize_baseline_satisfaction()
    
    def _initialize_baseline_satisfaction(self) -> None:
        """Set initial member satisfaction based on faction archetype."""
        archetype = getattr(self.faction_ref, 'archetype', 'unknown')
        
        satisfaction_by_archetype = {
            'religious_cult': 0.8,      # High initial devotion
            'trade_guild': 0.6,         # Moderate satisfaction
            'rogue_military': 0.5,      # Disciplined but potentially restless
            'thieves_guild': 0.4,       # Inherently unstable
            'rebel_movement': 0.7,      # High initial enthusiasm
            'scholar_collective': 0.8,  # Intellectual satisfaction
            'unknown': 0.5
        }
        
        self.member_satisfaction = satisfaction_by_archetype.get(archetype, 0.5)
        self.leadership_stability = random.uniform(0.6, 0.9)
    
    def evaluate_pressure(self, 
                         external_factors: Optional[Dict[str, float]] = None,
                         resource_shortfall: float = 0.0,
                         recent_failures: int = 0,
                         recent_successes: int = 0) -> Dict[str, float]:
        """
        Evaluate and update internal and external pressure levels.
        
        Args:
            external_factors: Dict of external pressure sources
            resource_shortfall: How much resources are below needs (0.0-1.0)
            recent_failures: Number of recent goal failures
            recent_successes: Number of recent goal successes
            
        Returns:
            Dict containing pressure analysis
        """
        external_factors = external_factors or {}
        
        # === INTERNAL PRESSURE CALCULATION ===
        
        # Resource pressure
        resource_pressure = min(1.0, resource_shortfall * 2.0)
        
        # Leadership stability pressure
        leadership_pressure = 1.0 - self.leadership_stability
        
        # Member satisfaction pressure
        satisfaction_pressure = 1.0 - self.member_satisfaction
        
        # Goal failure pressure
        failure_pressure = min(1.0, recent_failures * 0.3)
        
        # Ideology coherence pressure (factions with extreme conflicting values)
        ideology = self.faction_ref.ideology
        coherence_conflicts = 0
        
        # Check for ideological contradictions
        if ideology['order'] > 0.7 and ideology['freedom'] > 0.7:
            coherence_conflicts += 0.3
        if ideology['violence'] > 0.7 and ideology['justice'] > 0.7:
            coherence_conflicts += 0.2
        if ideology['tradition'] > 0.7 and ideology['progress'] > 0.7:
            coherence_conflicts += 0.2
        
        ideology_pressure = min(1.0, coherence_conflicts)
        
        # Calculate total internal pressure
        internal_components = {
            'resource_shortage': resource_pressure * 0.3,
            'leadership_instability': leadership_pressure * 0.25,
            'member_dissatisfaction': satisfaction_pressure * 0.25,
            'goal_failures': failure_pressure * 0.15,
            'ideology_conflicts': ideology_pressure * 0.05
        }
        
        new_internal = sum(internal_components.values())
        
        # === EXTERNAL PRESSURE CALCULATION ===
        
        # Base external factors
        external_components = {}
        for factor, value in external_factors.items():
            external_components[factor] = min(1.0, max(0.0, value))
        
        # Faction size vulnerability (smaller factions more vulnerable)
        member_count = len(self.faction_ref.members)
        size_vulnerability = max(0.0, 1.0 - (member_count / 100.0))  # Vulnerable if < 100 members
        external_components['size_vulnerability'] = size_vulnerability * 0.2
        
        # Regional instability (more factions = more conflict)
        # This would be calculated externally and passed in, for now use base value
        external_components['regional_instability'] = external_factors.get('regional_instability', 0.1)
        
        new_external = min(1.0, sum(external_components.values()))
        
        # === PRESSURE UPDATE WITH MOMENTUM ===
        
        # Apply momentum (gradual change rather than instant)
        momentum_factor = 0.3
        self.internal_pressure = (self.internal_pressure * (1 - momentum_factor) + 
                                 new_internal * momentum_factor)
        self.external_pressure = (self.external_pressure * (1 - momentum_factor) + 
                                 new_external * momentum_factor)
        
        # Apply natural decay
        self.internal_pressure *= (1 - self.pressure_decay_rate)
        self.external_pressure *= (1 - self.pressure_decay_rate)
        
        # Clamp to valid range
        self.internal_pressure = max(0.0, min(1.0, self.internal_pressure))
        self.external_pressure = max(0.0, min(1.0, self.external_pressure))
        
        # Update history
        self.pressure_history.append((self.internal_pressure, self.external_pressure))
        if len(self.pressure_history) > 20:  # Keep last 20 readings
            self.pressure_history.pop(0)
        
        analysis = {
            'internal_pressure': self.internal_pressure,
            'external_pressure': self.external_pressure,
            'internal_components': internal_components,
            'external_components': external_components,
            'total_pressure': (self.internal_pressure + self.external_pressure) / 2.0
        }
        
        return analysis
    
    def shift_ideology(self, pressure_analysis: Dict[str, float]) -> Dict[str, float]:
        """
        Modify faction ideology based on current pressures and circumstances.
        
        Args:
            pressure_analysis: Results from evaluate_pressure()
            
        Returns:
            Dict of ideology changes made
        """
        ideology = self.faction_ref.ideology
        changes = {}
        
        total_pressure = pressure_analysis['total_pressure']
        internal_pressure = pressure_analysis['internal_pressure']
        external_pressure = pressure_analysis['external_pressure']
        
        # === PRESSURE-BASED IDEOLOGY SHIFTS ===
        
        # High external pressure -> more authoritarian responses
        if external_pressure > 0.6:
            if random.random() < external_pressure:
                authority_shift = random.uniform(0.02, self.ideology_change_rate)
                ideology['authority'] = min(1.0, ideology['authority'] + authority_shift)
                changes['authority'] = f"+{authority_shift:.3f} (external threats)"
                
                # Reduce freedom under external pressure
                freedom_shift = random.uniform(0.01, self.ideology_change_rate * 0.7)
                ideology['freedom'] = max(0.0, ideology['freedom'] - freedom_shift)
                changes['freedom'] = f"-{freedom_shift:.3f} (security over liberty)"
        
        # High internal pressure -> different responses based on faction type
        if internal_pressure > 0.5:
            archetype = getattr(self.faction_ref, 'archetype', 'unknown')
            
            if archetype in ['rogue_military', 'thieves_guild']:
                # Military/criminal factions turn to violence under pressure
                if random.random() < internal_pressure * 0.8:
                    violence_shift = random.uniform(0.02, self.ideology_change_rate)
                    ideology['violence'] = min(1.0, ideology['violence'] + violence_shift)
                    changes['violence'] = f"+{violence_shift:.3f} (internal pressure -> force)"
            
            elif archetype in ['rebel_movement', 'scholar_collective']:
                # Rebels/scholars turn to freedom and progress under pressure
                if random.random() < internal_pressure * 0.6:
                    freedom_shift = random.uniform(0.01, self.ideology_change_rate * 0.8)
                    ideology['freedom'] = min(1.0, ideology['freedom'] + freedom_shift)
                    changes['freedom'] = f"+{freedom_shift:.3f} (pressure -> liberation)"
                    
                    progress_shift = random.uniform(0.01, self.ideology_change_rate * 0.6)
                    ideology['progress'] = min(1.0, ideology['progress'] + progress_shift)
                    changes['progress'] = f"+{progress_shift:.3f} (reform pressure)"
            
            elif archetype == 'religious_cult':
                # Religious factions become more traditional under pressure
                if random.random() < internal_pressure * 0.7:
                    tradition_shift = random.uniform(0.02, self.ideology_change_rate)
                    ideology['tradition'] = min(1.0, ideology['tradition'] + tradition_shift)
                    changes['tradition'] = f"+{tradition_shift:.3f} (return to roots)"
        
        # === SUCCESS/FAILURE ADAPTATIONS ===
        
        # Recent successes reinforce current ideology
        recent_successes = len([e for e in self.recent_events if 'success' in e])
        if recent_successes > 0:
            # Slightly reinforce dominant ideological traits
            dominant_trait = max(ideology.items(), key=lambda x: x[1])
            if dominant_trait[1] < 0.9:
                reinforce_shift = random.uniform(0.01, 0.03) * recent_successes
                ideology[dominant_trait[0]] = min(1.0, ideology[dominant_trait[0]] + reinforce_shift)
                changes[dominant_trait[0]] = f"+{reinforce_shift:.3f} (success reinforcement)"
        
        # Recent failures cause ideological questioning
        recent_failures = len([e for e in self.recent_events if 'failure' in e])
        if recent_failures > 1:
            # Question dominant ideology, shift toward pragmatism
            if random.random() < 0.4:
                # Reduce extreme values slightly
                for trait, value in ideology.items():
                    if value > 0.8:
                        reduction = random.uniform(0.01, 0.03) * recent_failures
                        ideology[trait] = max(0.0, ideology[trait] - reduction)
                        changes[trait] = f"-{reduction:.3f} (failure adaptation)"
                        break
        
        # === RANDOM IDEOLOGICAL DRIFT ===
        
        # Small random changes to represent natural evolution
        if random.random() < 0.2:
            trait_to_change = random.choice(list(ideology.keys()))
            drift_amount = random.uniform(-0.02, 0.02)
            old_value = ideology[trait_to_change]
            ideology[trait_to_change] = max(0.0, min(1.0, old_value + drift_amount))
            
            if abs(drift_amount) > 0.005:  # Only log significant drifts
                changes[trait_to_change] = f"{drift_amount:+.3f} (natural drift)"
        
        # Update faction ideology
        self.faction_ref.ideology = ideology
        
        return changes
    
    def adjust_goals(self, pressure_analysis: Dict[str, float]) -> Dict[str, Any]:
        """
        Update faction goals based on current circumstances and pressures.
        
        Args:
            pressure_analysis: Current pressure analysis
            
        Returns:
            Dict of goal changes made
        """
        goals = self.faction_ref.goals.copy()
        changes = {
            'added_goals': [],
            'removed_goals': [],
            'modified_goals': []
        }
        
        total_pressure = pressure_analysis['total_pressure']
        internal_pressure = pressure_analysis['internal_pressure']
        external_pressure = pressure_analysis['external_pressure']
        
        # === PRESSURE-BASED GOAL ADAPTATION ===
        
        # High internal pressure -> focus on internal stability
        if internal_pressure > 0.7:
            stability_goals = [
                "consolidate internal power",
                "purge disloyal members", 
                "reform leadership structure",
                "improve member conditions",
                "resolve ideological conflicts"
            ]
            
            # Add stability goal if not present
            current_goal_text = ' '.join(goals)
            needs_stability_goal = not any(goal in current_goal_text.lower() 
                                          for goal in ['consolidate', 'purge', 'reform', 'improve'])
            
            if needs_stability_goal and len(goals) < 5:
                new_goal = random.choice(stability_goals)
                goals.append(new_goal)
                changes['added_goals'].append(f"'{new_goal}' (internal pressure response)")
        
        # High external pressure -> defensive/aggressive goals
        if external_pressure > 0.6:
            defensive_goals = [
                "strengthen defenses against threats",
                "form defensive alliances",
                "gather intelligence on enemies",
                "secure additional resources",
                "establish backup strongholds"
            ]
            
            aggressive_goals = [
                "eliminate primary threat",
                "launch preemptive strike", 
                "expand territorial control",
                "destabilize enemy factions"
            ]
            
            # Choose response based on faction ideology
            ideology = self.faction_ref.ideology
            
            if ideology['violence'] > 0.6 and random.random() < 0.6:
                # Aggressive response
                new_goal = random.choice(aggressive_goals)
                goals.insert(0, new_goal)  # High priority
                changes['added_goals'].append(f"'{new_goal}' (aggressive response to threats)")
            else:
                # Defensive response
                new_goal = random.choice(defensive_goals)
                goals.append(new_goal)
                changes['added_goals'].append(f"'{new_goal}' (defensive response to threats)")
        
        # === GOAL SUCCESS/FAILURE ADAPTATION ===
        
        # Simulate goal progress and outcomes
        for i, goal in enumerate(goals[:]):
            # Random chance of goal completion or failure
            completion_chance = 0.1 + (self.member_satisfaction * 0.1)
            failure_chance = 0.05 + (total_pressure * 0.15)
            
            if random.random() < completion_chance:
                # Goal succeeded
                goals.remove(goal)
                changes['removed_goals'].append(f"'{goal}' (COMPLETED)")
                self.recent_events.append(f"goal_success: {goal}")
                
                # Success improves satisfaction
                self.member_satisfaction = min(1.0, self.member_satisfaction + 0.05)
                
            elif random.random() < failure_chance:
                # Goal failed
                goals.remove(goal)
                changes['removed_goals'].append(f"'{goal}' (FAILED)")
                self.recent_events.append(f"goal_failure: {goal}")
                
                # Failure reduces satisfaction
                self.member_satisfaction = max(0.0, self.member_satisfaction - 0.08)
        
        # === OPPORTUNISTIC GOAL GENERATION ===
        
        # Add new goals based on faction archetype and current ideology
        if len(goals) < 4 and random.random() < 0.3:
            archetype = getattr(self.faction_ref, 'archetype', 'unknown')
            ideology = self.faction_ref.ideology
            
            archetype_goals = {
                'religious_cult': [
                    "convert more followers",
                    "build new temple",
                    "spread the faith to neighboring regions",
                    "acquire sacred artifacts"
                ],
                'trade_guild': [
                    "establish new trade routes", 
                    "monopolize key commodities",
                    "negotiate favorable trade agreements",
                    "eliminate competition"
                ],
                'rogue_military': [
                    "recruit experienced soldiers",
                    "acquire better weapons and armor", 
                    "establish military base",
                    "take control of strategic location"
                ],
                'thieves_guild': [
                    "infiltrate merchant guilds",
                    "establish fencing operation",
                    "corrupt local officials",
                    "expand criminal network"
                ],
                'rebel_movement': [
                    "overthrow current leadership",
                    "liberate oppressed peoples", 
                    "expose government corruption",
                    "organize popular uprising"
                ],
                'scholar_collective': [
                    "establish research library",
                    "discover ancient knowledge",
                    "educate the masses",
                    "preserve important texts"
                ]
            }
            
            potential_goals = archetype_goals.get(archetype, [
                "expand influence",
                "gather resources", 
                "improve capabilities",
                "achieve recognition"
            ])
            
            # Modify goals based on dominant ideology
            if ideology['violence'] > 0.7:
                potential_goals.extend([
                    "eliminate key rivals",
                    "demonstrate power through force",
                    "crush opposition"
                ])
            
            if ideology['freedom'] > 0.7:
                potential_goals.extend([
                    "liberate oppressed groups",
                    "break unjust laws",
                    "promote individual rights"
                ])
            
            new_goal = random.choice(potential_goals)
            if new_goal not in goals:
                goals.append(new_goal)
                changes['added_goals'].append(f"'{new_goal}' (opportunistic expansion)")
        
        # Update faction goals
        self.faction_ref.goals = goals
        
        return changes
    
    def trigger_internal_events(self, pressure_analysis: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Simulate internal faction events based on current pressures.
        
        Args:
            pressure_analysis: Current pressure analysis
            
        Returns:
            List of events that occurred
        """
        events = []
        
        total_pressure = pressure_analysis['total_pressure']
        internal_pressure = pressure_analysis['internal_pressure']
        
        # Base event probability modified by pressure
        event_probability = self.event_probability_base + (total_pressure * 0.3)
        
        # === LEADERSHIP EVENTS ===
        
        if random.random() < event_probability * 0.4:
            leadership_events = []
            
            if self.leadership_stability < 0.4:
                leadership_events.extend([
                    "leadership_coup", "power_struggle", "leadership_purge"
                ])
            elif self.leadership_stability < 0.7:
                leadership_events.extend([
                    "leadership_challenge", "succession_dispute", "advisor_conflict"
                ])
            else:
                leadership_events.extend([
                    "leadership_consolidation", "new_appointments", "policy_reform"
                ])
            
            if leadership_events:
                event_type = random.choice(leadership_events)
                
                if event_type in ["leadership_coup", "power_struggle"]:
                    # Major leadership change
                    self.leadership_stability = random.uniform(0.2, 0.6)
                    self.member_satisfaction *= 0.8  # Disruption
                    
                    event = {
                        'type': event_type,
                        'description': f"Major leadership upheaval in {self.faction_ref.name}",
                        'impact': 'high',
                        'stability_change': -0.3,
                        'satisfaction_change': -0.2
                    }
                    
                elif event_type in ["leadership_challenge", "succession_dispute"]:
                    # Moderate leadership stress
                    self.leadership_stability *= 0.9
                    
                    event = {
                        'type': event_type, 
                        'description': f"Internal leadership tensions in {self.faction_ref.name}",
                        'impact': 'medium',
                        'stability_change': -0.1,
                        'satisfaction_change': -0.05
                    }
                    
                else:
                    # Positive leadership development
                    self.leadership_stability = min(1.0, self.leadership_stability + 0.1)
                    self.member_satisfaction = min(1.0, self.member_satisfaction + 0.05)
                    
                    event = {
                        'type': event_type,
                        'description': f"Leadership strengthened in {self.faction_ref.name}",
                        'impact': 'positive',
                        'stability_change': 0.1,
                        'satisfaction_change': 0.05
                    }
                
                events.append(event)
                self.recent_events.append(f"{event_type}: {event['description']}")
        
        # === MEMBERSHIP EVENTS ===
        
        if random.random() < event_probability * 0.3:
            membership_events = []
            
            if self.member_satisfaction < 0.3:
                membership_events.extend([
                    "mass_defection", "member_revolt", "splinter_group_formation"
                ])
            elif self.member_satisfaction < 0.6:
                membership_events.extend([
                    "member_unrest", "demands_for_change", "faction_criticism"
                ])
            else:
                membership_events.extend([
                    "recruitment_surge", "member_loyalty_increase", "new_talent_join"
                ])
            
            if membership_events:
                event_type = random.choice(membership_events)
                member_count = len(self.faction_ref.members)
                
                if event_type in ["mass_defection", "member_revolt"]:
                    # Lose members
                    members_lost = random.randint(1, max(1, member_count // 4))
                    for _ in range(min(members_lost, len(self.faction_ref.members))):
                        if self.faction_ref.members:
                            self.faction_ref.members.pop()
                    
                    self.member_satisfaction = max(0.0, self.member_satisfaction - 0.15)
                    
                    event = {
                        'type': event_type,
                        'description': f"{members_lost} members left {self.faction_ref.name}",
                        'impact': 'negative',
                        'members_changed': -members_lost,
                        'satisfaction_change': -0.15
                    }
                    
                elif event_type in ["recruitment_surge", "new_talent_join"]:
                    # Gain members
                    new_members = random.randint(1, max(1, member_count // 6))
                    for i in range(new_members):
                        new_member_id = f"recruit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"
                        self.faction_ref.members.append(new_member_id)
                    
                    self.member_satisfaction = min(1.0, self.member_satisfaction + 0.1)
                    
                    event = {
                        'type': event_type,
                        'description': f"{new_members} new members joined {self.faction_ref.name}",
                        'impact': 'positive',
                        'members_changed': new_members,
                        'satisfaction_change': 0.1
                    }
                    
                else:
                    # Neutral membership events
                    satisfaction_change = random.uniform(-0.05, 0.05)
                    self.member_satisfaction = max(0.0, min(1.0, 
                                                          self.member_satisfaction + satisfaction_change))
                    
                    event = {
                        'type': event_type,
                        'description': f"Membership dynamics shifted in {self.faction_ref.name}",
                        'impact': 'neutral',
                        'members_changed': 0,
                        'satisfaction_change': satisfaction_change
                    }
                
                events.append(event)
                self.recent_events.append(f"{event_type}: {event['description']}")
        
        # === DOCTRINAL/IDEOLOGICAL EVENTS ===
        
        if random.random() < event_probability * 0.2:
            doctrinal_events = [
                "doctrinal_reform", "ideological_purge", "theological_debate",
                "policy_revision", "fundamental_reassessment"
            ]
            
            event_type = random.choice(doctrinal_events)
            
            # These events can cause ideology shifts
            ideology_trait = random.choice(list(self.faction_ref.ideology.keys()))
            shift_amount = random.uniform(-0.1, 0.1)
            
            old_value = self.faction_ref.ideology[ideology_trait]
            self.faction_ref.ideology[ideology_trait] = max(0.0, min(1.0, old_value + shift_amount))
            
            event = {
                'type': event_type,
                'description': f"Doctrinal shift in {self.faction_ref.name}: {ideology_trait} {shift_amount:+.3f}",
                'impact': 'ideological',
                'ideology_change': {ideology_trait: shift_amount}
            }
            
            events.append(event)
            self.recent_events.append(f"{event_type}: doctrinal change")
        
        # Clean up old events (keep last 10)
        if len(self.recent_events) > 10:
            self.recent_events = self.recent_events[-10:]
        
        return events
    
    def log_evolution(self, 
                     pressure_analysis: Dict[str, float],
                     ideology_changes: Dict[str, float],
                     goal_changes: Dict[str, Any],
                     internal_events: List[Dict[str, Any]]) -> None:
        """
        Store a timestamped snapshot of changes made during current tick.
        
        Args:
            pressure_analysis: Pressure evaluation results
            ideology_changes: Ideology shifts made
            goal_changes: Goal adjustments made  
            internal_events: Internal events that occurred
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'faction_id': self.faction_ref.faction_id,
            'faction_name': self.faction_ref.name,
            'pressures': {
                'internal': pressure_analysis['internal_pressure'],
                'external': pressure_analysis['external_pressure'],
                'total': pressure_analysis['total_pressure']
            },
            'faction_state': {
                'member_count': len(self.faction_ref.members),
                'member_satisfaction': self.member_satisfaction,
                'leadership_stability': self.leadership_stability,
                'ideology': self.faction_ref.ideology.copy(),
                'goals': self.faction_ref.goals.copy()
            },
            'changes': {
                'ideology_shifts': ideology_changes,
                'goal_changes': goal_changes,
                'internal_events': internal_events
            }
        }
        
        self.evolution_log.append(log_entry)
        
        # Keep last 50 log entries
        if len(self.evolution_log) > 50:
            self.evolution_log.pop(0)
    
    def simulate_tick(self, 
                     external_factors: Optional[Dict[str, float]] = None,
                     player_actions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run full AI logic for a single time step.
        
        Args:
            external_factors: External pressure sources
            player_actions: Player interference effects
            
        Returns:
            Dict summarizing all changes made during this tick
        """
        external_factors = external_factors or {}
        player_actions = player_actions or {}
        
        # Apply player actions first
        if player_actions:
            self._apply_player_actions(player_actions)
        
        # Evaluate current pressures
        pressure_analysis = self.evaluate_pressure(
            external_factors=external_factors,
            resource_shortfall=random.uniform(0.0, 0.3),  # Simulate resource variation
            recent_failures=len([e for e in self.recent_events if 'failure' in e]),
            recent_successes=len([e for e in self.recent_events if 'success' in e])
        )
        
        # Make AI decisions
        ideology_changes = self.shift_ideology(pressure_analysis)
        goal_changes = self.adjust_goals(pressure_analysis)
        internal_events = self.trigger_internal_events(pressure_analysis)
        
        # Log everything
        self.log_evolution(pressure_analysis, ideology_changes, goal_changes, internal_events)
        
        # Update last evaluation time
        self.last_evaluation = datetime.now()
        
        return {
            'tick_summary': {
                'faction': self.faction_ref.name,
                'pressure_total': pressure_analysis['total_pressure'],
                'ideology_changes': len(ideology_changes),
                'goal_changes': sum(len(v) if isinstance(v, list) else 1 for v in goal_changes.values()),
                'internal_events': len(internal_events),
                'member_count': len(self.faction_ref.members),
                'satisfaction': self.member_satisfaction,
                'stability': self.leadership_stability
            },
            'detailed_changes': {
                'pressures': pressure_analysis,
                'ideology': ideology_changes,
                'goals': goal_changes,
                'events': internal_events
            }
        }
    
    def _apply_player_actions(self, player_actions: Dict[str, Any]) -> None:
        """Apply player interference to faction state."""
        if 'pressure_external' in player_actions:
            self.external_pressure = min(1.0, self.external_pressure + player_actions['pressure_external'])
        
        if 'pressure_internal' in player_actions:
            self.internal_pressure = min(1.0, self.internal_pressure + player_actions['pressure_internal'])
        
        if 'satisfaction_change' in player_actions:
            self.member_satisfaction = max(0.0, min(1.0, 
                                                   self.member_satisfaction + player_actions['satisfaction_change']))
        
        if 'stability_change' in player_actions:
            self.leadership_stability = max(0.0, min(1.0,
                                                    self.leadership_stability + player_actions['stability_change']))
    
    def get_faction_status(self) -> Dict[str, Any]:
        """Get comprehensive status report for the faction."""
        return {
            'faction_info': {
                'id': self.faction_ref.faction_id,
                'name': self.faction_ref.name,
                'archetype': getattr(self.faction_ref, 'archetype', 'unknown'),
                'member_count': len(self.faction_ref.members)
            },
            'ai_state': {
                'internal_pressure': self.internal_pressure,
                'external_pressure': self.external_pressure,
                'member_satisfaction': self.member_satisfaction,
                'leadership_stability': self.leadership_stability
            },
            'faction_state': {
                'ideology': self.faction_ref.ideology,
                'goals': self.faction_ref.goals,
                'recent_events': self.recent_events[-5:]  # Last 5 events
            },
            'evolution_summary': {
                'total_log_entries': len(self.evolution_log),
                'major_changes': len([log for log in self.evolution_log 
                                    if len(log['changes']['ideology_shifts']) > 0])
            }
        }


# Test harness
if __name__ == "__main__":
    print("=== Faction AI Controller Test Harness ===\n")
    
    # Create test factions with different archetypes
    from faction_generator import Faction
    
    # Create factions with specific archetypes for testing
    test_factions = []
    
    # Religious cult - high tradition/authority
    cult_faction = Faction.generate_faction("Crimson Faith", "mountain_region", "religious_cult")
    cult_faction.ideology = {
        'order': 0.8, 'freedom': 0.2, 'violence': 0.3, 'tradition': 0.9,
        'progress': 0.1, 'authority': 0.8, 'loyalty': 0.9, 'justice': 0.6
    }
    cult_faction.goals = ["spread the faith", "build mountain temple", "convert nonbelievers"]
    test_factions.append(("Crimson Faith (Religious Cult)", cult_faction))
    
    # Rebel movement - high freedom/progress
    rebel_faction = Faction.generate_faction("Liberation Front", "city_district", "rebel_movement") 
    rebel_faction.ideology = {
        'order': 0.2, 'freedom': 0.9, 'violence': 0.6, 'tradition': 0.1,
        'progress': 0.8, 'authority': 0.1, 'loyalty': 0.4, 'justice': 0.7
    }
    rebel_faction.goals = ["overthrow corrupt government", "liberate the oppressed", "establish democracy"]
    test_factions.append(("Liberation Front (Rebel Movement)", rebel_faction))
    
    # Trade guild - moderate/pragmatic
    trade_faction = Faction.generate_faction("Merchant League", "port_city", "trade_guild")
    trade_faction.ideology = {
        'order': 0.6, 'freedom': 0.5, 'violence': 0.2, 'tradition': 0.4,
        'progress': 0.6, 'authority': 0.5, 'loyalty': 0.6, 'justice': 0.5
    }
    trade_faction.goals = ["control trade routes", "eliminate competitors", "maximize profits"]
    test_factions.append(("Merchant League (Trade Guild)", trade_faction))
    
    # Initialize AI controllers
    ai_controllers = []
    for name, faction in test_factions:
        ai = FactionAIController(faction)
        ai_controllers.append((name, ai))
        
        print(f"Created AI for {name}")
        print(f"  Initial ideology: {faction.ideology}")
        print(f"  Initial goals: {faction.goals}")
        print(f"  Members: {len(faction.members)}")
        print(f"  AI satisfaction: {ai.member_satisfaction:.2f}")
        print()
    
    print("=== Running 10 simulation ticks per faction ===\n")
    
    for faction_name, ai in ai_controllers:
        print(f"--- {faction_name} Evolution ---")
        
        for tick in range(10):
            # Simulate different external conditions
            external_factors = {
                'regional_instability': random.uniform(0.0, 0.5),
                'economic_pressure': random.uniform(0.0, 0.4),
                'political_pressure': random.uniform(0.0, 0.6)
            }
            
            # Occasionally add player interference
            player_actions = {}
            if random.random() < 0.2:
                player_actions = {
                    'pressure_external': random.uniform(-0.1, 0.2),
                    'satisfaction_change': random.uniform(-0.1, 0.1)
                }
            
            # Run AI tick
            tick_result = ai.simulate_tick(external_factors, player_actions)
            summary = tick_result['tick_summary']
            changes = tick_result['detailed_changes']
            
            # Report significant changes
            print(f"  Tick {tick + 1:2d}: P={summary['pressure_total']:.2f} "
                  f"S={summary['satisfaction']:.2f} "
                  f"L={summary['stability']:.2f} "
                  f"M={summary['member_count']}")
            
            # Report ideology changes
            if changes['ideology']:
                for trait, change_desc in changes['ideology'].items():
                    print(f"    IDEOLOGY: {trait} {change_desc}")
            
            # Report goal changes
            for added_goal in changes['goals']['added_goals']:
                print(f"    GOAL ADDED: {added_goal}")
            for removed_goal in changes['goals']['removed_goals']:
                print(f"    GOAL REMOVED: {removed_goal}")
            
            # Report major events
            for event in changes['events']:
                if event['impact'] in ['high', 'negative', 'positive']:
                    print(f"    EVENT: {event['description']} ({event['impact']})")
        
        # Final state summary
        final_status = ai.get_faction_status()
        print(f"\n  FINAL STATE:")
        print(f"    Ideology changes: {final_status['evolution_summary']['major_changes']}")
        print(f"    Current goals: {final_status['faction_state']['goals']}")
        print(f"    Pressure: I={ai.internal_pressure:.2f} E={ai.external_pressure:.2f}")
        print(f"    Satisfaction: {ai.member_satisfaction:.2f}")
        print(f"    Members: {len(ai.faction_ref.members)}")
        print()
    
    print("=== Test Complete ===")
    print("Faction AI successfully demonstrated autonomous behavior including:")
    print("- Pressure-based ideology shifts")
    print("- Dynamic goal adaptation") 
    print("- Internal events (leadership changes, membership fluctuations)")
    print("- Response to external factors and player actions")
    print("- Realistic faction evolution over time") 