"""
Caravan System for Age of Scribes
=================================

Modular system for simulating resource transport between settlements.
"""

from typing import List, Dict, Tuple, Optional, Any
import uuid
import math
import logging
from dataclasses import dataclass, field
from settlement_system import Settlement, ResourceType

logger = logging.getLogger(__name__)


@dataclass
class Caravan:
    """Represents a caravan transporting resources between settlements."""
    
    origin_id: str
    destination_id: str
    resource_manifest: Dict[str, float]
    departure_day: int
    travel_duration: int
    status: str = "in_transit"
    risk_score: float = 0.0
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    def __post_init__(self):
        """Calculate risk score based on cargo value and distance."""
        # Simple risk calculation based on cargo value
        total_cargo = sum(self.resource_manifest.values())
        self.risk_score = min(1.0, total_cargo / 1000.0)
    
    def get_arrival_day(self) -> int:
        """Get the scheduled arrival day."""
        return self.departure_day + self.travel_duration


def generate_caravans(settlements: List[Settlement], current_day: int) -> List[Caravan]:
    """Generate caravans based on settlement resource supply and demand."""
    new_caravans = []
    active_settlements = [s for s in settlements if s.is_active]
    
    for settlement in active_settlements:
        # Check each resource for deficits
        for resource_type, resource_data in settlement.resources.items():
            daily_production = resource_data.production_base
            daily_consumption = resource_data.consumption_base
            current_imports = resource_data.import_volume
            
            # Calculate deficit
            total_supply = daily_production + current_imports
            deficit = daily_consumption - total_supply
            
            # If deficit > 10% of consumption, look for suppliers
            if deficit > 0 and deficit / daily_consumption > 0.1:
                quantity_needed = deficit * 10  # 10-day supply
                
                # Find best supplier
                best_supplier = None
                best_priority = 0
                
                for supplier in active_settlements:
                    if supplier.name == settlement.name:
                        continue
                    
                    supplier_resource = supplier.resources.get(resource_type)
                    if not supplier_resource:
                        continue
                    
                    # Check if supplier has surplus
                    supplier_production = supplier_resource.production_base
                    supplier_consumption = supplier_resource.consumption_base
                    available_surplus = supplier_resource.stockpile - (supplier_consumption * 20)
                    
                    if available_surplus > 10:  # Minimum surplus threshold
                        # Calculate distance (Euclidean)
                        x1, y1 = settlement.location
                        x2, y2 = supplier.location
                        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                        
                        if distance <= 50:  # Maximum search distance
                            priority = available_surplus / max(1.0, distance)
                            if priority > best_priority:
                                best_supplier = supplier
                                best_priority = priority
                
                # Create caravan if supplier found
                if best_supplier:
                    supplier_resource = best_supplier.resources[resource_type]
                    cargo_quantity = min(quantity_needed, supplier_resource.stockpile * 0.3)
                    
                    if cargo_quantity >= 5:  # Minimum viable cargo
                        # Calculate travel time
                        x1, y1 = settlement.location
                        x2, y2 = best_supplier.location
                        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                        travel_duration = max(1, int(distance / 2.0))
                        
                        # Create caravan
                        caravan = Caravan(
                            origin_id=best_supplier.name,
                            destination_id=settlement.name,
                            resource_manifest={resource_type.value: cargo_quantity},
                            departure_day=current_day,
                            travel_duration=travel_duration
                        )
                        
                        # Update supplier resources
                        supplier_resource.export_volume += cargo_quantity
                        supplier_resource.stockpile -= cargo_quantity
                        
                        new_caravans.append(caravan)
                        
                        logger.info(f"Generated caravan: {caravan.origin_id} → {caravan.destination_id}")
    
    return new_caravans


def resolve_caravans(caravans: List[Caravan], settlements: List[Settlement], current_day: int) -> None:
    """Resolve caravans that have completed their journeys."""
    settlements_by_name = {s.name: s for s in settlements}
    
    for caravan in caravans:
        if current_day >= caravan.get_arrival_day() and caravan.status == "in_transit":
            # Simple risk check
            import random
            if random.random() < caravan.risk_score * 0.1:
                caravan.status = "intercepted"
                logger.warning(f"Caravan {caravan.id} intercepted!")
                continue
            
            # Successful delivery
            destination = settlements_by_name.get(caravan.destination_id)
            if destination:
                for resource_type, quantity in caravan.resource_manifest.items():
                    resource_data = destination.resources.get(ResourceType(resource_type))
                    if resource_data:
                        resource_data.import_volume += quantity
                        resource_data.stockpile += quantity
                
                caravan.status = "delivered"
                logger.info(f"Delivered caravan {caravan.id}")


# Example usage
if __name__ == "__main__":
    from settlement_system import Settlement, SettlementTier, ResourceType
    
    # Create test settlements
    settlements = [
        Settlement("Farm Village", 300, SettlementTier.VILLAGE, (10.0, 10.0)),
        Settlement("Mining Town", 800, SettlementTier.TOWN, (25.0, 15.0))
    ]
    
    # Create resource imbalance
    farm = settlements[0]
    farm.resources[ResourceType.FOOD].stockpile = 2000
    farm.resources[ResourceType.TOOLS].consumption_base = 30
    farm.resources[ResourceType.TOOLS].production_base = 5
    
    mine = settlements[1]
    mine.resources[ResourceType.TOOLS].stockpile = 500
    mine.resources[ResourceType.FOOD].consumption_base = 80
    mine.resources[ResourceType.FOOD].production_base = 40
    
    print("=== Caravan System Test ===")
    
    active_caravans = []
    
    for day in range(1, 6):
        print(f"\n--- Day {day} ---")
        
        new_caravans = generate_caravans(settlements, day)
        active_caravans.extend(new_caravans)
        print(f"Generated {len(new_caravans)} caravans")
        
        resolve_caravans(active_caravans, settlements, day)
        
        in_transit = sum(1 for c in active_caravans if c.status == "in_transit")
        delivered = sum(1 for c in active_caravans if c.status == "delivered")
        print(f"In transit: {in_transit}, Delivered: {delivered}")
    
    print(f"\nTotal caravans created: {len(active_caravans)}") 