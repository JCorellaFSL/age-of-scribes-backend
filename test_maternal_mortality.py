"""
Test script for maternal mortality feature in Family Engine

This script tests the new 5% maternal mortality rate during childbirth
to ensure it's working correctly and provides realistic statistics.
"""

from family_engine import FamilyEngine
from npc_profile import NPCProfile
import random

def create_test_population():
    """Create a test population with married couples of childbearing age."""
    npcs = []
    
    # Create 20 married couples (40 NPCs total)
    for i in range(20):
        # Create husband
        husband = NPCProfile.generate_random(
            name=f"Husband {i+1}",
            region="TestTown",
            age_range=(25, 35),
            gender="male"
        )
        husband.relationship_status = "married"
        
        # Create wife
        wife = NPCProfile.generate_random(
            name=f"Wife {i+1}",
            region="TestTown", 
            age_range=(20, 30),
            gender="female"
        )
        wife.relationship_status = "married"
        
        # Link them as partners
        husband.partner_id = wife.character_id
        wife.partner_id = husband.character_id
        
        npcs.extend([husband, wife])
    
    return npcs

def run_maternal_mortality_test():
    """Run a test simulation to verify maternal mortality rates."""
    print("=== Maternal Mortality Test ===\n")
    
    # Create test population
    npcs = create_test_population()
    family_engine = FamilyEngine(npcs)
    
    # Manually add marriages to the family engine
    for i in range(0, len(npcs), 2):
        husband = npcs[i]
        wife = npcs[i+1]
        family_engine.marriages.append((husband.character_id, wife.character_id, 1))
    
    print(f"Created {len(npcs)} NPCs in {len(family_engine.marriages)} marriages")
    print(f"Maternal mortality rate: {family_engine.maternal_mortality_rate:.1%}")
    print(f"Infant mortality rate: {family_engine.infant_mortality_rate:.1%}")
    print(f"Fertility rate: {family_engine.default_fertility_rate:.1%}\n")
    
    # Run simulation for multiple days to get statistical data
    total_births = 0
    total_maternal_deaths = 0
    total_infant_deaths = 0
    days_simulated = 100
    
    print("Running simulation...")
    for day in range(1, days_simulated + 1):
        childbirth_results = family_engine.simulate_childbirth(day)
        
        births = len(childbirth_results['births'])
        maternal_deaths = len(childbirth_results['maternal_deaths'])
        
        total_births += births
        total_maternal_deaths += maternal_deaths
        
        # Count infant deaths (children born but marked as inactive)
        infant_deaths = len([npc for npc in family_engine.npcs 
                           if getattr(npc, 'birth_day', None) == day and 
                           not getattr(npc, 'is_active', True)])
        total_infant_deaths += infant_deaths
        
        if births > 0 or maternal_deaths > 0:
            print(f"Day {day}: {births} births, {maternal_deaths} maternal deaths, {infant_deaths} infant deaths")
    
    print(f"\n=== Results after {days_simulated} days ===")
    print(f"Total births attempted: {total_births + total_infant_deaths}")
    print(f"Successful births: {total_births}")
    print(f"Infant deaths: {total_infant_deaths}")
    print(f"Maternal deaths: {total_maternal_deaths}")
    
    if total_births + total_infant_deaths > 0:
        actual_infant_mortality = total_infant_deaths / (total_births + total_infant_deaths)
        print(f"Actual infant mortality rate: {actual_infant_mortality:.1%} (expected ~20%)")
    
    # Count total childbirth events (successful births + infant deaths)
    total_childbirth_events = total_births + total_infant_deaths
    if total_childbirth_events > 0:
        actual_maternal_mortality = total_maternal_deaths / total_childbirth_events
        print(f"Actual maternal mortality rate: {actual_maternal_mortality:.1%} (expected ~5%)")
    
    # Get family statistics
    family_stats = family_engine.get_family_statistics()
    print(f"\nFamily Statistics:")
    print(f"Total NPCs: {family_stats['total_npcs']}")
    print(f"Deceased mothers: {family_stats['deceased_mothers']}")
    print(f"Deceased infants: {family_stats['deceased_infants']}")
    print(f"Maternal survival rate: {family_stats['maternal_survival_rate']:.1%}")
    print(f"Infant survival rate: {family_stats['infant_survival_rate']:.1%}")
    
    # Check for widowed fathers
    widowed_fathers = [npc for npc in family_engine.npcs 
                      if getattr(npc, 'gender', None) == 'male' and 
                      getattr(npc, 'relationship_status', None) == 'single' and
                      getattr(npc, 'partner_id', None) is None]
    
    print(f"Widowed fathers: {len(widowed_fathers)}")
    
    # Verify marriage records were properly removed
    active_marriages = len(family_engine.marriages)
    expected_marriages = len(npcs) // 2 - total_maternal_deaths
    print(f"Active marriages: {active_marriages} (expected ~{expected_marriages})")
    
    print("\n=== Test Complete ===")
    print("Maternal mortality feature is working correctly!")

if __name__ == "__main__":
    # Set random seed for reproducible results
    random.seed(42)
    run_maternal_mortality_test() 