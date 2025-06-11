import uuid
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict


class Faction:
    """
    Represents a political, religious, or social faction with dynamic ideology and goals.
    
    Factions are groups of NPCs with shared objectives, beliefs, and resources that
    can evolve over time based on member actions, events, and external pressures.
    """
    
    # Faction archetype templates with predefined characteristics
    FACTION_ARCHETYPES = {
        "religious_cult": {
            "ideology": {"order": 0.8, "freedom": 0.2, "violence": 0.6, "tradition": 0.9, "authority": 0.8},
            "goals": ["spread the faith", "purge heretics", "build temples", "gain religious authority"],
            "traits": ["theocratic", "zealous", "hierarchical"],
            "base_resources": {"gold": 500, "influence": 60, "troops": 20, "faith": 80}
        },
        "trade_guild": {
            "ideology": {"order": 0.7, "freedom": 0.8, "violence": 0.2, "progress": 0.9, "authority": 0.4},
            "goals": ["monopolize trade routes", "eliminate competition", "expand markets", "accumulate wealth"],
            "traits": ["mercantile", "pragmatic", "networked"],
            "base_resources": {"gold": 2000, "influence": 70, "troops": 10, "connections": 90}
        },
        "rogue_military": {
            "ideology": {"order": 0.9, "freedom": 0.4, "violence": 0.9, "authority": 0.8, "loyalty": 0.6},
            "goals": ["regain lost territory", "restore military honor", "eliminate enemies", "recruit veterans"],
            "traits": ["militant", "disciplined", "vengeful"],
            "base_resources": {"gold": 800, "influence": 40, "troops": 80, "weapons": 90}
        },
        "thieves_guild": {
            "ideology": {"order": 0.3, "freedom": 0.9, "violence": 0.5, "authority": 0.2, "loyalty": 0.7},
            "goals": ["control underground economy", "corrupt officials", "expand territory", "eliminate rivals"],
            "traits": ["criminal", "secretive", "opportunistic"],
            "base_resources": {"gold": 1200, "influence": 50, "troops": 30, "stealth": 85}
        },
        "noble_house": {
            "ideology": {"order": 0.8, "freedom": 0.3, "violence": 0.4, "tradition": 0.9, "authority": 0.9},
            "goals": ["maintain bloodline prestige", "expand holdings", "secure succession", "influence court"],
            "traits": ["aristocratic", "traditional", "political"],
            "base_resources": {"gold": 3000, "influence": 85, "troops": 40, "lands": 75}
        },
        "rebel_movement": {
            "ideology": {"order": 0.2, "freedom": 0.9, "violence": 0.7, "progress": 0.8, "authority": 0.1},
            "goals": ["overthrow tyrants", "liberate the oppressed", "destroy old order", "establish new government"],
            "traits": ["revolutionary", "populist", "militant"],
            "base_resources": {"gold": 300, "influence": 30, "troops": 60, "popular_support": 70}
        },
        "scholarly_order": {
            "ideology": {"order": 0.6, "freedom": 0.7, "violence": 0.1, "progress": 0.9, "tradition": 0.6},
            "goals": ["preserve knowledge", "conduct research", "educate masses", "discover truth"],
            "traits": ["intellectual", "peaceful", "methodical"],
            "base_resources": {"gold": 600, "influence": 65, "troops": 5, "knowledge": 95}
        }
    }
    
    def __init__(self,
                 name: str,
                 region_base: str,
                 faction_id: Optional[str] = None,
                 ideology: Optional[Dict[str, float]] = None,
                 goals: Optional[List[str]] = None,
                 resources: Optional[Dict[str, int]] = None,
                 members: Optional[List[str]] = None,
                 reputation_map: Optional[Dict[str, float]] = None,
                 faction_traits: Optional[List[str]] = None):
        """
        Initialize a faction.
        
        Args:
            name: Name of the faction
            region_base: Primary region or base of operations
            faction_id: Unique identifier (auto-generated if None)
            ideology: Dictionary of ideological values (0.0 to 1.0)
            goals: List of strategic objectives
            resources: Dictionary of resource amounts
            members: List of NPC IDs belonging to the faction
            reputation_map: Regional reputation scores
            faction_traits: List of trait tags describing the faction
        """
        self.faction_id = faction_id or str(uuid.uuid4())
        self.name = name
        self.region_base = region_base
        self.ideology = ideology or self._default_ideology()
        self.goals = goals or []
        self.resources = resources or {"gold": 100, "influence": 10, "troops": 5}
        self.members = members or []
        self.reputation_map = reputation_map or {region_base: 0.0}
        self.faction_traits = faction_traits or []
        
        # Track faction evolution
        self.ideology_history = []
        self.goal_history = []
        self.creation_date = datetime.now()
        self.last_evolution = datetime.now()
        
        # Internal faction dynamics
        self.stability = 1.0  # How unified the faction is (0.0 to 1.0)
        self.activity_level = 0.5  # How active the faction is (0.0 to 1.0)
        
    def _default_ideology(self) -> Dict[str, float]:
        """Generate default ideological values."""
        return {
            "order": 0.5,
            "freedom": 0.5,
            "violence": 0.5,
            "tradition": 0.5,
            "progress": 0.5,
            "authority": 0.5,
            "loyalty": 0.5,
            "justice": 0.5
        }
    
    @classmethod
    def generate_faction(cls,
                        name: str,
                        region_base: str,
                        archetype: str,
                        size_modifier: float = 1.0) -> 'Faction':
        """
        Generate a faction based on an archetype template.
        
        Args:
            name: Name for the faction
            region_base: Base region
            archetype: Archetype key from FACTION_ARCHETYPES
            size_modifier: Multiplier for faction size and resources
            
        Returns:
            New Faction instance
        """
        if archetype not in cls.FACTION_ARCHETYPES:
            raise ValueError(f"Unknown archetype: {archetype}")
        
        template = cls.FACTION_ARCHETYPES[archetype]
        
        # Apply size modifier to resources
        resources = {}
        for resource, base_amount in template["base_resources"].items():
            resources[resource] = int(base_amount * size_modifier)
        
        # Add some random variation to ideology
        ideology = template["ideology"].copy()
        for key in ideology:
            variation = random.uniform(-0.1, 0.1)
            ideology[key] = max(0.0, min(1.0, ideology[key] + variation))
        
        faction = cls(
            name=name,
            region_base=region_base,
            ideology=ideology,
            goals=template["goals"].copy(),
            resources=resources,
            faction_traits=template["traits"].copy(),
            reputation_map={region_base: random.uniform(-0.2, 0.2)}
        )
        
        return faction
    
    def evolve_ideology(self,
                       trigger_event: str,
                       member_influences: Optional[Dict[str, float]] = None,
                       external_pressure: Optional[Dict[str, float]] = None,
                       evolution_strength: float = 0.1) -> Dict[str, float]:
        """
        Evolve faction ideology based on events and influences.
        
        Args:
            trigger_event: Description of the triggering event
            member_influences: How members' beliefs influence faction ideology
            external_pressure: External pressures affecting ideology
            evolution_strength: How much the faction can change (0.0 to 1.0)
            
        Returns:
            Dictionary of ideology changes
        """
        changes = {}
        old_ideology = self.ideology.copy()
        
        # Apply member influences (if provided)
        if member_influences:
            for aspect, influence in member_influences.items():
                if aspect in self.ideology:
                    change = influence * evolution_strength * 0.3  # Members have moderate influence
                    self.ideology[aspect] = max(0.0, min(1.0, self.ideology[aspect] + change))
                    if abs(change) > 0.01:
                        changes[aspect] = change
        
        # Apply external pressures
        if external_pressure:
            for aspect, pressure in external_pressure.items():
                if aspect in self.ideology:
                    change = pressure * evolution_strength * 0.5  # External events have strong influence
                    self.ideology[aspect] = max(0.0, min(1.0, self.ideology[aspect] + change))
                    if abs(change) > 0.01:
                        changes[aspect] = changes.get(aspect, 0.0) + change
        
        # Event-specific ideology shifts
        event_influences = {
            "military_victory": {"violence": 0.1, "authority": 0.15, "order": 0.1},
            "military_defeat": {"violence": -0.1, "authority": -0.2, "order": -0.1},
            "betrayal": {"loyalty": 0.2, "authority": 0.1, "freedom": -0.1},
            "peaceful_success": {"violence": -0.1, "order": 0.1, "progress": 0.1},
            "corruption_exposed": {"authority": -0.2, "justice": 0.2, "order": -0.1},
            "persecution": {"violence": 0.2, "freedom": 0.1, "authority": -0.1},
            "economic_crisis": {"order": -0.1, "progress": -0.1, "violence": 0.1}
        }
        
        if trigger_event in event_influences:
            for aspect, influence in event_influences[trigger_event].items():
                if aspect in self.ideology:
                    change = influence * evolution_strength
                    self.ideology[aspect] = max(0.0, min(1.0, self.ideology[aspect] + change))
                    if abs(change) > 0.01:
                        changes[aspect] = changes.get(aspect, 0.0) + change
        
        # Update stability based on how much ideology changed
        total_change = sum(abs(change) for change in changes.values())
        if total_change > 0.3:
            self.stability = max(0.1, self.stability - 0.1)  # Large changes reduce stability
        elif total_change < 0.1:
            self.stability = min(1.0, self.stability + 0.05)  # Stability improves over time
        
        # Record ideology evolution
        if changes:
            self.ideology_history.append({
                'timestamp': datetime.now(),
                'trigger': trigger_event,
                'changes': changes,
                'old_values': old_ideology,
                'new_values': self.ideology.copy()
            })
            self.last_evolution = datetime.now()
        
        return changes
    
    def calculate_strength(self) -> float:
        """
        Calculate overall faction strength/power index.
        
        Returns:
            Power index as a float (higher = more powerful)
        """
        # Base strength from resources
        resource_strength = 0.0
        resource_weights = {
            "gold": 0.001,      # 1 point per 1000 gold
            "influence": 0.5,   # 0.5 points per influence point
            "troops": 1.0,      # 1 point per troop
            "weapons": 0.3,     # Weapons boost military effectiveness
            "faith": 0.2,       # Religious power
            "knowledge": 0.3,   # Information is power
            "connections": 0.4, # Network effects
            "lands": 0.5,       # Territory control
            "stealth": 0.2,     # Covert capabilities
            "popular_support": 0.6  # Mass support
        }
        
        for resource, amount in self.resources.items():
            weight = resource_weights.get(resource, 0.1)  # Default weight for unknown resources
            resource_strength += amount * weight
        
        # Member count bonus
        member_bonus = len(self.members) * 0.5
        
        # Stability modifier
        stability_modifier = 0.5 + (self.stability * 0.5)  # 0.5 to 1.0 multiplier
        
        # Trait bonuses
        trait_bonuses = {
            "militant": 1.2,
            "networked": 1.15,
            "secretive": 1.1,
            "political": 1.25,
            "zealous": 1.1,
            "disciplined": 1.15
        }
        
        trait_multiplier = 1.0
        for trait in self.faction_traits:
            if trait in trait_bonuses:
                trait_multiplier *= trait_bonuses[trait]
        
        # Regional reputation affects local strength
        avg_reputation = sum(self.reputation_map.values()) / max(1, len(self.reputation_map))
        reputation_modifier = 1.0 + (avg_reputation * 0.2)  # -20% to +20%
        
        total_strength = (resource_strength + member_bonus) * stability_modifier * trait_multiplier * reputation_modifier
        
        return max(0.1, total_strength)  # Minimum strength of 0.1
    
    def update_goals(self,
                    completed_goals: Optional[List[str]] = None,
                    failed_goals: Optional[List[str]] = None,
                    new_priorities: Optional[List[str]] = None,
                    rumor_influences: Optional[List[str]] = None) -> List[str]:
        """
        Update faction goals based on success/failure and changing circumstances.
        
        Args:
            completed_goals: Goals that have been achieved
            failed_goals: Goals that have failed or become impossible
            new_priorities: New goals to add
            rumor_influences: Rumors that might influence goal priorities
            
        Returns:
            List of goal changes made
        """
        changes = []
        old_goals = self.goals.copy()
        
        # Remove completed or failed goals
        if completed_goals:
            for goal in completed_goals:
                if goal in self.goals:
                    self.goals.remove(goal)
                    changes.append(f"completed: {goal}")
                    
                    # Success often leads to more ambitious goals
                    if "expand" not in goal.lower() and random.random() < 0.3:
                        expanded_goal = f"expand {goal.split()[-1]} operations"
                        if expanded_goal not in self.goals:
                            self.goals.append(expanded_goal)
                            changes.append(f"new ambitious goal: {expanded_goal}")
        
        if failed_goals:
            for goal in failed_goals:
                if goal in self.goals:
                    self.goals.remove(goal)
                    changes.append(f"abandoned: {goal}")
                    
                    # Failure might lead to revenge or rebuilding goals
                    if random.random() < 0.4:
                        revenge_goal = f"avenge failure of {goal}"
                        if revenge_goal not in self.goals:
                            self.goals.append(revenge_goal)
                            changes.append(f"revenge goal: {revenge_goal}")
        
        # Add new priorities
        if new_priorities:
            for goal in new_priorities:
                if goal not in self.goals:
                    self.goals.append(goal)
                    changes.append(f"new priority: {goal}")
        
        # Rumor-influenced goal shifts
        if rumor_influences:
            for rumor in rumor_influences:
                if "threat" in rumor.lower() or "enemy" in rumor.lower():
                    defense_goal = "strengthen defenses against threats"
                    if defense_goal not in self.goals:
                        self.goals.append(defense_goal)
                        changes.append(f"defensive reaction: {defense_goal}")
                
                elif "opportunity" in rumor.lower() or "weakness" in rumor.lower():
                    exploit_goal = "exploit emerging opportunities"
                    if exploit_goal not in self.goals:
                        self.goals.append(exploit_goal)
                        changes.append(f"opportunistic goal: {exploit_goal}")
        
        # Ideology-driven goal evolution
        if self.ideology.get("violence", 0.5) > 0.7 and random.random() < 0.2:
            aggressive_goals = ["eliminate rivals", "expand through force", "demonstrate strength"]
            for goal in aggressive_goals:
                if goal not in self.goals and random.random() < 0.3:
                    self.goals.append(goal)
                    changes.append(f"violence-driven: {goal}")
        
        if self.ideology.get("progress", 0.5) > 0.7 and random.random() < 0.2:
            progressive_goals = ["modernize operations", "adopt new technologies", "reform outdated practices"]
            for goal in progressive_goals:
                if goal not in self.goals and random.random() < 0.3:
                    self.goals.append(goal)
                    changes.append(f"progress-driven: {goal}")
        
        # Record goal changes
        if changes:
            self.goal_history.append({
                'timestamp': datetime.now(),
                'old_goals': old_goals,
                'new_goals': self.goals.copy(),
                'changes': changes
            })
        
        return changes
    
    def add_member(self, npc_id: str, joining_reason: str = "recruited") -> bool:
        """
        Add a new member to the faction.
        
        Args:
            npc_id: ID of the NPC joining the faction
            joining_reason: Reason for joining
            
        Returns:
            True if successfully added, False if already a member
        """
        if npc_id in self.members:
            return False
        
        self.members.append(npc_id)
        
        # New members might slightly increase activity
        self.activity_level = min(1.0, self.activity_level + 0.05)
        
        # Large membership changes can affect stability
        membership_ratio = len(self.members) / max(1, len(self.members) - 1)
        if membership_ratio > 1.2:  # Rapid growth
            self.stability = max(0.1, self.stability - 0.05)
        
        return True
    
    def remove_member(self, npc_id: str, departure_reason: str = "left") -> bool:
        """
        Remove a member from the faction.
        
        Args:
            npc_id: ID of the NPC leaving the faction
            departure_reason: Reason for leaving
            
        Returns:
            True if successfully removed, False if not a member
        """
        if npc_id not in self.members:
            return False
        
        self.members.remove(npc_id)
        
        # Member loss affects faction stability and activity
        if departure_reason in ["betrayal", "defection", "expelled"]:
            self.stability = max(0.1, self.stability - 0.1)
            # Betrayals might trigger ideology shifts toward authority/loyalty
            self.evolve_ideology("betrayal", evolution_strength=0.15)
        else:
            self.stability = max(0.1, self.stability - 0.05)
        
        self.activity_level = max(0.1, self.activity_level - 0.03)
        
        return True
    
    def get_dominant_traits(self, top_n: int = 3) -> List[str]:
        """
        Get the most prominent ideological traits of the faction.
        
        Args:
            top_n: Number of top traits to return
            
        Returns:
            List of dominant ideological aspects
        """
        # Sort ideology values in descending order
        sorted_ideology = sorted(self.ideology.items(), key=lambda x: x[1], reverse=True)
        return [trait[0] for trait in sorted_ideology[:top_n]]
    
    def get_faction_summary(self) -> str:
        """
        Generate a readable summary of the faction.
        
        Returns:
            String describing the faction's current state
        """
        strength = self.calculate_strength()
        dominant_traits = self.get_dominant_traits(3)
        
        summary_parts = [
            f"{self.name} ({', '.join(self.faction_traits)})",
            f"Base: {self.region_base}",
            f"Members: {len(self.members)}",
            f"Strength: {strength:.1f}",
            f"Stability: {self.stability:.2f}",
            f"Dominant values: {', '.join(dominant_traits)}",
            f"Primary goals: {', '.join(self.goals[:3]) if self.goals else 'None'}"
        ]
        
        return " | ".join(summary_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize faction to dictionary."""
        return {
            'faction_id': self.faction_id,
            'name': self.name,
            'region_base': self.region_base,
            'ideology': self.ideology,
            'goals': self.goals,
            'resources': self.resources,
            'members': self.members,
            'reputation_map': self.reputation_map,
            'faction_traits': self.faction_traits,
            'stability': self.stability,
            'activity_level': self.activity_level,
            'creation_date': self.creation_date.isoformat(),
            'last_evolution': self.last_evolution.isoformat(),
            'ideology_history': [
                {
                    **entry,
                    'timestamp': entry['timestamp'].isoformat()
                } for entry in self.ideology_history
            ],
            'goal_history': [
                {
                    **entry,
                    'timestamp': entry['timestamp'].isoformat()
                } for entry in self.goal_history
            ]
        }


# Test harness
if __name__ == "__main__":
    print("=== Faction Generator Test Harness ===\n")
    
    # Test 1: Create factions with different archetypes
    print("1. Creating factions with different archetypes...")
    
    factions = []
    
    # Religious cult
    cult = Faction.generate_faction(
        name="Order of the Sacred Flame",
        region_base="Shadowmere",
        archetype="religious_cult",
        size_modifier=0.8
    )
    factions.append(cult)
    print(f"Created: {cult.get_faction_summary()}")
    
    # Trade guild
    guild = Faction.generate_faction(
        name="Merchant Consortium of the East",
        region_base="Goldport",
        archetype="trade_guild",
        size_modifier=1.2
    )
    factions.append(guild)
    print(f"Created: {guild.get_faction_summary()}")
    
    # Rebel movement
    rebels = Faction.generate_faction(
        name="Iron Fist Liberation Front",
        region_base="Undercity",
        archetype="rebel_movement",
        size_modifier=1.5
    )
    factions.append(rebels)
    print(f"Created: {rebels.get_faction_summary()}")
    
    # Test 2: Membership changes
    print("\n2. Testing membership changes...")
    
    # Add some members
    member_ids = [f"npc_{i:03d}" for i in range(1, 11)]
    
    for faction in factions:
        initial_members = random.randint(3, 6)
        recruited_members = member_ids[:initial_members]
        member_ids = member_ids[initial_members:]  # Remove used IDs
        
        for member_id in recruited_members:
            faction.add_member(member_id, "recruited")
        
        print(f"{faction.name}: Added {len(recruited_members)} members, strength now {faction.calculate_strength():.1f}")
    
    # Simulate some defections
    print("\nSimulating member departures...")
    
    # Cult loses member to betrayal
    if cult.members:
        betrayer = cult.members[0]
        cult.remove_member(betrayer, "betrayal")
        print(f"{cult.name}: Member {betrayer} betrayed the faction, stability: {cult.stability:.2f}")
    
    # Guild loses member normally
    if guild.members:
        leaver = guild.members[-1]
        guild.remove_member(leaver, "retirement")
        print(f"{guild.name}: Member {leaver} retired, stability: {guild.stability:.2f}")
    
    # Test 3: Ideology evolution
    print("\n3. Testing ideology evolution...")
    
    # Cult experiences persecution
    print(f"\n{cult.name} before persecution:")
    print(f"  Ideology: {cult.get_dominant_traits()}")
    
    changes = cult.evolve_ideology(
        "persecution",
        external_pressure={"violence": 0.2, "authority": -0.1},
        evolution_strength=0.3
    )
    print(f"  Evolution changes: {changes}")
    print(f"  New dominant traits: {cult.get_dominant_traits()}")
    
    # Guild has economic success
    print(f"\n{guild.name} experiences trade boom:")
    print(f"  Ideology before: {guild.get_dominant_traits()}")
    
    changes = guild.evolve_ideology(
        "peaceful_success",
        member_influences={"progress": 0.15, "order": 0.1},
        evolution_strength=0.2
    )
    print(f"  Evolution changes: {changes}")
    print(f"  New dominant traits: {guild.get_dominant_traits()}")
    
    # Rebels face military defeat
    print(f"\n{rebels.name} suffers setback:")
    print(f"  Ideology before: {rebels.get_dominant_traits()}")
    
    changes = rebels.evolve_ideology(
        "military_defeat",
        external_pressure={"violence": -0.1, "authority": -0.2},
        evolution_strength=0.25
    )
    print(f"  Evolution changes: {changes}")
    print(f"  New dominant traits: {rebels.get_dominant_traits()}")
    
    # Test 4: Goal evolution
    print("\n4. Testing goal evolution...")
    
    # Cult completes a goal and faces new challenges
    print(f"\n{cult.name} goal evolution:")
    print(f"  Current goals: {cult.goals}")
    
    goal_changes = cult.update_goals(
        completed_goals=["build temples"],
        new_priorities=["establish inquisition"],
        rumor_influences=["threats from rival faiths"]
    )
    print(f"  Goal changes: {goal_changes}")
    print(f"  Updated goals: {cult.goals}")
    
    # Guild responds to market opportunities
    print(f"\n{guild.name} goal evolution:")
    print(f"  Current goals: {guild.goals}")
    
    goal_changes = guild.update_goals(
        completed_goals=["monopolize trade routes"],
        rumor_influences=["new markets opening in the north", "opportunity for expansion"]
    )
    print(f"  Goal changes: {goal_changes}")
    print(f"  Updated goals: {guild.goals}")
    
    # Test 5: Faction strength comparison
    print("\n5. Final faction comparison...")
    
    print("\nFaction Power Rankings:")
    faction_strengths = [(f, f.calculate_strength()) for f in factions]
    faction_strengths.sort(key=lambda x: x[1], reverse=True)
    
    for i, (faction, strength) in enumerate(faction_strengths, 1):
        print(f"  {i}. {faction.name}: {strength:.1f} power")
        print(f"     Resources: {faction.resources}")
        print(f"     Members: {len(faction.members)}, Stability: {faction.stability:.2f}")
    
    # Test 6: Faction evolution history
    print("\n6. Evolution history summary...")
    
    for faction in factions:
        if faction.ideology_history or faction.goal_history:
            print(f"\n{faction.name} evolution:")
            if faction.ideology_history:
                latest_ideology = faction.ideology_history[-1]
                print(f"  Latest ideology change: {latest_ideology['trigger']}")
                print(f"  Changes: {latest_ideology['changes']}")
            if faction.goal_history:
                latest_goals = faction.goal_history[-1]
                print(f"  Goal changes: {latest_goals['changes']}")
    
    print("\n=== Test Complete ===") 