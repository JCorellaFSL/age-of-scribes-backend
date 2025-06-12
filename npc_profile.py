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
        
        # Guild membership attributes
        self.guild_membership: Optional[str] = None  # ID of local guild chapter or None
        self.guild_rank: Optional[str] = None        # e.g., "apprentice", "journeyman", "master", "guildmaster"
        self.guild_loyalty_score: float = 0.0        # -1.0 (disloyal) to 1.0 (devoted)
        self.guild_history: List[Dict[str, Any]] = []  # historical record of guild involvement
        
        # Initialize memory bank
        self.memory_bank = MemoryBank(self.npc_id)
        
        # Track trait evolution
        self.trait_evolution_history = []
        self.last_trait_update = datetime.now()
        
        # Motivational weights for internal decision scoring
        self.motivational_weights = {
            "survival": 0.8,
            "wealth": 0.6,
            "duty": 0.5,
            "freedom": 0.4,
            "knowledge": 0.3
        }

        # Relationships: trust map to other NPCs (-1.0 to 1.0)
        self.relationships: Dict[str, float] = {}

        # High-level ambition scaffold
        self.goals: List[str] = []
        
        # Family and life tracking attributes
        self.birth_day: Optional[int] = None  # Day of birth in simulation
        self.parent_ids: List[str] = []  # IDs of parent NPCs
        self.cause_of_death: Optional[str] = None  # Cause if deceased
        self.death_day: Optional[int] = None  # Day of death in simulation
        self.is_active: bool = True  # False if deceased
        
        # Relationship attributes for family engine
        self.gender: Optional[str] = None  # "male" or "female"
        self.social_class: Optional[str] = None  # Social class identifier
        self.character_id: str = self.npc_id  # Alias for family engine compatibility
        self.relationship_status: str = "single"  # "single", "courting", "married", "div.single", "div.courting"
        self.partner_id: Optional[str] = None  # ID of current partner/spouse
        
        # Guild and profession attributes
        self.guild_id: Optional[str] = None  # ID of the guild this NPC belongs to
        self.sub_guild: Optional[str] = None  # Sub-guild within the main guild
        self.job_class: Optional[str] = None  # Specific job class/profession
        self.guild_rank: Optional[str] = None  # "apprentice", "journeyman", "master"
        
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
                       archetype: Optional[str] = None,
                       surname: Optional[str] = None,
                       parent_ids: Optional[List[str]] = None,
                       gender: Optional[str] = None,
                       social_class: Optional[str] = None,
                       assign_guild: bool = True) -> 'NPCProfile':
        """
        Generate a randomized NPC profile.
        
        Args:
            name: Name for the NPC (will be combined with surname if provided)
            region: Primary region
            age_range: Tuple of (min_age, max_age)
            num_traits: Number of personality traits to assign
            archetype: Optional archetype to base generation on
            surname: Optional surname to append to name
            parent_ids: Optional list of parent NPC IDs
            gender: Optional gender ("male" or "female")
            social_class: Optional social class identifier
            assign_guild: Whether to assign guild membership and job class
            
        Returns:
            New NPCProfile instance
        """
        age = random.randint(age_range[0], age_range[1])
        
        # Handle name with optional surname
        full_name = name
        if surname:
            if ' ' in name:
                # Name already has spaces, replace last part with surname
                name_parts = name.split()
                full_name = ' '.join(name_parts[:-1] + [surname])
            else:
                # Simple first name, add surname
                full_name = f"{name} {surname}"
        
        # Generate random gender if not provided
        npc_gender = gender or random.choice(["male", "female"])
        
        # Generate random social class if not provided
        social_classes = ["peasant", "merchant", "noble", "artisan", "clergy"]
        npc_social_class = social_class or random.choice(social_classes)
        
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
        
        # Create the NPC instance
        npc = cls(
            name=full_name,
            age=age,
            region=region,
            faction_affiliation=faction,
            personality_traits=traits,
            belief_system=beliefs,
            reputation_local={region: random.uniform(-0.2, 0.2)}  # Start near neutral
        )
        
        # Set the additional attributes
        npc.gender = npc_gender
        npc.social_class = npc_social_class
        if parent_ids:
            npc.parent_ids = parent_ids.copy()
        
        # Assign guild membership and job class if requested
        if assign_guild and npc.age >= 10:  # Only assign guilds to those old enough
            npc._assign_guild_membership()
            
        return npc
    
    def _assign_guild_membership(self) -> None:
        """
        Assign guild membership, sub-guild, job class, and rank to this NPC.
        
        Uses the GuildRegistry to randomly select appropriate guild assignments
        based on the NPC's age and characteristics.
        """
        try:
            from guild_registry import GuildRegistry
        except ImportError:
            # If guild_registry is not available, skip guild assignment
            return
        
        registry = GuildRegistry()
        
        # Skip guild assignment for certain social classes or archetypes
        if (hasattr(self, 'social_class') and self.social_class in ['noble', 'clergy']) or \
           (hasattr(self, 'archetype') and self.archetype in ['noble', 'clergy', 'royalty']):
            return
        
        # Get all guilds that allow NPC membership
        available_guilds = registry.get_guilds_for_npc_membership()
        
        if not available_guilds:
            return
        
        # Random chance to not have a guild (some NPCs are unemployed/independent)
        if random.random() < 0.3:  # 30% chance of no guild
            return
        
        # Randomly select a guild
        guild_id = random.choice(list(available_guilds.keys()))
        guild = available_guilds[guild_id]
        
        # Randomly select a sub-guild
        sub_guild_name = random.choice(list(guild.sub_guilds.keys()))
        
        # Randomly select a job class from the sub-guild
        job_classes = guild.sub_guilds[sub_guild_name]
        job_class = random.choice(job_classes)
        
        # Assign rank based on age
        if self.age < 10:
            rank = None  # Too young
        elif self.age <= 17:
            rank = "apprentice"
        elif self.age <= 29:
            rank = "journeyman"
        else:
            rank = "master"
        
        # Set the guild attributes
        self.guild_id = guild_id
        self.sub_guild = sub_guild_name
        self.job_class = job_class
        self.guild_rank = rank
    
    def assign_profession(self, guild_id: str, sub_guild: str, job_class: str, 
                         guild_rank: Optional[str] = None) -> None:
        """
        Manually assign a profession to this NPC.
        
        Args:
            guild_id: ID of the guild
            sub_guild: Name of the sub-guild
            job_class: Specific job class
            guild_rank: Optional rank ("apprentice", "journeyman", "master")
        """
        self.guild_id = guild_id
        self.sub_guild = sub_guild
        self.job_class = job_class
        
        # Auto-assign rank based on age if not provided
        if guild_rank is None:
            if self.age < 10:
                self.guild_rank = None
            elif self.age <= 17:
                self.guild_rank = "apprentice"
            elif self.age <= 29:
                self.guild_rank = "journeyman"
            else:
                self.guild_rank = "master"
        else:
            self.guild_rank = guild_rank
    
    def clear_profession(self) -> None:
        """Remove all profession/guild assignments from this NPC."""
        self.guild_id = None
        self.sub_guild = None
        self.job_class = None
        self.guild_rank = None
    
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
            'guild_membership': self.guild_membership,
            'guild_rank': self.guild_rank,
            'guild_loyalty_score': self.guild_loyalty_score,
            'guild_history': self.guild_history,
            'trait_evolution_history': [
                {
                    'timestamp': entry['timestamp'].isoformat(),
                    'memory_id': entry['memory_id'],
                    'changes': entry['changes']
                } for entry in self.trait_evolution_history
            ],
            'last_trait_update': self.last_trait_update.isoformat(),
            'motivational_weights': self.motivational_weights,
            'relationships': self.relationships,
            'goals': self.goals,
            # Family and life tracking attributes
            'birth_day': self.birth_day,
            'parent_ids': self.parent_ids,
            'cause_of_death': self.cause_of_death,
            'death_day': self.death_day,
            'is_active': self.is_active,
            # Relationship attributes
            'gender': self.gender,
            'social_class': self.social_class,
            'character_id': self.character_id,
            'relationship_status': self.relationship_status,
            'partner_id': self.partner_id,
            # Guild and profession attributes
            'guild_id': self.guild_id,
            'sub_guild': self.sub_guild,
            'job_class': self.job_class,
            'guild_rank': self.guild_rank
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
        
        # Restore guild attributes
        profile.guild_membership = data.get('guild_membership')
        profile.guild_rank = data.get('guild_rank')
        profile.guild_loyalty_score = data.get('guild_loyalty_score', 0.0)
        profile.guild_history = data.get('guild_history', [])
        
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
        
        # Restore simulation elements (with defaults for backward compatibility)
        profile.motivational_weights = data.get('motivational_weights', {
            "survival": 0.8,
            "wealth": 0.6,
            "duty": 0.5,
            "freedom": 0.4,
            "knowledge": 0.3
        })
        profile.relationships = data.get('relationships', {})
        profile.goals = data.get('goals', [])
        
        # Restore family and life tracking attributes (with defaults for backward compatibility)
        profile.birth_day = data.get('birth_day')
        profile.parent_ids = data.get('parent_ids', [])
        profile.cause_of_death = data.get('cause_of_death')
        profile.death_day = data.get('death_day')
        profile.is_active = data.get('is_active', True)
        
        # Restore relationship attributes (with defaults for backward compatibility)
        profile.gender = data.get('gender')
        profile.social_class = data.get('social_class')
        profile.character_id = data.get('character_id', profile.npc_id)
        profile.relationship_status = data.get('relationship_status', 'single')
        profile.partner_id = data.get('partner_id')
        
        # Restore guild and profession attributes (with defaults for backward compatibility)
        profile.guild_id = data.get('guild_id')
        profile.sub_guild = data.get('sub_guild')
        profile.job_class = data.get('job_class')
        profile.guild_rank = data.get('guild_rank')
        
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
    
    def add_relationship(self, npc_id: str, trust_level: float) -> None:
        """
        Add or update a relationship with another NPC.
        
        Args:
            npc_id: The ID of the other NPC
            trust_level: Trust level from -1.0 (distrust) to 1.0 (trust)
        """
        self.relationships[npc_id] = max(-1.0, min(1.0, trust_level))
    
    def adjust_relationship(self, npc_id: str, trust_change: float) -> None:
        """
        Adjust an existing relationship.
        
        Args:
            npc_id: The ID of the other NPC
            trust_change: Amount to change trust level by
        """
        current_trust = self.relationships.get(npc_id, 0.0)
        self.relationships[npc_id] = max(-1.0, min(1.0, current_trust + trust_change))
    
    def get_relationship_strength(self, npc_id: str) -> str:
        """
        Get descriptive relationship strength.
        
        Args:
            npc_id: The ID of the other NPC
            
        Returns:
            Descriptive string of relationship strength
        """
        trust = self.relationships.get(npc_id, 0.0)
        
        if trust >= 0.7:
            return "close ally"
        elif trust >= 0.3:
            return "trusted friend"
        elif trust >= 0.1:
            return "acquaintance"
        elif trust >= -0.1:
            return "neutral"
        elif trust >= -0.3:
            return "disliked"
        elif trust >= -0.7:
            return "distrusted"
        else:
            return "enemy"
    
    def add_goal(self, goal: str) -> None:
        """
        Add a new goal to the NPC's ambitions.
        
        Args:
            goal: Description of the goal
        """
        if goal not in self.goals:
            self.goals.append(goal)
    
    def remove_goal(self, goal: str) -> bool:
        """
        Remove a goal from the NPC's ambitions.
        
        Args:
            goal: Description of the goal to remove
            
        Returns:
            True if goal was removed, False if not found
        """
        if goal in self.goals:
            self.goals.remove(goal)
            return True
        return False
    
    def adjust_motivation(self, motivation_type: str, adjustment: float) -> None:
        """
        Adjust a motivational weight.
        
        Args:
            motivation_type: Type of motivation to adjust
            adjustment: Amount to adjust by (can be negative)
        """
        if motivation_type in self.motivational_weights:
            current_weight = self.motivational_weights[motivation_type]
            self.motivational_weights[motivation_type] = max(0.0, min(1.0, current_weight + adjustment))
    
    def get_primary_motivation(self) -> str:
        """
        Get the NPC's strongest motivation.
        
        Returns:
            The motivation type with the highest weight
        """
        return max(self.motivational_weights.items(), key=lambda x: x[1])[0]
    
    def get_profession_summary(self) -> str:
        """
        Generate a readable summary of the NPC's profession and guild membership.
        
        Returns:
            String describing the NPC's professional status
        """
        if not self.guild_id:
            return "unemployed/independent"
        
        # Build profession description
        parts = []
        
        if self.guild_rank:
            parts.append(self.guild_rank)
        
        if self.job_class:
            parts.append(self.job_class)
        elif self.sub_guild:
            parts.append(f"{self.sub_guild.lower()} worker")
        
        if self.guild_id:
            # Clean up guild name for display
            guild_name = self.guild_id.replace('_', ' ').title()
            if not guild_name.endswith('Guild'):
                guild_name += " Guild"
            parts.append(f"of the {guild_name}")
        
        return " ".join(parts) if parts else "guild member"
    
    def get_simulation_summary(self) -> str:
        """
        Get a summary of simulation-relevant attributes.
        
        Returns:
            Formatted string with key simulation data
        """
        primary_motivation = self.get_primary_motivation()
        relationship_count = len(self.relationships)
        goal_count = len(self.goals)
        
        summary = f"=== {self.name} Simulation Profile ===\n"
        summary += f"Age: {self.age} | Profession: {self.get_profession_summary()}\n"
        summary += f"Primary Motivation: {primary_motivation} ({self.motivational_weights[primary_motivation]:.2f})\n"
        summary += f"Relationships: {relationship_count} NPCs\n"
        summary += f"Active Goals: {goal_count}\n"
        
        if self.relationships:
            summary += "\nKey Relationships:\n"
            for npc_id, trust in sorted(self.relationships.items(), key=lambda x: abs(x[1]), reverse=True)[:3]:
                strength = self.get_relationship_strength(npc_id)
                summary += f"  {npc_id}: {strength} ({trust:+.2f})\n"
        
        if self.goals:
            summary += "\nCurrent Goals:\n"
            for goal in self.goals[:3]:  # Show top 3 goals
                summary += f"  - {goal}\n"
        
        return summary


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