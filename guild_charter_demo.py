"""
Guild Charter and Administration System - Demonstration Script

This script demonstrates the key features of the Guild Charter System:
1. Creating guild charters for different guild types
2. Evaluating member compliance with charter requirements
3. Processing punishments according to charter policies
4. Applying policy changes to guild charters
5. Integration with existing guild and NPC systems

This serves as both documentation and testing for the charter system.
"""

from datetime import datetime
from guild_charter_system import (
    GuildCharter, 
    generate_default_charter,
    evaluate_guild_policy_compliance,
    evaluate_member_compliance,
    process_guild_punishment,
    PunishmentType
)
from guild_event_engine import LocalGuild, GuildType
from npc_profile import NPCProfile

def demonstrate_charter_creation():
    """Demonstrate creating charters for different guild types."""
    print("=== GUILD CHARTER CREATION DEMONSTRATION ===\n")
    
    # Create different types of guild charters
    guild_types = [
        ("merchants", "Riverside Merchants Guild"),
        ("craftsmen", "Master Artisans Brotherhood"),
        ("scholars", "Academy of Ancient Lore"),
        ("warriors", "Defenders of the Realm")
    ]
    
    charters = {}
    
    for guild_type, guild_name in guild_types:
        print(f"Creating charter for {guild_name} ({guild_type}):")
        
        # Generate default charter
        charter = generate_default_charter(
            guild_id=f"guild_{guild_type}_001",
            guild_type=guild_type,
            guild_name=guild_name
        )
        
        charters[guild_type] = charter
        
        print(f"  Core Doctrine: {charter.core_doctrine}")
        print(f"  Accepted Professions: {', '.join(charter.accepted_professions)}")
        print(f"  Economic Rights: {len([k for k, v in charter.economic_rights.items() if v])} granted")
        print(f"  Punishment Policies: {len(charter.punishment_policy)} offenses defined")
        print()
    
    return charters

def demonstrate_member_compliance_evaluation():
    """Demonstrate evaluating member compliance with charter requirements."""
    print("=== MEMBER COMPLIANCE EVALUATION DEMONSTRATION ===\n")
    
    # Create a sample merchant guild charter
    charter = generate_default_charter(
        guild_id="demo_guild_001",
        guild_type="merchants",
        guild_name="Demo Merchants Guild"
    )
    
    # Create sample NPCs with different compliance levels
    test_npcs = [
        # Compliant member
        NPCProfile(
            name="Honest Marcus",
            age=35,
            region="Riverside",
            personality_traits=["honest", "diplomatic", "pragmatic"],
            reputation_local={"Riverside": 0.6}
        ),
        
        # Low loyalty member
        NPCProfile(
            name="Disloyal Sarah",
            age=28,
            region="Riverside",
            personality_traits=["rebellious", "cunning", "greedy"],
            reputation_local={"Riverside": 0.2}
        ),
        
        # Poor reputation member
        NPCProfile(
            name="Shady Tom",
            age=42,
            region="Riverside",
            personality_traits=["secretive", "aggressive", "greedy"],
            reputation_local={"Riverside": -0.3}
        )
    ]
    
    # Set profession and loyalty for testing
    for npc in test_npcs:
        npc.profession = "merchant"
    
    test_npcs[0].guild_loyalty_score = 0.7  # High loyalty
    test_npcs[1].guild_loyalty_score = 0.1  # Low loyalty
    test_npcs[2].guild_loyalty_score = 0.3  # Medium loyalty but poor reputation
    
    # Evaluate each NPC
    for npc in test_npcs:
        print(f"Evaluating {npc.name}:")
        compliance_report = evaluate_member_compliance(npc, charter)
        
        print(f"  Overall Compliant: {compliance_report['overall_compliant']}")
        print(f"  Compliance Score: {compliance_report['compliance_score']:.2f}")
        
        if compliance_report['violations']:
            print(f"  Violations ({len(compliance_report['violations'])}):")
            for violation in compliance_report['violations']:
                print(f"    - {violation['type']}: {violation['description']} (Severity: {violation['severity']})")
        
        if compliance_report['warnings']:
            print(f"  Warnings ({len(compliance_report['warnings'])}):")
            for warning in compliance_report['warnings']:
                print(f"    - {warning['type']}: {warning['description']}")
        
        if compliance_report['recommended_action']:
            print(f"  Recommended Action: {compliance_report['recommended_action']}")
        
        print()

def demonstrate_punishment_processing():
    """Demonstrate processing punishments according to charter policies."""
    print("=== PUNISHMENT PROCESSING DEMONSTRATION ===\n")
    
    # Create guild with charter
    guild = LocalGuild(
        guild_id="demo_guild_002",
        name="Demo Justice Guild",
        guild_type=GuildType.MERCHANTS,
        base_settlement="Justice Town"
    )
    
    # Assign charter to guild
    guild.charter = generate_default_charter(
        guild_id=guild.guild_id,
        guild_type="merchants",
        guild_name=guild.name
    )
    
    # Create test NPC
    test_npc = NPCProfile(
        name="Guilty Gary",
        age=30,
        region="Justice Town",
        guild_membership=guild.guild_id,
        personality_traits=["impulsive", "greedy"]
    )
    
    test_npc.guild_rank = "journeyman"
    test_npc.guild_loyalty_score = 0.5
    test_npc.reputation_local = {"Justice Town": 0.3}
    
    # Test different offenses and their punishments
    test_offenses = [
        "minor_theft",
        "smuggling", 
        "violence_against_member",
        "charter_violation",
        "treason"
    ]
    
    print(f"Processing punishments for {test_npc.name} in {guild.name}:\n")
    
    for offense in test_offenses:
        print(f"Offense: {offense}")
        
        # Get expected punishment from charter
        expected_punishment = guild.charter.punishment_policy.get(offense, "warning")
        print(f"  Charter Policy: {expected_punishment}")
        
        # Process the punishment (simulate)
        punishment_result = process_guild_punishment(guild, test_npc, offense)
        
        if punishment_result.get('success', False):
            print(f"  Punishment Applied: {punishment_result['punishment_type']}")
            print(f"  Effects: {', '.join(punishment_result['effects'])}")
        else:
            print(f"  Error: {punishment_result.get('error', 'Unknown error')}")
        
        print()

def demonstrate_policy_application():
    """Demonstrate applying policy changes to guild charters."""
    print("=== POLICY APPLICATION DEMONSTRATION ===\n")
    
    # Create guild with charter
    guild = LocalGuild(
        guild_id="demo_guild_003",
        name="Adaptive Merchants Guild",
        guild_type=GuildType.MERCHANTS,
        base_settlement="Policy Town"
    )
    
    guild.charter = generate_default_charter(
        guild_id=guild.guild_id,
        guild_type="merchants",
        guild_name=guild.name
    )
    
    print(f"Initial Charter Settings for {guild.name}:")
    print(f"  Violation Tolerance: {guild.charter.violation_tolerance}")
    print(f"  Min Loyalty Requirement: {guild.charter.membership_requirements['min_loyalty']}")
    print(f"  Smuggling Punishment: {guild.charter.punishment_policy['smuggling']}")
    print(f"  Monopoly Rights: {guild.charter.economic_rights['monopoly_rights']}")
    print()
    
    # Apply various policy changes
    policy_changes = [
        ("violation_tolerance", 0.2, "Make guild stricter"),
        ("membership_min_loyalty", 0.4, "Increase loyalty requirement"),
        ("punishment_smuggling", "blacklist", "Harsher smuggling penalty"),
        ("economic_monopoly_rights", True, "Grant monopoly rights"),
        ("outlaw_status", False, "Ensure guild is not outlawed")
    ]
    
    print("Applying Policy Changes:")
    for policy_key, value, description in policy_changes:
        print(f"  {description}: {policy_key} = {value}")
        guild.apply_policy(policy_key, value)
    
    print()
    print("Updated Charter Settings:")
    print(f"  Violation Tolerance: {guild.charter.violation_tolerance}")
    print(f"  Min Loyalty Requirement: {guild.charter.membership_requirements['min_loyalty']}")
    print(f"  Smuggling Punishment: {guild.charter.punishment_policy['smuggling']}")
    print(f"  Monopoly Rights: {guild.charter.economic_rights['monopoly_rights']}")
    print(f"  Outlawed Status: {guild.charter.is_outlawed}")
    print()

def demonstrate_pc_guild_governance():
    """Demonstrate PC-specific guild governance scenarios."""
    print("=== PC GUILD GOVERNANCE DEMONSTRATION ===\n")
    
    # Simulate PC-founded guild
    pc_guild = LocalGuild(
        guild_id="pc_guild_001",
        name="Player's Trading Company",
        guild_type=GuildType.MERCHANTS,
        base_settlement="Player Town"
    )
    
    # PC must define charter at founding
    pc_guild.charter = generate_default_charter(
        guild_id=pc_guild.guild_id,
        guild_type="merchants",
        guild_name=pc_guild.name
    )
    
    print(f"PC-Founded Guild: {pc_guild.name}")
    print(f"Charter Required: Yes")
    print(f"Core Doctrine: {pc_guild.charter.core_doctrine}")
    print()
    
    # Simulate charter amendment proposal
    print("Charter Amendment Scenario:")
    print("  PC proposes to change core doctrine")
    print("  Amendment Type: Doctrine Change")
    print("  Support Required: 75% of masters")
    print("  Current Masters: 5")
    print("  Votes Needed: 4")
    print()
    
    # Simulate PC charter violation
    print("PC Charter Violation Scenario:")
    print("  PC commits smuggling offense")
    print("  Charter Policy: expulsion")
    print("  Consequences:")
    print("    - PC subject to same punishment as NPCs")
    print("    - No special exemptions for leadership")
    print("    - Guild stability may decrease if members disagree")
    print("    - Potential for rebellion if PC tries to override")
    print()
    
    # Simulate unjust charter override attempt
    print("Unjust Charter Override Scenario:")
    print("  PC attempts to punish member without charter justification")
    print("  Potential Consequences:")
    print("    - Member loyalty decreases")
    print("    - Risk of rebellion from loyal members")
    print("    - Possible splinter chapter formation")
    print("    - Guild stability and reputation damage")
    print()

def demonstrate_integration_hooks():
    """Demonstrate integration with other game systems."""
    print("=== SYSTEM INTEGRATION DEMONSTRATION ===\n")
    
    # Create guild and member for integration testing
    guild = LocalGuild(
        guild_id="integration_guild_001",
        name="Integrated Systems Guild",
        guild_type=GuildType.CRAFTSMEN
    )
    
    guild.charter = generate_default_charter(
        guild_id=guild.guild_id,
        guild_type="craftsmen",
        guild_name=guild.name
    )
    
    violating_member = NPCProfile(
        name="Integration Testie",
        age=25,
        region="Integration City",
        guild_membership=guild.guild_id
    )
    
    violating_member.guild_loyalty_score = -0.2  # Disloyal
    violating_member.reputation_local = {"Integration City": -0.1}
    
    print("Integration with Other Systems:")
    print()
    
    # Reputation System Integration
    print("1. Reputation System Integration:")
    print("   - Charter violations affect internal guild reputation")
    print("   - Repeated violations damage external reputation")
    print("   - Fair enforcement improves guild stability")
    print(f"   Example: {violating_member.name} has poor reputation ({violating_member.reputation_local})")
    print()
    
    # Faction Integration
    print("2. Faction Integration:")
    print("   - Factions can ban or subsidize guilds based on charters")
    print("   - Political alignment affects faction relationships")
    print("   - Outlawed status impacts guild operations")
    print(f"   Example: Guild political alignment: {guild.charter.political_alignment}")
    print()
    
    # Rumor Engine Integration
    print("3. Rumor Engine Integration:")
    print("   - Charter violations can spread via gossip")
    print("   - Punishment events generate rumors")
    print("   - Unfair enforcement creates negative rumors")
    print("   Example: News of punishment spreads through settlement")
    print()
    
    # Memory Core Integration
    print("4. Memory Core Integration:")
    print("   - NPCs remember internal injustices or unfair trials")
    print("   - Punishment history affects future behavior")
    print("   - Charter enforcement impacts NPC personality development")
    print(f"   Example: {violating_member.name} will remember any punishment")
    print()

def run_full_demonstration():
    """Run the complete guild charter system demonstration."""
    print("GUILD CHARTER AND ADMINISTRATION SYSTEM DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Run all demonstration functions
    demonstrate_charter_creation()
    demonstrate_member_compliance_evaluation()
    demonstrate_punishment_processing()
    demonstrate_policy_application()
    demonstrate_pc_guild_governance()
    demonstrate_integration_hooks()
    
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("The Guild Charter System provides:")
    print("- Consistent internal governance for all guilds")
    print("- Fair and equal treatment of NPCs and PCs")
    print("- Rich consequences for charter violations")
    print("- Deep integration with existing game systems")
    print("- Realistic organizational behavior and politics")

if __name__ == "__main__":
    run_full_demonstration() 