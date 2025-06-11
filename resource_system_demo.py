"""
Mercantile Resource System - Demonstration Script

This script demonstrates the key features of the Resource System:
1. Resource registry usage and querying
2. Trade opportunity analysis between regions
3. Caravan load optimization calculations
4. Market simulation and pricing dynamics
5. Integration with existing game systems

This serves as both documentation and testing for the resource system.
"""

from resource_system import (
    Resource, 
    ResourceRegistry,
    get_resource_registry,
    calculate_caravan_load_efficiency,
    evaluate_trade_opportunities,
    simulate_market_fluctuation,
    get_seasonal_resources,
    integrate_with_economy_tick,
    integrate_with_caravan_system,
    integrate_with_faction_system
)

def demonstrate_resource_registry():
    """Demonstrate resource registry operations and queries."""
    print("=== RESOURCE REGISTRY DEMONSTRATION ===\n")
    
    registry = get_resource_registry()
    
    # Show basic registry statistics
    print("Registry Statistics:")
    print(f"  Total Resources: {len(registry.resources)}")
    print(f"  Categories: {len(registry.categories)}")
    print(f"  Rarity Groups: {len(registry.rarity_groups)}")
    print()
    
    # Demonstrate category-based queries
    print("Resources by Category:")
    for category, resource_names in registry.categories.items():
        print(f"  {category.title()}: {len(resource_names)} resources")
        for name in resource_names[:3]:  # Show first 3
            resource = registry.get_resource(name)
            print(f"    - {name} (rarity: {resource.rarity}, price: {resource.base_price})")
        if len(resource_names) > 3:
            print(f"    ... and {len(resource_names) - 3} more")
        print()
    
    # Demonstrate rarity-based queries
    print("Resources by Rarity:")
    for rarity, resource_names in registry.rarity_groups.items():
        print(f"  {rarity.title()}: {len(resource_names)} resources")
        example_names = resource_names[:2]
        print(f"    Examples: {', '.join(example_names)}")
    print()
    
    # Demonstrate tag-based queries
    print("Popular Tags:")
    popular_tags = sorted(registry.tag_index.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    for tag, resource_names in popular_tags:
        print(f"  '{tag}': {len(resource_names)} resources")
        print(f"    Resources: {', '.join(resource_names[:3])}")
    print()

def demonstrate_trade_opportunities():
    """Demonstrate trade opportunity analysis between regions."""
    print("=== TRADE OPPORTUNITY ANALYSIS DEMONSTRATION ===\n")
    
    # Analyze trade opportunities between different regions
    trade_scenarios = [
        ("farmlands", "mountain_city", 200.0, 0.5),
        ("coastal_town", "desert_oasis", 150.0, 0.3),
        ("forest_settlement", "trading_hub", 300.0, 0.7)
    ]
    
    for origin, destination, capacity, risk_tolerance in trade_scenarios:
        print(f"Trade Route: {origin} → {destination}")
        print(f"Caravan Capacity: {capacity}")
        print(f"Risk Tolerance: {risk_tolerance}")
        print()
        
        opportunities = evaluate_trade_opportunities(
            origin_region=origin,
            destination_region=destination,
            caravan_capacity=capacity,
            risk_tolerance=risk_tolerance
        )
        
        if opportunities:
            print("Top Trade Opportunities:")
            for i, opp in enumerate(opportunities[:5], 1):
                print(f"  {i}. {opp['resource_name']}")
                print(f"     Profit Margin: {opp['profit_margin']:.1%}")
                print(f"     Risk Score: {opp['risk_score']:.2f}")
                print(f"     Recommendation: {opp['recommendation']}")
                if opp['risk_factors']:
                    print(f"     Risk Factors: {', '.join(opp['risk_factors'])}")
                print()
        else:
            print("  No profitable opportunities found with current parameters.\n")
        
        print("-" * 50)
        print()

def demonstrate_caravan_optimization():
    """Demonstrate caravan load optimization calculations."""
    print("=== CARAVAN LOAD OPTIMIZATION DEMONSTRATION ===\n")
    
    # Test different cargo configurations
    cargo_scenarios = [
        ("Balanced Mixed Load", [
            ("Cattle Meat", 8),
            ("Iron Ore", 5),
            ("Silk Cloth", 2),
            ("Grain (Wheat)", 15)
        ], 150.0),
        
        ("High-Value Luxury Focus", [
            ("Living Ink", 3),
            ("Jeweled Ornaments", 2),
            ("Ancient Texts", 1),
            ("Silk Cloth", 5)
        ], 100.0),
        
        ("Bulk Materials", [
            ("Stone (Durable)", 20),
            ("Iron Ore", 15),
            ("Hardwood Timber", 8)
        ], 300.0),
        
        ("Perishable Goods Rush", [
            ("Large Fish", 6),
            ("Leafy Greens", 20),
            ("Deer Meat", 4)
        ], 120.0)
    ]
    
    for scenario_name, cargo, capacity in cargo_scenarios:
        print(f"Scenario: {scenario_name}")
        print(f"Caravan Capacity: {capacity}")
        print("Cargo Manifest:")
        for resource_name, quantity in cargo:
            print(f"  - {resource_name}: {quantity} units")
        print()
        
        efficiency = calculate_caravan_load_efficiency(cargo, capacity)
        
        print("Load Analysis:")
        print(f"  Total Weight: {efficiency['total_weight']:.1f}")
        print(f"  Total Volume: {efficiency['total_volume']:.1f}")
        print(f"  Total Value: {efficiency['total_value']:.0f} gold")
        print(f"  Capacity Used: {efficiency['capacity_used']:.1f}")
        print(f"  Capacity Efficiency: {efficiency['capacity_efficiency']:.1%}")
        print(f"  Value per Capacity: {efficiency['value_per_capacity']:.2f} gold/unit")
        
        if efficiency['over_capacity']:
            print("  ⚠️  WARNING: Cargo exceeds caravan capacity!")
        
        print()
        print("-" * 50)
        print()

def demonstrate_market_simulation():
    """Demonstrate market price fluctuation simulation."""
    print("=== MARKET SIMULATION DEMONSTRATION ===\n")
    
    # Simulate market fluctuations for different regions
    regions = ["trading_hub", "remote_village", "coastal_town"]
    
    for region in regions:
        print(f"Market Simulation: {region.replace('_', ' ').title()}")
        
        # Simulate 14 days of market activity
        market_data = simulate_market_fluctuation(region, days=14)
        
        # Analyze a few key resources
        key_resources = ["Cattle Meat", "Iron Ore", "Silk Cloth"]
        
        for resource_name in key_resources:
            if resource_name in market_data:
                prices = market_data[resource_name]
                avg_price = sum(prices) / len(prices)
                min_price = min(prices)
                max_price = max(prices)
                volatility = (max_price - min_price) / avg_price
                
                print(f"  {resource_name}:")
                print(f"    Average Price: {avg_price:.2f} gold")
                print(f"    Price Range: {min_price:.2f} - {max_price:.2f} gold")
                print(f"    Volatility: {volatility:.1%}")
        
        print()

def demonstrate_seasonal_availability():
    """Demonstrate seasonal resource availability."""
    print("=== SEASONAL AVAILABILITY DEMONSTRATION ===\n")
    
    seasons = ["spring", "summer", "autumn", "winter"]
    test_region = "farmlands"
    
    print(f"Seasonal Resource Availability in {test_region.replace('_', ' ').title()}:\n")
    
    for season in seasons:
        print(f"{season.title()}:")
        seasonal_resources = get_seasonal_resources(season, test_region)
        
        # Group by category
        by_category = {}
        for resource in seasonal_resources:
            if resource.category not in by_category:
                by_category[resource.category] = []
            by_category[resource.category].append(resource.name)
        
        for category, resource_names in by_category.items():
            print(f"  {category.title()}: {len(resource_names)} available")
            print(f"    {', '.join(resource_names[:4])}")
            if len(resource_names) > 4:
                print(f"    ... and {len(resource_names) - 4} more")
        
        print()

def demonstrate_system_integration():
    """Demonstrate integration with existing game systems."""
    print("=== SYSTEM INTEGRATION DEMONSTRATION ===\n")
    
    # Economy Tick System Integration
    print("1. Economy Tick System Integration:")
    settlement_data = {
        'settlement_name': 'Trading Hub',
        'population': 5000,
        'trade_balance': 0.0,
        'import_value': 0.0,
        'export_value': 0.0
    }
    
    resource_flows = {
        'Grain (Wheat)': 100,    # Import 100 units
        'Iron Ore': -50,         # Export 50 units
        'Silk Cloth': 20,        # Import 20 units
        'Stone (Durable)': -80   # Export 80 units
    }
    
    print(f"  Before Integration: Trade Balance = {settlement_data['trade_balance']}")
    
    updated_settlement = integrate_with_economy_tick(settlement_data, resource_flows)
    
    print(f"  After Integration:")
    print(f"    Trade Balance: {updated_settlement['trade_balance']:.0f} gold")
    print(f"    Import Value: {updated_settlement['import_value']:.0f} gold")
    print(f"    Export Value: {updated_settlement['export_value']:.0f} gold")
    print()
    
    # Caravan System Integration
    print("2. Caravan System Integration:")
    caravan_data = {
        'caravan_id': 'caravan_001',
        'origin': 'farmlands',
        'destination': 'mountain_city',
        'base_risk': 0.2
    }
    
    cargo_manifest = [
        ('Cattle Meat', 10),
        ('Living Ink', 2),
        ('Jeweled Ornaments', 1)
    ]
    
    print(f"  Before Integration: Base Risk = {caravan_data.get('base_risk', 0.0)}")
    
    updated_caravan = integrate_with_caravan_system(caravan_data, cargo_manifest)
    
    print(f"  After Integration:")
    print(f"    Cargo Value: {updated_caravan['cargo_value']:.0f} gold")
    print(f"    Risk Multiplier: {updated_caravan['risk_multiplier']:.2f}")
    print(f"    Prestige Cargo: {updated_caravan['prestige_cargo']}")
    print()
    
    # Faction System Integration
    print("3. Faction System Integration:")
    faction_data = {
        'faction_id': 'scholar_faction',
        'faction_name': 'Academy of Lore',
        'base_influence': 50.0,
        'cultural_influence': 0.0
    }
    
    available_resources = ['Ancient Texts', 'Living Ink', 'Silk Cloth', 'Iron Ore']
    
    print(f"  Before Integration: Cultural Influence = {faction_data['cultural_influence']}")
    
    updated_faction = integrate_with_faction_system(faction_data, available_resources)
    
    print(f"  After Integration:")
    print(f"    Cultural Influence: {updated_faction['cultural_influence']:.1f}")
    print(f"    Restricted Resources: {len(updated_faction['restricted_resources'])}")
    if updated_faction['restricted_resources']:
        print(f"    Restrictions: {', '.join(updated_faction['restricted_resources'][:3])}")
    print()

def demonstrate_custom_resource_creation():
    """Demonstrate creating and registering custom resources."""
    print("=== CUSTOM RESOURCE CREATION DEMONSTRATION ===\n")
    
    registry = get_resource_registry()
    
    # Create custom resources
    custom_resources = [
        Resource(
            name="Dragon Scale",
            category="material",
            subtype="exotic_component",
            rarity="legendary",
            tags=["magical", "armor_component", "rare"],
            trade_modifier=2.0,
            faction_restricted=True,
            magic_affinity=0.9,
            base_price=500.0,
            weight=0.5,
            volume=0.2,
            contraband_regions=["anti_magic_kingdom"],
            cultural_significance={"mage_faction": 3.0}
        ),
        
        Resource(
            name="Preserved Honey",
            category="food",
            subtype="sweetener",
            rarity="uncommon",
            tags=["luxury", "medicinal", "storeable"],
            trade_modifier=0.4,
            base_price=6.0,
            weight=0.8,
            volume=0.6,
            shelf_life=365,  # 1 year shelf life
            production_time=90,
            seasonal_availability=["summer", "autumn"],
            cultural_significance={"noble_faction": 1.2}
        ),
        
        Resource(
            name="Compass Stones",
            category="tool",
            subtype="navigation",
            rarity="rare",
            tags=["magical", "navigation", "trade"],
            trade_modifier=0.8,
            faction_restricted=True,
            magic_affinity=0.3,
            base_price=75.0,
            weight=1.0,
            volume=0.5,
            regional_origins=["mystical_isles"],
            cultural_significance={"merchant_faction": 2.0, "explorer_faction": 2.5}
        )
    ]
    
    print("Creating Custom Resources:")
    for resource in custom_resources:
        success = registry.register_resource(resource)
        if success:
            print(f"  ✓ Successfully registered: {resource.name}")
            print(f"    Category: {resource.category}, Rarity: {resource.rarity}")
            print(f"    Trade Modifier: {resource.trade_modifier:.1f}")
            if resource.cultural_significance:
                print(f"    Cultural Significance: {resource.cultural_significance}")
        else:
            print(f"  ✗ Failed to register: {resource.name} (duplicate name)")
        print()
    
    # Demonstrate updated registry statistics
    print("Updated Registry Statistics:")
    print(f"  Total Resources: {len(registry.resources)}")
    print(f"  Legendary Resources: {len(registry.get_resources_by_rarity('legendary'))}")
    
    # Show magical resources
    magical_resources = registry.get_resources_by_tag('magical')
    print(f"  Magical Resources: {len(magical_resources)}")
    for resource in magical_resources:
        print(f"    - {resource.name} (affinity: {resource.magic_affinity})")
    print()

def run_full_demonstration():
    """Run the complete resource system demonstration."""
    print("MERCANTILE RESOURCE SYSTEM DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Run all demonstration functions
    demonstrate_resource_registry()
    demonstrate_trade_opportunities()
    demonstrate_caravan_optimization()
    demonstrate_market_simulation()
    demonstrate_seasonal_availability()
    demonstrate_system_integration()
    demonstrate_custom_resource_creation()
    
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("The Mercantile Resource System provides:")
    print("- Structured resource classification and management")
    print("- Dynamic pricing and market simulation")
    print("- Trade opportunity analysis and optimization")
    print("- Seamless integration with existing game systems")
    print("- Scalable framework for economic simulation")
    print("- Rich faction interactions and cultural significance")

if __name__ == "__main__":
    run_full_demonstration() 