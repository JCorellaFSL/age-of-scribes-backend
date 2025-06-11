import uuid
import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any, Set
from memory_core import MemoryNode, MemoryBank


class Rumor:
    """
    Represents a single rumor with metadata and spreading/decay functionality.
    
    A Rumor contains information that spreads between NPCs, potentially mutating
    and losing credibility over time as it propagates through the network.
    """
    
    def __init__(self,
                 content: str,
                 originator_id: str,
                 location_origin: Tuple[float, float],
                 source_memory: Optional[MemoryNode] = None,
                 rumor_id: Optional[str] = None,
                 confidence_level: float = 1.0,
                 decay_rate: float = 0.05,
                 timestamp_created: Optional[datetime] = None):
        """
        Initialize a new rumor.
        
        Args:
            content: Brief summary of the rumor
            originator_id: NPC or player ID who started the rumor
            location_origin: Tuple of (x, y) coordinates where rumor originated
            source_memory: Optional reference to the MemoryNode that spawned this rumor
            rumor_id: Unique identifier for the rumor (auto-generated if None)
            confidence_level: Initial confidence level (0.0 to 1.0)
            decay_rate: Rate at which confidence decays over time
            timestamp_created: When the rumor was created (current time if None)
        """
        self.rumor_id = rumor_id or str(uuid.uuid4())
        self.source_memory = source_memory
        self.originator_id = originator_id
        self.content = content
        self.location_origin = location_origin
        self.confidence_level = max(0.0, min(1.0, confidence_level))
        self.spread_count = 0
        self.timestamp_created = timestamp_created or datetime.now()
        self.decay_rate = decay_rate
        self.heard_by: Set[str] = {originator_id}
        self.original_content = content
        
    def spread(self, spreader_id: str, target_id: str, 
               mutation_chance: float = 0.3) -> 'Rumor':
        """
        Create a new version of this rumor as it spreads to another NPC.
        
        Args:
            spreader_id: ID of the NPC spreading the rumor
            target_id: ID of the NPC receiving the rumor
            mutation_chance: Probability of content mutation during spread
            
        Returns:
            New Rumor instance representing the spread version
        """
        new_content = self.content
        new_confidence = self.confidence_level
        
        # Simulate content mutation during spread
        if random.random() < mutation_chance:
            new_content = self._mutate_content(new_content)
            new_confidence *= 0.9  # Reduce confidence due to mutation
            
        # Create new rumor instance
        spread_rumor = Rumor(
            content=new_content,
            originator_id=self.originator_id,
            location_origin=self.location_origin,
            source_memory=self.source_memory,
            confidence_level=new_confidence,
            decay_rate=self.decay_rate,
            timestamp_created=self.timestamp_created
        )
        
        spread_rumor.spread_count = self.spread_count + 1
        spread_rumor.heard_by = self.heard_by.copy()
        spread_rumor.heard_by.add(target_id)
        
        return spread_rumor
        
    def _mutate_content(self, content: str) -> str:
        """
        Apply simple mutations to rumor content to simulate misrepresentation.
        
        Args:
            content: Original content to mutate
            
        Returns:
            Mutated content string
        """
        # Simple mutation strategies
        mutations = [
            lambda s: s.replace("saw", "heard"),
            lambda s: s.replace("heard", "saw"),
            lambda s: s.replace("might", "definitely"),
            lambda s: s.replace("someone", "everyone"),
            lambda s: s.replace("small", "large"),
            lambda s: s.replace("few", "many"),
            lambda s: s.replace("whispered", "shouted"),
            lambda s: s.replace("maybe", "certainly"),
        ]
        
        # Apply a random mutation
        if mutations:
            mutation = random.choice(mutations)
            return mutation(content)
        
        return content
        
    def decay(self, time_passed_hours: Optional[float] = None) -> None:
        """
        Apply decay to the rumor's confidence level over time.
        
        Args:
            time_passed_hours: Hours since last decay (auto-calculated if None)
        """
        if time_passed_hours is None:
            time_delta = datetime.now() - self.timestamp_created
            time_passed_hours = time_delta.total_seconds() / 3600.0
            
        # Apply exponential decay to confidence
        decay_factor = math.exp(-self.decay_rate * time_passed_hours)
        self.confidence_level *= decay_factor
        
        # Ensure confidence doesn't go below 0
        self.confidence_level = max(0.0, self.confidence_level)
        
    def transform(self, context_tags: Optional[List[str]] = None,
                  environmental_factor: Optional[str] = None) -> None:
        """
        Transform rumor content based on environmental context or goals.
        
        Args:
            context_tags: Tags that might influence the rumor transformation
            environmental_factor: Environmental context (e.g., "tension", "celebration")
        """
        if not context_tags and not environmental_factor:
            return
            
        # Transform based on environmental factors
        if environmental_factor == "tension":
            # Make rumors more dramatic during tense times
            self.content = self.content.replace("argument", "violent fight")
            self.content = self.content.replace("disagreement", "heated argument")
            
        elif environmental_factor == "celebration":
            # Make rumors more positive during celebrations
            self.content = self.content.replace("stole", "generously gave")
            self.content = self.content.replace("conflict", "friendly competition")
            
        # Transform based on context tags
        if context_tags:
            if "crime" in context_tags:
                # Crime rumors become more serious
                self.content = self.content.replace("took", "stole")
                self.content = self.content.replace("left", "fled")
                
            elif "romance" in context_tags:
                # Romance rumors become more scandalous
                self.content = self.content.replace("talked to", "was seen with")
                self.content = self.content.replace("met", "secretly met")
            
    def is_expired(self, min_confidence: float = 0.05) -> bool:
        """
        Check if the rumor has decayed below the minimum confidence threshold.
        
        Args:
            min_confidence: Minimum confidence level to consider valid
            
        Returns:
            True if the rumor should be considered expired
        """
        return self.confidence_level < min_confidence
        
    def get_age_hours(self) -> float:
        """
        Get the age of the rumor in hours.
        
        Returns:
            Age in hours since creation
        """
        time_delta = datetime.now() - self.timestamp_created
        return time_delta.total_seconds() / 3600.0


class RumorNetwork:
    """
    Manages the spread and lifecycle of rumors across a network of NPCs.
    
    The RumorNetwork handles rumor propagation, decay, and cleanup across
    multiple NPCs with consideration for social connections and geography.
    """
    
    def __init__(self, max_rumors: int = 500):
        """
        Initialize a new rumor network.
        
        Args:
            max_rumors: Maximum number of rumors to track simultaneously
        """
        self.max_rumors = max_rumors
        self.active_rumors: List[Rumor] = []
        self.npc_memory_banks: Dict[str, MemoryBank] = {}
        self.last_tick_time = datetime.now()
        
    def register_npc(self, npc_id: str, memory_bank: MemoryBank) -> None:
        """
        Register an NPC with their memory bank to the network.
        
        Args:
            npc_id: Unique identifier for the NPC
            memory_bank: The NPC's MemoryBank instance
        """
        self.npc_memory_banks[npc_id] = memory_bank
        
    def seed_rumor_from_memory(self, npc_id: str, memory_node: MemoryNode,
                               rumor_threshold: float = 0.7) -> Optional[Rumor]:
        """
        Create a rumor from a memory if it meets the threshold for interestingness.
        
        Args:
            npc_id: ID of the NPC whose memory is spawning the rumor
            memory_node: The memory to potentially turn into a rumor
            rumor_threshold: Minimum memory strength to spawn a rumor
            
        Returns:
            New Rumor instance if created, None otherwise
        """
        if memory_node.strength < rumor_threshold:
            return None
            
        # Create rumor content based on memory
        rumor_content = f"I heard that {memory_node.description}"
        
        # Adjust confidence based on memory strength and context
        confidence = memory_node.strength
        if "witnessed" in memory_node.context_tags:
            confidence *= 1.2  # Boost for firsthand accounts
        elif "rumor" in memory_node.context_tags:
            confidence *= 0.8  # Reduce for secondhand info
            
        rumor = Rumor(
            content=rumor_content,
            originator_id=npc_id,
            location_origin=memory_node.location,
            source_memory=memory_node,
            confidence_level=min(1.0, confidence)
        )
        
        self.active_rumors.append(rumor)
        self._cleanup_old_rumors()
        
        return rumor
        
    def daily_tick(self, npc_locations: Dict[str, Tuple[float, float]],
                   social_connections: Dict[str, List[str]],
                   spread_radius: float = 50.0,
                   spread_probability: float = 0.3) -> Dict[str, Any]:
        """
        Simulate a daily tick of rumor spreading, decay, and cleanup.
        
        Args:
            npc_locations: Dictionary mapping NPC IDs to their current locations
            social_connections: Dictionary mapping NPC IDs to lists of connected NPCs
            spread_radius: Maximum distance for rumor spreading
            spread_probability: Base probability of spreading a rumor
            
        Returns:
            Dictionary with statistics about the tick
        """
        current_time = datetime.now()
        time_delta = current_time - self.last_tick_time
        hours_passed = time_delta.total_seconds() / 3600.0
        
        stats = {
            'rumors_spread': 0,
            'rumors_decayed': 0,
            'rumors_expired': 0,
            'new_rumors_created': 0
        }
        
        # Apply decay to all active rumors
        for rumor in self.active_rumors:
            old_confidence = rumor.confidence_level
            rumor.decay(hours_passed)
            if rumor.confidence_level < old_confidence:
                stats['rumors_decayed'] += 1
                
        # Attempt to spread rumors between connected NPCs
        new_rumors = []
        for rumor in self.active_rumors[:]:  # Copy list to avoid modification issues
            if rumor.is_expired():
                continue
                
            # Find potential spreaders (NPCs who have heard this rumor)
            potential_spreaders = [npc_id for npc_id in rumor.heard_by 
                                 if npc_id in npc_locations]
            
            for spreader_id in potential_spreaders:
                if random.random() > spread_probability:
                    continue
                    
                # Find nearby NPCs or social connections
                targets = self._find_spread_targets(
                    spreader_id, npc_locations, social_connections, 
                    spread_radius, rumor.heard_by
                )
                
                # Spread to a random target
                if targets:
                    target_id = random.choice(targets)
                    spread_rumor = rumor.spread(spreader_id, target_id)
                    new_rumors.append(spread_rumor)
                    stats['rumors_spread'] += 1
                    
        # Add new rumors from spreading
        self.active_rumors.extend(new_rumors)
        
        # Generate new rumors from NPC memories
        for npc_id, memory_bank in self.npc_memory_banks.items():
            if random.random() < 0.1:  # 10% chance per NPC per day
                strongest_memories = memory_bank.get_strongest_memories(3)
                for memory in strongest_memories:
                    if random.random() < 0.3:  # 30% chance per strong memory
                        new_rumor = self.seed_rumor_from_memory(npc_id, memory)
                        if new_rumor:
                            stats['new_rumors_created'] += 1
                            
        # Clean up expired rumors
        initial_count = len(self.active_rumors)
        self._cleanup_old_rumors()
        stats['rumors_expired'] = initial_count - len(self.active_rumors)
        
        self.last_tick_time = current_time
        return stats
        
    def _find_spread_targets(self, spreader_id: str, 
                           npc_locations: Dict[str, Tuple[float, float]],
                           social_connections: Dict[str, List[str]],
                           spread_radius: float,
                           already_heard: Set[str]) -> List[str]:
        """
        Find potential targets for rumor spreading based on proximity and social connections.
        
        Args:
            spreader_id: ID of the NPC spreading the rumor
            npc_locations: Dictionary of NPC locations
            social_connections: Dictionary of social connections
            spread_radius: Maximum distance for spreading
            already_heard: Set of NPC IDs who have already heard this rumor
            
        Returns:
            List of potential target NPC IDs
        """
        targets = []
        spreader_location = npc_locations.get(spreader_id)
        
        if not spreader_location:
            return targets
            
        # Check social connections first
        if spreader_id in social_connections:
            for connected_npc in social_connections[spreader_id]:
                if connected_npc not in already_heard and connected_npc in npc_locations:
                    targets.append(connected_npc)
                    
        # Check nearby NPCs within spread radius
        for npc_id, location in npc_locations.items():
            if npc_id == spreader_id or npc_id in already_heard:
                continue
                
            distance = math.sqrt(
                (location[0] - spreader_location[0]) ** 2 +
                (location[1] - spreader_location[1]) ** 2
            )
            
            if distance <= spread_radius:
                targets.append(npc_id)
                
        return targets
        
    def _cleanup_old_rumors(self) -> None:
        """
        Remove expired rumors and enforce maximum rumor limit.
        """
        # Remove expired rumors
        self.active_rumors = [r for r in self.active_rumors if not r.is_expired()]
        
        # Enforce maximum rumor limit by removing oldest
        if len(self.active_rumors) > self.max_rumors:
            self.active_rumors.sort(key=lambda r: r.timestamp_created)
            self.active_rumors = self.active_rumors[-self.max_rumors:]
            
    def get_rumors_by_topic(self, keywords: List[str]) -> List[Rumor]:
        """
        Retrieve rumors that contain any of the specified keywords.
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            List of matching rumors
        """
        matching_rumors = []
        for rumor in self.active_rumors:
            if any(keyword.lower() in rumor.content.lower() for keyword in keywords):
                matching_rumors.append(rumor)
                
        return sorted(matching_rumors, key=lambda r: r.confidence_level, reverse=True)
        
    def get_rumors_by_actor(self, actor_id: str) -> List[Rumor]:
        """
        Retrieve rumors that mention a specific actor.
        
        Args:
            actor_id: ID of the actor to search for
            
        Returns:
            List of rumors mentioning the actor
        """
        matching_rumors = []
        for rumor in self.active_rumors:
            # Check if actor is mentioned in content or source memory
            if (actor_id in rumor.content or 
                rumor.originator_id == actor_id or
                (rumor.source_memory and actor_id in rumor.source_memory.actor_ids)):
                matching_rumors.append(rumor)
                
        return sorted(matching_rumors, key=lambda r: r.confidence_level, reverse=True)
        
    def get_rumors_by_location(self, location: Tuple[float, float], 
                              radius: float = 25.0) -> List[Rumor]:
        """
        Retrieve rumors that originated near a specific location.
        
        Args:
            location: Tuple of (x, y) coordinates
            radius: Search radius around the location
            
        Returns:
            List of rumors within the specified area
        """
        matching_rumors = []
        for rumor in self.active_rumors:
            distance = math.sqrt(
                (rumor.location_origin[0] - location[0]) ** 2 +
                (rumor.location_origin[1] - location[1]) ** 2
            )
            if distance <= radius:
                matching_rumors.append(rumor)
                
        return sorted(matching_rumors, key=lambda r: r.confidence_level, reverse=True)
        
    def get_network_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current state of the rumor network.
        
        Returns:
            Dictionary containing network statistics
        """
        if not self.active_rumors:
            return {
                'total_rumors': 0,
                'avg_confidence': 0.0,
                'avg_spread_count': 0.0,
                'oldest_rumor_hours': 0.0,
                'most_spread_rumor': None
            }
            
        total_confidence = sum(r.confidence_level for r in self.active_rumors)
        total_spread = sum(r.spread_count for r in self.active_rumors)
        oldest_rumor = min(self.active_rumors, key=lambda r: r.timestamp_created)
        most_spread = max(self.active_rumors, key=lambda r: r.spread_count)
        
        return {
            'total_rumors': len(self.active_rumors),
            'avg_confidence': total_confidence / len(self.active_rumors),
            'avg_spread_count': total_spread / len(self.active_rumors),
            'oldest_rumor_hours': oldest_rumor.get_age_hours(),
            'most_spread_rumor': {
                'content': most_spread.content,
                'spread_count': most_spread.spread_count,
                'confidence': most_spread.confidence_level
            }
        }


# Test harness to demonstrate rumor spreading
if __name__ == "__main__":
    print("=== Rumor Engine Test Harness ===\n")
    
    # Create a rumor network
    network = RumorNetwork()
    
    # Create 5 NPCs with memory banks
    npc_ids = ["guard_001", "merchant_002", "farmer_003", "innkeeper_004", "noble_005"]
    npc_locations = {
        "guard_001": (10.0, 20.0),
        "merchant_002": (15.0, 25.0),
        "farmer_003": (30.0, 10.0),
        "innkeeper_004": (12.0, 22.0),
        "noble_005": (5.0, 35.0)
    }
    
    # Social connections (who talks to whom)
    social_connections = {
        "guard_001": ["merchant_002", "innkeeper_004"],
        "merchant_002": ["guard_001", "farmer_003", "innkeeper_004"],
        "farmer_003": ["merchant_002"],
        "innkeeper_004": ["guard_001", "merchant_002", "noble_005"],
        "noble_005": ["innkeeper_004"]
    }
    
    print("1. Setting up NPCs and their memories...")
    
    # Create memory banks and memorable events
    for npc_id in npc_ids:
        memory_bank = MemoryBank(npc_id)
        network.register_npc(npc_id, memory_bank)
        
        # Add some interesting memories that could spawn rumors
        if npc_id == "guard_001":
            crime_memory = MemoryNode(
                description="saw a cloaked figure breaking into the merchant's shop",
                location=(16.0, 24.0),
                actor_ids=["unknown_thief", "merchant_002"],
                context_tags=["crime", "witnessed", "theft"],
                timestamp=datetime.now() - timedelta(hours=1)
            )
            memory_bank.add_memory(crime_memory)
            
        elif npc_id == "innkeeper_004":
            gossip_memory = MemoryNode(
                description="overheard the noble discussing secret dealings with strangers",
                location=(6.0, 34.0),
                actor_ids=["noble_005", "unknown_visitor"],
                context_tags=["rumor", "politics", "secret"],
                timestamp=datetime.now() - timedelta(hours=3)
            )
            memory_bank.add_memory(gossip_memory)
            
    print(f"Created {len(npc_ids)} NPCs with memory banks")
    
    # Seed initial rumors from memories
    print("\n2. Seeding initial rumors from memories...")
    initial_rumors = 0
    for npc_id, memory_bank in network.npc_memory_banks.items():
        strongest_memories = memory_bank.get_strongest_memories(2)
        for memory in strongest_memories:
            rumor = network.seed_rumor_from_memory(npc_id, memory, rumor_threshold=0.5)
            if rumor:
                initial_rumors += 1
                print(f"  {npc_id} started rumor: {rumor.content}")
                
    print(f"Seeded {initial_rumors} initial rumors")
    
    # Simulate several daily ticks
    print("\n3. Simulating rumor spread over 3 days...")
    for day in range(1, 4):
        print(f"\n--- Day {day} ---")
        stats = network.daily_tick(npc_locations, social_connections)
        print(f"Rumors spread: {stats['rumors_spread']}")
        print(f"Rumors decayed: {stats['rumors_decayed']}")
        print(f"New rumors created: {stats['new_rumors_created']}")
        print(f"Rumors expired: {stats['rumors_expired']}")
        
        # Show current network state
        network_stats = network.get_network_stats()
        print(f"Total active rumors: {network_stats['total_rumors']}")
        print(f"Average confidence: {network_stats['avg_confidence']:.3f}")
        
    # Test query functionality
    print("\n4. Testing rumor queries...")
    
    # Search by topic
    crime_rumors = network.get_rumors_by_topic(["thief", "breaking", "crime"])
    print(f"\nCrime-related rumors: {len(crime_rumors)}")
    for rumor in crime_rumors[:2]:  # Show top 2
        print(f"  Confidence: {rumor.confidence_level:.3f} - {rumor.content}")
        
    # Search by actor
    noble_rumors = network.get_rumors_by_actor("noble_005")
    print(f"\nRumors about noble_005: {len(noble_rumors)}")
    for rumor in noble_rumors[:2]:
        print(f"  Confidence: {rumor.confidence_level:.3f} - {rumor.content}")
        
    # Search by location
    tavern_area_rumors = network.get_rumors_by_location((12.0, 22.0), radius=10.0)
    print(f"\nRumors near tavern area: {len(tavern_area_rumors)}")
    for rumor in tavern_area_rumors[:2]:
        print(f"  Confidence: {rumor.confidence_level:.3f} - {rumor.content}")
        
    # Final network statistics
    print("\n5. Final network statistics:")
    final_stats = network.get_network_stats()
    for key, value in final_stats.items():
        if key != 'most_spread_rumor':
            print(f"  {key}: {value}")
        else:
            print(f"  Most spread rumor: {value['content']} (spread {value['spread_count']} times)")
            
    print("\n=== Test Complete ===") 