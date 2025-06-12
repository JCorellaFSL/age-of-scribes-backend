"""
Master Workplace System Demonstration

This script demonstrates the MasterWorkplace system's integration with guild hiring
mechanics, showing economic scaling, moral profiles, and labor oversight in action.

Usage: python master_workplace_demo.py
"""

from master_workplace import MasterWorkplace, MasterWorkplaceManager
from npc_profile import NPCProfile
from guild_registry import GuildRegistry
import random

def create_mock_settlement():
    """Create a mock settlement object for testing."""
    class MockSettlement:
        def __init__(self):
            self.economic_prosperity = random.uniform(0.3, 0.9)
            self.stability_score = random.uniform(40, 90)
            
            # Mock resources
            class MockResource:
                def __init__(self):
                    self.stockpile = random.uniform(50, 200)
            
            self.resources = {
                'food': MockResource(),
                'ore': MockResource(),
                'cloth': MockResource(),
                'wood': MockResource()
            }
    
    return MockSettlement()

def generate_moral_profile():
    """Generate a random moral profile for testing."""
    return {
        "bribable": random.uniform(0.1, 0.9),
        "rigid": random.uniform(0.1, 0.9),
        "pragmatic": random.uniform(0.1, 0.9)
    }

def main():
    print("=== Master Workplace System Demonstration ===\n")
    
    # Initialize systems
    guild_registry = GuildRegistry()
    workplace_manager = MasterWorkplaceManager()
    settlement = create_mock_settlement()
    
    print(f"Settlement Economic Prosperity: {settlement.economic_prosperity:.2f}")
    print(f"Settlement Stability Score: {settlement.stability_score:.1f}\n")
    
    # Create master craftsmen NPCs
    masters = []
    for i in range(5):
        master = NPCProfile.generate_random(
            name=f"Master Craftsman {i+1}",
            region="Riverside",
            age_range=(35, 55),  # Masters are typically older
            assign_guild=True
        )
        masters.append(master)
        print(f"Created {master.name}: {master.get_profession_summary()}")
    
    print("\n=== Creating Master Workplaces ===")
    
    # Create workplaces for each master
    workplaces = []
    for master in masters:
        moral_profile = generate_moral_profile()
        
        workplace = workplace_manager.create_workplace(
            owner_id=master.character_id,
            guild_id=master.guild_id or "smithing_guild",  # Default to smithing
            economic_score=settlement.economic_prosperity,
            moral_profile=moral_profile
        )
        workplaces.append(workplace)
        
        print(f"\n{master.name}'s Workplace:")
        print(f"  Guild: {workplace.guild_id}")
        print(f"  Economic Score: {workplace.economic_score:.2f}")
        print(f"  Moral Profile: Bribable={moral_profile['bribable']:.2f}, "
              f"Rigid={moral_profile['rigid']:.2f}, Pragmatic={moral_profile['pragmatic']:.2f}")
        print(f"  Initial Capacity: {workplace.max_journeymen} journeymen, {workplace.max_apprentices} apprentices")
    
    print("\n=== Updating Hiring Capacities ===")
    
    # Simulate guild member data
    guild_members = {
        "smithing_guild": [f"member_{i}" for i in range(15)],
        "textile_guild": [f"member_{i}" for i in range(12)],
        "woodworking_guild": [f"member_{i}" for i in range(8)]
    }
    
    # Update all workplace capacities
    workplace_manager.update_all_capacities(settlement, guild_members)
    
    for i, workplace in enumerate(workplaces):
        master = masters[i]
        print(f"\n{master.name}'s Updated Workplace:")
        print(f"  Updated Capacity: {workplace.max_journeymen} journeymen, {workplace.max_apprentices} apprentices")
        print(f"  Guild Saturation: {workplace._guild_saturation_cache:.2f}")
    
    print("\n=== Simulating Hiring ===")
    
    # Create some worker NPCs
    workers = []
    for i in range(15):
        worker = NPCProfile.generate_random(
            name=f"Worker {i+1}",
            region="Riverside",
            age_range=(16, 30),
            assign_guild=True
        )
        workers.append(worker)
    
    # Simulate hiring process
    for workplace in workplaces:
        master = next(m for m in masters if m.character_id == workplace.owner_id)
        print(f"\n{master.name} is hiring:")
        
        # Try to hire some workers
        hired_count = 0
        for worker in workers[:8]:  # Try first 8 workers
            if hired_count >= 3:  # Limit hiring for demo
                break
                
            # Determine position type based on worker age
            position_type = "apprentice" if worker.age < 20 else "journeyman"
            
            if workplace.can_hire(position_type + "s"):  # Note: method expects plural
                if workplace.hire_employee(worker.character_id, position_type):
                    print(f"  Hired {worker.name} as {position_type}")
                    hired_count += 1
        
        available = workplace.get_available_positions()
        print(f"  Remaining positions: {available['journeymen']} journeymen, {available['apprentices']} apprentices")
    
    print("\n=== Evaluating Labor Flags ===")
    
    # Create mock relationship data
    npc_relationships = {}
    for master in masters:
        master_relationships = {}
        for worker in workers:
            # Some workers have high trust (family/allies), others don't
            trust_level = random.uniform(-0.5, 1.0)
            master_relationships[worker.character_id] = trust_level
        npc_relationships[master.character_id] = master_relationships
    
    # Simulate some overhiring for demonstration
    if workplaces:
        workplace = workplaces[0]
        master = masters[0]
        
        # Force overhiring to trigger abuse flag
        for i in range(5):
            fake_worker_id = f"fake_worker_{i}"
            workplace.employed_apprentices.append(fake_worker_id)
        
        print(f"\nForced overhiring at {master.name}'s workplace for demonstration")
    
    # Evaluate flags for all workplaces
    workplace_manager.evaluate_all_flags(npc_relationships)
    
    for i, workplace in enumerate(workplaces):
        master = masters[i]
        stats = workplace.get_employment_statistics()
        
        print(f"\n{master.name}'s Labor Oversight:")
        print(f"  Abuse Detected: {workplace.labor_flags['abuse_detected']}")
        print(f"  Favoritism: {workplace.labor_flags['favoritism']}")
        print(f"  Audit Risk: {workplace.labor_flags['audit_risk']}")
        print(f"  Utilization Rate: {stats['utilization']['total_rate']:.1%}")
    
    print("\n=== Manager Statistics ===")
    
    manager_stats = workplace_manager.get_manager_statistics()
    print(f"Total Workplaces: {manager_stats['total_workplaces']}")
    print(f"Guild Distribution: {manager_stats['guild_distribution']}")
    print(f"Employment Capacity: {manager_stats['employment_capacity']}")
    print(f"Current Employment: {manager_stats['current_employment']}")
    print(f"Utilization Rates: Journeymen {manager_stats['utilization_rates']['journeymen']:.1%}, "
          f"Apprentices {manager_stats['utilization_rates']['apprentices']:.1%}")
    print(f"Labor Violations: {manager_stats['labor_violations']}")
    
    print("\n=== Hiring Opportunities ===")
    
    opportunities = workplace_manager.get_hiring_opportunities()
    if opportunities:
        print("Available positions across all workplaces:")
        for owner_id, positions in opportunities.items():
            master_name = next(m.name for m in masters if m.character_id == owner_id)
            print(f"  {master_name}: {positions['journeymen']} journeymen, {positions['apprentices']} apprentices")
    else:
        print("No hiring opportunities available")
    
    print("\n=== Hiring Preference Scoring ===")
    
    if workplaces and workers:
        workplace = workplaces[0]
        master = masters[0]
        
        print(f"\n{master.name}'s hiring preferences:")
        for worker in workers[:5]:
            preference_score = workplace.get_hiring_preference_score(
                worker.character_id, 
                npc_relationships
            )
            relationship_trust = npc_relationships[master.character_id].get(worker.character_id, 0.0)
            print(f"  {worker.name}: Preference {preference_score:.2f}, Trust {relationship_trust:.2f}")
    
    print("\n=== Demonstration Complete ===")
    print("The Master Workplace system successfully demonstrates:")
    print("- Economic-based capacity scaling")
    print("- Moral profile effects on hiring")
    print("- Labor oversight and flag detection")
    print("- Integration with guild and NPC systems")
    print("- Comprehensive workplace management")

if __name__ == "__main__":
    main() 