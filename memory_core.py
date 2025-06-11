import uuid
import math
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any


class MemoryNode:
    """
    Represents a single memory event with metadata and decay functionality.
    
    A MemoryNode stores information about an event that occurred in the game world,
    including who was involved, when and where it happened, and what kind of event it was.
    """
    
    def __init__(self, 
                 description: str,
                 location: Tuple[float, float],
                 actor_ids: List[str],
                 context_tags: List[str],
                 event_id: Optional[str] = None,
                 timestamp: Optional[datetime] = None,
                 initial_strength: float = 1.0):
        """
        Initialize a new memory node.
        
        Args:
            description: Text description of the event
            location: Tuple of (x, y) coordinates where event occurred
            actor_ids: List of NPC or player IDs involved in the event
            context_tags: List of contextual tags (e.g., "crime", "witnessed", "rumor")
            event_id: Unique identifier for the event (auto-generated if None)
            timestamp: When the event occurred (current time if None)
            initial_strength: Initial memory strength (0.0 to 1.0)
        """
        self.event_id = event_id or str(uuid.uuid4())
        self.description = description
        self.timestamp = timestamp or datetime.now()
        self.location = location
        self.actor_ids = actor_ids.copy()  # Make a copy to avoid reference issues
        self.context_tags = context_tags.copy()
        self.strength = max(0.0, min(1.0, initial_strength))  # Clamp between 0 and 1
        
    def decay(self, decay_rate: float = 0.1, time_passed_hours: Optional[float] = None) -> None:
        """
        Apply exponential decay to the memory strength based on time passed.
        
        Args:
            decay_rate: Rate of decay (higher = faster decay)
            time_passed_hours: Hours since last decay (auto-calculated if None)
        """
        if time_passed_hours is None:
            # Calculate time passed since memory creation
            time_delta = datetime.now() - self.timestamp
            time_passed_hours = time_delta.total_seconds() / 3600.0
        
        # Apply exponential decay: strength = initial_strength * e^(-decay_rate * time)
        decay_factor = math.exp(-decay_rate * time_passed_hours)
        self.strength *= decay_factor
        
        # Ensure strength doesn't go below 0
        self.strength = max(0.0, self.strength)
    
    def recall(self, query_tags: Optional[List[str]] = None, 
               query_actors: Optional[List[str]] = None) -> Tuple[Dict[str, Any], float]:
        """
        Attempt to recall this memory with a confidence rating.
        
        Args:
            query_tags: Tags to match against for relevance boost
            query_actors: Actor IDs to match against for relevance boost
            
        Returns:
            Tuple of (memory_data, confidence_rating)
            memory_data contains all the memory information
            confidence_rating is a float between 0.0 and 1.0
        """
        # Base confidence starts with current strength
        confidence = self.strength
        
        # Boost confidence based on tag relevance
        if query_tags:
            matching_tags = set(self.context_tags).intersection(set(query_tags))
            if matching_tags:
                tag_boost = len(matching_tags) / len(query_tags)
                confidence = min(1.0, confidence * (1.0 + tag_boost))
        
        # Boost confidence based on actor relevance
        if query_actors:
            matching_actors = set(self.actor_ids).intersection(set(query_actors))
            if matching_actors:
                actor_boost = len(matching_actors) / len(query_actors)
                confidence = min(1.0, confidence * (1.0 + actor_boost))
        
        # Compile memory data
        memory_data = {
            'event_id': self.event_id,
            'description': self.description,
            'timestamp': self.timestamp,
            'location': self.location,
            'actor_ids': self.actor_ids,
            'context_tags': self.context_tags,
            'strength': self.strength
        }
        
        return memory_data, confidence


class MemoryBank:
    """
    Container for an NPC's collection of memories with management functionality.
    
    The MemoryBank belongs to a specific NPC and manages all their memories,
    including adding new memories, applying decay over time, and recalling
    relevant memories based on queries.
    """
    
    def __init__(self, owner_id: str, max_memories: int = 1000):
        """
        Initialize a new memory bank.
        
        Args:
            owner_id: ID of the NPC who owns this memory bank
            max_memories: Maximum number of memories to store (oldest removed first)
        """
        self.owner_id = owner_id
        self.max_memories = max_memories
        self.memories: List[MemoryNode] = []
        self.last_decay_time = datetime.now()
    
    def add_memory(self, memory_node: MemoryNode) -> None:
        """
        Add a new memory to the bank.
        
        Args:
            memory_node: The MemoryNode to add
        """
        self.memories.append(memory_node)
        
        # Remove oldest memories if we exceed the limit
        if len(self.memories) > self.max_memories:
            # Sort by timestamp and remove the oldest
            self.memories.sort(key=lambda m: m.timestamp)
            self.memories = self.memories[-self.max_memories:]
    
    def decay_all_memories(self, decay_rate: float = 0.1) -> None:
        """
        Apply decay to all memories based on time since last decay.
        
        Args:
            decay_rate: Rate of decay to apply to all memories
        """
        current_time = datetime.now()
        time_delta = current_time - self.last_decay_time
        time_passed_hours = time_delta.total_seconds() / 3600.0
        
        # Apply decay to all memories
        for memory in self.memories:
            memory.decay(decay_rate, time_passed_hours)
        
        # Remove memories that have decayed to near zero strength
        self.memories = [m for m in self.memories if m.strength > 0.01]
        
        self.last_decay_time = current_time
    
    def recall_memories(self, 
                       query_tags: Optional[List[str]] = None,
                       query_actors: Optional[List[str]] = None,
                       min_confidence: float = 0.1,
                       max_results: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        """
        Attempt to recall memories based on query parameters.
        
        Args:
            query_tags: Tags to search for in memories
            query_actors: Actor IDs to search for in memories
            min_confidence: Minimum confidence threshold for returned memories
            max_results: Maximum number of memories to return
            
        Returns:
            List of tuples containing (memory_data, confidence_rating)
            sorted by confidence in descending order
        """
        # First, apply decay to ensure memories are up to date
        self.decay_all_memories()
        
        recalled_memories = []
        
        for memory in self.memories:
            memory_data, confidence = memory.recall(query_tags, query_actors)
            
            if confidence >= min_confidence:
                recalled_memories.append((memory_data, confidence))
        
        # Sort by confidence (highest first) and limit results
        recalled_memories.sort(key=lambda x: x[1], reverse=True)
        return recalled_memories[:max_results]
    
    def get_memory_count(self) -> int:
        """
        Get the current number of memories in the bank.
        
        Returns:
            Number of memories currently stored
        """
        return len(self.memories)
    
    def get_strongest_memories(self, count: int = 5) -> List[MemoryNode]:
        """
        Get the strongest memories currently in the bank.
        
        Args:
            count: Number of memories to return
            
        Returns:
            List of MemoryNode objects sorted by strength (strongest first)
        """
        sorted_memories = sorted(self.memories, key=lambda m: m.strength, reverse=True)
        return sorted_memories[:count]


# Test harness to demonstrate usage
if __name__ == "__main__":
    print("=== Memory Core Test Harness ===\n")
    
    # Create a memory bank for an NPC
    npc_memory = MemoryBank("guard_001")
    
    # Create some test memories
    print("1. Creating test memories...")
    
    # Memory 1: A crime witnessed
    crime_memory = MemoryNode(
        description="Saw a hooded figure steal bread from the baker's stall",
        location=(10.5, 23.7),
        actor_ids=["thief_unknown", "baker_john"],
        context_tags=["crime", "witnessed", "theft"],
        timestamp=datetime.now() - timedelta(hours=2)
    )
    
    # Memory 2: A conversation overheard
    conversation_memory = MemoryNode(
        description="Overheard two merchants discussing increased bandit activity",
        location=(15.2, 18.9),
        actor_ids=["merchant_alice", "merchant_bob"],
        context_tags=["rumor", "bandits", "trade"],
        timestamp=datetime.now() - timedelta(hours=6)
    )
    
    # Memory 3: A friendly interaction
    friendly_memory = MemoryNode(
        description="Player helped me catch a runaway chicken",
        location=(8.1, 30.4),
        actor_ids=["player_hero"],
        context_tags=["helpful", "friendly", "animals"],
        timestamp=datetime.now() - timedelta(minutes=30)
    )
    
    # Add memories to the bank
    npc_memory.add_memory(crime_memory)
    npc_memory.add_memory(conversation_memory)
    npc_memory.add_memory(friendly_memory)
    
    print(f"Added 3 memories. Total memories: {npc_memory.get_memory_count()}")
    
    # Test recall functionality
    print("\n2. Testing memory recall...")
    
    # Recall crime-related memories
    print("\nRecalling crime-related memories:")
    crime_recalls = npc_memory.recall_memories(query_tags=["crime", "theft"])
    for memory_data, confidence in crime_recalls:
        print(f"  Confidence: {confidence:.2f} - {memory_data['description']}")
    
    # Recall memories involving specific actors
    print("\nRecalling memories involving merchants:")
    merchant_recalls = npc_memory.recall_memories(query_actors=["merchant_alice", "merchant_bob"])
    for memory_data, confidence in merchant_recalls:
        print(f"  Confidence: {confidence:.2f} - {memory_data['description']}")
    
    # Test decay functionality
    print("\n3. Testing memory decay...")
    print("Memory strengths before decay:")
    for i, memory in enumerate(npc_memory.memories):
        print(f"  Memory {i+1}: {memory.strength:.3f}")
    
    # Apply decay (simulate 12 hours passing)
    for memory in npc_memory.memories:
        memory.decay(decay_rate=0.2, time_passed_hours=12)
    
    print("\nMemory strengths after 12 hours of decay:")
    for i, memory in enumerate(npc_memory.memories):
        print(f"  Memory {i+1}: {memory.strength:.3f}")
    
    # Test recall after decay
    print("\n4. Testing recall after decay...")
    all_recalls = npc_memory.recall_memories(min_confidence=0.01)
    print(f"Recalled {len(all_recalls)} memories with confidence > 0.01:")
    for memory_data, confidence in all_recalls:
        print(f"  Confidence: {confidence:.3f} - {memory_data['description'][:50]}...")
    
    print("\n=== Test Complete ===") 