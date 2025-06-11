import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

# Social simulation system imports
from memory_core import MemoryBank, MemoryNode
from npc_profile import NPCProfile
from rumor_engine import RumorNetwork, Rumor


class FactionLoyaltyEngine:
    """
    Manages faction loyalty dynamics for NPCs, including defection scenarios,
    loyalty shifts based on experiences, and the influence of loyalty on behavior.
    
    This system creates believable faction politics where NPCs can become
    disillusioned, defect, or become zealous based on their experiences.
    """
    
    # Loyalty categories for interpretation
    LOYALTY_CATEGORIES = {
        0.8: "Zealous",      # Will die for the faction
        0.5: "Loyal",        # Strongly committed
        0.2: "Committed",    # Generally supportive
        0.0: "Neutral",      # Indifferent
        -0.2: "Skeptical",   # Having doubts
        -0.5: "Disloyal",    # Actively opposed
        -0.8: "Rebellious"   # Seeking to destroy faction
    }
    
    # Events that affect loyalty
    LOYALTY_MODIFIERS = {
        "faction_victory": 0.15,
        "faction_defeat": -0.1,
        "personal_promotion": 0.2,
        "personal_betrayal": -0.4,
        "faction_corruption": -0.3,
        "faction_protection": 0.25,
        "broken_promise": -0.2,
        "resource_sharing": 0.1,
        "ideological_alignment": 0.1,
        "ideological_conflict": -0.15,
        "leader_change": -0.05,  # Uncertainty
        "faction_expansion": 0.1,
        "faction_decline": -0.1
    }
    
    def __init__(self, npc_profile: NPCProfile, faction_id: Optional[str] = None):
        self.npc_profile = npc_profile
        self.faction_id = faction_id or npc_profile.faction_affiliation
        
        # Initialize loyalty based on personality and beliefs
        self.loyalty_score = self._calculate_initial_loyalty()
        
        # Historical tracking
        self.historical_alignment = []
        if self.faction_id:
            self.historical_alignment.append({
                "faction_id": self.faction_id,
                "join_timestamp": datetime.now() - timedelta(days=random.randint(30, 365)),
                "join_reason": "initial_background",
                "exit_timestamp": None,
                "exit_cause": None,
                "peak_loyalty": self.loyalty_score
            })
        
        # Loyalty tracking
        self.loyalty_history = [(datetime.now(), self.loyalty_score, "initial")]
        self.defection_warnings = 0
        self.propaganda_resistance = 0.0
        
        # Decision influence weights
        self.loyalty_decision_weight = 0.3  # How much loyalty affects decisions
        
        # Internal state
        self.pending_defection = False
        self.defection_threshold = -0.5
        self.last_loyalty_update = datetime.now()
        
    def _calculate_initial_loyalty(self) -> float:
        """Calculate starting loyalty based on personality and beliefs."""
        base_loyalty = 0.0
        
        traits = self.npc_profile.personality_traits
        beliefs = self.npc_profile.belief_system
        
        # Personality influences
        if "loyal" in traits:
            base_loyalty += 0.4
        if "rebellious" in traits:
            base_loyalty -= 0.3
        if "pragmatic" in traits:
            base_loyalty += 0.1  # Sees value in organization
        if "idealistic" in traits:
            base_loyalty += 0.2  # Believes in causes
        if "cynical" in traits:
            base_loyalty -= 0.2
        if "ambitious" in traits:
            base_loyalty += 0.1  # Sees opportunity
        if "independent" in traits:
            base_loyalty -= 0.1
        
        # Belief system influences
        loyalty_belief = beliefs.get("loyalty", 0.5)
        authority_belief = beliefs.get("authority", 0.5)
        tradition_belief = beliefs.get("tradition", 0.5)
        
        base_loyalty += (loyalty_belief - 0.5) * 0.3
        base_loyalty += (authority_belief - 0.5) * 0.2
        base_loyalty += (tradition_belief - 0.5) * 0.1
        
        # Add some randomness for individual variation
        base_loyalty += random.uniform(-0.2, 0.2)
        
        return max(-1.0, min(1.0, base_loyalty))
    
    def update_loyalty(self, faction_events: List[Dict] = None, 
                      memory_inputs: List[MemoryNode] = None,
                      rumor_inputs: List[Rumor] = None) -> Dict[str, Any]:
        """
        Update loyalty score based on recent faction events, memories, and rumors.
        
        Returns:
            Summary of loyalty changes and reasons
        """
        if not self.faction_id:
            return {"loyalty_change": 0.0, "reasons": ["No faction affiliation"]}
        
        faction_events = faction_events or []
        memory_inputs = memory_inputs or []
        rumor_inputs = rumor_inputs or []
        
        old_loyalty = self.loyalty_score
        changes = []
        total_change = 0.0
        
        # Process faction events
        for event in faction_events:
            event_type = event.get("type", "unknown")
            modifier = self.LOYALTY_MODIFIERS.get(event_type, 0.0)
            
            # Personality affects how events are interpreted
            if "cynical" in self.npc_profile.personality_traits:
                modifier *= 0.7  # Less affected by positive events
            if "loyal" in self.npc_profile.personality_traits:
                modifier *= 1.3  # More affected by all events
            if "pragmatic" in self.npc_profile.personality_traits:
                if event_type in ["faction_victory", "personal_promotion", "resource_sharing"]:
                    modifier *= 1.2  # Values practical benefits
            
            total_change += modifier
            changes.append(f"Event '{event_type}': {modifier:+.2f}")
        
        # Process memory inputs for faction-related experiences
        for memory in memory_inputs:
            memory_change = self._analyze_memory_for_loyalty(memory)
            if memory_change != 0.0:
                total_change += memory_change
                changes.append(f"Memory impact: {memory_change:+.2f}")
        
        # Process rumors about faction
        for rumor in rumor_inputs:
            rumor_change = self._analyze_rumor_for_loyalty(rumor)
            if rumor_change != 0.0:
                total_change += rumor_change
                changes.append(f"Rumor impact: {rumor_change:+.2f}")
        
        # Apply natural loyalty decay/growth over time
        time_since_update = (datetime.now() - self.last_loyalty_update).total_seconds() / 3600
        if time_since_update > 24:  # Daily loyalty adjustment
            natural_change = self._natural_loyalty_drift()
            total_change += natural_change
            if abs(natural_change) > 0.01:
                changes.append(f"Natural drift: {natural_change:+.2f}")
        
        # Apply total change
        self.loyalty_score = max(-1.0, min(1.0, self.loyalty_score + total_change))
        
        # Record loyalty change
        self.loyalty_history.append((datetime.now(), self.loyalty_score, f"Update: {total_change:+.2f}"))
        self.last_loyalty_update = datetime.now()
        
        # Update historical peak loyalty
        if self.historical_alignment:
            current_entry = self.historical_alignment[-1]
            if current_entry["faction_id"] == self.faction_id:
                current_entry["peak_loyalty"] = max(current_entry["peak_loyalty"], self.loyalty_score)
        
        return {
            "loyalty_change": total_change,
            "old_loyalty": old_loyalty,
            "new_loyalty": self.loyalty_score,
            "loyalty_category": self.get_loyalty_category(),
            "reasons": changes
        }
    
    def _analyze_memory_for_loyalty(self, memory: MemoryNode) -> float:
        """Analyze how a memory affects faction loyalty."""
        if not memory.context_tags:
            return 0.0
        
        change = 0.0
        content_lower = memory.description.lower()
        
        # Faction-related memory analysis
        if any(tag in memory.context_tags for tag in ["betrayal", "corruption"]):
            if self.faction_id.lower() in content_lower:
                change -= 0.3  # Direct faction betrayal
            else:
                change -= 0.1  # General corruption affects trust in institutions
        
        if "loyalty" in memory.context_tags or "help" in memory.context_tags:
            if self.faction_id.lower() in content_lower:
                change += 0.2  # Faction helped the NPC
        
        if "promotion" in memory.context_tags or "reward" in memory.context_tags:
            change += 0.15  # Personal advancement
        
        if "punishment" in memory.context_tags or "discipline" in memory.context_tags:
            if self.faction_id.lower() in content_lower:
                change -= 0.2  # Faction punished the NPC
        
        if "ideological" in memory.context_tags:
            # Check if memory aligns with NPC's beliefs
            justice_belief = self.npc_profile.belief_system.get("justice", 0.5)
            if "injustice" in content_lower and justice_belief > 0.6:
                change -= 0.15  # Faction committed injustice
            elif "justice" in content_lower and justice_belief > 0.6:
                change += 0.1  # Faction upheld justice
        
        # Scale by memory strength and recency
        hours_ago = (datetime.now() - memory.timestamp).total_seconds() / 3600
        recency_factor = max(0.1, 1.0 - (hours_ago / 168))  # Decay over a week
        
        return change * memory.strength * recency_factor
    
    def _analyze_rumor_for_loyalty(self, rumor: Rumor) -> float:
        """Analyze how a rumor affects faction loyalty."""
        if not self.faction_id:
            return 0.0
        
        change = 0.0
        content_lower = rumor.content.lower()
        faction_lower = self.faction_id.lower()
        
        # Direct faction mentions
        if faction_lower in content_lower:
            if any(word in content_lower for word in ["corrupt", "betrayed", "failed", "defeat"]):
                change -= 0.1 * rumor.confidence_level
            elif any(word in content_lower for word in ["victory", "success", "honor", "heroic"]):
                change += 0.08 * rumor.confidence_level
        
        # Leadership mentions
        if any(word in content_lower for word in ["leader", "captain", "commander"]):
            if any(word in content_lower for word in ["corrupt", "incompetent", "traitor"]):
                change -= 0.15 * rumor.confidence_level
            elif any(word in content_lower for word in ["wise", "heroic", "successful"]):
                change += 0.1 * rumor.confidence_level
        
        # General reputation effects
        if any(word in content_lower for word in ["organization", "guild", "order"]):
            if "corrupt" in content_lower:
                change -= 0.05 * rumor.confidence_level  # General institutional distrust
        
        return change
    
    def _natural_loyalty_drift(self) -> float:
        """Calculate natural loyalty changes over time."""
        drift = 0.0
        
        # Extreme loyalties tend to moderate over time
        if self.loyalty_score > 0.8:
            drift -= 0.02  # Zealotry fades slightly
        elif self.loyalty_score < -0.8:
            drift += 0.01  # Extreme hatred moderates slightly
        
        # Personality affects drift
        if "loyal" in self.npc_profile.personality_traits:
            drift += 0.01  # Naturally tends toward loyalty
        if "rebellious" in self.npc_profile.personality_traits:
            drift -= 0.01  # Naturally tends toward rebellion
        
        # Random small fluctuations
        drift += random.uniform(-0.005, 0.005)
        
        return drift
    
    def evaluate_defection_threshold(self, threshold: float = -0.5) -> bool:
        """Check if NPC should consider defection based on loyalty threshold."""
        if not self.faction_id:
            return False
        
        self.defection_threshold = threshold
        
        if self.loyalty_score <= threshold:
            self.defection_warnings += 1
            
            # Multiple warnings increase defection likelihood
            defection_probability = 0.2 + (self.defection_warnings * 0.1)
            
            # Personality affects defection likelihood
            if "rebellious" in self.npc_profile.personality_traits:
                defection_probability += 0.3
            if "loyal" in self.npc_profile.personality_traits:
                defection_probability -= 0.2
            if "pragmatic" in self.npc_profile.personality_traits:
                defection_probability += 0.1  # Will leave if it's not working out
            if "cowardly" in self.npc_profile.personality_traits:
                defection_probability -= 0.1  # Afraid to leave
            
            # High stress makes defection more likely
            if hasattr(self.npc_profile, 'behavior_controller'):
                stress = getattr(self.npc_profile.behavior_controller, 'stress_level', 0.0)
                defection_probability += stress * 0.2
            
            if random.random() < defection_probability:
                self.pending_defection = True
                return True
        else:
            # Reset warnings if loyalty improves
            self.defection_warnings = max(0, self.defection_warnings - 1)
        
        return False
    
    def trigger_defection(self) -> Dict[str, Any]:
        """Handle the defection process and update faction membership."""
        if not self.faction_id or not self.pending_defection:
            return {"defected": False, "reason": "No pending defection"}
        
        old_faction = self.faction_id
        defection_reason = self._determine_defection_reason()
        
        # Update historical record
        if self.historical_alignment:
            current_entry = self.historical_alignment[-1]
            if current_entry["faction_id"] == old_faction and current_entry["exit_timestamp"] is None:
                current_entry["exit_timestamp"] = datetime.now()
                current_entry["exit_cause"] = defection_reason
        
        # Remove faction affiliation
        self.faction_id = None
        self.npc_profile.faction_affiliation = None
        
        # Reset loyalty and state
        self.loyalty_score = 0.0  # Neutral after defection
        self.pending_defection = False
        self.defection_warnings = 0
        
        # Record the defection
        self.loyalty_history.append((datetime.now(), self.loyalty_score, f"Defected from {old_faction}"))
        
        return {
            "defected": True,
            "old_faction": old_faction,
            "reason": defection_reason,
            "new_loyalty": self.loyalty_score,
            "timestamp": datetime.now()
        }
    
    def _determine_defection_reason(self) -> str:
        """Determine the primary reason for defection based on recent experiences."""
        reasons = []
        
        # Analyze recent loyalty history for patterns
        recent_changes = [entry for entry in self.loyalty_history[-10:] 
                         if "Update:" in entry[2]]
        
        if any("betrayal" in str(entry).lower() for entry in recent_changes):
            reasons.append("personal_betrayal")
        if any("corruption" in str(entry).lower() for entry in recent_changes):
            reasons.append("faction_corruption")
        if any("defeat" in str(entry).lower() for entry in recent_changes):
            reasons.append("faction_failure")
        
        # Personality-based reasons
        if "idealistic" in self.npc_profile.personality_traits:
            reasons.append("ideological_differences")
        if "pragmatic" in self.npc_profile.personality_traits:
            reasons.append("lack_of_benefits")
        if "ambitious" in self.npc_profile.personality_traits:
            reasons.append("limited_advancement")
        
        return random.choice(reasons) if reasons else "general_disillusionment"
    
    def influence_decision_making(self, decision_context: Dict) -> Dict[str, float]:
        """
        Apply loyalty influence to modify behavior and decision-making.
        
        Returns weights that should be applied to various decision factors.
        """
        if not self.faction_id:
            return {"faction_loyalty": 0.0}
        
        loyalty_category = self.get_loyalty_category()
        influences = {}
        
        # Base loyalty influence
        influences["faction_loyalty"] = self.loyalty_score * self.loyalty_decision_weight
        
        # Specific decision modifications based on loyalty level
        if loyalty_category == "Zealous":
            influences["faction_orders_compliance"] = 1.0
            influences["faction_member_trust_bonus"] = 0.3
            influences["outsider_suspicion"] = 0.2
            influences["risk_taking_for_faction"] = 0.4
            
        elif loyalty_category == "Loyal":
            influences["faction_orders_compliance"] = 0.8
            influences["faction_member_trust_bonus"] = 0.2
            influences["outsider_suspicion"] = 0.1
            influences["risk_taking_for_faction"] = 0.2
            
        elif loyalty_category == "Committed":
            influences["faction_orders_compliance"] = 0.6
            influences["faction_member_trust_bonus"] = 0.1
            
        elif loyalty_category == "Skeptical":
            influences["faction_orders_compliance"] = 0.3
            influences["information_sharing_reduction"] = 0.2
            influences["independent_action_bias"] = 0.1
            
        elif loyalty_category == "Disloyal":
            influences["faction_orders_compliance"] = 0.1
            influences["information_sharing_reduction"] = 0.4
            influences["independent_action_bias"] = 0.3
            influences["sabotage_consideration"] = 0.1
            
        elif loyalty_category == "Rebellious":
            influences["faction_orders_compliance"] = -0.2
            influences["information_sharing_reduction"] = 0.6
            influences["independent_action_bias"] = 0.5
            influences["sabotage_consideration"] = 0.3
            influences["defection_consideration"] = 0.4
        
        # Stress amplifies negative loyalty effects
        if hasattr(self.npc_profile, 'behavior_controller'):
            stress = getattr(self.npc_profile.behavior_controller, 'stress_level', 0.0)
            if stress > 0.5 and self.loyalty_score < 0.0:
                for key, value in influences.items():
                    if "reduction" in key or "sabotage" in key or "defection" in key:
                        influences[key] = value * (1.0 + stress)
        
        return influences
    
    def propaganda_effect(self, propaganda_type: str, intensity: float = 0.5) -> Dict[str, Any]:
        """
        Simulate faction attempts to influence loyalty through propaganda.
        
        Args:
            propaganda_type: Type of propaganda (fear, reward, ideology, manipulation)
            intensity: Strength of propaganda effort (0.0 to 1.0)
        """
        if not self.faction_id:
            return {"effect": 0.0, "resistance_built": 0.0}
        
        # Calculate propaganda effectiveness
        base_effect = intensity * 0.1  # Base propaganda effectiveness
        
        # Personality affects susceptibility
        susceptibility = 1.0
        
        if "cynical" in self.npc_profile.personality_traits:
            susceptibility *= 0.3  # Highly resistant
        if "naive" in self.npc_profile.personality_traits:
            susceptibility *= 1.5  # More susceptible
        if "intelligent" in self.npc_profile.personality_traits:
            susceptibility *= 0.7  # Can see through manipulation
        if "loyal" in self.npc_profile.personality_traits:
            if propaganda_type == "ideology":
                susceptibility *= 1.3  # Responds to ideological appeals
        if "fearful" in self.npc_profile.personality_traits:
            if propaganda_type == "fear":
                susceptibility *= 1.4  # Fear tactics work well
        if "greedy" in self.npc_profile.personality_traits:
            if propaganda_type == "reward":
                susceptibility *= 1.2  # Responds to material incentives
        
        # Resistance builds over time
        resistance_factor = max(0.1, 1.0 - self.propaganda_resistance)
        effective_propaganda = base_effect * susceptibility * resistance_factor
        
        # Apply different propaganda types
        loyalty_change = 0.0
        resistance_increase = intensity * 0.05  # Default resistance building
        
        if propaganda_type == "fear":
            # Fear-based propaganda increases loyalty through intimidation
            loyalty_change = effective_propaganda * 0.8
            
        elif propaganda_type == "reward":
            # Reward-based propaganda through material benefits
            loyalty_change = effective_propaganda * 1.0
            
        elif propaganda_type == "ideology":
            # Ideological propaganda appeals to beliefs
            justice_belief = self.npc_profile.belief_system.get("justice", 0.5)
            loyalty_belief = self.npc_profile.belief_system.get("loyalty", 0.5)
            belief_alignment = (justice_belief + loyalty_belief) / 2
            loyalty_change = effective_propaganda * belief_alignment * 1.2
            
        elif propaganda_type == "manipulation":
            # Manipulation through misinformation and social pressure
            loyalty_change = effective_propaganda * 0.6
            # Manipulation builds more resistance
            resistance_increase = intensity * 0.1
        else:
            loyalty_change = effective_propaganda * 0.5  # Default effectiveness
            resistance_increase = intensity * 0.05
        
        # Apply loyalty change
        old_loyalty = self.loyalty_score
        self.loyalty_score = max(-1.0, min(1.0, self.loyalty_score + loyalty_change))
        
        # Build resistance to future propaganda
        self.propaganda_resistance = min(0.8, self.propaganda_resistance + resistance_increase)
        
        # Record the propaganda effect
        self.loyalty_history.append((datetime.now(), self.loyalty_score, 
                                   f"Propaganda ({propaganda_type}): {loyalty_change:+.2f}"))
        
        return {
            "effect": loyalty_change,
            "old_loyalty": old_loyalty,
            "new_loyalty": self.loyalty_score,
            "resistance_built": resistance_increase,
            "total_resistance": self.propaganda_resistance
        }
    
    def join_faction(self, new_faction_id: str, join_reason: str = "recruitment") -> Dict[str, Any]:
        """Handle joining a new faction."""
        old_faction = self.faction_id
        
        # Leave current faction if any
        if self.faction_id:
            self.trigger_defection()  # Clean exit from current faction
        
        # Join new faction
        self.faction_id = new_faction_id
        self.npc_profile.faction_affiliation = new_faction_id
        
        # Calculate initial loyalty to new faction
        self.loyalty_score = self._calculate_initial_loyalty()
        
        # Add to historical alignment
        self.historical_alignment.append({
            "faction_id": new_faction_id,
            "join_timestamp": datetime.now(),
            "join_reason": join_reason,
            "exit_timestamp": None,
            "exit_cause": None,
            "peak_loyalty": self.loyalty_score
        })
        
        # Record the change
        self.loyalty_history.append((datetime.now(), self.loyalty_score, 
                                   f"Joined {new_faction_id}"))
        
        return {
            "joined": True,
            "old_faction": old_faction,
            "new_faction": new_faction_id,
            "initial_loyalty": self.loyalty_score,
            "join_reason": join_reason
        }
    
    def get_loyalty_category(self) -> str:
        """Get descriptive loyalty category for current loyalty score."""
        for threshold, category in sorted(self.LOYALTY_CATEGORIES.items(), reverse=True):
            if self.loyalty_score >= threshold:
                return category
        return "Rebellious"
    
    def get_loyalty_summary(self) -> Dict[str, Any]:
        """Get comprehensive loyalty status summary."""
        return {
            "faction_id": self.faction_id,
            "loyalty_score": self.loyalty_score,
            "loyalty_category": self.get_loyalty_category(),
            "defection_warnings": self.defection_warnings,
            "pending_defection": self.pending_defection,
            "propaganda_resistance": self.propaganda_resistance,
            "faction_count": len(self.historical_alignment),
            "loyalty_trend": self._calculate_loyalty_trend(),
            "last_update": self.last_loyalty_update
        }
    
    def _calculate_loyalty_trend(self) -> str:
        """Calculate recent loyalty trend direction."""
        if len(self.loyalty_history) < 2:
            return "stable"
        
        recent_entries = self.loyalty_history[-5:]  # Last 5 entries
        if len(recent_entries) < 2:
            return "stable"
        
        trend_sum = 0
        for i in range(1, len(recent_entries)):
            trend_sum += recent_entries[i][1] - recent_entries[i-1][1]
        
        avg_trend = trend_sum / (len(recent_entries) - 1)
        
        if avg_trend > 0.05:
            return "increasing"
        elif avg_trend < -0.05:
            return "decreasing"
        else:
            return "stable"


def create_loyalty_test_harness():
    """Test harness demonstrating faction loyalty dynamics and defection scenarios."""
    print("=== FACTION LOYALTY ENGINE TEST HARNESS ===\n")
    
    # Create test NPCs with different personalities
    from npc_profile import NPCProfile
    
    # NPC 1: Loyal guard who will be betrayed
    guard_profile = NPCProfile.generate_random("Commander Torres", "city_center", 
                                              archetype="guardian")
    guard_profile.personality_traits = ["loyal", "honorable", "dutiful", "idealistic", "brave"]
    guard_profile.faction_affiliation = "city_watch"
    guard_profile.belief_system = {"loyalty": 0.8, "justice": 0.9, "authority": 0.7}
    
    # NPC 2: Pragmatic merchant who joins for benefits
    merchant_profile = NPCProfile.generate_random("Elena Blackwood", "market_district", 
                                                 archetype="merchant")
    merchant_profile.personality_traits = ["pragmatic", "ambitious", "greedy", "clever", "cautious"]
    merchant_profile.faction_affiliation = "merchants_guild"
    merchant_profile.belief_system = {"loyalty": 0.4, "justice": 0.5, "authority": 0.3}
    
    # Create loyalty engines
    guard_loyalty = FactionLoyaltyEngine(guard_profile)
    merchant_loyalty = FactionLoyaltyEngine(merchant_profile)
    
    print("=== INITIAL LOYALTY STATUS ===")
    print(f"Commander Torres (City Watch): {guard_loyalty.loyalty_score:.2f} ({guard_loyalty.get_loyalty_category()})")
    print(f"Elena Blackwood (Merchants Guild): {merchant_loyalty.loyalty_score:.2f} ({merchant_loyalty.get_loyalty_category()})")
    
    # Create memory banks for faction experiences
    from memory_core import MemoryBank
    
    guard_memory = MemoryBank("torres_guard", 100)
    merchant_memory = MemoryBank("elena_merchant", 100)
    
    print(f"\n{'='*60}")
    print("FACTION LOYALTY SIMULATION - DAY BY DAY")
    print("="*60)
    
    # Day 1: Normal operations, some propaganda
    print("\n--- DAY 1: Normal Operations ---")
    
    # Faction tries propaganda on both NPCs
    guard_propaganda = guard_loyalty.propaganda_effect("ideology", 0.6)
    merchant_propaganda = merchant_loyalty.propaganda_effect("reward", 0.5)
    
    print(f"Guard responds to ideological propaganda: {guard_propaganda['effect']:+.2f}")
    print(f"Merchant responds to reward propaganda: {merchant_propaganda['effect']:+.2f}")
    
    # Day 2: Faction achievements
    print("\n--- DAY 2: Faction Victories ---")
    
    faction_events = [
        {"type": "faction_victory", "description": "successful operation against smugglers"},
        {"type": "personal_promotion", "description": "Torres promoted to senior commander"}
    ]
    
    guard_changes = guard_loyalty.update_loyalty(faction_events=faction_events)
    merchant_changes = merchant_loyalty.update_loyalty(faction_events=[
        {"type": "resource_sharing", "description": "guild shared profitable trade route"}
    ])
    
    print(f"Guard loyalty change: {guard_changes['loyalty_change']:+.2f} -> {guard_changes['new_loyalty']:.2f}")
    print(f"Merchant loyalty change: {merchant_changes['loyalty_change']:+.2f} -> {merchant_changes['new_loyalty']:.2f}")
    
    # Day 3: First signs of corruption
    print("\n--- DAY 3: Corruption Discovery ---")
    
    # Guard discovers corruption in city watch
    corruption_memory = MemoryNode(
        description="discovered Captain Mills taking bribes from criminal syndicate",
        location=(15.2, 18.7),
        actor_ids=["captain_mills", "criminal_syndicate"],
        context_tags=["corruption", "betrayal", "authority"],
        timestamp=datetime.now(),
        initial_strength=0.9
    )
    guard_memory.add_memory(corruption_memory)
    
    guard_changes = guard_loyalty.update_loyalty(memory_inputs=[corruption_memory])
    
    print(f"Guard discovers corruption - loyalty change: {guard_changes['loyalty_change']:+.2f}")
    print(f"New guard loyalty: {guard_changes['new_loyalty']:.2f} ({guard_loyalty.get_loyalty_category()})")
    
    # Day 4: Personal betrayal
    print("\n--- DAY 4: Personal Betrayal ---")
    
    # Guard is betrayed by trusted colleague
    betrayal_memory = MemoryNode(
        description="Lieutenant Shaw sold information about my investigation to the criminals",
        location=(20.1, 15.3),
        actor_ids=["lieutenant_shaw", "criminal_network"],
        context_tags=["betrayal", "personal", "trust"],
        timestamp=datetime.now(),
        initial_strength=0.95
    )
    guard_memory.add_memory(betrayal_memory)
    
    # Also add faction failure event
    betrayal_events = [
        {"type": "personal_betrayal", "description": "trusted colleague betrayed investigation"},
        {"type": "faction_corruption", "description": "widespread corruption revealed"}
    ]
    
    guard_changes = guard_loyalty.update_loyalty(
        faction_events=betrayal_events,
        memory_inputs=[betrayal_memory]
    )
    
    print(f"Personal betrayal - loyalty change: {guard_changes['loyalty_change']:+.2f}")
    print(f"Guard loyalty now: {guard_changes['new_loyalty']:.2f} ({guard_loyalty.get_loyalty_category()})")
    
    # Check for defection threshold
    defection_check = guard_loyalty.evaluate_defection_threshold()
    print(f"Defection threshold check: {'TRIGGERED' if defection_check else 'Not reached'}")
    
    # Day 5: Broken promises for merchant
    print("\n--- DAY 5: Broken Promises ---")
    
    # Merchant guild breaks promises about trade routes
    broken_promise_events = [
        {"type": "broken_promise", "description": "guild leaders kept best routes for themselves"},
        {"type": "faction_corruption", "description": "guild leadership embezzling funds"}
    ]
    
    merchant_changes = merchant_loyalty.update_loyalty(faction_events=broken_promise_events)
    
    print(f"Merchant faces broken promises - loyalty change: {merchant_changes['loyalty_change']:+.2f}")
    print(f"Merchant loyalty: {merchant_changes['new_loyalty']:.2f} ({merchant_loyalty.get_loyalty_category()})")
    
    # Day 6: Propaganda intensifies
    print("\n--- DAY 6: Propaganda Campaign ---")
    
    # Faction tries to retain loyalty through fear and manipulation
    guard_fear_prop = guard_loyalty.propaganda_effect("fear", 0.8)
    merchant_manip_prop = merchant_loyalty.propaganda_effect("manipulation", 0.7)
    
    print(f"Fear propaganda on guard: {guard_fear_prop['effect']:+.2f} (resistance: {guard_fear_prop['resistance_built']:.2f})")
    print(f"Manipulation on merchant: {merchant_manip_prop['effect']:+.2f} (resistance: {merchant_manip_prop['resistance_built']:.2f})")
    
    # Day 7: Final straw
    print("\n--- DAY 7: Final Betrayal ---")
    
    # Guard faces retaliation for investigating corruption
    retaliation_memory = MemoryNode(
        description="city watch command threatened my family to stop investigation",
        location=(20.1, 15.3),
        actor_ids=["watch_command", "my_family"],
        context_tags=["threat", "retaliation", "family", "corruption"],
        timestamp=datetime.now(),
        initial_strength=1.0
    )
    guard_memory.add_memory(retaliation_memory)
    
    final_events = [
        {"type": "personal_betrayal", "description": "faction threatened family"},
        {"type": "faction_corruption", "description": "complete institutional failure"}
    ]
    
    guard_changes = guard_loyalty.update_loyalty(
        faction_events=final_events,
        memory_inputs=[retaliation_memory]
    )
    
    print(f"Final betrayal - loyalty change: {guard_changes['loyalty_change']:+.2f}")
    print(f"Final guard loyalty: {guard_changes['new_loyalty']:.2f} ({guard_loyalty.get_loyalty_category()})")
    
    # Check for defection
    defection_triggered = guard_loyalty.evaluate_defection_threshold(-0.3)  # Lower threshold due to severity
    print(f"Defection evaluation: {'DEFECTION IMMINENT' if defection_triggered else 'Still loyal'}")
    
    if defection_triggered:
        defection_result = guard_loyalty.trigger_defection()
        print(f"DEFECTION EXECUTED: {defection_result['reason']}")
        print(f"Torres has left the City Watch!")
    
    # Day 8: Merchant also considers leaving
    print("\n--- DAY 8: Merchant Weighs Options ---")
    
    # Merchant gets better offer from another organization
    merchant_defection = merchant_loyalty.evaluate_defection_threshold(-0.2)
    
    if merchant_defection:
        print("Elena considers leaving the Merchants Guild...")
        defection_result = merchant_loyalty.trigger_defection()
        print(f"Elena defects: {defection_result['reason']}")
        
        # Elena joins a rival organization
        join_result = merchant_loyalty.join_faction("free_traders_alliance", "better_opportunities")
        print(f"Elena joins {join_result['new_faction']} with loyalty {join_result['initial_loyalty']:.2f}")
    
    # Final loyalty summary
    print(f"\n{'='*60}")
    print("FINAL LOYALTY ANALYSIS")
    print("="*60)
    
    npcs = [
        ("Commander Torres", guard_loyalty),
        ("Elena Blackwood", merchant_loyalty)
    ]
    
    for name, loyalty_engine in npcs:
        summary = loyalty_engine.get_loyalty_summary()
        print(f"\n{name}:")
        print(f"  Current Faction: {summary['faction_id'] or 'None (Defected)'}")
        print(f"  Loyalty Score: {summary['loyalty_score']:.2f} ({summary['loyalty_category']})")
        print(f"  Loyalty Trend: {summary['loyalty_trend']}")
        print(f"  Defection Warnings: {summary['defection_warnings']}")
        print(f"  Propaganda Resistance: {summary['propaganda_resistance']:.2f}")
        print(f"  Total Factions: {summary['faction_count']}")
        
        # Decision-making influence
        influences = loyalty_engine.influence_decision_making({"context": "general"})
        print(f"  Decision Influences:")
        for factor, weight in influences.items():
            if abs(weight) > 0.1:
                print(f"    {factor}: {weight:+.2f}")
    
    print(f"\n=== FACTION LOYALTY TEST COMPLETE ===")
    print("Demonstrated behaviors:")
    print("- Loyalty evolution from experiences and memories")
    print("- Defection triggered by betrayal and corruption")
    print("- Propaganda effects with resistance building")
    print("- Personality-based loyalty susceptibility")
    print("- Faction switching and new loyalties")
    print("- Decision-making influence from loyalty levels")


if __name__ == "__main__":
    create_loyalty_test_harness() 