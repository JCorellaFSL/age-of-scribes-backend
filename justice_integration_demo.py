#!/usr/bin/env python3
"""
Justice System Integration Demo

Demonstrates how the justice system integrates with the existing
memory, rumor, reputation, and NPC systems.
"""

import sys
from datetime import datetime, timedelta

# Import existing systems
from memory_core import MemoryNode, MemoryBank
from rumor_engine import Rumor, RumorNetwork
from reputation_tracker import ReputationEngine
from justice_system import JusticeEngine, JusticeCase


def main():
    print("=== Justice System Integration Demo ===\n")
    
    # Initialize all systems
    print("1. Initializing integrated systems...")
    memory_bank = MemoryBank("justice_system")  # Provide required owner_id
    rumor_network = RumorNetwork()
    reputation_engine = ReputationEngine()
    justice_engine = JusticeEngine()
    
    # Create some NPCs with reputations
    npcs = ["merchant_alice", "guard_bob", "thief_charlie", "noble_diana"]
    for npc in npcs:
        # Set some baseline reputations (ReputationEngine creates entities automatically)
        reputation_engine.update_reputation(npc, region="Capital", delta=0.1)
        reputation_engine.update_reputation(npc, faction="citizens", delta=0.0)
    
    print("Systems initialized with 4 NPCs")
    
    # Create a crime memory
    print("\n2. Creating a witnessed crime...")
    crime_memory = MemoryNode(
        description="Saw thief_charlie pickpocket merchant_alice's purse at the market",
        location="Capital_Market",
        actor_ids=["thief_charlie", "merchant_alice", "guard_bob"],
        context_tags=["theft", "witnessed", "crime", "market"]
    )
    
    # Add memory to bank
    memory_bank.add_memory(crime_memory)
    print(f"Crime memory created: {crime_memory.event_id}")
    print(f"Description: {crime_memory.description}")
    print(f"Actors: {crime_memory.actor_ids}")
    print(f"Initial strength: {crime_memory.strength:.3f}")
    
    # Create case from memory
    print("\n3. Creating justice case from memory...")
    case = justice_engine.create_case_from_memory(
        crime_memory,
        accused_id="thief_charlie",
        region="Capital"
    )
    
    print(f"Case created: {case.case_id}")
    print(f"Crime type: {case.crime_type}")
    print(f"Evidence strength: {case.evidence_strength:.3f}")
    print(f"Witnesses: {case.witness_ids}")
    
    # Meanwhile, create a rumor about the crime
    print("\n4. Creating rumor about the incident...")
    rumor = Rumor(
        source_memory=crime_memory,
        originator_id="guard_bob",
        content="I heard that thief_charlie has been stealing from merchants in broad daylight",
        location_origin="Capital_Market"
    )
    
    rumor_network.active_rumors.append(rumor)  # Add directly to active rumors list
    print(f"Rumor created: {rumor.rumor_id}")
    print(f"Content: {rumor.content}")
    print(f"Confidence: {rumor.confidence_level:.3f}")
    
    # Add rumor evidence to case
    print("\n5. Adding rumor as supporting evidence...")
    case.add_evidence(
        evidence_source=f"rumor_{rumor.rumor_id}",
        strength_delta=0.15,
        notes=f"Corroborating rumor: {rumor.content[:50]}..."
    )
    
    print(f"Updated evidence strength: {case.evidence_strength:.3f}")
    
    # Check reputations before case resolution
    print("\n6. Pre-trial reputations...")
    for npc in npcs:
        reputation = reputation_engine.get_reputation(npc, region="Capital")
        print(f"  {npc}: {reputation:.3f} in Capital")
    
    # Resolve the case
    print("\n7. Resolving case in Capital (law-abiding region)...")
    
    # Create witness credibility map based on reputation
    witness_credibility = {}
    for witness_id in case.witness_ids:
        reputation = reputation_engine.get_reputation(witness_id, region="Capital")
        # Convert reputation (-1 to 1) to credibility (0 to 1)
        credibility = (reputation + 1.0) / 2.0
        credibility = max(0.1, min(0.9, credibility))  # Clamp between 0.1 and 0.9
        witness_credibility[witness_id] = credibility
    
    print(f"Witness credibility: {witness_credibility}")
    
    resolution = justice_engine.resolve_case(
        case.case_id,
        region_profile="law_abiding_city",
        judge_id="judge_stern",
        witness_credibility_map=witness_credibility
    )
    
    print(f"Verdict: {resolution['verdict']}")
    print(f"Guilt probability: {resolution['guilt_probability']:.3f}")
    print(f"Judge: {resolution['judge_id']}")
    
    # Apply punishment
    print("\n8. Applying punishment...")
    punishment = justice_engine.apply_case_punishment(
        case.case_id,
        reputation_engine,
        "law_abiding_city"
    )
    
    print(f"Punishments applied: {punishment['punishments_applied']}")
    print(f"Reputation changes: {punishment['reputation_changes']}")
    print(f"Faction impacts: {punishment['faction_impacts']}")
    
    # Check post-trial reputations
    print("\n9. Post-trial reputations...")
    for npc in npcs:
        reputation = reputation_engine.get_reputation(npc, region="Capital")
        print(f"  {npc}: {reputation:.3f} in Capital")
    
    # Show justice system statistics
    print("\n10. Justice system summary...")
    stats = justice_engine.get_case_statistics()
    print(f"Total cases: {stats['total_cases']}")
    print(f"Conviction rate: {stats['conviction_rate']:.1%}")
    print(f"Cases by type: {stats['by_crime_type']}")
    
    # Create a rumor about the trial outcome
    print("\n11. Creating post-trial rumor...")
    if "guilty" in case.verdict:
        trial_rumor_content = f"Justice was served! {case.accused_id} was found {case.verdict} of {case.crime_type}"
    else:
        trial_rumor_content = f"{case.accused_id} walked free from the {case.crime_type} charges"
    
    trial_rumor = Rumor(
        source_memory=crime_memory,
        originator_id="judge_stern",
        content=trial_rumor_content,
        location_origin="Capital_Courthouse"
    )
    
    rumor_network.active_rumors.append(trial_rumor)
    print(f"Trial outcome rumor: {trial_rumor.content}")
    
    # Show how memories can decay over time, affecting future cases
    print("\n12. Demonstrating memory decay impact...")
    print(f"Current memory strength: {crime_memory.strength:.3f}")
    
    # Fast-forward time
    crime_memory.timestamp = datetime.now() - timedelta(days=30)
    crime_memory.decay()
    
    print(f"Memory strength after 30 days: {crime_memory.strength:.3f}")
    print("Future cases based on this memory would have weaker evidence")
    
    print("\n=== Integration Demo Complete ===")
    print("\nThe justice system successfully integrates with:")
    print("- Memory system: Cases created from flagged memories")
    print("- Rumor system: Evidence from rumors, outcomes create new rumors")
    print("- Reputation system: Witness credibility, punishment application")
    print("- NPC system: All entities tracked consistently across systems")


if __name__ == "__main__":
    main() 