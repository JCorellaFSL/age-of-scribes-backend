import uuid
import json
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from memory_core import MemoryBank, MemoryNode
# from rumor_engine import Rumor  # Commented to avoid circular import


class NPCProfile:
    """
    Comprehensive NPC profile with personality, beliefs, reputation, and memory integration.
    
    This class represents a complete NPC with dynamic personality traits that can evolve
    based on experiences, regional reputation that changes based on actions and rumors,
    and integration with the memory system for realistic behavior patterns.
    """
    
    # Personality trait weights for random generation
    TRAIT_WEIGHTS = {
        "stoic": 0.15,
        "vengeful": 0.10,
        "cautious": 0.20,
        "impulsive": 0.15,
        "generous": 0.12,
        "greedy": 0.08,
        "loyal": 0.18,
        "rebellious": 0.08,
        "scholarly": 0.10,
        "pragmatic": 0.16,
        "superstitious": 0.12,
        "cynical": 0.14,
        "optimistic": 0.16,
        "aggressive": 0.09,
        "diplomatic": 0.13,
        "secretive": 0.11,
        "gossipy": 0.14,
        "honest": 0.17,
        "cunning": 0.10,
        "compassionate": 0.15
    }
    
    # Personality archetypes with predefined trait combinations
    ARCHETYPES = {
        "pacifist": {
            "traits": ["compassionate", "diplomatic", "cautious", "honest"],
            "beliefs": {"violence": 0.0, "law": 0.8, "loyalty": 0.7, "religion": 0.6}
        },
        "zealot": {
            "traits": ["loyal", "aggressive", "superstitious", "stoic"],
            "beliefs": {"religion": 1.0, "violence": 0.7, "law": 0.9, "loyalty": 1.0}
        },
        "rebel": {
            "traits": ["rebellious", "impulsive", "cynical", "cunning"],
            "beliefs": {"law": 0.1, "violence": 0.6, "loyalty": 0.3, "religion": 0.2}
        },
        "opportunist": {
            "traits": ["greedy", "cunning", "pragmatic", "secretive"],
            "beliefs": {"law": 0.4, "violence": 0.5, "loyalty": 0.2, "religion": 0.3}
        },
        "scholar": {
            "traits": ["scholarly", "cautious", "honest", "diplomatic"],
            "beliefs": {"law": 0.7, "violence": 0.2, "loyalty": 0.6, "religion": 0.5}
        },
        "guardian": {
            "traits": ["loyal", "stoic", "aggressive", "honest"],
            "beliefs": {"law": 0.9, "violence": 0.8, "loyalty": 1.0, "religion": 0.6}
        },
        "merchant": {
            "traits": ["pragmatic", "diplomatic", "greedy", "cautious"],
            "beliefs": {"law": 0.8, "violence": 0.3, "loyalty": 0.5, "religion": 0.4}
        }
    }
    
    def __init__(self,
                 name: str,
                 age: int,
                 region: str,
                 npc_id: Optional[str] = None,
                 faction_affiliation: Optional[str] = None,
                 personality_traits: Optional[List[str]] = None,
                 belief_system: Optional[Dict[str, float]] = None,
                 social_circle: Optional[List[str]] = None,
                 reputation_local: Optional[Dict[str, float]] = None):
        """
        Initialize an NPC profile.
        
        Args:
            name: Display name of the NPC
            age: Age in years
            region: Primary region where NPC resides
            npc_id: Unique identifier (auto-generated if None)
            faction_affiliation: Optional faction membership
            personality_traits: List of personality trait tags
            belief_system: Dictionary of belief values (0.0 to 1.0)
            social_circle: List of other NPC IDs they interact with
            reputation_local: Regional reputation scores (-1.0 to 1.0)
        """
        self.npc_id = npc_id or str(uuid.uuid4())
        self.name = name
        self.age = age
        self.region = region
        self.faction_affiliation = faction_affiliation
        self.personality_traits = personality_traits or []
        self.belief_system = belief_system or self._default_beliefs()
        self.social_circle = social_circle or []
        self.reputation_local = reputation_local or {region: 0.0}
        
        # Initialize memory bank
        self.memory_bank = MemoryBank(self.npc_id)
        
        # Track trait evolution
        self.trait_evolution_history = []
        self.last_trait_update = datetime.now()
        
    def _default_beliefs(self) -> Dict[str, float]:
        """
        Generate default belief system values.
        
        Returns:
            Dictionary with baseline belief values
        """
        return {
            "loyalty": 0.5,
            "religion": 0.5,
            "law": 0.5,
            "violence": 0.5,
            "tradition": 0.5,
            "progress": 0.5,
            "authority": 0.5,
            "freedom": 0.5
        }
    
    @classmethod
    def generate_random(cls, 
                       name: str, 
                       region: str,
                       age_range: Tuple[int, int] = (18, 65),
                       num_traits: int = 4,
                       archetype: Optional[str] = None) -> 'NPCProfile':
        """
        Generate a randomized NPC profile.
        
        Args:
            name: Name for the NPC
            region: Primary region
            age_range: Tuple of (min_age, max_age)
            num_traits: Number of personality traits to assign
            archetype: Optional archetype to base generation on
            
        Returns:
            New NPCProfile instance
        """
        age = random.randint(age_range[0], age_range[1])
        
        if archetype and archetype in cls.ARCHETYPES:
            # Use archetype template
            template = cls.ARCHETYPES[archetype]
            traits = template["traits"].copy()
            beliefs = template["beliefs"].copy()
            
            # Add some random variation
            if len(traits) < num_traits:
                additional_traits = random.choices(
                    list(cls.TRAIT_WEIGHTS.keys()),
                    weights=list(cls.TRAIT_WEIGHTS.values()),
                    k=num_traits - len(traits)
                )
                traits.extend([t for t in additional_traits if t not in traits])
        else:
            # Fully random generation
            traits = random.choices(
                list(cls.TRAIT_WEIGHTS.keys()),
                weights=list(cls.TRAIT_WEIGHTS.values()),
                k=num_traits
            )
            traits = list(set(traits))  # Remove duplicates
            
            beliefs = {}
            for belief in ["loyalty", "religion", "law", "violence", "tradition", "progress", "authority", "freedom"]:
                beliefs[belief] = random.uniform(0.0, 1.0)
        
        # Random faction affiliation
        factions = ["merchants_guild", "city_guard", "temple_order", "thieves_guild", None, None, None]  # None more likely
        faction = random.choice(factions)
        
        return cls(
            name=name,
            age=age,
            region=region,
            faction_affiliation=faction,
            personality_traits=traits,
            belief_system=beliefs,
            reputation_local={region: random.uniform(-0.2, 0.2)}  # Start near neutral
        )
    
    def update_personality_from_memory(self, 
                                     memory_node: MemoryNode,
                                     trait_influence_strength: float = 0.1) -> List[str]:
        """
        Update personality traits based on a significant memory.
        
        Args:
            memory_node: Memory that might influence personality
            trait_influence_strength: How much the memory affects traits (0.0 to 1.0)
            
        Returns:
            List of personality changes made
        """
        changes = []
        
        # Analyze memory context tags for trait influences
        trait_influences = {
            "crime": {"vengeful": 0.2, "cynical": 0.15, "cautious": 0.1},
            "betrayal": {"vengeful": 0.3, "cynical": 0.25, "loyal": -0.2},
            "violence": {"aggressive": 0.2, "stoic": 0.1, "compassionate": -0.15},
            "kindness": {"compassionate": 0.2, "optimistic": 0.15, "cynical": -0.1},
            "injustice": {"rebellious": 0.25, "cynical": 0.2, "honest": 0.1},
            "corruption": {"cynical": 0.3, "rebellious": 0.2, "honest": 0.15},
            "sacrifice": {"loyal": 0.25, "compassionate": 0.2, "stoic": 0.15},
            "celebration": {"optimistic": 0.15, "generous": 0.1, "cynical": -0.1}
        }
        
        # Check memory strength - only strong memories cause personality changes
        if memory_node.strength < 0.7:
            return changes
            
        for tag in memory_node.context_tags:
            if tag in trait_influences:
                for trait, influence in trait_influences[tag].items():
                    adjusted_influence = influence * trait_influence_strength * memory_node.strength
                    
                    if adjusted_influence > 0:
                        # Increase likelihood of gaining trait
                        if trait not in self.personality_traits and random.random() < adjusted_influence:
                            self.personality_traits.append(trait)
                            changes.append(f"gained trait: {trait}")
                    else:
                        # Decrease likelihood of keeping trait
                        if trait in self.personality_traits and random.random() < abs(adjusted_influence):
                            self.personality_traits.remove(trait)
                            changes.append(f"lost trait: {trait}")
        
        # Update belief system based on memory
        belief_influences = {
            "crime": {"law": 0.1, "violence": 0.05},
            "justice": {"law": 0.15, "authority": 0.1},
            "corruption": {"law": -0.1, "authority": -0.15},
            "religious": {"religion": 0.2},
            "betrayal": {"loyalty": -0.2, "authority": -0.1}
        }
        
        for tag in memory_node.context_tags:
            if tag in belief_influences:
                for belief, influence in belief_influences[tag].items():
                    if belief in self.belief_system:
                        old_value = self.belief_system[belief]
                        adjustment = influence * trait_influence_strength * memory_node.strength
                        self.belief_system[belief] = max(0.0, min(1.0, old_value + adjustment))
                        
                        if abs(adjustment) > 0.05:
                            changes.append(f"belief {belief}: {old_value:.2f} -> {self.belief_system[belief]:.2f}")
        
        # Record trait evolution
        if changes:
            self.trait_evolution_history.append({
                'timestamp': datetime.now(),
                'memory_id': memory_node.event_id,
                'changes': changes
            })
            self.last_trait_update = datetime.now()
        
        return changes
    
    def update_reputation(self, 
                         region: str,
                         reputation_change: float,
                         reason: str,
                         is_rumor: bool = False) -> None:
        """
        Update regional reputation based on actions or rumors.
        
        Args:
            region: Region where reputation is affected
            reputation_change: Change in reputation (-1.0 to 1.0)
            reason: Description of what caused the change
            is_rumor: Whether this change is based on a rumor (less reliable)
        """
        # Initialize region if not present
        if region not in self.reputation_local:
            self.reputation_local[region] = 0.0
        
        # Apply rumor dampening
        if is_rumor:
            reputation_change *= 0.6  # Rumors have less impact
        
        # Apply personality-based modifiers
        if "diplomatic" in self.personality_traits:
            reputation_change *= 1.2 if reputation_change > 0 else 0.8
        if "secretive" in self.personality_traits:
            reputation_change *= 0.7  # Secretive NPCs' actions have less public impact
        
        # Update reputation
        old_rep = self.reputation_local[region]
        self.reputation_local[region] = max(-1.0, min(1.0, old_rep + reputation_change))
        
        # Create memory of reputation change if significant
        if abs(reputation_change) > 0.1:
            rep_memory = MemoryNode(
                description=f"reputation in {region} changed due to: {reason}",
                location=(0.0, 0.0),  # Abstract location for reputation events
                actor_ids=[self.npc_id],
                context_tags=["reputation", "social", region],
                initial_strength=min(1.0, abs(reputation_change) * 2)
            )
            self.memory_bank.add_memory(rep_memory)
    
    def get_reputation_descriptor(self, region: str) -> str:
        """
        Get a text description of reputation in a region.
        
        Args:
            region: Region to check reputation for
            
        Returns:
            Text description of reputation level
        """
        if region not in self.reputation_local:
            return "unknown"
        
        rep = self.reputation_local[region]
        if rep >= 0.8:
            return "beloved"
        elif rep >= 0.5:
            return "respected"
        elif rep >= 0.2:
            return "liked"
        elif rep >= -0.2:
            return "neutral"
        elif rep >= -0.5:
            return "disliked"
        elif rep >= -0.8:
            return "despised"
        else:
            return "reviled"
    
    def get_personality_summary(self) -> str:
        """
        Generate a readable summary of the NPC's personality.
        
        Returns:
            String describing the NPC's personality
        """
        if not self.personality_traits:
            return "unremarkable"
        
        # Group traits by category for better readability
        positive_traits = [t for t in self.personality_traits if t in 
                          ["generous", "loyal", "honest", "compassionate", "diplomatic", "optimistic"]]
        negative_traits = [t for t in self.personality_traits if t in 
                          ["vengeful", "greedy", "cynical", "aggressive", "rebellious", "secretive"]]
        neutral_traits = [t for t in self.personality_traits if t not in positive_traits + negative_traits]
        
        parts = []
        if positive_traits:
            parts.append(f"positive: {', '.join(positive_traits)}")
        if negative_traits:
            parts.append(f"challenging: {', '.join(negative_traits)}")
        if neutral_traits:
            parts.append(f"traits: {', '.join(neutral_traits)}")
        
        return "; ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the NPC profile to a dictionary.
        
        Returns:
            Dictionary representation of the profile
        """
        return {
            'npc_id': self.npc_id,
            'name': self.name,
            'age': self.age,
            'region': self.region,
            'faction_affiliation': self.faction_affiliation,
            'personality_traits': self.personality_traits,
            'belief_system': self.belief_system,
            'social_circle': self.social_circle,
            'reputation_local': self.reputation_local,
            'trait_evolution_history': [
                {
                    'timestamp': entry['timestamp'].isoformat(),
                    'memory_id': entry['memory_id'],
                    'changes': entry['changes']
                } for entry in self.trait_evolution_history
            ],
            'last_trait_update': self.last_trait_update.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NPCProfile':
        """
        Deserialize an NPC profile from a dictionary.
        
        Args:
            data: Dictionary containing profile data
            
        Returns:
            NPCProfile instance
        """
        profile = cls(
            npc_id=data['npc_id'],
            name=data['name'],
            age=data['age'],
            region=data['region'],
            faction_affiliation=data.get('faction_affiliation'),
            personality_traits=data.get('personality_traits', []),
            belief_system=data.get('belief_system', {}),
            social_circle=data.get('social_circle', []),
            reputation_local=data.get('reputation_local', {})
        )
        
        # Restore trait evolution history
        if 'trait_evolution_history' in data:
            profile.trait_evolution_history = [
                {
                    'timestamp': datetime.fromisoformat(entry['timestamp']),
                    'memory_id': entry['memory_id'],
                    'changes': entry['changes']
                } for entry in data['trait_evolution_history']
            ]
        
        if 'last_trait_update' in data:
            profile.last_trait_update = datetime.fromisoformat(data['last_trait_update'])
        
        return profile
    
    def to_json(self) -> str:
        """
        Serialize the NPC profile to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'NPCProfile':
        """
        Deserialize an NPC profile from JSON string.
        
        Args:
            json_str: JSON string containing profile data
            
        Returns:
            NPCProfile instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def compatibility_score(self, other: 'NPCProfile') -> float:
        """
        Calculate compatibility score with another NPC (0.0 to 1.0).
        
        Args:
            other: Another NPCProfile to compare with
            
        Returns:
            Compatibility score
        """
        score = 0.0
        factors = 0
        
        # Personality trait compatibility
        common_traits = set(self.personality_traits).intersection(set(other.personality_traits))
        conflicting_pairs = [
            ("generous", "greedy"), ("loyal", "rebellious"), ("honest", "cunning"),
            ("optimistic", "cynical"), ("diplomatic", "aggressive")
        ]
        
        conflicts = 0
        for trait1, trait2 in conflicting_pairs:
            if (trait1 in self.personality_traits and trait2 in other.personality_traits) or \
               (trait2 in self.personality_traits and trait1 in other.personality_traits):
                conflicts += 1
        
        trait_score = (len(common_traits) * 0.2) - (conflicts * 0.3)
        score += max(0.0, min(1.0, 0.5 + trait_score))
        factors += 1
        
        # Belief system compatibility
        belief_diff = 0.0
        common_beliefs = set(self.belief_system.keys()).intersection(set(other.belief_system.keys()))
        for belief in common_beliefs:
            belief_diff += abs(self.belief_system[belief] - other.belief_system[belief])
        
        if common_beliefs:
            belief_score = 1.0 - (belief_diff / len(common_beliefs))
            score += belief_score
            factors += 1
        
        # Faction compatibility
        if self.faction_affiliation and other.faction_affiliation:
            if self.faction_affiliation == other.faction_affiliation:
                score += 0.8
            else:
                # Some factions are inherently opposed
                opposed_factions = [
                    ("city_guard", "thieves_guild"),
                    ("temple_order", "thieves_guild")
                ]
                is_opposed = any(
                    (self.faction_affiliation in pair and other.faction_affiliation in pair)
                    for pair in opposed_factions
                )
                score += 0.2 if not is_opposed else 0.0
            factors += 1
        
        return score / max(1, factors)


# Test harness
if __name__ == "__main__":
    print("=== NPC Profile Test Harness ===\n")
    
    # Test 1: Create random NPCs with different archetypes
    print("1. Creating NPCs with different archetypes...")
    
    npcs = []
    archetypes = ["pacifist", "zealot", "rebel", "opportunist", "scholar"]
    
    for i, archetype in enumerate(archetypes):
        npc = NPCProfile.generate_random(
            name=f"{archetype.title()} {chr(65+i)}",
            region="Westford",
            archetype=archetype
        )
        npcs.append(npc)
        print(f"  {npc.name}: {npc.get_personality_summary()}")
        print(f"    Beliefs - Law: {npc.belief_system['law']:.2f}, Violence: {npc.belief_system['violence']:.2f}")
    
    # Test 2: Memory-based personality evolution
    print("\n2. Testing personality evolution from memories...")
    
    test_npc = npcs[0]  # Use the pacifist
    print(f"Initial {test_npc.name} traits: {test_npc.personality_traits}")
    
    # Create a traumatic memory that might change personality
    betrayal_memory = MemoryNode(
        description="was betrayed by a trusted friend who stole my life savings",
        location=(15.0, 20.0),
        actor_ids=["former_friend_bob", test_npc.npc_id],
        context_tags=["betrayal", "crime", "theft", "emotional_trauma"],
        initial_strength=0.9
    )
    
    test_npc.memory_bank.add_memory(betrayal_memory)
    changes = test_npc.update_personality_from_memory(betrayal_memory, trait_influence_strength=0.3)
    
    print(f"Memory added: {betrayal_memory.description}")
    print(f"Personality changes: {changes}")
    print(f"Updated traits: {test_npc.personality_traits}")
    
    # Test 3: Reputation system
    print("\n3. Testing reputation system...")
    
    merchant_npc = npcs[3]  # Use the opportunist
    print(f"{merchant_npc.name} initial reputation in Westford: {merchant_npc.get_reputation_descriptor('Westford')}")
    
    # Simulate some reputation-affecting events
    merchant_npc.update_reputation("Westford", 0.3, "helped during plague outbreak", is_rumor=False)
    merchant_npc.update_reputation("Eastdale", -0.4, "accused of price gouging", is_rumor=True)
    merchant_npc.update_reputation("Westford", -0.1, "rumored to have cheated customers", is_rumor=True)
    
    print(f"After events:")
    print(f"  Westford: {merchant_npc.get_reputation_descriptor('Westford')} ({merchant_npc.reputation_local['Westford']:.2f})")
    print(f"  Eastdale: {merchant_npc.get_reputation_descriptor('Eastdale')} ({merchant_npc.reputation_local['Eastdale']:.2f})")
    
    # Test 4: Compatibility scoring
    print("\n4. Testing NPC compatibility...")
    
    for i in range(len(npcs)):
        for j in range(i+1, len(npcs)):
            compatibility = npcs[i].compatibility_score(npcs[j])
            print(f"  {npcs[i].name} & {npcs[j].name}: {compatibility:.2f}")
    
    # Test 5: Serialization
    print("\n5. Testing JSON serialization...")
    
    # Serialize to JSON
    json_data = test_npc.to_json()
    print(f"Serialized {test_npc.name} to JSON ({len(json_data)} characters)")
    
    # Deserialize from JSON
    restored_npc = NPCProfile.from_json(json_data)
    print(f"Restored NPC: {restored_npc.name}, traits: {restored_npc.personality_traits}")
    print(f"Evolution history entries: {len(restored_npc.trait_evolution_history)}")
    
    # Test 6: Social connections and reputation propagation
    print("\n6. Setting up social network...")
    
    # Create social connections
    for i, npc in enumerate(npcs):
        # Each NPC knows 2-3 others
        potential_connections = [other.npc_id for j, other in enumerate(npcs) if i != j]
        num_connections = random.randint(2, min(3, len(potential_connections)))
        npc.social_circle = random.sample(potential_connections, num_connections)
        
        connection_names = [npcs[j].name for j, other in enumerate(npcs) 
                          if other.npc_id in npc.social_circle]
        print(f"  {npc.name} knows: {', '.join(connection_names)}")
    
    print("\n=== Test Complete ===") 