"""
Mercantile Resource System for Age of Scribes

This module provides a structured, scalable resource management system for trade,
economy, and faction interactions. Resources are categorized by type with detailed
attributes affecting trade desirability, rarity, and faction restrictions.

The system integrates with Economy Tick, Caravan, and Faction systems to provide
realistic resource-driven economic simulation.
"""

import random
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Tuple
from enum import Enum
from datetime import datetime

class ResourceCategory(Enum):
    """Categories of resources in the economic system."""
    FOOD = "food"
    MATERIAL = "material"
    LUXURY = "luxury"
    TOOL = "tool"
    WEAPON = "weapon"
    ARMOR = "armor"
    MAGIC = "magic"
    INFORMATION = "information"

class ResourceRarity(Enum):
    """Rarity levels affecting availability and base pricing."""
    COMMON = "common"           # 0.8-1.2x base price
    UNCOMMON = "uncommon"       # 1.2-1.8x base price
    RARE = "rare"               # 1.8-3.0x base price
    REGIONAL = "regional"       # 2.0-4.0x base price (location dependent)
    LEGENDARY = "legendary"     # 5.0-10.0x base price

@dataclass
class Resource:
    """
    Represents a tradeable resource in the mercantile system.
    
    This class defines all attributes that affect resource behavior in
    economic simulation, faction interactions, and trade calculations.
    """
    name: str                           # Human-readable name
    category: str                       # 'food', 'material', 'luxury', etc.
    subtype: str                        # Specific classification (e.g. 'protein_large')
    rarity: str                         # 'common', 'uncommon', 'rare', 'regional', 'legendary'
    tags: List[str]                     # Descriptive tags affecting behavior
    trade_modifier: float               # +/- value affecting desirability and profit margins
    faction_restricted: bool = False    # Restricted by ideology or law
    magic_affinity: float = 0.0         # 0.0–1.0 scale for enchantment systems
    
    # Economic attributes
    base_price: float = 1.0             # Base economic value
    weight: float = 1.0                 # Physical weight (affects transport)
    volume: float = 1.0                 # Storage volume required
    shelf_life: Optional[int] = None    # Days before spoilage (None = no spoilage)
    
    # Production and availability
    production_time: int = 1            # Days to produce one unit
    production_requirements: List[str] = field(default_factory=list)  # Required resources/conditions
    seasonal_availability: Optional[List[str]] = None  # Seasons when available
    regional_origins: List[str] = field(default_factory=list)  # Regions where naturally available
    
    # Trade and faction attributes
    cultural_significance: Dict[str, float] = field(default_factory=dict)  # faction_id -> importance
    diplomatic_weight: float = 0.0      # How much this affects diplomatic relations
    contraband_regions: List[str] = field(default_factory=list)  # Where this is illegal
    
    # Resource ID for tracking
    resource_id: str = field(default_factory=lambda: str(uuid.uuid4()))

class ResourceRegistry:
    """
    Central registry for all resources in the game world.
    
    Manages resource definitions, pricing, availability, and provides
    query interfaces for economic and faction systems.
    """
    
    def __init__(self):
        self.resources: Dict[str, Resource] = {}
        self.categories: Dict[str, List[str]] = {}
        self.rarity_groups: Dict[str, List[str]] = {}
        self.tag_index: Dict[str, List[str]] = {}
        self.faction_restrictions: Dict[str, List[str]] = {}
        
        # Pricing modifiers by rarity
        self.rarity_price_multipliers = {
            ResourceRarity.COMMON.value: (0.8, 1.2),
            ResourceRarity.UNCOMMON.value: (1.2, 1.8),
            ResourceRarity.RARE.value: (1.8, 3.0),
            ResourceRarity.REGIONAL.value: (2.0, 4.0),
            ResourceRarity.LEGENDARY.value: (5.0, 10.0)
        }
        
        # Load default resources
        self._initialize_default_resources()
    
    def register_resource(self, resource: Resource) -> bool:
        """
        Register a new resource in the system.
        
        Args:
            resource: Resource object to register
            
        Returns:
            True if successfully registered, False if duplicate name
        """
        if resource.name in self.resources:
            return False
        
        # Register resource
        self.resources[resource.name] = resource
        
        # Update category index
        if resource.category not in self.categories:
            self.categories[resource.category] = []
        self.categories[resource.category].append(resource.name)
        
        # Update rarity index
        if resource.rarity not in self.rarity_groups:
            self.rarity_groups[resource.rarity] = []
        self.rarity_groups[resource.rarity].append(resource.name)
        
        # Update tag index
        for tag in resource.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            self.tag_index[tag].append(resource.name)
        
        # Update faction restriction index
        if resource.faction_restricted:
            for region in resource.contraband_regions:
                if region not in self.faction_restrictions:
                    self.faction_restrictions[region] = []
                self.faction_restrictions[region].append(resource.name)
        
        return True
    
    def get_resource(self, name: str) -> Optional[Resource]:
        """Get resource by name."""
        return self.resources.get(name)
    
    def get_resources_by_category(self, category: str) -> List[Resource]:
        """Get all resources in a specific category."""
        resource_names = self.categories.get(category, [])
        return [self.resources[name] for name in resource_names]
    
    def get_resources_by_rarity(self, rarity: str) -> List[Resource]:
        """Get all resources of a specific rarity."""
        resource_names = self.rarity_groups.get(rarity, [])
        return [self.resources[name] for name in resource_names]
    
    def get_resources_by_tag(self, tag: str) -> List[Resource]:
        """Get all resources with a specific tag."""
        resource_names = self.tag_index.get(tag, [])
        return [self.resources[name] for name in resource_names]
    
    def get_available_resources(self, region: str, faction_id: Optional[str] = None) -> List[Resource]:
        """
        Get resources available in a specific region, considering faction restrictions.
        
        Args:
            region: Region name
            faction_id: Optional faction ID for restriction checking
            
        Returns:
            List of available resources
        """
        available = []
        
        for resource in self.resources.values():
            # Check regional availability
            if resource.regional_origins and region not in resource.regional_origins:
                continue
            
            # Check contraband restrictions
            if region in resource.contraband_regions:
                continue
            
            # Check faction restrictions
            if faction_id and resource.faction_restricted:
                # This could be expanded with more complex faction logic
                pass
            
            available.append(resource)
        
        return available
    
    def calculate_resource_price(self, 
                                resource_name: str, 
                                region: str,
                                supply: float = 1.0,
                                demand: float = 1.0,
                                faction_modifier: float = 1.0) -> float:
        """
        Calculate current price for a resource considering various factors.
        
        Args:
            resource_name: Name of the resource
            region: Current region
            supply: Supply level (0.1 to 10.0+)
            demand: Demand level (0.1 to 10.0+)
            faction_modifier: Faction-based price modification
            
        Returns:
            Calculated price
        """
        resource = self.get_resource(resource_name)
        if not resource:
            return 0.0
        
        # Base price
        price = resource.base_price
        
        # Rarity modifier
        rarity_min, rarity_max = self.rarity_price_multipliers[resource.rarity]
        rarity_modifier = random.uniform(rarity_min, rarity_max)
        price *= rarity_modifier
        
        # Trade modifier from resource
        price *= (1.0 + resource.trade_modifier)
        
        # Supply and demand
        price *= (demand / supply)
        
        # Faction modifier
        price *= faction_modifier
        
        # Regional modifiers
        if resource.rarity == ResourceRarity.REGIONAL.value:
            if region in resource.regional_origins:
                price *= 0.7  # Cheaper in origin region
            else:
                price *= 1.5  # More expensive elsewhere
        
        return max(0.1, price)  # Minimum price floor
    
    def evaluate_trade_desirability(self, 
                                   resource_name: str,
                                   origin_region: str,
                                   destination_region: str,
                                   caravan_capacity: float = 100.0) -> Dict[str, Any]:
        """
        Evaluate how desirable a resource is for trade between regions.
        
        Args:
            resource_name: Resource to evaluate
            origin_region: Starting region
            destination_region: Target region
            caravan_capacity: Available caravan capacity
            
        Returns:
            Dictionary with trade evaluation metrics
        """
        resource = self.get_resource(resource_name)
        if not resource:
            return {'error': 'Resource not found'}
        
        evaluation = {
            'resource_name': resource_name,
            'origin_region': origin_region,
            'destination_region': destination_region,
            'base_desirability': resource.trade_modifier,
            'weight_factor': 1.0 / max(0.1, resource.weight),
            'volume_factor': 1.0 / max(0.1, resource.volume),
            'capacity_efficiency': 0.0,
            'risk_factors': [],
            'profit_potential': 'unknown',
            'recommendation': 'evaluate'
        }
        
        # Capacity efficiency
        units_per_capacity = caravan_capacity / (resource.weight + resource.volume)
        evaluation['capacity_efficiency'] = units_per_capacity
        
        # Risk factors
        if resource.faction_restricted:
            evaluation['risk_factors'].append('faction_restricted')
        
        if destination_region in resource.contraband_regions:
            evaluation['risk_factors'].append('contraband_destination')
        
        if resource.shelf_life and resource.shelf_life < 7:
            evaluation['risk_factors'].append('perishable')
        
        if resource.rarity in [ResourceRarity.RARE.value, ResourceRarity.LEGENDARY.value]:
            evaluation['risk_factors'].append('high_value_target')
        
        # Calculate profit potential
        origin_price = self.calculate_resource_price(resource_name, origin_region, supply=1.2, demand=0.8)
        dest_price = self.calculate_resource_price(resource_name, destination_region, supply=0.8, demand=1.2)
        
        if dest_price > origin_price * 1.3:
            evaluation['profit_potential'] = 'high'
            evaluation['recommendation'] = 'recommended'
        elif dest_price > origin_price * 1.1:
            evaluation['profit_potential'] = 'medium'
            evaluation['recommendation'] = 'consider'
        else:
            evaluation['profit_potential'] = 'low'
            evaluation['recommendation'] = 'avoid'
        
        return evaluation
    
    def get_seasonal_resources(self, season: str, region: str) -> List[Resource]:
        """Get resources available in a specific season and region."""
        seasonal_resources = []
        
        for resource in self.resources.values():
            # Check seasonal availability
            if resource.seasonal_availability:
                if season not in resource.seasonal_availability:
                    continue
            
            # Check regional availability
            if resource.regional_origins and region not in resource.regional_origins:
                continue
            
            seasonal_resources.append(resource)
        
        return seasonal_resources
    
    def _initialize_default_resources(self):
        """Initialize the system with default resource definitions."""
        
        # Food Resources - Comprehensive list matching specification
        food_resources = [
            Resource(
                name="Cattle Meat", category="food", subtype="protein_large", rarity="common",
                tags=["domestic", "prestige"], trade_modifier=0.2,
                base_price=3.0, weight=2.0, volume=1.5, shelf_life=7,
                production_time=365, regional_origins=["grasslands", "plains"]
            ),
            Resource(
                name="Deer Meat", category="food", subtype="protein_medium", rarity="uncommon",
                tags=["wild", "seasonal"], trade_modifier=0.1,
                base_price=2.5, weight=1.5, volume=1.0, shelf_life=5,
                seasonal_availability=["autumn", "winter"], regional_origins=["forests", "hills"]
            ),
            Resource(
                name="Large Fish", category="food", subtype="protein_large", rarity="rare",
                tags=["coastal", "feast"], trade_modifier=0.5,
                base_price=4.0, weight=1.8, volume=1.2, shelf_life=3,
                regional_origins=["coastal", "rivers"]
            ),
            Resource(
                name="Leafy Greens", category="food", subtype="greens", rarity="common",
                tags=["fast_grow", "spoils_quickly"], trade_modifier=0.0,
                base_price=0.5, weight=0.3, volume=0.8, shelf_life=2,
                production_time=30, seasonal_availability=["spring", "summer"]
            ),
            Resource(
                name="Grain (Wheat)", category="food", subtype="staple", rarity="common",
                tags=["staple", "storeable", "bulk"], trade_modifier=0.1,
                base_price=1.0, weight=1.0, volume=1.0, shelf_life=180,
                production_time=120, seasonal_availability=["summer", "autumn"]
            ),
            Resource(
                name="Exotic Spices", category="food", subtype="seasoning", rarity="regional",
                tags=["luxury", "preservation", "trade"], trade_modifier=0.8,
                base_price=8.0, weight=0.1, volume=0.1, faction_restricted=True,
                regional_origins=["desert", "tropical"],
                cultural_significance={"merchant_faction": 1.5, "noble_faction": 1.2}
            )
        ]
        
        # Material Resources - Extended with comprehensive materials
        material_resources = [
            Resource(
                name="Stone (Durable)", category="material", subtype="stone_durable", rarity="common",
                tags=["infrastructure"], trade_modifier=0.1,
                base_price=0.8, weight=5.0, volume=2.0,
                regional_origins=["mountains", "hills", "quarries"]
            ),
            Resource(
                name="Iron Ore", category="material", subtype="metal_industrial", rarity="common",
                tags=["critical", "military"], trade_modifier=0.2,
                base_price=2.0, weight=3.0, volume=1.0,
                regional_origins=["mountains", "mines"]
            ),
            Resource(
                name="Gold", category="material", subtype="metal_precious", rarity="rare",
                tags=["coinage", "prestige"], trade_modifier=0.6,
                base_price=50.0, weight=0.5, volume=0.1,
                regional_origins=["mines", "rivers"]
            ),
            Resource(
                name="Hardwood Timber", category="material", subtype="wood_quality", rarity="uncommon",
                tags=["crafting", "building", "quality"], trade_modifier=0.3,
                base_price=1.5, weight=2.5, volume=3.0,
                production_time=1825, regional_origins=["forests"]  # 5 years
            ),
            Resource(
                name="Fine Clay", category="material", subtype="ceramic", rarity="uncommon",
                tags=["crafting", "pottery", "artistic"], trade_modifier=0.2,
                base_price=1.2, weight=2.0, volume=1.5,
                regional_origins=["rivers", "coastal"]
            )
        ]
        
        # Luxury Resources - Expanded luxury goods
        luxury_resources = [
            Resource(
                name="Silk Cloth", category="luxury", subtype="textile_fine", rarity="regional",
                tags=["prestige", "diplomacy"], trade_modifier=0.9, faction_restricted=True,
                base_price=15.0, weight=0.3, volume=0.5,
                production_time=90, regional_origins=["silk_regions"],
                cultural_significance={"noble_faction": 1.5, "merchant_faction": 1.2}
            ),
            Resource(
                name="Living Ink", category="luxury", subtype="magic_component", rarity="rare",
                tags=["magic", "ritual"], trade_modifier=1.2, faction_restricted=True,
                base_price=25.0, weight=0.1, volume=0.1, magic_affinity=1.0,
                contraband_regions=["anti_magic_regions"],
                cultural_significance={"scholar_faction": 2.0, "mage_faction": 2.5}
            ),
            Resource(
                name="Jeweled Ornaments", category="luxury", subtype="jewelry", rarity="rare",
                tags=["prestige", "wealth", "gift"], trade_modifier=0.7,
                base_price=30.0, weight=0.2, volume=0.1,
                production_requirements=["Gold", "Fine Gems"],
                cultural_significance={"merchant_faction": 1.3, "noble_faction": 1.8}
            ),
            Resource(
                name="Ancient Texts", category="luxury", subtype="knowledge", rarity="legendary",
                tags=["knowledge", "historical", "power"], trade_modifier=1.5, faction_restricted=True,
                base_price=100.0, weight=0.5, volume=0.3,
                cultural_significance={"scholar_faction": 3.0, "religious_faction": 2.5}
            )
        ]
        
        # Register all default resources
        all_resources = food_resources + material_resources + luxury_resources
        
        for resource in all_resources:
            self.register_resource(resource)

# Global resource registry instance
RESOURCE_REGISTRY = ResourceRegistry()

def get_resource_registry() -> ResourceRegistry:
    """Get the global resource registry instance."""
    return RESOURCE_REGISTRY

def calculate_caravan_load_efficiency(resources: List[Tuple[str, int]], caravan_capacity: float) -> Dict[str, Any]:
    """
    Calculate how efficiently a caravan load uses available capacity.
    
    Args:
        resources: List of (resource_name, quantity) tuples
        caravan_capacity: Maximum caravan capacity
        
    Returns:
        Dictionary with efficiency metrics
    """
    registry = get_resource_registry()
    
    total_weight = 0.0
    total_volume = 0.0
    total_value = 0.0
    
    load_details = []
    
    for resource_name, quantity in resources:
        resource = registry.get_resource(resource_name)
        if resource:
            item_weight = resource.weight * quantity
            item_volume = resource.volume * quantity
            item_value = resource.base_price * quantity
            
            total_weight += item_weight
            total_volume += item_volume
            total_value += item_value
            
            load_details.append({
                'resource': resource_name,
                'quantity': quantity,
                'weight': item_weight,
                'volume': item_volume,
                'value': item_value
            })
    
    # Calculate capacity usage
    capacity_used = max(total_weight, total_volume)  # Limited by the greater constraint
    capacity_efficiency = min(1.0, capacity_used / caravan_capacity) if caravan_capacity > 0 else 0.0
    
    return {
        'total_weight': total_weight,
        'total_volume': total_volume,
        'total_value': total_value,
        'capacity_used': capacity_used,
        'capacity_efficiency': capacity_efficiency,
        'value_per_capacity': total_value / max(1.0, capacity_used),
        'load_details': load_details,
        'over_capacity': capacity_used > caravan_capacity
    }

def evaluate_trade_opportunities(origin_region: str, 
                               destination_region: str,
                               caravan_capacity: float = 100.0,
                               risk_tolerance: float = 0.5) -> List[Dict[str, Any]]:
    """
    Evaluate trade opportunities between two regions.
    
    Args:
        origin_region: Starting region
        destination_region: Target region  
        caravan_capacity: Available caravan capacity
        risk_tolerance: 0.0 (risk averse) to 1.0 (risk seeking)
        
    Returns:
        List of trade opportunities sorted by potential profit
    """
    registry = get_resource_registry()
    
    opportunities = []
    
    for resource in registry.resources.values():
        # Calculate basic trade metrics
        origin_price = registry.calculate_resource_price(resource.name, origin_region, supply=1.2, demand=0.8)
        dest_price = registry.calculate_resource_price(resource.name, destination_region, supply=0.8, demand=1.2)
        
        if dest_price <= origin_price * 1.05:  # Skip if profit margin too low
            continue
        
        # Calculate risk factors
        risk_factors = []
        risk_score = 0.0
        
        if resource.faction_restricted:
            risk_factors.append('faction_restricted')
            risk_score += 0.3
        
        if destination_region in resource.contraband_regions:
            risk_factors.append('contraband_destination')
            risk_score += 0.5
        
        if resource.shelf_life and resource.shelf_life < 7:
            risk_factors.append('perishable')
            risk_score += 0.2
        
        if resource.rarity in ['rare', 'legendary']:
            risk_factors.append('high_value_target')
            risk_score += 0.15
        
        # Filter based on risk tolerance
        if risk_score > risk_tolerance and dest_price < origin_price * 1.5:
            continue
        
        # Calculate profit potential
        profit_margin = (dest_price - origin_price) / origin_price
        
        if profit_margin > 0.5:
            profit_potential = 'high'
            recommendation = 'recommended'
        elif profit_margin > 0.2:
            profit_potential = 'medium'
            recommendation = 'consider'
        else:
            profit_potential = 'low'
            recommendation = 'marginal'
        
        opportunity = {
            'resource_name': resource.name,
            'origin_region': origin_region,
            'destination_region': destination_region,
            'origin_price': origin_price,
            'destination_price': dest_price,
            'profit_margin': profit_margin,
            'profit_potential': profit_potential,
            'risk_factors': risk_factors,
            'risk_score': risk_score,
            'recommendation': recommendation,
            'trade_modifier': resource.trade_modifier,
            'capacity_efficiency': caravan_capacity / (resource.weight + resource.volume)
        }
        
        opportunities.append(opportunity)
    
    # Sort by profit potential and capacity efficiency
    def sort_key(opp):
        profit_weights = {'high': 3, 'medium': 2, 'low': 1, 'marginal': 0.5}
        profit_score = profit_weights.get(opp['profit_potential'], 0)
        efficiency_score = min(2.0, opp['capacity_efficiency'] / 10.0)  # Normalize efficiency
        risk_penalty = opp['risk_score']
        return profit_score + efficiency_score - risk_penalty
    
    opportunities.sort(key=sort_key, reverse=True)
    return opportunities

def get_faction_preferred_resources(faction_id: str) -> List[Resource]:
    """
    Get resources that have cultural significance for a specific faction.
    
    Args:
        faction_id: Faction identifier
        
    Returns:
        List of culturally significant resources
    """
    registry = get_resource_registry()
    preferred = []
    
    for resource in registry.resources.values():
        if faction_id in resource.cultural_significance:
            preferred.append(resource)
    
    # Sort by cultural significance
    preferred.sort(key=lambda r: r.cultural_significance.get(faction_id, 0.0), reverse=True)
    return preferred

def get_seasonal_resources(season: str, region: str) -> List[Resource]:
    """Get resources available in a specific season and region."""
    registry = get_resource_registry()
    seasonal_resources = []
    
    for resource in registry.resources.values():
        # Check seasonal availability
        if resource.seasonal_availability:
            if season not in resource.seasonal_availability:
                continue
        
        # Check regional availability
        if resource.regional_origins and region not in resource.regional_origins:
            continue
        
        seasonal_resources.append(resource)
    
    return seasonal_resources

def simulate_market_fluctuation(region: str, days: int = 30) -> Dict[str, List[float]]:
    """
    Simulate market price fluctuations for resources over time.
    
    Args:
        region: Region to simulate
        days: Number of days to simulate
        
    Returns:
        Dictionary mapping resource names to daily price lists
    """
    registry = get_resource_registry()
    market_data = {}
    
    for resource in registry.resources.values():
        daily_prices = []
        
        for day in range(days):
            # Simulate supply and demand fluctuations
            supply = random.uniform(0.7, 1.3)
            demand = random.uniform(0.8, 1.2)
            
            # Add seasonal effects
            if resource.seasonal_availability:
                current_season = ["spring", "summer", "autumn", "winter"][day % 4]
                if current_season not in resource.seasonal_availability:
                    supply *= 0.3  # Low supply out of season
                    demand *= 1.5  # Higher demand when scarce
            
            # Add random market events
            if random.random() < 0.05:  # 5% chance of market event
                event_modifier = random.uniform(0.5, 2.0)
                supply *= event_modifier
            
            price = registry.calculate_resource_price(
                resource.name, region, supply, demand
            )
            daily_prices.append(price)
        
        market_data[resource.name] = daily_prices
    
    return market_data

# Integration functions for existing systems

def integrate_with_economy_tick(settlement_data: Dict[str, Any], 
                              resource_flows: Dict[str, float]) -> Dict[str, Any]:
    """
    Integration hook for the Economy Tick System.
    
    Args:
        settlement_data: Current settlement economic data
        resource_flows: Dictionary of resource_name -> flow_amount
        
    Returns:
        Updated economic data with resource-based modifications
    """
    registry = get_resource_registry()
    
    # Calculate trade balance adjustments
    import_value = 0.0
    export_value = 0.0
    
    for resource_name, flow_amount in resource_flows.items():
        resource = registry.get_resource(resource_name)
        if resource:
            base_value = resource.base_price * abs(flow_amount)
            modified_value = base_value * (1.0 + resource.trade_modifier)
            
            if flow_amount > 0:  # Import
                import_value += modified_value
            else:  # Export
                export_value += modified_value
    
    # Update settlement economic indicators
    trade_balance = export_value - import_value
    settlement_data['trade_balance'] = settlement_data.get('trade_balance', 0.0) + trade_balance
    settlement_data['import_value'] = settlement_data.get('import_value', 0.0) + import_value
    settlement_data['export_value'] = settlement_data.get('export_value', 0.0) + export_value
    
    return settlement_data

def integrate_with_caravan_system(caravan_data: Dict[str, Any],
                                 cargo_manifest: List[Tuple[str, int]]) -> Dict[str, Any]:
    """
    Integration hook for the Caravan System.
    
    Args:
        caravan_data: Current caravan state data
        cargo_manifest: List of (resource_name, quantity) tuples
        
    Returns:
        Updated caravan data with resource-based risk and value calculations
    """
    registry = get_resource_registry()
    
    total_value = 0.0
    risk_multiplier = 1.0
    prestige_cargo = False
    
    for resource_name, quantity in cargo_manifest:
        resource = registry.get_resource(resource_name)
        if resource:
            # Calculate cargo value
            item_value = resource.base_price * quantity * (1.0 + resource.trade_modifier)
            total_value += item_value
            
            # Adjust risk based on resource properties
            if resource.faction_restricted:
                risk_multiplier *= 1.3
            
            if resource.rarity in ['rare', 'legendary']:
                risk_multiplier *= 1.2
                prestige_cargo = True
            
            if 'prestige' in resource.tags:
                prestige_cargo = True
    
    # Update caravan data
    caravan_data['cargo_value'] = total_value
    caravan_data['risk_multiplier'] = caravan_data.get('risk_multiplier', 1.0) * risk_multiplier
    caravan_data['prestige_cargo'] = prestige_cargo
    
    return caravan_data

def integrate_with_faction_system(faction_data: Dict[str, Any],
                                 available_resources: List[str]) -> Dict[str, Any]:
    """
    Integration hook for the Faction System.
    
    Args:
        faction_data: Current faction state data
        available_resources: List of resource names available to faction
        
    Returns:
        Updated faction data with resource-based influence and restrictions
    """
    registry = get_resource_registry()
    faction_id = faction_data.get('faction_id', '')
    
    cultural_value = 0.0
    restricted_access = []
    
    for resource_name in available_resources:
        resource = registry.get_resource(resource_name)
        if resource:
            # Calculate cultural significance
            if faction_id in resource.cultural_significance:
                cultural_value += resource.cultural_significance[faction_id]
            
            # Check access restrictions
            if resource.faction_restricted and faction_id not in resource.cultural_significance:
                restricted_access.append(resource_name)
    
    # Update faction influence based on culturally significant resources
    faction_data['cultural_influence'] = faction_data.get('cultural_influence', 0.0) + cultural_value
    faction_data['restricted_resources'] = restricted_access
    
    return faction_data
    """
    Calculate how efficiently a caravan load uses available capacity.
    
    Args:
        resources: List of (resource_name, quantity) tuples
        caravan_capacity: Maximum caravan capacity
        
    Returns:
        Dictionary with efficiency metrics
    """
    registry = get_resource_registry()
    
    total_weight = 0.0
    total_volume = 0.0
    total_value = 0.0
    
    load_details = []
    
    for resource_name, quantity in resources:
        resource = registry.get_resource(resource_name)
        if resource:
            item_weight = resource.weight * quantity
            item_volume = resource.volume * quantity
            item_value = resource.base_price * quantity
            
            total_weight += item_weight
            total_volume += item_volume
            total_value += item_value
            
            load_details.append({
                'resource': resource_name,
                'quantity': quantity,
                'weight': item_weight,
                'volume': item_volume,
                'value': item_value
            })
    
    # Calculate capacity usage
    capacity_used = max(total_weight, total_volume)  # Limited by the greater constraint
    capacity_efficiency = min(1.0, capacity_used / caravan_capacity) if caravan_capacity > 0 else 0.0
    
    return {
        'total_weight': total_weight,
        'total_volume': total_volume,
        'total_value': total_value,
        'capacity_used': capacity_used,
        'capacity_efficiency': capacity_efficiency,
        'value_per_capacity': total_value / max(1.0, capacity_used),
        'load_details': load_details,
        'over_capacity': capacity_used > caravan_capacity
    }

def evaluate_regional_trade_opportunities(origin_region: str, 
                                        destination_region: str,
                                        caravan_capacity: float = 100.0,
                                        risk_tolerance: float = 0.5) -> List[Dict[str, Any]]:
    """
    Evaluate trade opportunities between two regions.
    
    Args:
        origin_region: Starting region
        destination_region: Target region  
        caravan_capacity: Available caravan capacity
        risk_tolerance: 0.0 (risk averse) to 1.0 (risk seeking)
        
    Returns:
        List of trade opportunities sorted by potential profit
    """
    registry = get_resource_registry()
    
    available_resources = registry.get_available_resources(origin_region)
    opportunities = []
    
    for resource in available_resources:
        evaluation = registry.evaluate_trade_desirability(
            resource.name, origin_region, destination_region, caravan_capacity
        )
        
        # Calculate risk score
        risk_score = len(evaluation['risk_factors']) * 0.25
        
        # Filter based on risk tolerance
        if risk_score <= risk_tolerance or evaluation['profit_potential'] == 'high':
            evaluation['risk_score'] = risk_score
            opportunities.append(evaluation)
    
    # Sort by profit potential and risk
    def sort_key(opp):
        profit_weights = {'high': 3, 'medium': 2, 'low': 1}
        profit_score = profit_weights.get(opp['profit_potential'], 0)
        risk_penalty = opp['risk_score']
        return profit_score - risk_penalty
    
    opportunities.sort(key=sort_key, reverse=True)
    return opportunities

def get_faction_preferred_resources(faction_id: str) -> List[Resource]:
    """
    Get resources that have cultural significance for a specific faction.
    
    Args:
        faction_id: Faction identifier
        
    Returns:
        List of culturally significant resources
    """
    registry = get_resource_registry()
    preferred = []
    
    for resource in registry.resources.values():
        if faction_id in resource.cultural_significance:
            preferred.append(resource)
    
    # Sort by cultural significance
    preferred.sort(key=lambda r: r.cultural_significance.get(faction_id, 0.0), reverse=True)
    return preferred

def simulate_resource_market_fluctuation(region: str, days: int = 30) -> Dict[str, List[float]]:
    """
    Simulate market price fluctuations for resources over time.
    
    Args:
        region: Region to simulate
        days: Number of days to simulate
        
    Returns:
        Dictionary mapping resource names to daily price lists
    """
    registry = get_resource_registry()
    available_resources = registry.get_available_resources(region)
    
    market_data = {}
    
    for resource in available_resources:
        daily_prices = []
        
        for day in range(days):
            # Simulate supply and demand fluctuations
            supply = random.uniform(0.7, 1.3)
            demand = random.uniform(0.8, 1.2)
            
            # Add seasonal effects
            if resource.seasonal_availability:
                current_season = ["spring", "summer", "autumn", "winter"][day % 4]
                if current_season not in resource.seasonal_availability:
                    supply *= 0.3  # Low supply out of season
                    demand *= 1.5  # Higher demand when scarce
            
            # Add random market events
            if random.random() < 0.05:  # 5% chance of market event
                event_modifier = random.uniform(0.5, 2.0)
                supply *= event_modifier
            
            price = registry.calculate_resource_price(
                resource.name, region, supply, demand
            )
            daily_prices.append(price)
        
        market_data[resource.name] = daily_prices
    
    return market_data 