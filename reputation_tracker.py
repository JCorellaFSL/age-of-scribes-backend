import uuid
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict


class ReputationMap:
    """
    Tracks reputation for a single entity across regions and factions.
    
    Manages both regional and factional reputation with support for
    event-based changes, natural decay, and historical tracking.
    """
    
    def __init__(self, entity_id: str):
        """
        Initialize reputation map for an entity.
        
        Args:
            entity_id: Unique identifier for the entity (NPC or player)
        """
        self.entity_id = entity_id
        self.regional_reputation: Dict[str, float] = {}
        self.faction_reputation: Dict[str, float] = {}
        
        # Track reputation history for analysis
        self.reputation_history: List[Dict[str, Any]] = []
        self.last_decay = datetime.now()
        
        # Reputation momentum - how quickly reputation changes
        self.momentum = 1.0  # 1.0 = normal rate, higher = faster changes
        
    def update_reputation(self, 
                         region: Optional[str] = None, 
                         faction: Optional[str] = None, 
                         delta: float = 0.0,
                         reason: str = "unspecified") -> Dict[str, float]:
        """
        Adjust reputation by delta value.
        
        Args:
            region: Region to update (if any)
            faction: Faction to update (if any)
            delta: Change in reputation (-1.0 to 1.0)
            reason: Reason for the change
            
        Returns:
            Dictionary of actual changes made
        """
        changes = {}
        
        # Apply momentum modifier
        actual_delta = delta * self.momentum
        
        # Update regional reputation
        if region is not None:
            old_value = self.regional_reputation.get(region, 0.0)
            new_value = max(-1.0, min(1.0, old_value + actual_delta))
            self.regional_reputation[region] = new_value
            changes[f"region_{region}"] = new_value - old_value
        
        # Update faction reputation
        if faction is not None:
            old_value = self.faction_reputation.get(faction, 0.0)
            new_value = max(-1.0, min(1.0, old_value + actual_delta))
            self.faction_reputation[faction] = new_value
            changes[f"faction_{faction}"] = new_value - old_value
        
        # Record the change
        if changes:
            self.reputation_history.append({
                'timestamp': datetime.now(),
                'region': region,
                'faction': faction,
                'delta_requested': delta,
                'delta_actual': actual_delta,
                'changes': changes,
                'reason': reason
            })
        
        return changes
    
    def get_reputation(self, 
                      region: Optional[str] = None, 
                      faction: Optional[str] = None) -> float:
        """
        Get current reputation level.
        
        Args:
            region: Region to query (if any)
            faction: Faction to query (if any)
            
        Returns:
            Reputation value (-1.0 to 1.0), 0.0 if not found
        """
        if region is not None:
            return self.regional_reputation.get(region, 0.0)
        elif faction is not None:
            return self.faction_reputation.get(faction, 0.0)
        else:
            # Return average reputation if no specific target
            all_reps = list(self.regional_reputation.values()) + list(self.faction_reputation.values())
            return sum(all_reps) / len(all_reps) if all_reps else 0.0
    
    def decay_reputation(self, rate: float = 0.01) -> Dict[str, float]:
        """
        Gradually normalize reputation values toward 0 over time.
        
        Args:
            rate: Decay rate per hour (0.0 to 1.0)
            
        Returns:
            Dictionary of reputation changes due to decay
        """
        current_time = datetime.now()
        time_delta = current_time - self.last_decay
        hours_passed = time_delta.total_seconds() / 3600.0
        
        decay_factor = rate * hours_passed
        changes = {}
        
        # Decay regional reputation
        for region in list(self.regional_reputation.keys()):
            old_value = self.regional_reputation[region]
            if abs(old_value) < 0.01:  # Already close to zero
                continue
                
            # Move toward zero
            decay_amount = decay_factor * abs(old_value)
            if old_value > 0:
                new_value = max(0.0, old_value - decay_amount)
            else:
                new_value = min(0.0, old_value + decay_amount)
                
            self.regional_reputation[region] = new_value
            change = new_value - old_value
            if abs(change) > 0.001:
                changes[f"region_{region}"] = change
        
        # Decay faction reputation
        for faction in list(self.faction_reputation.keys()):
            old_value = self.faction_reputation[faction]
            if abs(old_value) < 0.01:
                continue
                
            decay_amount = decay_factor * abs(old_value)
            if old_value > 0:
                new_value = max(0.0, old_value - decay_amount)
            else:
                new_value = min(0.0, old_value + decay_amount)
                
            self.faction_reputation[faction] = new_value
            change = new_value - old_value
            if abs(change) > 0.001:
                changes[f"faction_{faction}"] = change
        
        self.last_decay = current_time
        
        # Record decay if significant
        if changes:
            self.reputation_history.append({
                'timestamp': current_time,
                'region': None,
                'faction': None,
                'delta_requested': 0.0,
                'delta_actual': 0.0,
                'changes': changes,
                'reason': f"natural_decay_{rate}"
            })
        
        return changes
    
    def apply_event_influence(self, event: Dict[str, Any]) -> Dict[str, float]:
        """
        Modify reputation based on a structured event.
        
        Args:
            event: Dictionary containing event details
                   Expected keys: type, regions, factions, severity, context
                   
        Returns:
            Dictionary of reputation changes made
        """
        event_type = event.get('type', 'unknown')
        regions = event.get('regions', [])
        factions = event.get('factions', [])
        severity = event.get('severity', 1.0)  # 0.0 to 2.0 multiplier
        context = event.get('context', {})
        
        # Define event impact templates
        event_impacts = {
            'heroic_act': {
                'regional_base': 0.15,
                'faction_base': 0.1,
                'public_multiplier': 1.5
            },
            'crime_committed': {
                'regional_base': -0.2,
                'faction_base': -0.15,
                'law_faction_multiplier': 2.0
            },
            'crime_witnessed': {
                'regional_base': -0.1,
                'faction_base': -0.05,
                'witness_protection': 0.5
            },
            'betrayal': {
                'regional_base': -0.25,
                'faction_base': -0.3,
                'loyalty_penalty': 2.0
            },
            'charitable_act': {
                'regional_base': 0.1,
                'faction_base': 0.05,
                'religious_bonus': 1.5
            },
            'corruption': {
                'regional_base': -0.15,
                'faction_base': -0.2,
                'authority_penalty': 1.8
            },
            'rumor_spread': {
                'regional_base': 0.05,
                'faction_base': 0.02,
                'gossip_multiplier': 1.2,
                'credibility_factor': True
            },
            'faction_service': {
                'regional_base': 0.0,
                'faction_base': 0.2,
                'loyalty_bonus': 1.3
            },
            'faction_betrayal': {
                'regional_base': -0.1,
                'faction_base': -0.4,
                'enemy_bonus': 0.5
            }
        }
        
        if event_type not in event_impacts:
            return {}
        
        impact = event_impacts[event_type]
        all_changes = {}
        
        # Apply regional reputation changes
        for region in regions:
            base_change = impact['regional_base'] * severity
            
            # Apply context modifiers
            if 'public_multiplier' in impact and context.get('public', False):
                base_change *= impact['public_multiplier']
            if 'witness_protection' in impact and context.get('witnessed', False):
                base_change *= impact['witness_protection']
                
            changes = self.update_reputation(
                region=region, 
                delta=base_change,
                reason=f"{event_type}_in_{region}"
            )
            all_changes.update(changes)
        
        # Apply faction reputation changes
        for faction_id in factions:
            base_change = impact['faction_base'] * severity
            
            # Apply faction-specific modifiers
            faction_type = context.get('faction_types', {}).get(faction_id, 'unknown')
            
            if 'law_faction_multiplier' in impact and faction_type == 'law_enforcement':
                base_change *= impact['law_faction_multiplier']
            elif 'religious_bonus' in impact and faction_type == 'religious':
                base_change *= impact['religious_bonus']
            elif 'authority_penalty' in impact and faction_type == 'government':
                base_change *= impact['authority_penalty']
            elif 'loyalty_bonus' in impact and faction_type == 'affiliated':
                base_change *= impact['loyalty_bonus']
            
            # Special case for faction betrayal - improve reputation with enemies
            if event_type == 'faction_betrayal' and 'enemy_bonus' in impact:
                enemy_factions = context.get('enemy_factions', [])
                for enemy_faction in enemy_factions:
                    enemy_change = abs(base_change) * impact['enemy_bonus']
                    enemy_changes = self.update_reputation(
                        faction=enemy_faction,
                        delta=enemy_change,
                        reason=f"enemy_of_my_enemy_{faction_id}"
                    )
                    all_changes.update(enemy_changes)
            
            changes = self.update_reputation(
                faction=faction_id,
                delta=base_change,
                reason=f"{event_type}_with_{faction_id}"
            )
            all_changes.update(changes)
        
        return all_changes
    
    def get_reputation_descriptor(self, value: float) -> str:
        """Convert numerical reputation to descriptive text."""
        if value >= 0.8: return "revered"
        elif value >= 0.5: return "respected"
        elif value >= 0.2: return "liked"
        elif value >= -0.2: return "neutral"
        elif value >= -0.5: return "disliked"
        elif value >= -0.8: return "despised"
        else: return "reviled"
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive reputation summary."""
        regional_avg = sum(self.regional_reputation.values()) / max(1, len(self.regional_reputation))
        faction_avg = sum(self.faction_reputation.values()) / max(1, len(self.faction_reputation))
        
        return {
            'entity_id': self.entity_id,
            'regional_average': regional_avg,
            'faction_average': faction_avg,
            'overall_average': (regional_avg + faction_avg) / 2 if self.regional_reputation or self.faction_reputation else 0.0,
            'regional_count': len(self.regional_reputation),
            'faction_count': len(self.faction_reputation),
            'reputation_events': len(self.reputation_history),
            'momentum': self.momentum
        }


class ReputationEngine:
    """
    Global manager for reputation tracking across all entities.
    
    Handles reputation map storage, cross-entity queries, and integration
    with memory and rumor systems for automatic reputation updates.
    """
    
    def __init__(self):
        """Initialize the reputation engine."""
        self.reputation_maps: Dict[str, ReputationMap] = {}
        self.region_registry: Set[str] = set()
        self.faction_registry: Set[str] = set()
        self.last_global_decay = datetime.now()
        
        # Integration hooks (would connect to actual systems)
        self.memory_integration_enabled = True
        self.rumor_integration_enabled = True
        
    def get_or_create_reputation_map(self, entity_id: str) -> ReputationMap:
        """
        Get existing reputation map or create new one.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            ReputationMap instance for the entity
        """
        if entity_id not in self.reputation_maps:
            self.reputation_maps[entity_id] = ReputationMap(entity_id)
        return self.reputation_maps[entity_id]
    
    def update_reputation(self, 
                         entity_id: str, 
                         region: Optional[str] = None, 
                         faction: Optional[str] = None, 
                         delta: float = 0.0,
                         reason: str = "direct_update") -> Dict[str, float]:
        """
        Update reputation for an entity.
        
        Args:
            entity_id: Entity to update
            region: Region to update (if any)
            faction: Faction to update (if any)
            delta: Change in reputation
            reason: Reason for change
            
        Returns:
            Dictionary of changes made
        """
        reputation_map = self.get_or_create_reputation_map(entity_id)
        
        # Register region/faction for tracking
        if region: self.region_registry.add(region)
        if faction: self.faction_registry.add(faction)
        
        return reputation_map.update_reputation(region, faction, delta, reason)
    
    def get_reputation(self, 
                      entity_id: str, 
                      region: Optional[str] = None, 
                      faction: Optional[str] = None) -> float:
        """
        Get reputation for an entity.
        
        Args:
            entity_id: Entity to query
            region: Specific region (if any)
            faction: Specific faction (if any)
            
        Returns:
            Reputation value (-1.0 to 1.0)
        """
        if entity_id not in self.reputation_maps:
            return 0.0
        return self.reputation_maps[entity_id].get_reputation(region, faction)
    
    def apply_event(self, entity_id: str, event: Dict[str, Any]) -> Dict[str, float]:
        """
        Apply event-based reputation changes.
        
        Args:
            entity_id: Entity affected by event
            event: Event details dictionary
            
        Returns:
            Dictionary of reputation changes
        """
        reputation_map = self.get_or_create_reputation_map(entity_id)
        
        # Register regions and factions from event
        for region in event.get('regions', []):
            self.region_registry.add(region)
        for faction in event.get('factions', []):
            self.faction_registry.add(faction)
            
        return reputation_map.apply_event_influence(event)
    
    def process_memory_influence(self, entity_id: str, memory_node: Any) -> Dict[str, float]:
        """
        Process reputation effects from memory events.
        
        Args:
            entity_id: Entity whose memory is being processed
            memory_node: MemoryNode from memory_core
            
        Returns:
            Dictionary of reputation changes
        """
        if not self.memory_integration_enabled:
            return {}
        
        # Convert memory to reputation event
        context_tags = getattr(memory_node, 'context_tags', [])
        location = getattr(memory_node, 'location', (0, 0))
        actor_ids = getattr(memory_node, 'actor_ids', [])
        strength = getattr(memory_node, 'strength', 1.0)
        
        # Determine event type from context tags
        event_type = 'unknown'
        if 'crime' in context_tags:
            event_type = 'crime_witnessed' if entity_id not in actor_ids else 'crime_committed'
        elif 'heroic' in context_tags or 'helpful' in context_tags:
            event_type = 'heroic_act'
        elif 'betrayal' in context_tags:
            event_type = 'betrayal'
        elif 'charitable' in context_tags or 'generous' in context_tags:
            event_type = 'charitable_act'
        elif 'corruption' in context_tags:
            event_type = 'corruption'
        
        # Create event from memory
        event = {
            'type': event_type,
            'regions': [f"region_at_{location[0]:.0f}_{location[1]:.0f}"],  # Simplified region mapping
            'factions': [],  # Would need faction mapping logic
            'severity': strength,
            'context': {
                'witnessed': entity_id not in actor_ids,
                'public': 'witnessed' in context_tags or 'public' in context_tags
            }
        }
        
        return self.apply_event(entity_id, event)
    
    def process_rumor_influence(self, entity_id: str, rumor: Any) -> Dict[str, float]:
        """
        Process reputation effects from rumors.
        
        Args:
            entity_id: Entity affected by rumor
            rumor: Rumor from rumor_engine
            
        Returns:
            Dictionary of reputation changes
        """
        if not self.rumor_integration_enabled:
            return {}
        
        # Extract rumor properties
        content = getattr(rumor, 'content', '')
        confidence = getattr(rumor, 'confidence_level', 0.5)
        spread_count = getattr(rumor, 'spread_count', 1)
        location_origin = getattr(rumor, 'location_origin', (0, 0))
        
        # Determine if rumor is positive or negative
        negative_keywords = ['stole', 'betrayed', 'corrupt', 'criminal', 'evil', 'bad']
        positive_keywords = ['helped', 'saved', 'generous', 'heroic', 'good', 'noble']
        
        sentiment = 0.0
        for keyword in negative_keywords:
            if keyword in content.lower():
                sentiment -= 0.1
        for keyword in positive_keywords:
            if keyword in content.lower():
                sentiment += 0.1
        
        # Create reputation event
        event = {
            'type': 'rumor_spread',
            'regions': [f"region_at_{location_origin[0]:.0f}_{location_origin[1]:.0f}"],
            'factions': [],
            'severity': confidence * min(2.0, spread_count / 3.0),  # More spread = more impact
            'context': {
                'credibility_factor': confidence,
                'sentiment': sentiment
            }
        }
        
        # Apply sentiment modifier to the base reputation change
        changes = self.apply_event(entity_id, event)
        
        # Modify changes based on sentiment
        if sentiment != 0.0:
            sentiment_changes = {}
            for key, value in changes.items():
                adjusted_value = value * (1.0 + sentiment)
                sentiment_changes[key] = adjusted_value - value
                # Apply the sentiment adjustment
                if 'region_' in key:
                    region = key.replace('region_', '')
                    self.update_reputation(entity_id, region=region, delta=sentiment_changes[key], reason="rumor_sentiment")
                elif 'faction_' in key:
                    faction = key.replace('faction_', '')
                    self.update_reputation(entity_id, faction=faction, delta=sentiment_changes[key], reason="rumor_sentiment")
            
            changes.update(sentiment_changes)
        
        return changes
    
    def decay_all_reputations(self, rate: float = 0.01) -> Dict[str, Dict[str, float]]:
        """
        Apply decay to all reputation maps.
        
        Args:
            rate: Decay rate per hour
            
        Returns:
            Dictionary of entity_id -> changes
        """
        all_changes = {}
        current_time = datetime.now()
        
        for entity_id, reputation_map in self.reputation_maps.items():
            changes = reputation_map.decay_reputation(rate)
            if changes:
                all_changes[entity_id] = changes
        
        self.last_global_decay = current_time
        return all_changes
    
    def get_regional_standings(self, region: str) -> List[Tuple[str, float, str]]:
        """
        Get all entities' standings in a specific region.
        
        Args:
            region: Region to query
            
        Returns:
            List of (entity_id, reputation, descriptor) tuples sorted by reputation
        """
        standings = []
        for entity_id, reputation_map in self.reputation_maps.items():
            rep_value = reputation_map.get_reputation(region=region)
            if rep_value != 0.0:  # Only include entities with non-zero reputation
                descriptor = reputation_map.get_reputation_descriptor(rep_value)
                standings.append((entity_id, rep_value, descriptor))
        
        standings.sort(key=lambda x: x[1], reverse=True)
        return standings
    
    def get_faction_standings(self, faction: str) -> List[Tuple[str, float, str]]:
        """
        Get all entities' standings with a specific faction.
        
        Args:
            faction: Faction to query
            
        Returns:
            List of (entity_id, reputation, descriptor) tuples sorted by reputation
        """
        standings = []
        for entity_id, reputation_map in self.reputation_maps.items():
            rep_value = reputation_map.get_reputation(faction=faction)
            if rep_value != 0.0:
                descriptor = reputation_map.get_reputation_descriptor(rep_value)
                standings.append((entity_id, rep_value, descriptor))
        
        standings.sort(key=lambda x: x[1], reverse=True)
        return standings
    
    def get_cross_entity_analysis(self, entities: List[str]) -> Dict[str, Any]:
        """
        Analyze reputation relationships between multiple entities.
        
        Args:
            entities: List of entity IDs to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        analysis = {
            'entities': entities,
            'regional_comparison': {},
            'faction_comparison': {},
            'overall_rankings': [],
            'reputation_correlations': {}
        }
        
        # Regional comparison
        for region in self.region_registry:
            region_data = []
            for entity_id in entities:
                if entity_id in self.reputation_maps:
                    rep = self.reputation_maps[entity_id].get_reputation(region=region)
                    region_data.append((entity_id, rep))
            analysis['regional_comparison'][region] = sorted(region_data, key=lambda x: x[1], reverse=True)
        
        # Faction comparison
        for faction in self.faction_registry:
            faction_data = []
            for entity_id in entities:
                if entity_id in self.reputation_maps:
                    rep = self.reputation_maps[entity_id].get_reputation(faction=faction)
                    faction_data.append((entity_id, rep))
            analysis['faction_comparison'][faction] = sorted(faction_data, key=lambda x: x[1], reverse=True)
        
        # Overall rankings
        overall_data = []
        for entity_id in entities:
            if entity_id in self.reputation_maps:
                summary = self.reputation_maps[entity_id].get_summary()
                overall_data.append((entity_id, summary['overall_average']))
        analysis['overall_rankings'] = sorted(overall_data, key=lambda x: x[1], reverse=True)
        
        return analysis
    
    def get_engine_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the reputation engine."""
        total_entities = len(self.reputation_maps)
        total_regions = len(self.region_registry)
        total_factions = len(self.faction_registry)
        
        # Calculate distribution statistics
        all_regional_reps = []
        all_faction_reps = []
        for reputation_map in self.reputation_maps.values():
            all_regional_reps.extend(reputation_map.regional_reputation.values())
            all_faction_reps.extend(reputation_map.faction_reputation.values())
        
        regional_avg = sum(all_regional_reps) / len(all_regional_reps) if all_regional_reps else 0.0
        faction_avg = sum(all_faction_reps) / len(all_faction_reps) if all_faction_reps else 0.0
        
        return {
            'total_entities': total_entities,
            'total_regions': total_regions,
            'total_factions': total_factions,
            'total_regional_relationships': len(all_regional_reps),
            'total_faction_relationships': len(all_faction_reps),
            'average_regional_reputation': regional_avg,
            'average_faction_reputation': faction_avg,
            'reputation_events_total': sum(len(rm.reputation_history) for rm in self.reputation_maps.values()),
            'regions': list(self.region_registry),
            'factions': list(self.faction_registry)
        }


# Test harness
if __name__ == "__main__":
    print("=== Reputation Tracker Test Harness ===\n")
    
    # Initialize reputation engine
    engine = ReputationEngine()
    
    # Test entities
    entities = ["hero_player", "merchant_bob", "guard_captain"]
    regions = ["Westford", "Eastdale", "Shadowmere"]
    factions = ["merchants_guild", "city_guard", "thieves_guild", "temple_order"]
    
    print("1. Setting up initial reputations...")
    
    # Initialize some base reputations
    engine.update_reputation("hero_player", region="Westford", delta=0.3, reason="helped_citizens")
    engine.update_reputation("hero_player", faction="merchants_guild", delta=0.2, reason="protected_caravan")
    
    engine.update_reputation("merchant_bob", region="Westford", delta=0.5, reason="fair_trader")
    engine.update_reputation("merchant_bob", region="Eastdale", delta=0.1, reason="new_to_area")
    engine.update_reputation("merchant_bob", faction="merchants_guild", delta=0.7, reason="guild_member")
    
    engine.update_reputation("guard_captain", region="Westford", delta=0.4, reason="maintains_order")
    engine.update_reputation("guard_captain", faction="city_guard", delta=0.8, reason="leadership_role")
    engine.update_reputation("guard_captain", faction="thieves_guild", delta=-0.6, reason="enemy_of_crime")
    
    # Print initial state
    for entity in entities:
        print(f"\n{entity} initial reputation:")
        reputation_map = engine.reputation_maps[entity]
        for region in regions:
            rep = reputation_map.get_reputation(region=region)
            if rep != 0.0:
                descriptor = reputation_map.get_reputation_descriptor(rep)
                print(f"  {region}: {rep:.2f} ({descriptor})")
        for faction in factions:
            rep = reputation_map.get_reputation(faction=faction)
            if rep != 0.0:
                descriptor = reputation_map.get_reputation_descriptor(rep)
                print(f"  {faction}: {rep:.2f} ({descriptor})")
    
    print("\n2. Testing event-based reputation changes...")
    
    # Hero commits a crime (accidentally)
    crime_event = {
        'type': 'crime_committed',
        'regions': ['Westford'],
        'factions': ['city_guard'],
        'severity': 0.8,
        'context': {'public': True}
    }
    
    print(f"\nHero commits a public crime in Westford:")
    changes = engine.apply_event("hero_player", crime_event)
    print(f"  Reputation changes: {changes}")
    
    # Merchant performs charitable act
    charity_event = {
        'type': 'charitable_act',
        'regions': ['Eastdale'],
        'factions': ['temple_order'],
        'severity': 1.2,
        'context': {'religious': True}
    }
    
    print(f"\nMerchant Bob donates to temple in Eastdale:")
    changes = engine.apply_event("merchant_bob", charity_event)
    print(f"  Reputation changes: {changes}")
    
    # Guard captain betrays thieves guild informant
    betrayal_event = {
        'type': 'faction_betrayal',
        'regions': ['Shadowmere'],
        'factions': ['thieves_guild'],
        'severity': 1.5,
        'context': {
            'faction_types': {'thieves_guild': 'criminal'},
            'enemy_factions': ['city_guard']
        }
    }
    
    print(f"\nGuard captain exposes thieves guild operations:")
    changes = engine.apply_event("guard_captain", betrayal_event)
    print(f"  Reputation changes: {changes}")
    
    print("\n3. Testing rumor-based reputation effects...")
    
    # Simulate a rumor about the hero
    class MockRumor:
        def __init__(self, content, confidence, spread_count, location):
            self.content = content
            self.confidence_level = confidence
            self.spread_count = spread_count
            self.location_origin = location
    
    positive_rumor = MockRumor(
        "Hero saved a child from burning building",
        0.8, 5, (10, 20)
    )
    
    print(f"\nPositive rumor spreads about hero:")
    print(f"  Rumor: {positive_rumor.content}")
    changes = engine.process_rumor_influence("hero_player", positive_rumor)
    print(f"  Reputation changes: {changes}")
    
    negative_rumor = MockRumor(
        "Merchant Bob was seen taking bribes from criminals",
        0.6, 3, (15, 25)
    )
    
    print(f"\nNegative rumor spreads about merchant:")
    print(f"  Rumor: {negative_rumor.content}")
    changes = engine.process_rumor_influence("merchant_bob", negative_rumor)
    print(f"  Reputation changes: {changes}")
    
    print("\n4. Testing memory-based reputation effects...")
    
    # Simulate a memory node
    class MockMemory:
        def __init__(self, description, context_tags, location, actor_ids, strength):
            self.description = description
            self.context_tags = context_tags
            self.location = location
            self.actor_ids = actor_ids
            self.strength = strength
    
    heroic_memory = MockMemory(
        "Rescued merchants from bandits on the road",
        ["heroic", "witnessed", "public"],
        (12, 18),
        ["hero_player", "bandit_leader"],
        0.9
    )
    
    print(f"\nHero's heroic memory processed:")
    print(f"  Memory: {heroic_memory.description}")
    changes = engine.process_memory_influence("hero_player", heroic_memory)
    print(f"  Reputation changes: {changes}")
    
    print("\n5. Testing reputation decay...")
    
    print("\nApplying reputation decay (simulating passage of time):")
    decay_changes = engine.decay_all_reputations(rate=0.05)  # Higher rate for testing
    for entity_id, changes in decay_changes.items():
        if changes:
            print(f"  {entity_id} decay: {changes}")
    
    print("\n6. Regional and faction standings...")
    
    print(f"\nWestford regional standings:")
    westford_standings = engine.get_regional_standings("Westford")
    for entity_id, reputation, descriptor in westford_standings:
        print(f"  {entity_id}: {reputation:.2f} ({descriptor})")
    
    print(f"\nMerchants Guild faction standings:")
    guild_standings = engine.get_faction_standings("merchants_guild")
    for entity_id, reputation, descriptor in guild_standings:
        print(f"  {entity_id}: {reputation:.2f} ({descriptor})")
    
    print("\n7. Cross-entity analysis...")
    
    analysis = engine.get_cross_entity_analysis(entities)
    print(f"\nOverall reputation rankings:")
    for entity_id, avg_reputation in analysis['overall_rankings']:
        print(f"  {entity_id}: {avg_reputation:.2f}")
    
    print(f"\nRegional comparison (Westford):")
    if 'Westford' in analysis['regional_comparison']:
        for entity_id, reputation in analysis['regional_comparison']['Westford']:
            if reputation != 0.0:
                print(f"  {entity_id}: {reputation:.2f}")
    
    print("\n8. Engine statistics...")
    
    stats = engine.get_engine_statistics()
    print(f"\nReputation Engine Statistics:")
    print(f"  Total entities tracked: {stats['total_entities']}")
    print(f"  Total regions: {stats['total_regions']}")
    print(f"  Total factions: {stats['total_factions']}")
    print(f"  Total reputation relationships: {stats['total_regional_relationships'] + stats['total_faction_relationships']}")
    print(f"  Total reputation events: {stats['reputation_events_total']}")
    print(f"  Average regional reputation: {stats['average_regional_reputation']:.3f}")
    print(f"  Average faction reputation: {stats['average_faction_reputation']:.3f}")
    
    print("\n=== Test Complete ===") 