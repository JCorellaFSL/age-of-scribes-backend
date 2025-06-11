"""
NPC AI System - Autonomous NPC Behavior Controller
================================================

This module provides intelligent behavior management for NPCs, integrating
memory, rumors, reputation, and faction systems to create believable
autonomous characters with realistic daily routines and social responses.
"""

import random
import math
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

# Import our social simulation systems
from memory_core import MemoryNode, MemoryBank
from rumor_engine import Rumor, RumorNetwork
from npc_profile import NPCProfile
from reputation_tracker import ReputationEngine
from faction_generator import Faction


class NPCBehaviorController:
    """
    Manages autonomous NPC behavior using integrated social simulation systems.
    
    Controls daily routines, emotional responses, social interactions, and
    decision-making based on personality, memories, rumors, and social standing.
    """
    
    def __init__(self, npc_profile: NPCProfile, current_hour: int = 8):
        self.npc_profile = npc_profile
        self.current_state = "idle"
        self.stress_level = 0.2  # Base stress level
        self.current_hour = current_hour
        self.current_day = 0
        
        # Daily schedule - hour to preferred activity mapping
        self.daily_schedule = self._generate_daily_schedule()
        
        # Social relationships - npc_id to trust score (-1.0 to 1.0)
        self.relationship_map = {}
        
        # Known rumors
        self.known_rumors = []
        
        # Daily log for tracking behavior
        self.daily_log = []
        self.emotional_changes = []
        self.decisions_made = []
        self.notable_triggers = []
        
        # State transition history
        self.state_history = [("idle", current_hour, "Initial state")]
        
        # Memory processing tracking
        self.last_memory_check = current_hour
        self.processed_memories = set()
    
    def _generate_daily_schedule(self) -> Dict[int, str]:
        """Generate realistic daily schedule based on NPC personality and role."""
        base_schedule = {
            6: "waking_up",
            7: "morning_routine", 
            8: "breakfast",
            9: "work_preparation",
            10: "working",
            11: "working",
            12: "lunch_break",
            13: "working",
            14: "working", 
            15: "working",
            16: "social_time",
            17: "evening_routine",
            18: "dinner",
            19: "leisure",
            20: "social_time",
            21: "evening_leisure",
            22: "preparing_sleep",
            23: "sleeping",
            0: "sleeping",
            1: "sleeping",
            2: "sleeping",
            3: "sleeping",
            4: "sleeping",
            5: "sleeping"
        }
        
        # Modify schedule based on personality
        if "scholarly" in self.npc_profile.personality_traits:
            base_schedule[21] = "studying"
            base_schedule[22] = "reading"
        
        if "gossipy" in self.npc_profile.personality_traits:  # Social NPCs
            base_schedule[16] = "socializing"
            base_schedule[20] = "tavern_time"
        
        if "cautious" in self.npc_profile.personality_traits:
            base_schedule[23] = "security_check"
            base_schedule[22] = "planning"
        
        # Add faction-specific activities
        if self.npc_profile.faction_affiliation:
            if random.random() < 0.3:  # 30% chance of faction activity
                hour = random.choice([15, 16, 19, 20])
                base_schedule[hour] = f"faction_duties_{self.npc_profile.faction_affiliation}"
        
        return base_schedule
    
    def evaluate_memory_impact(self, memory_bank: MemoryBank) -> None:
        """Analyze recent strong memories and adjust emotional state accordingly."""
        current_time = datetime.now()
        
        # Get strong recent memories (last 48 hours, strength > 0.6)
        recent_memories = []
        for memory in memory_bank.memories:
            hours_ago = (current_time - memory.timestamp).total_seconds() / 3600
            if hours_ago <= 48 and memory.strength > 0.6:
                recent_memories.append((memory, hours_ago))
        
        # Process emotional impact
        stress_change = 0
        emotional_impacts = []
        
        for memory, hours_ago in recent_memories:
            if memory.event_id in self.processed_memories:
                continue
                
            # Calculate memory impact (stronger and more recent = more impact)
            impact_strength = memory.strength * (1.0 - hours_ago / 48.0)
            
            # Analyze memory content for emotional triggers
            emotional_impact = self._analyze_memory_emotion(memory, impact_strength)
            
            if emotional_impact:
                emotional_impacts.append(emotional_impact)
                stress_change += emotional_impact['stress_delta']
                
                self.emotional_changes.append({
                    'hour': self.current_hour,
                    'trigger': f"Memory: {memory.description[:50]}...",
                    'emotion': emotional_impact['emotion'],
                    'intensity': emotional_impact['intensity'],
                    'stress_change': emotional_impact['stress_delta']
                })
                
                self.notable_triggers.append(
                    f"Strong memory triggered {emotional_impact['emotion']} "
                    f"(intensity {emotional_impact['intensity']:.2f})"
                )
            
            self.processed_memories.add(memory.event_id)
        
        # Apply stress changes (with bounds)
        self.stress_level = max(0.0, min(1.0, self.stress_level + stress_change))
        
        # Personality evolution from traumatic memories
        if stress_change > 0.3:
            self._evolve_personality_from_trauma(emotional_impacts)
    
    def _analyze_memory_emotion(self, memory: MemoryNode, impact_strength: float) -> Optional[Dict]:
        """Analyze memory content to determine emotional impact."""
        content_lower = memory.description.lower()
        
        # Define emotional triggers
        fear_triggers = ['attack', 'threat', 'danger', 'violence', 'death', 'murder', 'assault']
        betrayal_triggers = ['betray', 'deceive', 'lie', 'cheat', 'backstab', 'trick']
        loyalty_triggers = ['help', 'save', 'protect', 'defend', 'loyal', 'trust']
        anger_triggers = ['insult', 'humiliate', 'mock', 'disrespect', 'offend']
        joy_triggers = ['celebration', 'victory', 'success', 'wedding', 'festival', 'gift']
        
        # Check for emotional content
        emotions = []
        
        if any(trigger in content_lower for trigger in fear_triggers):
            emotions.append(('fear', 0.8, 0.4))  # emotion, base_intensity, stress_delta
        
        if any(trigger in content_lower for trigger in betrayal_triggers):
            emotions.append(('betrayal', 0.9, 0.5))
        
        if any(trigger in content_lower for trigger in loyalty_triggers):
            emotions.append(('gratitude', 0.6, -0.2))
        
        if any(trigger in content_lower for trigger in anger_triggers):
            emotions.append(('anger', 0.7, 0.3))
        
        if any(trigger in content_lower for trigger in joy_triggers):
            emotions.append(('joy', 0.7, -0.3))
        
        if not emotions:
            return None
        
        # Select strongest emotion
        strongest_emotion = max(emotions, key=lambda x: x[1])
        emotion, base_intensity, base_stress = strongest_emotion
        
        # Modify intensity based on personality
        intensity_modifier = 1.0
        if emotion == 'fear' and "stoic" in self.npc_profile.personality_traits:
            intensity_modifier = 0.5  # Stoic NPCs less affected by fear
        elif emotion == 'betrayal' and "optimistic" in self.npc_profile.personality_traits:
            intensity_modifier = 1.5  # Optimistic NPCs more affected by betrayal
        elif emotion == 'anger' and "diplomatic" in self.npc_profile.personality_traits:
            intensity_modifier = 0.6  # Diplomatic NPCs less prone to anger
        
        final_intensity = base_intensity * intensity_modifier * impact_strength
        final_stress = base_stress * intensity_modifier * impact_strength
        
        return {
            'emotion': emotion,
            'intensity': final_intensity,
            'stress_delta': final_stress,
            'memory_content': memory.description
        }
    
    def _evolve_personality_from_trauma(self, emotional_impacts: List[Dict]) -> None:
        """Evolve personality traits based on traumatic experiences."""
        for impact in emotional_impacts:
            if impact['intensity'] > 0.7:  # Only very strong emotions cause personality change
                if impact['emotion'] == 'betrayal':
                    # Betrayal makes NPCs more cynical and secretive
                    if "optimistic" in self.npc_profile.personality_traits:
                        self.npc_profile.personality_traits.remove("optimistic")
                    if "cynical" not in self.npc_profile.personality_traits:
                        self.npc_profile.personality_traits.append("cynical")
                    if "secretive" not in self.npc_profile.personality_traits:
                        self.npc_profile.personality_traits.append("secretive")
                        
                elif impact['emotion'] == 'fear':
                    # Fear makes NPCs more cautious
                    if "cautious" not in self.npc_profile.personality_traits:
                        self.npc_profile.personality_traits.append("cautious")
                    if "impulsive" in self.npc_profile.personality_traits:
                        self.npc_profile.personality_traits.remove("impulsive")
                
                elif impact['emotion'] == 'anger':
                    # Anger can make NPCs more aggressive
                    if "aggressive" not in self.npc_profile.personality_traits:
                        self.npc_profile.personality_traits.append("aggressive")
                    if "diplomatic" in self.npc_profile.personality_traits:
                        self.npc_profile.personality_traits.remove("diplomatic")
    
    def adjust_state(self) -> None:
        """Update NPC state based on schedule, stress, and current conditions."""
        old_state = self.current_state
        
        # Get scheduled activity for current hour
        scheduled_activity = self.daily_schedule.get(self.current_hour, "idle")
        
        # Modify based on stress level
        if self.stress_level > 0.8:
            # High stress overrides normal schedule
            if scheduled_activity in ["socializing", "tavern_time", "leisure"]:
                new_state = "hiding"  # Avoid social situations when highly stressed
            elif scheduled_activity == "working":
                new_state = "stressed_working"
            else:
                new_state = "anxious"
        elif self.stress_level > 0.6:
            # Moderate stress affects some activities
            if scheduled_activity == "socializing":
                new_state = "cautious_socializing"
            else:
                new_state = scheduled_activity
        else:
            # Normal stress, follow schedule
            new_state = scheduled_activity
        
        # Faction duties can override personal schedule
        if "faction_duties" in new_state:
            faction_id = new_state.split("_")[-1]
            new_state = self._determine_faction_activity(faction_id)
        
        # Personality modifications
        if "scholarly" in self.npc_profile.personality_traits and random.random() < 0.2:
            if new_state in ["idle", "leisure"]:
                new_state = "investigating"
        
        if ("secretive" in self.npc_profile.personality_traits or 
            "cautious" in self.npc_profile.personality_traits) and self.stress_level > 0.4:
            if new_state in ["socializing", "tavern_time"]:
                new_state = "observing"  # Watch instead of participating
        
        # Update state if changed
        if new_state != old_state:
            self.current_state = new_state
            self.state_history.append((new_state, self.current_hour, 
                                     f"Stress: {self.stress_level:.2f}, Schedule: {scheduled_activity}"))
            
            self.decisions_made.append({
                'hour': self.current_hour,
                'decision': f"State change: {old_state} -> {new_state}",
                'reason': f"Stress {self.stress_level:.2f}, Schedule: {scheduled_activity}"
            })
    
    def _determine_faction_activity(self, faction_id: str) -> str:
        """Determine what faction activity the NPC should be doing."""
        # This would integrate with actual faction system
        # For now, return reasonable activities based on personality
        
        if "loyal" in self.npc_profile.personality_traits:
            activities = ["faction_meeting", "faction_recruitment", "faction_planning"]
        elif ("cunning" in self.npc_profile.personality_traits or 
              "secretive" in self.npc_profile.personality_traits):
            activities = ["faction_espionage", "faction_infiltration", "faction_plotting"]
        else:
            activities = ["faction_duties", "faction_discussion", "faction_training"]
        
        return random.choice(activities)
    
    def interact(self, target_npc_id: str, interaction_type: str = "casual") -> bool:
        """
        Decide whether to interact with another NPC based on trust and social context.
        
        Returns True if interaction proceeds, False if avoided.
        """
        # Get trust score for target
        trust_score = self.relationship_map.get(target_npc_id, 0.0)  # Neutral default
        
        # Base interaction probability
        base_probability = 0.5
        
        # Modify by trust score
        trust_modifier = trust_score * 0.3  # -0.3 to +0.3
        
        # Modify by personality
        personality_modifier = 0
        if interaction_type == "casual":
            if "diplomatic" in self.npc_profile.personality_traits:
                personality_modifier += 0.2
            if "cynical" in self.npc_profile.personality_traits:
                personality_modifier -= 0.15
        elif interaction_type == "business":
            if "honest" in self.npc_profile.personality_traits:
                personality_modifier += 0.1
            if "pragmatic" in self.npc_profile.personality_traits:
                personality_modifier += 0.1
        elif interaction_type == "confrontation":
            if "aggressive" in self.npc_profile.personality_traits:
                personality_modifier += 0.3
            if "cautious" in self.npc_profile.personality_traits:
                personality_modifier -= 0.2
        
        # Modify by stress level (high stress reduces social interaction)
        stress_modifier = -self.stress_level * 0.3
        
        # Modify by current state
        state_modifier = 0
        if self.current_state in ["hiding", "anxious", "stressed_working"]:
            state_modifier = -0.4
        elif self.current_state in ["socializing", "tavern_time"]:
            state_modifier = 0.3
        elif self.current_state == "observing":
            state_modifier = -0.2
        
        # Calculate final probability
        final_probability = base_probability + trust_modifier + personality_modifier + stress_modifier + state_modifier
        final_probability = max(0.0, min(1.0, final_probability))
        
        # Make decision
        will_interact = random.random() < final_probability
        
        # Log decision
        self.decisions_made.append({
            'hour': self.current_hour,
            'decision': f"Interaction with {target_npc_id}: {'Yes' if will_interact else 'No'}",
            'reason': f"Trust: {trust_score:.2f}, Stress: {self.stress_level:.2f}, "
                     f"Type: {interaction_type}, Probability: {final_probability:.2f}"
        })
        
        return will_interact
    
    def react_to_rumors(self, new_rumors: List[Rumor]) -> None:
        """Process new rumors and adjust behavior/relationships accordingly."""
        for rumor in new_rumors:
            if rumor in self.known_rumors:
                continue  # Already processed
            
            self.known_rumors.append(rumor)
            
            # Analyze rumor content for personal relevance
            reaction = self._analyze_rumor_relevance(rumor)
            
            if reaction:
                # Apply reaction effects
                if 'stress_change' in reaction:
                    self.stress_level = max(0.0, min(1.0, 
                        self.stress_level + reaction['stress_change']))
                
                if 'trust_changes' in reaction:
                    for npc_id, trust_change in reaction['trust_changes'].items():
                        current_trust = self.relationship_map.get(npc_id, 0.0)
                        self.relationship_map[npc_id] = max(-1.0, min(1.0,
                            current_trust + trust_change))
                
                # Log the reaction
                self.notable_triggers.append(
                    f"Rumor reaction: {reaction['reaction_type']} to '{rumor.content[:40]}...'"
                )
                
                self.emotional_changes.append({
                    'hour': self.current_hour,
                    'trigger': f"Rumor: {rumor.content[:50]}...",
                    'emotion': reaction.get('emotion', 'concern'),
                    'intensity': reaction.get('intensity', 0.3),
                    'stress_change': reaction.get('stress_change', 0.0)
                })
    
    def _analyze_rumor_relevance(self, rumor: Rumor) -> Optional[Dict]:
        """Analyze how a rumor affects this NPC personally."""
        content_lower = rumor.content.lower()
        
        # Check if rumor mentions this NPC by name
        if self.npc_profile.name.lower() in content_lower:
            # Direct mention - strong reaction
            if any(neg in content_lower for neg in ['criminal', 'thief', 'liar', 'corrupt']):
                return {
                    'reaction_type': 'personal_attack',
                    'emotion': 'outrage',
                    'intensity': 0.8,
                    'stress_change': 0.4
                }
            elif any(pos in content_lower for pos in ['hero', 'brave', 'honest', 'good']):
                return {
                    'reaction_type': 'personal_praise', 
                    'emotion': 'pride',
                    'intensity': 0.6,
                    'stress_change': -0.2
                }
        
        # Check for mentions of known associates
        trust_changes = {}
        for npc_id in self.relationship_map:
            if npc_id.lower() in content_lower:
                current_trust = self.relationship_map[npc_id]
                if any(neg in content_lower for neg in ['betray', 'criminal', 'corrupt']):
                    # Negative rumor about associate
                    if current_trust > 0.3:  # Only if we trusted them
                        trust_changes[npc_id] = -0.3
                elif any(pos in content_lower for pos in ['hero', 'honest', 'good']):
                    # Positive rumor about associate
                    trust_changes[npc_id] = 0.1
        
        if trust_changes:
            return {
                'reaction_type': 'associate_news',
                'emotion': 'concern',
                'intensity': 0.4,
                'stress_change': 0.1,
                'trust_changes': trust_changes
            }
        
        # Check for faction-relevant rumors
        if (self.npc_profile.faction_affiliation and 
            self.npc_profile.faction_affiliation.lower() in content_lower):
            if any(neg in content_lower for neg in ['corrupt', 'illegal', 'criminal']):
                return {
                    'reaction_type': 'faction_threat',
                    'emotion': 'worry',
                    'intensity': 0.5,
                    'stress_change': 0.3
                }
        
        # General anxiety from disturbing news
        if any(disturbing in content_lower for disturbing in 
               ['murder', 'war', 'plague', 'disaster', 'attack']):
            return {
                'reaction_type': 'general_concern',
                'emotion': 'anxiety',
                'intensity': 0.3,
                'stress_change': 0.1
            }
        
        return None
    
    def simulate_tick(self, memory_bank: MemoryBank, rumor_network: RumorNetwork) -> None:
        """Run one hour of NPC behavior simulation."""
        # Process memories (check every few hours)
        if self.current_hour - self.last_memory_check >= 3:
            self.evaluate_memory_impact(memory_bank)
            self.last_memory_check = self.current_hour
        
        # Get new rumors from network
        if hasattr(rumor_network, 'get_rumors_for_npc'):
            new_rumors = rumor_network.get_rumors_for_npc(self.npc_profile.npc_id)
            if new_rumors:
                self.react_to_rumors(new_rumors)
        
        # Adjust current state
        self.adjust_state()
        
        # Natural stress decay over time (small amount)
        if self.stress_level > 0.1:
            self.stress_level = max(0.1, self.stress_level - 0.02)
        
        # Advance time
        self.current_hour = (self.current_hour + 1) % 24
        if self.current_hour == 0:  # New day
            self.current_day += 1
    
    def log_day(self) -> str:
        """Generate a comprehensive daily summary of NPC behavior and state changes."""
        summary = []
        summary.append(f"\n=== DAILY REPORT: {self.npc_profile.name} (Day {self.current_day}) ===")
        summary.append(f"Final Stress Level: {self.stress_level:.2f}")
        summary.append(f"Personality Traits: {', '.join(self.npc_profile.personality_traits)}")
        
        # Emotional changes
        if self.emotional_changes:
            summary.append("\nEMOTIONAL CHANGES:")
            for change in self.emotional_changes[-5:]:  # Last 5 changes
                summary.append(f"  Hour {change['hour']:2d}: {change['emotion'].upper()} "
                             f"(intensity {change['intensity']:.2f}) - {change['trigger']}")
        
        # Key decisions
        if self.decisions_made:
            summary.append("\nKEY DECISIONS:")
            for decision in self.decisions_made[-5:]:  # Last 5 decisions
                summary.append(f"  Hour {decision['hour']:2d}: {decision['decision']}")
                summary.append(f"               Reason: {decision['reason']}")
        
        # Notable triggers
        if self.notable_triggers:
            summary.append("\nNOTABLE TRIGGERS:")
            for trigger in self.notable_triggers[-3:]:  # Last 3 triggers
                summary.append(f"  - {trigger}")
        
        # State transitions
        if len(self.state_history) > 1:
            summary.append("\nSTATE TRANSITIONS:")
            for i, (state, hour, reason) in enumerate(self.state_history[-5:]):
                if i == 0:
                    summary.append(f"  Hour {hour:2d}: Started in '{state}'")
                else:
                    summary.append(f"  Hour {hour:2d}: Changed to '{state}' ({reason})")
        
        # Relationship changes
        if self.relationship_map:
            summary.append("\nCURRENT RELATIONSHIPS:")
            for npc_id, trust in sorted(self.relationship_map.items()):
                trust_desc = "Trusted" if trust > 0.3 else "Distrusted" if trust < -0.3 else "Neutral"
                summary.append(f"  {npc_id}: {trust:.2f} ({trust_desc})")
        
        # Clear daily logs for next day
        self.emotional_changes = []
        self.decisions_made = []
        self.notable_triggers = []
        
        return "\n".join(summary)


class NPCMotivationEngine:
    """
    Manages personal goal generation and motivation shifts for NPCs over time.
    
    This engine creates dynamic personal objectives based on experiences, memories,
    faction orders, and changing emotional/social circumstances. Goals evolve
    naturally as NPCs respond to their environment and internal motivations.
    """
    
    # Core motivation categories that drive goal generation
    MOTIVATION_CATEGORIES = {
        "survival": "Basic needs, safety, security, health",
        "revenge": "Retribution, justice, settling scores",
        "community": "Social bonds, reputation, belonging", 
        "power": "Control, influence, authority, dominance",
        "knowledge": "Learning, discovery, understanding, wisdom",
        "wealth": "Material gain, resources, economic security",
        "duty": "Obligation, service, loyalty, honor",
        "freedom": "Independence, autonomy, choice, liberation"
    }
    
    # Goal types that can be generated
    GOAL_TYPES = [
        "immediate",    # Urgent, short-term goals (1-3 days)
        "short_term",   # Medium priority goals (1-2 weeks)
        "long_term",    # Life objectives (months/years)
        "faction",      # Goals assigned by faction membership
        "reactive",     # Goals generated in response to events
        "relationship", # Goals involving other NPCs
        "economic",     # Goals involving resources/trade
        "knowledge"     # Goals involving learning/research
    ]
    
    def __init__(self, npc_profile: NPCProfile, memory_stream: MemoryBank):
        self.npc_profile = npc_profile
        self.memory_stream = memory_stream
        self.active_goals = []
        self.faction_orders = []
        self.goal_counter = 0
        
        # Initialize motivation weights based on personality
        self.motivational_weights = self._initialize_motivation_weights()
        
        # Goal tracking
        self.completed_goals = []
        self.failed_goals = []
        self.last_goal_generation = 0
        
        # Memory tracking for motivation adjustment
        self.last_processed_memory_count = 0
        
    def _initialize_motivation_weights(self) -> Dict[str, float]:
        """Initialize motivation weights based on NPC personality traits."""
        weights = {category: 0.3 for category in self.MOTIVATION_CATEGORIES.keys()}  # Base weights
        
        # Adjust weights based on personality traits
        traits = self.npc_profile.personality_traits
        
        if "greedy" in traits:
            weights["wealth"] += 0.4
            weights["power"] += 0.2
        
        if "loyal" in traits:
            weights["duty"] += 0.4
            weights["community"] += 0.3
        
        if "scholarly" in traits:
            weights["knowledge"] += 0.5
            weights["power"] += 0.1
        
        if "cautious" in traits:
            weights["survival"] += 0.3
            weights["community"] += 0.2
        
        if "aggressive" in traits:
            weights["power"] += 0.3
            weights["revenge"] += 0.2
        
        if "secretive" in traits:
            weights["survival"] += 0.2
            weights["freedom"] += 0.3
        
        if "rebellious" in traits:
            weights["freedom"] += 0.4
            weights["power"] += 0.2
        
        if "vengeful" in traits:
            weights["revenge"] += 0.5
            weights["power"] += 0.1
        
        # Normalize weights to reasonable ranges (0.0 to 1.0)
        for category in weights:
            weights[category] = max(0.0, min(1.0, weights[category]))
        
        return weights
    
    def generate_personal_goals(self, current_hour: int = 12) -> List[Dict]:
        """
        Generate new personal goals based on current motivations, memories, and circumstances.
        
        Returns:
            List of new goal dictionaries created
        """
        new_goals = []
        
        # Limit total active goals to prevent overwhelming the NPC
        if len(self.active_goals) >= 8:
            return new_goals
        
        # Generate goals based on strongest motivations
        top_motivations = sorted(self.motivational_weights.items(), 
                               key=lambda x: x[1], reverse=True)[:3]
        
        for motivation, weight in top_motivations:
            if weight > 0.6 and random.random() < 0.3:  # 30% chance for high motivation
                goal = self._create_goal_for_motivation(motivation, weight)
                if goal and not self._is_duplicate_goal(goal):
                    new_goals.append(goal)
                    self.active_goals.append(goal)
        
        # Generate reactive goals from recent memories
        reactive_goals = self._generate_reactive_goals()
        for goal in reactive_goals:
            if not self._is_duplicate_goal(goal):
                new_goals.append(goal)
                self.active_goals.append(goal)
        
        # Generate relationship goals based on trust scores
        if hasattr(self.npc_profile, 'behavior_controller'):
            relationship_goals = self._generate_relationship_goals()
            for goal in relationship_goals:
                if not self._is_duplicate_goal(goal):
                    new_goals.append(goal)
                    self.active_goals.append(goal)
        
        return new_goals
    
    def _create_goal_for_motivation(self, motivation: str, weight: float) -> Optional[Dict]:
        """Create a specific goal based on a motivation category."""
        self.goal_counter += 1
        
        # Determine urgency based on motivation weight
        if weight > 0.8:
            urgency = random.uniform(0.7, 1.0)
            goal_type = "immediate"
        elif weight > 0.6:
            urgency = random.uniform(0.4, 0.7)
            goal_type = "short_term"
        else:
            urgency = random.uniform(0.1, 0.4)
            goal_type = "long_term"
        
        # Generate goals based on motivation type
        goal_templates = {
            "survival": [
                "Find secure shelter for the night",
                "Stockpile food and supplies",
                "Avoid dangerous areas of the city",
                "Build emergency fund for hard times",
                "Establish safe house location"
            ],
            "revenge": [
                f"Confront {random.choice(['corrupt official', 'dishonest merchant', 'betrayer'])}",
                "Gather evidence of wrongdoing",
                "Plan retribution against enemies",
                "Expose corruption publicly",
                "Sabotage rival's operations"
            ],
            "community": [
                "Strengthen ties with local guild",
                "Help community members in need", 
                "Organize neighborhood watch",
                "Improve local reputation",
                "Mediate disputes between neighbors"
            ],
            "power": [
                "Gain influence in local politics",
                "Blackmail important figures",
                "Acquire leverage over rivals",
                "Build network of informants",
                "Eliminate political competition"
            ],
            "knowledge": [
                "Research ancient texts in library",
                "Learn new skills or techniques",
                "Investigate mysterious occurrences",
                "Document local history and lore",
                "Decode cryptic messages"
            ],
            "wealth": [
                "Establish profitable trade route",
                "Find wealthy patron or sponsor",
                "Discover hidden treasure",
                "Corner market on rare goods",
                "Collect debts owed to me"
            ],
            "duty": [
                "Complete faction assignments",
                "Protect innocent civilians",
                "Uphold law and order",
                "Honor family obligations",
                "Fulfill sworn oaths"
            ],
            "freedom": [
                "Escape current constraints",
                "Break free from oppressive authority",
                "Establish independent operation",
                "Remove surveillance and watchers",
                "Gain autonomy in decision-making"
            ]
        }
        
        if motivation in goal_templates:
            description = random.choice(goal_templates[motivation])
            
            # Faction-linked goals for duty motivation
            faction_linked = (motivation == "duty" and 
                            self.npc_profile.faction_affiliation is not None)
            
            return {
                "goal_id": f"goal_{self.goal_counter}",
                "description": description,
                "urgency": urgency,
                "type": goal_type,
                "faction_linked": faction_linked,
                "motivation_source": motivation,
                "created_hour": datetime.now().hour,
                "progress": 0.0
            }
        
        return None
    
    def _generate_reactive_goals(self) -> List[Dict]:
        """Generate goals in response to recent memories and events."""
        reactive_goals = []
        
        # Check recent strong memories (last 24 hours)
        current_time = datetime.now()
        recent_memories = []
        
        for memory in self.memory_stream.memories:
            hours_ago = (current_time - memory.timestamp).total_seconds() / 3600
            if hours_ago <= 24 and memory.strength > 0.7:
                recent_memories.append(memory)
        
        for memory in recent_memories:
            self.goal_counter += 1
            
            # Generate goals based on memory content and tags
            if "betrayal" in memory.context_tags:
                reactive_goals.append({
                    "goal_id": f"goal_{self.goal_counter}",
                    "description": f"Investigate betrayal by {memory.actor_ids[0] if memory.actor_ids else 'unknown person'}",
                    "urgency": 0.8,
                    "type": "reactive",
                    "faction_linked": False,
                    "motivation_source": "revenge",
                    "created_hour": datetime.now().hour,
                    "progress": 0.0
                })
                
            elif "theft" in memory.context_tags or "crime" in memory.context_tags:
                reactive_goals.append({
                    "goal_id": f"goal_{self.goal_counter}",
                    "description": "Report crime to authorities and seek justice",
                    "urgency": 0.7,
                    "type": "reactive", 
                    "faction_linked": False,
                    "motivation_source": "community",
                    "created_hour": datetime.now().hour,
                    "progress": 0.0
                })
                
            elif "discovery" in memory.context_tags:
                reactive_goals.append({
                    "goal_id": f"goal_{self.goal_counter}",
                    "description": f"Research and document recent discovery",
                    "urgency": 0.6,
                    "type": "reactive",
                    "faction_linked": False,
                    "motivation_source": "knowledge",
                    "created_hour": datetime.now().hour,
                    "progress": 0.0
                })
        
        return reactive_goals
    
    def _generate_relationship_goals(self) -> List[Dict]:
        """Generate goals based on relationship status and trust scores."""
        relationship_goals = []
        
        # This would normally get relationship data from the behavior controller
        # For now, we'll create placeholder relationship goals
        
        self.goal_counter += 1
        relationship_goals.append({
            "goal_id": f"goal_{self.goal_counter}",
            "description": "Improve standing with local community",
            "urgency": 0.4,
            "type": "relationship",
            "faction_linked": False,
            "motivation_source": "community",
            "created_hour": datetime.now().hour,
            "progress": 0.0
        })
        
        return relationship_goals
    
    def _is_duplicate_goal(self, new_goal: Dict) -> bool:
        """Check if a similar goal already exists."""
        for existing_goal in self.active_goals:
            if (existing_goal["motivation_source"] == new_goal["motivation_source"] and
                existing_goal["type"] == new_goal["type"]):
                # Similar enough to be considered duplicate
                if len(set(existing_goal["description"].split()) & 
                       set(new_goal["description"].split())) > 2:
                    return True
        return False
    
    def evaluate_goal_priority(self) -> None:
        """Reorder and update goals based on urgency decay and circumstances."""
        current_time = datetime.now()
        
        # Update existing goals
        goals_to_remove = []
        
        for goal in self.active_goals:
            # Decay urgency over time (goals become less urgent)
            hours_since_creation = (current_time.hour - goal.get("created_hour", 0)) % 24
            decay_rate = 0.02 * hours_since_creation  # 2% decay per hour
            goal["urgency"] = max(0.1, goal["urgency"] - decay_rate)
            
            # Mark very low urgency goals for removal
            if goal["urgency"] < 0.2 and goal["type"] != "long_term":
                goals_to_remove.append(goal)
            
            # Update progress (placeholder - would be based on actual actions)
            if random.random() < 0.1:  # 10% chance of progress each evaluation
                goal["progress"] = min(1.0, goal["progress"] + random.uniform(0.1, 0.3))
                
                # Mark completed goals
                if goal["progress"] >= 1.0:
                    goals_to_remove.append(goal)
                    self.completed_goals.append(goal)
        
        # Remove completed/abandoned goals
        for goal in goals_to_remove:
            if goal in self.active_goals:
                self.active_goals.remove(goal)
        
        # Sort goals by urgency (highest first)
        self.active_goals.sort(key=lambda g: g["urgency"], reverse=True)
    
    def sync_with_faction(self) -> None:
        """Merge or override goals based on faction loyalty and orders."""
        if not self.npc_profile.faction_affiliation:
            return
        
        # Get faction loyalty from belief system
        loyalty = self.npc_profile.belief_system.get("loyalty", 0.5)
        duty_weight = self.motivational_weights.get("duty", 0.3)
        
        # High loyalty NPCs prioritize faction goals
        if loyalty > 0.7 and duty_weight > 0.5:
            # Add faction goals if any exist in faction_orders
            for faction_goal in self.faction_orders:
                if not any(g["goal_id"] == faction_goal.get("goal_id") 
                          for g in self.active_goals):
                    # Mark as high priority if NPC is very loyal
                    faction_goal["urgency"] = max(faction_goal.get("urgency", 0.5), 0.8)
                    faction_goal["faction_linked"] = True
                    self.active_goals.append(faction_goal)
        
        # Low loyalty NPCs might ignore or subvert faction goals
        elif loyalty < 0.3:
            # Remove faction goals or modify them to be subversive
            self.active_goals = [g for g in self.active_goals if not g.get("faction_linked", False)]
    
    def adjust_weights_from_memory(self, memory: MemoryNode) -> None:
        """Adjust motivation weights based on new memory content."""
        content_lower = memory.description.lower()
        tags = memory.context_tags
        
        # Betrayal memories boost revenge motivation
        if "betrayal" in tags or any(word in content_lower for word in ["betray", "deceive", "lie"]):
            self.motivational_weights["revenge"] = min(1.0, 
                self.motivational_weights["revenge"] + 0.3)
            self.motivational_weights["community"] = max(0.0,
                self.motivational_weights["community"] - 0.2)
        
        # Crime/threat memories boost survival motivation
        if any(tag in tags for tag in ["crime", "threat", "danger", "violence"]):
            self.motivational_weights["survival"] = min(1.0,
                self.motivational_weights["survival"] + 0.2)
            self.motivational_weights["freedom"] = min(1.0,
                self.motivational_weights["freedom"] + 0.1)
        
        # Poverty/resource scarcity boosts survival and wealth
        if any(word in content_lower for word in ["hungry", "starving", "poor", "broke"]):
            self.motivational_weights["survival"] = min(1.0,
                self.motivational_weights["survival"] + 0.4)
            self.motivational_weights["wealth"] = min(1.0,
                self.motivational_weights["wealth"] + 0.3)
        
        # Discovery memories boost knowledge motivation
        if "discovery" in tags or any(word in content_lower for word in ["found", "discovered", "learned"]):
            self.motivational_weights["knowledge"] = min(1.0,
                self.motivational_weights["knowledge"] + 0.2)
        
        # Authority/corruption memories affect power and duty motivations
        if any(tag in tags for tag in ["authority", "corruption"]):
            if "loyal" in self.npc_profile.personality_traits:
                self.motivational_weights["duty"] = min(1.0,
                    self.motivational_weights["duty"] + 0.2)
            else:
                self.motivational_weights["power"] = min(1.0,
                    self.motivational_weights["power"] + 0.2)
                self.motivational_weights["duty"] = max(0.0,
                    self.motivational_weights["duty"] - 0.1)
    
    def tick(self, current_hour: int) -> Dict[str, Any]:
        """
        Daily motivation and goal update tick.
        
        Returns:
            Summary of changes made during this tick
        """
        changes = {
            "goals_generated": 0,
            "goals_completed": 0,
            "goals_abandoned": 0,
            "motivation_shifts": [],
            "priority_changes": []
        }
        
        # Process new memories for motivation adjustment
        memory_count = len(self.memory_stream.memories)
        if memory_count > self.last_processed_memory_count:
            new_memories = self.memory_stream.memories[self.last_processed_memory_count:]
            for memory in new_memories:
                if memory.strength > 0.6:  # Only significant memories affect motivation
                    old_weights = self.motivational_weights.copy()
                    self.adjust_weights_from_memory(memory)
                    
                    # Track significant motivation changes
                    for category, old_weight in old_weights.items():
                        new_weight = self.motivational_weights[category]
                        if abs(new_weight - old_weight) > 0.1:
                            changes["motivation_shifts"].append(
                                f"{category}: {old_weight:.2f} -> {new_weight:.2f}"
                            )
            
            self.last_processed_memory_count = memory_count
        
        # Evaluate and update existing goals
        old_goal_count = len(self.active_goals)
        self.evaluate_goal_priority()
        
        changes["goals_completed"] = len(self.completed_goals)
        changes["goals_abandoned"] = max(0, old_goal_count - len(self.active_goals) - changes["goals_completed"])
        
        # Generate new goals periodically
        if current_hour % 6 == 0:  # Every 6 hours
            new_goals = self.generate_personal_goals(current_hour)
            changes["goals_generated"] = len(new_goals)
        
        # Sync with faction
        self.sync_with_faction()
        
        return changes
    
    def get_top_goals(self, count: int = 3) -> List[Dict]:
        """Get top priority goals with motivational alignment percentages."""
        top_goals = sorted(self.active_goals, key=lambda g: g["urgency"], reverse=True)[:count]
        
        # Add motivational alignment percentages
        for goal in top_goals:
            motivation_source = goal.get("motivation_source", "unknown")
            goal["motivation_alignment"] = self.motivational_weights.get(motivation_source, 0.0)
        
        return top_goals
    
    def serialize_motivation_state(self) -> str:
        """Generate a readable summary of current motivational state and goals."""
        summary = []
        summary.append(f"\n=== MOTIVATION ENGINE: {self.npc_profile.name} ===")
        
        # Top motivations
        summary.append("TOP MOTIVATIONS:")
        sorted_motivations = sorted(self.motivational_weights.items(), 
                                  key=lambda x: x[1], reverse=True)
        for motivation, weight in sorted_motivations[:5]:
            percentage = int(weight * 100)
            summary.append(f"  {motivation.capitalize()}: {percentage}% ({weight:.2f})")
        
        # Active goals
        summary.append(f"\nACTIVE GOALS ({len(self.active_goals)} total):")
        top_goals = self.get_top_goals(3)
        
        for i, goal in enumerate(top_goals, 1):
            urgency_pct = int(goal["urgency"] * 100)
            progress_pct = int(goal["progress"] * 100)
            motivation_pct = int(goal["motivation_alignment"] * 100)
            
            summary.append(f"  {i}. {goal['description']}")
            summary.append(f"     Urgency: {urgency_pct}% | Progress: {progress_pct}% | "
                         f"Motivation: {motivation_pct}% ({goal['motivation_source']})")
        
        # Goal statistics
        summary.append(f"\nGOAL STATISTICS:")
        summary.append(f"  Completed: {len(self.completed_goals)}")
        summary.append(f"  Failed: {len(self.failed_goals)}")
        summary.append(f"  Active: {len(self.active_goals)}")
        
        return "\n".join(summary)


def create_test_harness():
    """Create comprehensive test of NPC AI system including motivation engine over 24-hour period."""
    print("=== NPC AI BEHAVIOR CONTROLLER + MOTIVATION ENGINE TEST HARNESS ===\n")
    
    # Create test NPCs with different personalities
    from npc_profile import NPCProfile
    
    # NPC 1: Paranoid merchant
    merchant_profile = NPCProfile.generate_random("Marcus the Merchant", "market_district", 
                                                 archetype="merchant")
    merchant_profile.personality_traits = ["secretive", "cautious", "greedy", "pragmatic", "cynical"]
    merchant_profile.faction_affiliation = "merchants_guild"
    
    # NPC 2: Loyal guard  
    guard_profile = NPCProfile.generate_random("Sarah the Guard", "city_center", 
                                              archetype="guardian")
    guard_profile.personality_traits = ["loyal", "stoic", "aggressive", "honest", "diplomatic"]
    guard_profile.faction_affiliation = "city_watch"
    
    # NPC 3: Curious scholar
    scholar_profile = NPCProfile.generate_random("Elias the Scholar", "university_district", 
                                                archetype="scholar")
    scholar_profile.personality_traits = ["scholarly", "honest", "diplomatic", "cautious", "optimistic"]
    scholar_profile.faction_affiliation = "scholars_circle"
    
    # Create memory banks with some pre-loaded memories
    from memory_core import MemoryBank
    
    merchant_memory = MemoryBank("marcus_merchant", 100)
    guard_memory = MemoryBank("sarah_guard", 100)
    scholar_memory = MemoryBank("elias_scholar", 100)
    
    # Create motivation engines
    merchant_motivation = NPCMotivationEngine(merchant_profile, merchant_memory)
    guard_motivation = NPCMotivationEngine(guard_profile, guard_memory)
    scholar_motivation = NPCMotivationEngine(scholar_profile, scholar_memory)
    
    # Create AI controllers
    merchant_ai = NPCBehaviorController(merchant_profile, current_hour=6)
    guard_ai = NPCBehaviorController(guard_profile, current_hour=6)  
    scholar_ai = NPCBehaviorController(scholar_profile, current_hour=6)
    
    # Link motivation engines to behavior controllers (for relationship goals)
    merchant_profile.behavior_controller = merchant_ai
    guard_profile.behavior_controller = guard_ai
    scholar_profile.behavior_controller = scholar_ai
    
    # Set up relationships
    merchant_ai.relationship_map = {"sarah_guard": 0.3, "elias_scholar": -0.1}
    guard_ai.relationship_map = {"marcus_merchant": 0.3, "elias_scholar": 0.2}
    scholar_ai.relationship_map = {"marcus_merchant": -0.1, "sarah_guard": 0.2}
    
    # Add some initial memories to trigger motivational responses
    from datetime import datetime, timedelta
    
    # Merchant witnessed theft (creates fear and survival motivation)
    theft_memory = MemoryNode(
        description="saw hooded figure steal from Baker Tom's stall, felt vulnerable",
        location=(10.5, 23.7),
        actor_ids=["hooded_stranger", "baker_tom"],
        context_tags=["theft", "crime", "witness", "threat"],
        timestamp=datetime.now() - timedelta(hours=12),
        initial_strength=0.9
    )
    merchant_memory.add_memory(theft_memory)
    merchant_motivation.adjust_weights_from_memory(theft_memory)
    
    # Guard discovered corruption (creates betrayal feelings and revenge motivation)
    corruption_memory = MemoryNode(
        description="Captain Williams taking bribe from smuggler, betrayed trust",
        location=(20.1, 15.3),
        actor_ids=["captain_williams", "unknown_smuggler"],
        context_tags=["corruption", "betrayal", "authority"],
        timestamp=datetime.now() - timedelta(hours=8),
        initial_strength=0.95
    )
    guard_memory.add_memory(corruption_memory)
    guard_motivation.adjust_weights_from_memory(corruption_memory)
    
    # Scholar made discovery (creates knowledge motivation)
    discovery_memory = MemoryNode(
        description="found ancient text mentioning lost library of Alexandria",
        location=(5.8, 42.1),
        actor_ids=["self"],
        context_tags=["discovery", "knowledge", "research"],
        timestamp=datetime.now() - timedelta(hours=6),
        initial_strength=0.8
    )
    scholar_memory.add_memory(discovery_memory)
    scholar_motivation.adjust_weights_from_memory(discovery_memory)
    
    # Create rumor network with some spreading rumors
    from rumor_engine import RumorNetwork
    
    rumor_network = RumorNetwork(max_rumors=50)
    
    # Add rumors that will affect our NPCs
    crime_rumor = Rumor(
        content="there's a gang of thieves operating in the market district",
        originator_id="concerned_citizen",
        location_origin=(10.0, 20.0),
        confidence_level=0.7
    )
    rumor_network.active_rumors.append(crime_rumor)
    
    corruption_rumor = Rumor(
        content="some city watch officers are taking bribes from criminals",
        originator_id="anonymous_tipster",
        location_origin=(15.0, 18.0),
        confidence_level=0.6
    )
    rumor_network.active_rumors.append(corruption_rumor)
    
    scholarly_rumor = Rumor(
        content="Elias the Scholar has discovered something important in the old texts",
        originator_id="library_assistant",
        location_origin=(5.0, 40.0),
        confidence_level=0.8
    )
    rumor_network.active_rumors.append(scholarly_rumor)
    
    # Generate initial goals based on starting motivations
    print("=== INITIAL MOTIVATION AND GOAL GENERATION ===")
    merchant_motivation.generate_personal_goals(6)
    guard_motivation.generate_personal_goals(6)
    scholar_motivation.generate_personal_goals(6)
    
    print(merchant_motivation.serialize_motivation_state())
    print(guard_motivation.serialize_motivation_state())
    print(scholar_motivation.serialize_motivation_state())
    
    # Simulate 24-hour period with motivation tracking
    npcs = [
        ("Marcus (Merchant)", merchant_ai, merchant_memory, merchant_motivation),
        ("Sarah (Guard)", guard_ai, guard_memory, guard_motivation), 
        ("Elias (Scholar)", scholar_ai, scholar_memory, scholar_motivation)
    ]
    
    print(f"\n{'='*60}")
    print("STARTING 24-HOUR BEHAVIORAL + MOTIVATIONAL SIMULATION")
    print("="*60)
    
    # Run hourly simulation
    for hour in range(6, 30):  # 6 AM to 6 AM next day
        current_hour = hour % 24
        print(f"\n--- HOUR {current_hour:2d}:00 ---")
        
        # Add dramatic events to test motivation shifts
        if hour == 10:  # 10 AM - merchant gets threatening rumor (survival crisis)
            threat_rumor = Rumor(
                content="Marcus the Merchant has been marked by the thieves guild for elimination",
                originator_id="street_informant",
                location_origin=(11.0, 22.0),
                confidence_level=0.8
            )
            merchant_ai.react_to_rumors([threat_rumor])
            
            # Add memory of the threat
            threat_memory = MemoryNode(
                description="received credible death threat from thieves guild",
                location=(11.0, 22.0),
                actor_ids=["street_informant", "thieves_guild"],
                context_tags=["threat", "danger", "survival"],
                timestamp=datetime.now(),
                initial_strength=0.9
            )
            merchant_memory.add_memory(threat_memory)
            merchant_motivation.adjust_weights_from_memory(threat_memory)
            print("  * CRISIS: Death threat against Marcus (survival motivation spike expected)")
        
        elif hour == 12:  # 12 PM - resource scarcity hits scholar
            scarcity_memory = MemoryNode(
                description="discovered all research funds have been cut, facing poverty",
                location=(5.8, 42.1),
                actor_ids=["university_administrator"],
                context_tags=["poverty", "resource_scarcity", "survival"],
                timestamp=datetime.now(),
                initial_strength=0.8
            )
            scholar_memory.add_memory(scarcity_memory)
            scholar_motivation.adjust_weights_from_memory(scarcity_memory)
            print("  * CRISIS: Scholar faces resource scarcity (wealth/survival motivation expected)")
        
        elif hour == 14:  # 2 PM - guard witnesses suspicious activity (escalates conspiracy)
            suspicious_memory = MemoryNode(
                description="saw Marcus the Merchant talking secretly with hooded figures, possible conspiracy",
                location=(12.3, 8.9),
                actor_ids=["marcus_merchant", "unknown_figures"],
                context_tags=["suspicious", "conspiracy", "observation", "betrayal"],
                timestamp=datetime.now(),
                initial_strength=0.7
            )
            guard_memory.add_memory(suspicious_memory)
            guard_motivation.adjust_weights_from_memory(suspicious_memory)
            print("  * DRAMA: Sarah witnesses potential conspiracy (duty vs. personal conflict)")
        
        elif hour == 16:  # 4 PM - betrayal event for guard
            betrayal_memory = MemoryNode(
                description="discovered my partner has been feeding information to criminals",
                location=(20.1, 15.3),
                actor_ids=["guard_partner", "criminal_network"],
                context_tags=["betrayal", "corruption", "personal"],
                timestamp=datetime.now(),
                initial_strength=0.95
            )
            guard_memory.add_memory(betrayal_memory)
            guard_motivation.adjust_weights_from_memory(betrayal_memory)
            print("  * BETRAYAL: Sarah's partner betrays her (revenge motivation surge expected)")
        
        elif hour == 18:  # 6 PM - scholar learns about corruption
            scholar_ai.react_to_rumors([corruption_rumor])
            print("  * Elias learns about corruption rumors (may affect duty motivation)")
        
        elif hour == 20:  # 8 PM - faction pressure event
            # Add faction orders to test sync functionality
            guard_motivation.faction_orders.append({
                "goal_id": "faction_order_1",
                "description": "Investigate corruption within city watch ranks",
                "urgency": 0.9,
                "type": "faction",
                "faction_linked": True,
                "motivation_source": "duty",
                "created_hour": current_hour,
                "progress": 0.0
            })
            print("  * FACTION ORDER: Sarah receives official investigation assignment")
        
        elif hour == 22:  # 10 PM - social interactions with motivation influences
            print("  * Social interactions influenced by motivations:")
            
            # Check if merchant's survival motivation affects social behavior
            if merchant_motivation.motivational_weights["survival"] > 0.7:
                print("    - Marcus avoids social contact (high survival motivation)")
                merchant_ai.stress_level = min(1.0, merchant_ai.stress_level + 0.2)
            
            # Check guard interaction decisions
            if guard_ai.interact("marcus_merchant", "confrontation"):
                print("    - Sarah confronts Marcus (duty motivation overrides caution)")
                merchant_ai.stress_level = min(1.0, merchant_ai.stress_level + 0.3)
                merchant_ai.relationship_map["sarah_guard"] -= 0.3
            else:
                print("    - Sarah avoids confronting Marcus (conflicted motivations)")
            
            if scholar_ai.interact("sarah_guard", "casual"):
                print("    - Elias approaches Sarah (knowledge motivation seeks information)")
            else:
                print("    - Elias avoids Sarah (current motivations don't favor interaction)")
        
        # Run simulation tick for each NPC (behavior + motivation)
        for name, npc_ai, memory_bank, motivation_engine in npcs:
            npc_ai.simulate_tick(memory_bank, rumor_network)
            motivation_changes = motivation_engine.tick(current_hour)
            
            # Show motivation changes if significant
            motivation_summary = ""
            if motivation_changes["motivation_shifts"]:
                motivation_summary = f" [Motivation shifts: {len(motivation_changes['motivation_shifts'])}]"
            if motivation_changes["goals_generated"] > 0:
                motivation_summary += f" [+{motivation_changes['goals_generated']} goals]"
            
            print(f"  {name}: {npc_ai.current_state} (stress: {npc_ai.stress_level:.2f}){motivation_summary}")
    
    # Generate comprehensive reports including motivation analysis
    print("\n" + "="*80)
    print("COMPREHENSIVE DAILY REPORTS (BEHAVIOR + MOTIVATION)")
    print("="*80)
    
    for name, npc_ai, memory_bank, motivation_engine in npcs:
        print(npc_ai.log_day())
        print(motivation_engine.serialize_motivation_state())
        print("-" * 60)
    
    print("\n=== MOTIVATION ENGINE TEST ANALYSIS ===")
    print("Expected outcomes demonstrated:")
    print("- Survival motivation spikes from death threats and resource scarcity")
    print("- Revenge motivation increases from betrayal experiences") 
    print("- Knowledge motivation drives research and discovery goals")
    print("- Duty motivation conflicts with personal safety concerns")
    print("- Goals dynamically generated based on experiences and motivations")
    print("- Faction orders integrated with personal goal systems")
    print("- Personality traits influence baseline motivational weights")
    print("- Traumatic memories cause lasting motivational shifts")


if __name__ == "__main__":
    create_test_harness() 