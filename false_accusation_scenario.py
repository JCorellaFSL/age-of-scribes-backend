#!/usr/bin/env python3
"""
False Accusation Scenario Simulation

Demonstrates how the integrated backend systems handle a complex
scenario where the player character is falsely accused of arson.
"""

import random
from datetime import datetime, timedelta
from memory_core import MemoryNode, MemoryBank
from rumor_engine import Rumor, RumorNetwork
from reputation_tracker import ReputationEngine
from justice_system import JusticeEngine, JusticeCase
from npc_profile import NPCProfile
from faction_generator import Faction


def simulate_false_accusation_scenario():
    print("=== False Accusation Scenario: Ranch Fire ===\n")
    
    # Initialize all systems
    print("*** Initializing Greendale Township systems...")
    memory_banks = {}
    rumor_network = RumorNetwork()
    reputation_engine = ReputationEngine()
    justice_engine = JusticeEngine()
    
    # Create key NPCs
    npcs = {
        "player": "traveling_merchant_hero",
        "rancher": "old_mcdonalds",
        "sheriff": "sheriff_justice",
        "witness1": "farmer_jenkins", 
        "witness2": "tavern_keeper_mabel",
        "gossip": "seamstress_betty",
        "judge": "magistrate_stern"
    }
    
    # Initialize NPC memory banks and reputations
    for role, npc_id in npcs.items():
        memory_banks[npc_id] = MemoryBank(npc_id)
        reputation_engine.update_reputation(npc_id, region="Greendale", delta=0.0)
        if role != "player":  # NPCs start with slight positive reputation
            reputation_engine.update_reputation(npc_id, region="Greendale", delta=0.2)
    
    # Player starts as unknown outsider
    reputation_engine.update_reputation(npcs["player"], region="Greendale", delta=-0.1)
    print(f">>> Systems initialized with {len(npcs)} characters")
    
    # === MORNING: Player arrives in town ===
    print(f"\n*** DAWN - {npcs['player']} arrives in Greendale...")
    
    arrival_memory = MemoryNode(
        description=f"Stranger {npcs['player']} rode into town just after dawn, looking travel-worn",
        location="Greendale_TownSquare",
        actor_ids=[npcs["player"], npcs["witness2"]],  # Tavern keeper saw arrival
        context_tags=["arrival", "stranger", "witnessed", "early_morning"]
    )
    memory_banks[npcs["witness2"]].add_memory(arrival_memory)
    
    # === DISASTER: Ranch fire breaks out ===
    print(f"\n*** MORNING - {npcs['rancher']}'s ranch catches fire!")
    
    # Multiple witnesses create memories of the fire
    fire_memory_rancher = MemoryNode(
        description=f"My ranch burned to the ground! Lost everything - barn, animals, crops!",
        location="Greendale_RanchRoad",
        actor_ids=[npcs["rancher"], npcs["witness1"]],  # Neighbor farmer helped fight fire
        context_tags=["fire", "arson", "disaster", "property_loss", "witnessed"]
    )
    memory_banks[npcs["rancher"]].add_memory(fire_memory_rancher)
    
    fire_memory_witness = MemoryNode(
        description=f"Helped {npcs['rancher']} fight the terrible fire at his ranch. Whole place went up fast",
        location="Greendale_RanchRoad", 
        actor_ids=[npcs["rancher"], npcs["witness1"]],
        context_tags=["fire", "disaster", "heroic", "neighbor_help"]
    )
    memory_banks[npcs["witness1"]].add_memory(fire_memory_witness)
    
    print(f"   > Fire memories created - Rancher (strength: {fire_memory_rancher.strength:.2f})")
    print(f"   > Witness memories created - Farmer (strength: {fire_memory_witness.strength:.2f})")
    
    # === SUSPICION: Someone connects the timing ===
    print(f"\n*** MIDDAY - Suspicious connections made...")
    
    # Gossip NPC notices the timing coincidence
    suspicion_memory = MemoryNode(
        description=f"Strange how {npcs['player']} showed up the same morning {npcs['rancher']}'s ranch burned down",
        location="Greendale_TownSquare",
        actor_ids=[npcs["player"], npcs["rancher"], npcs["gossip"]],
        context_tags=["suspicion", "coincidence", "stranger", "fire", "timing"]
    )
    memory_banks[npcs["gossip"]].add_memory(suspicion_memory)
    
    print(f"   > Suspicion memory created by {npcs['gossip']} (strength: {suspicion_memory.strength:.2f})")
    
    # === RUMOR PHASE: Accusations spread ===
    print(f"\n*** AFTERNOON - Rumors begin spreading...")
    
    # Create initial accusation rumor
    accusation_rumor = Rumor(
        content=f"I bet that stranger {npcs['player']} had something to do with {npcs['rancher']}'s fire. Too convenient!",
        originator_id=npcs["gossip"],
        location_origin="Greendale_TownSquare",
        source_memory=suspicion_memory,
        confidence_level=0.4  # Initial uncertainty
    )
    rumor_network.active_rumors.append(accusation_rumor)
    
    # Rumor spreads and mutates
    print(f"   > Original rumor: '{accusation_rumor.content[:60]}...'")
    print(f"   > Initial confidence: {accusation_rumor.confidence_level:.2f}")
    
    # Simulate rumor spreading to other NPCs
    spread_targets = [npcs["witness2"], npcs["sheriff"], npcs["witness1"]]
    for i, target in enumerate(spread_targets):
        spread_rumor = accusation_rumor.spread(
            spreader_id=list(accusation_rumor.heard_by)[0] if accusation_rumor.heard_by else npcs["gossip"],
            target_id=target,
            mutation_chance=0.3
        )
        rumor_network.active_rumors.append(spread_rumor)
        print(f"   > Spread to {target}: '{spread_rumor.content[:60]}...' (conf: {spread_rumor.confidence_level:.2f})")
    
    # === REPUTATION IMPACT: Word gets around ===
    print(f"\n*** REPUTATION IMPACT - Player's standing damaged...")
    
    initial_rep = reputation_engine.get_reputation(npcs["player"], region="Greendale")
    print(f"   Before rumors: {initial_rep:.3f}")
    
    # Process rumor effects on reputation
    for rumor in rumor_network.active_rumors:
        if npcs["player"] in rumor.content:
            # Negative rumor impacts reputation
            reputation_engine.update_reputation(
                npcs["player"], 
                region="Greendale", 
                delta=-0.15,
                reason="suspected_of_arson"
            )
    
    post_rumor_rep = reputation_engine.get_reputation(npcs["player"], region="Greendale")
    print(f"   After rumors: {post_rumor_rep:.3f} (Change: {post_rumor_rep - initial_rep:+.3f})")
    
    # === LEGAL CASE: Sheriff investigates ===
    print(f"\n*** EVENING - {npcs['sheriff']} opens investigation...")
    
    # Create case from the strongest memories and rumors
    case = justice_engine.create_case_from_memory(
        fire_memory_rancher,
        accused_id=npcs["player"],
        region="Greendale",
        crime_type="arson"
    )
    
    print(f"   > Case opened: {case.case_id}")
    print(f"   > Crime type: {case.crime_type}")
    print(f"   > Initial evidence strength: {case.evidence_strength:.3f}")
    print(f"   > Witnesses: {case.witness_ids}")
    
    # Add rumor evidence (makes case stronger but less reliable)
    case.add_evidence(
        evidence_source=f"rumor_{accusation_rumor.rumor_id}",
        strength_delta=0.2,
        notes="Multiple townspeople reporting suspicious timing of arrival"
    )
    
    print(f"   > Evidence after rumors: {case.evidence_strength:.3f}")
    
    # === TRIAL PREPARATION: Witness credibility assessment ===
    print(f"\n*** PRE-TRIAL - Assessing witness credibility...")
    
    witness_credibility = {}
    for witness_id in case.witness_ids:
        reputation = reputation_engine.get_reputation(witness_id, region="Greendale")
        credibility = (reputation + 1.0) / 2.0  # Convert -1,1 to 0,1
        credibility = max(0.1, min(0.9, credibility))
        witness_credibility[witness_id] = credibility
        print(f"   > {witness_id}: reputation {reputation:.3f} -> credibility {credibility:.3f}")
    
    # === TRIAL: Justice system in action ===
    print(f"\n*** TRIAL DAY - Case goes before {npcs['judge']}...")
    
    # Greendale is a small farming town - law-abiding but suspicious of outsiders
    resolution = justice_engine.resolve_case(
        case.case_id,
        region_profile="law_abiding_city",
        judge_id=npcs["judge"],
        witness_credibility_map=witness_credibility
    )
    
    print(f"   > Verdict: {resolution['verdict'].upper()}")
    print(f"   > Guilt probability: {resolution['guilt_probability']:.1%}")
    print(f"   > Judge: {resolution['judge_id']}")
    
    # Show the evaluation breakdown
    evaluation = resolution['evaluation']
    print(f"\n   >>> TRIAL BREAKDOWN:")
    print(f"      Evidence strength: {evaluation['evidence_strength']:.3f}")
    print(f"      Witness factor: {evaluation['witness_factor']:.3f}")
    print(f"      Final probability: {evaluation['final_guilt_probability']:.3f}")
    print(f"      Recommended action: {evaluation['recommended_action']}")
    
    # === PUNISHMENT: Consequences applied ===
    print(f"\n*** SENTENCING - Applying consequences...")
    
    punishment = justice_engine.apply_case_punishment(
        case.case_id,
        reputation_engine,
        "law_abiding_city"
    )
    
    print(f"   > Punishments: {punishment['punishments_applied']}")
    print(f"   > Reputation changes: {punishment['reputation_changes']}")
    print(f"   > Faction impacts: {punishment['faction_impacts']}")
    
    # === AFTERMATH: Long-term consequences ===
    print(f"\n*** AFTERMATH - Measuring the damage...")
    
    final_rep = reputation_engine.get_reputation(npcs["player"], region="Greendale")
    total_rep_change = final_rep - initial_rep
    
    print(f"   >>> REPUTATION JOURNEY:")
    print(f"      Starting: {initial_rep:.3f} (unknown outsider)")
    print(f"      After rumors: {post_rumor_rep:.3f}")
    print(f"      After trial: {final_rep:.3f}")
    print(f"      Total change: {total_rep_change:+.3f}")
    
    # Create post-trial rumor about the outcome
    if "guilty" in case.verdict:
        outcome_rumor_content = f"Justice served! That stranger {npcs['player']} got what they deserved for burning down {npcs['rancher']}'s ranch"
        reputation_descriptor = "Criminal"
    else:
        outcome_rumor_content = f"Can you believe {npcs['player']} walked free? I still think they had something to do with that fire"
        reputation_descriptor = "Suspicious stranger"
    
    outcome_rumor = Rumor(
        content=outcome_rumor_content,
        originator_id=npcs["gossip"],
        location_origin="Greendale_Courthouse",
        confidence_level=0.8
    )
    rumor_network.active_rumors.append(outcome_rumor)
    
    # === SOCIAL DYNAMICS: How different NPCs react ===
    print(f"\n*** SOCIAL DYNAMICS - How the town sees you now...")
    
    npc_reactions = {
        npcs["rancher"]: "Vengeful - wants compensation regardless of verdict",
        npcs["sheriff"]: "Watchful - will keep an eye on you",
        npcs["witness1"]: "Neutral - focused on helping his neighbor recover", 
        npcs["witness2"]: "Cautious - might refuse service if reputation too low",
        npcs["gossip"]: "Vindicated - feels proven right about suspicions",
        npcs["judge"]: "Professional - judgment based on evidence presented"
    }
    
    for npc_id, reaction in npc_reactions.items():
        npc_rep = reputation_engine.get_reputation(npc_id, region="Greendale")
        print(f"   > {npc_id}: {reaction}")
    
    # === FUTURE IMPLICATIONS ===
    print(f"\n*** FUTURE IMPLICATIONS...")
    
    print(f"   > COMMERCE: Merchants may charge higher prices (rep: {final_rep:.3f})")
    print(f"   > LODGING: Inn keeper might refuse room if reputation < -0.3")
    print(f"   > QUESTS: NPCs less likely to trust you with important tasks")
    print(f"   > LAW: Any future legal troubles will be viewed more harshly")
    print(f"   > RUMORS: New rumors about you will spread faster and be believed more easily")
    
    if "guilty" in case.verdict:
        print(f"   > EXILE EFFECTS: Reputation damaged in neighboring regions too")
        print(f"   > FACTION STANDING: Law enforcement groups now hostile")
        print(f"   > COMPENSATION: May owe damages to {npcs['rancher']}")
    else:
        print(f"   > REDEMPTION PATH: Good deeds could slowly rebuild reputation")
        print(f"   > SUSPICION LINGERS: Many still doubt your innocence")
        print(f"   > CASE RECORD: Acquittal doesn't erase the accusation")
    
    # Show final justice system stats
    print(f"\n*** JUSTICE SYSTEM STATISTICS:")
    stats = justice_engine.get_case_statistics()
    print(f"   Cases processed: {stats['total_cases']}")
    print(f"   Conviction rate: {stats['conviction_rate']:.1%}")
    print(f"   Cases by type: {stats['by_crime_type']}")
    
    print(f"\n=== Scenario Complete ===")
    print(f"KEY INSIGHT: Even false accusations have lasting consequences")
    print(f"   in a social system with interconnected memory, rumors, and reputation!")


if __name__ == "__main__":
    simulate_false_accusation_scenario() 