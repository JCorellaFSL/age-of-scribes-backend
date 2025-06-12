#!/usr/bin/env python3
"""
Simulation Manager - Master Orchestrator for Age of Scribes Engine
==================================================================

This module provides the main simulation orchestrator that coordinates all
subsystems for full world simulation. Handles initialization, tick coordination,
state management, and provides API endpoints for external interfaces.
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import all systems
from settlement_system import Settlement, SettlementManager, update_all_settlements
from economy_tick_system import EconomyTickSystem
from npc_ai import NPCBehaviorController, NPCMotivationEngine
from npc_profile import NPCProfile, generate_npc_profile
from faction_ai import FactionAIController
from faction_generator import Faction, create_faction
from rumor_engine import RumorNetwork
from reputation_tracker import ReputationEngine
from justice_system import JusticeEngine, JusticeCase
from memory_core import MemoryBank
from guild_event_engine import generate_guild_events, apply_guild_events
from guild_elections_system import LocalGuild
from guild_system import GuildSystem
from caravan_system import CaravanRoute, generate_caravans, resolve_caravans, Caravan
from npc_faction_dynamics import FactionLoyaltyEngine
from report_engine import SimulationReporter


@dataclass
class SimulationConfig:
    """Configuration for simulation parameters."""
    # Time settings
    ticks_per_day: int = 24
    simulation_speed: float = 1.0  # 1.0 = real-time, higher = faster
    
    # World settings
    world_size: Tuple[float, float] = (1000.0, 1000.0)
    max_npcs: int = 10000
    max_settlements: int = 100
    max_factions: int = 50
    
    # AI settings
    npc_ai_enabled: bool = True
    faction_ai_enabled: bool = True
    rumor_propagation_enabled: bool = True
    
    # Economy settings
    economy_enabled: bool = True
    trade_routes_enabled: bool = True
    resource_scarcity_events: bool = True
    
    # Social systems
    justice_system_enabled: bool = True
    reputation_tracking_enabled: bool = True
    guild_systems_enabled: bool = True
    
    # Performance settings
    multithreading_enabled: bool = True
    max_worker_threads: int = 4
    batch_size: int = 50
    
    # Logging
    log_level: str = "INFO"
    performance_monitoring: bool = True


@dataclass
class SimulationState:
    """Current state of the simulation."""
    current_day: int = 0
    current_tick: int = 0
    total_ticks: int = 0
    is_running: bool = False
    is_paused: bool = False
    start_time: Optional[datetime] = None
    
    # Statistics
    active_npcs: int = 0
    active_settlements: int = 0
    active_factions: int = 0
    active_guilds: int = 0
    active_rumors: int = 0
    active_justice_cases: int = 0
    active_caravans: int = 0
    
    # Performance metrics
    last_tick_duration_ms: float = 0.0
    average_tick_duration_ms: float = 0.0
    ticks_per_second: float = 0.0


class SimulationManager:
    """Master orchestrator for the Age of Scribes simulation engine."""
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        """Initialize the simulation manager with all subsystems."""
        self.config = config or SimulationConfig()
        self.state = SimulationState()
        
        # Setup logging
        logging.basicConfig(level=getattr(logging, self.config.log_level))
        self.logger = logging.getLogger(__name__)
        
        # Initialize all subsystems
        self._initialize_subsystems()
        
        # Performance tracking
        self.tick_times = []
        self.performance_stats = {}
        
        self.logger.info("SimulationManager initialized successfully")
    
    def _initialize_subsystems(self):
        """Initialize all simulation subsystems."""
        self.logger.info("Initializing simulation subsystems...")
        
        # Core data structures
        self.settlements: List[Settlement] = []
        self.npcs: List[NPCProfile] = []
        self.factions: List[Faction] = []
        self.guilds: List[LocalGuild] = []
        self.caravan_routes: List[CaravanRoute] = []
        self.active_caravans: List[Caravan] = []
        
        # AI Controllers
        self.npc_controllers: Dict[str, NPCBehaviorController] = {}
        self.faction_controllers: Dict[str, FactionAIController] = {}
        self.loyalty_engines: Dict[str, FactionLoyaltyEngine] = {}
        
        # Memory and social systems
        self.memory_banks: Dict[str, MemoryBank] = {}
        self.rumor_network = RumorNetwork()
        self.reputation_engine = ReputationEngine()
        self.justice_engine = JusticeEngine()
        
        # Guild system
        self.guild_system = GuildSystem()
        
        # Economic systems
        self.economy_system = EconomyTickSystem()
        
        # Reporting system
        self.reporter = SimulationReporter()
        
        # Threading
        if self.config.multithreading_enabled:
            self.thread_pool = ThreadPoolExecutor(max_workers=self.config.max_worker_threads)
        
        self.logger.info("All subsystems initialized")
    
    def create_world(self, 
                    settlements_config: List[Dict[str, Any]],
                    npcs_config: List[Dict[str, Any]],
                    factions_config: List[Dict[str, Any]]) -> bool:
        """Create the initial world state from configuration."""
        try:
            self.logger.info("Creating world from configuration...")
            
            # Create settlements
            for settlement_data in settlements_config:
                settlement = Settlement(
                    name=settlement_data["name"],
                    initial_population=settlement_data["population"],
                    location=tuple(settlement_data["location"]),
                    founding_year=settlement_data.get("founding_year", 1000)
                )
                if settlement_data.get("governing_faction"):
                    settlement.set_governing_faction(
                        settlement_data["governing_faction"],
                        settlement_data.get("governance_type", "oligarchy")
                    )
                self.settlements.append(settlement)
            
            # Create factions
            for faction_data in factions_config:
                faction = create_faction(
                    faction_data["name"],
                    faction_data["ideology"],
                    faction_data.get("size", "medium"),
                    faction_data.get("influence", 50)
                )
                self.factions.append(faction)
                
                # Create AI controller for faction
                ai_controller = FactionAIController(faction)
                self.faction_controllers[faction.faction_id] = ai_controller
            
            # Create NPCs
            for npc_data in npcs_config:
                npc = generate_npc_profile(
                    npc_data["name"],
                    npc_data.get("archetype", "commoner")
                )
                npc.location = tuple(npc_data.get("location", (0.0, 0.0)))
                
                # Assign to faction if specified
                if npc_data.get("faction"):
                    npc.faction_affiliation = npc_data["faction"]
                
                self.npcs.append(npc)
                
                # Create AI controller and memory bank
                if self.config.npc_ai_enabled:
                    memory_bank = MemoryBank(npc.character_id)
                    self.memory_banks[npc.character_id] = memory_bank
                    
                    npc_controller = NPCBehaviorController(npc)
                    self.npc_controllers[npc.character_id] = npc_controller
                    
                    # Create loyalty engine if NPC has faction
                    if npc.faction_affiliation:
                        loyalty_engine = FactionLoyaltyEngine(npc)
                        self.loyalty_engines[npc.character_id] = loyalty_engine
            
            self.logger.info(f"World created: {len(self.settlements)} settlements, "
                           f"{len(self.npcs)} NPCs, {len(self.factions)} factions")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create world: {e}")
            return False
    
    def start_simulation(self) -> bool:
        """Start the main simulation loop."""
        if self.state.is_running:
            self.logger.warning("Simulation is already running")
            return False
        
        try:
            self.state.is_running = True
            self.state.is_paused = False
            self.state.start_time = datetime.now()
            
            self.logger.info("Starting simulation...")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start simulation: {e}")
            self.state.is_running = False
            return False
    
    def pause_simulation(self):
        """Pause the simulation."""
        self.state.is_paused = True
        self.logger.info("Simulation paused")
    
    def resume_simulation(self):
        """Resume the simulation."""
        self.state.is_paused = False
        self.logger.info("Simulation resumed")
    
    def stop_simulation(self):
        """Stop the simulation."""
        self.state.is_running = False
        self.state.is_paused = False
        self.logger.info("Simulation stopped")
    
    def step_simulation(self) -> Dict[str, Any]:
        """Execute one simulation tick and return results."""
        if not self.state.is_running or self.state.is_paused:
            return {"status": "not_running"}
        
        tick_start = time.time()
        tick_results = {}
        
        try:
            # Increment tick counters
            self.state.current_tick += 1
            self.state.total_ticks += 1
            
            # Check if we need to increment day
            if self.state.current_tick >= self.config.ticks_per_day:
                self.state.current_tick = 0
                self.state.current_day += 1
                tick_results["day_advanced"] = True

                # Start new day log
                self.reporter.start_new_day(self.state.current_day)
            
            # Execute subsystem ticks
            if self.config.multithreading_enabled:
                tick_results.update(self._execute_parallel_tick())
            else:
                tick_results.update(self._execute_sequential_tick())
            
            # Update state statistics
            self._update_state_statistics()
            
            # Performance tracking
            tick_duration = (time.time() - tick_start) * 1000
            self.state.last_tick_duration_ms = tick_duration
            self.tick_times.append(tick_duration)
            
            # Keep only last 100 tick times for average calculation
            if len(self.tick_times) > 100:
                self.tick_times = self.tick_times[-100:]
            
            self.state.average_tick_duration_ms = sum(self.tick_times) / len(self.tick_times)
            self.state.ticks_per_second = 1000.0 / self.state.average_tick_duration_ms if self.state.average_tick_duration_ms > 0 else 0
            
            tick_results.update({
                "status": "success",
                "tick": self.state.current_tick,
                "day": self.state.current_day,
                "duration_ms": tick_duration
            })
            
            return tick_results
            
        except Exception as e:
            self.logger.error(f"Error in simulation tick: {e}")
            return {"status": "error", "error": str(e)}
    
    def _execute_sequential_tick(self) -> Dict[str, Any]:
        """Execute all systems sequentially."""
        results = {}
        
        # Economy tick (if it's a new day)
        if self.state.current_tick == 0 and self.config.economy_enabled:
            self.economy_system.economy_tick(self.settlements)
            results["economy_processed"] = True
        
        # Settlement updates
        update_all_settlements(self.settlements)
        results["settlements_updated"] = len([s for s in self.settlements if s.is_active])
        
        # NPC AI ticks
        if self.config.npc_ai_enabled:
            npc_updates = 0
            for npc_id, controller in self.npc_controllers.items():
                if npc_id in self.memory_banks:
                    controller.simulate_tick(self.memory_banks[npc_id], self.rumor_network)
                    npc_updates += 1
            results["npcs_processed"] = npc_updates
        
        # Faction AI ticks
        if self.config.faction_ai_enabled:
            faction_updates = 0
            for faction_id, controller in self.faction_controllers.items():
                controller.simulate_tick()
                faction_updates += 1
            results["factions_processed"] = faction_updates
        
        # Rumor network tick
        if self.config.rumor_propagation_enabled and self.state.current_tick == 0:  # Daily
            npc_locations = {npc.character_id: npc.location for npc in self.npcs}
            social_connections = self._build_social_connections()
            rumor_stats = self.rumor_network.daily_tick(npc_locations, social_connections)
            results["rumor_stats"] = rumor_stats
        
        # === GUILD SYSTEM TICK ===
        if self.config.guild_systems_enabled and self.state.current_tick == 0:
            if hasattr(self, 'guild_system'):
                guild_log = self.guild_system.tick(self.state.current_day)
                results["guild_log"] = guild_log
                for entry in guild_log:
                    self.reporter.log_guild_event(self.state.current_day, {"event": entry})
        
        # === JUSTICE SYSTEM FINALIZATION ===
        if self.config.justice_system_enabled and self.state.current_tick == 0:
            finalized_cases = 0
            for case in self.justice_engine.get_open_cases():
                case.finalize_case()
                self.reporter.log_justice_outcome(
                    self.state.current_day,
                    case.case_id,
                    case.verdict,
                    ", ".join(case.punishment_applied)
                )
                finalized_cases += 1
            results["justice_cases_finalized"] = finalized_cases
        
        # === CARAVAN SYSTEM TICK ===
        if self.config.trade_routes_enabled and self.state.current_tick == 0:
            from caravan_system import generate_caravans, resolve_caravans

            self.caravan_routes = resolve_caravans(self.state.current_day, self.caravan_routes, self.settlements)
            new_routes = generate_caravans(self.settlements, self.state.current_day)
            self.caravan_routes += new_routes

            for route in new_routes:
                self.reporter.log_caravan_activity(self.state.current_day, f"Caravan dispatched: {route}")

            results["caravans_resolved"] = len(self.caravan_routes)
            results["caravans_generated"] = len(new_routes)
        
        return results
    
    def _execute_parallel_tick(self) -> Dict[str, Any]:
        """Execute systems in parallel using thread pool."""
        results = {}
        futures = []
        
        # Submit parallel tasks
        if self.config.npc_ai_enabled:
            # Batch NPCs for parallel processing
            npc_batches = [list(self.npc_controllers.items())[i:i + self.config.batch_size] 
                          for i in range(0, len(self.npc_controllers), self.config.batch_size)]
            
            for batch in npc_batches:
                future = self.thread_pool.submit(self._process_npc_batch, batch)
                futures.append(("npc_batch", future))
        
        if self.config.faction_ai_enabled:
            future = self.thread_pool.submit(self._process_all_factions)
            futures.append(("factions", future))
        
        # Wait for all tasks to complete
        for task_type, future in futures:
            try:
                result = future.result(timeout=5.0)  # 5 second timeout
                results[f"{task_type}_result"] = result
            except Exception as e:
                self.logger.error(f"Error in {task_type}: {e}")
                results[f"{task_type}_error"] = str(e)
        
        # Sequential tasks that can't be parallelized
        if self.state.current_tick == 0 and self.config.economy_enabled:
            self.economy_system.economy_tick(self.settlements)
            results["economy_processed"] = True
        
        return results
    
    def _process_npc_batch(self, npc_batch: List[Tuple[str, NPCBehaviorController]]) -> int:
        """Process a batch of NPCs."""
        processed = 0
        for npc_id, controller in npc_batch:
            if npc_id in self.memory_banks:
                controller.simulate_tick(self.memory_banks[npc_id], self.rumor_network)
                processed += 1
        return processed
    
    def _process_all_factions(self) -> int:
        """Process all faction AI controllers."""
        processed = 0
        for controller in self.faction_controllers.values():
            controller.simulate_tick()
            processed += 1
        return processed
    
    def _build_social_connections(self) -> Dict[str, List[str]]:
        """Build social connection graph for rumor propagation."""
        # Simple implementation - NPCs connect to others in same faction or nearby location
        connections = {}
        
        for npc in self.npcs:
            npc_connections = []
            
            for other_npc in self.npcs:
                if npc.character_id == other_npc.character_id:
                    continue
                
                # Connect if same faction
                if (npc.faction_affiliation and 
                    npc.faction_affiliation == other_npc.faction_affiliation):
                    npc_connections.append(other_npc.character_id)
                
                # Connect if physically close (within 50 units)
                elif npc.location and other_npc.location:
                    distance = ((npc.location[0] - other_npc.location[0]) ** 2 + 
                               (npc.location[1] - other_npc.location[1]) ** 2) ** 0.5
                    if distance <= 50.0:
                        npc_connections.append(other_npc.character_id)
            
            connections[npc.character_id] = npc_connections
        
        return connections
    
    def _process_justice_cases(self) -> Dict[str, Any]:
        """Process and finalize open justice cases."""
        results = {
            "cases_processed": 0,
            "cases_finalized": 0,
            "verdicts": []
        }
        
        try:
            # Get all open cases from the justice engine
            justice_stats = self.justice_engine.get_case_statistics()
            open_cases = [case for case in self.justice_engine.cases.values() if case.status == "open"]
            
            results["cases_processed"] = len(open_cases)
            
            # Process cases that are ready for finalization (older than 3 days)
            for case in open_cases:
                case_age = self.state.current_day - case.creation_date.day if hasattr(case.creation_date, 'day') else 3
                
                # Finalize cases that are at least 3 days old
                if case_age >= 3:
                    try:
                        finalization_result = case.finalize_case()
                        results["cases_finalized"] += 1
                        results["verdicts"].append({
                            "case_id": case.case_id,
                            "crime_type": case.crime_type,
                            "verdict": finalization_result["verdict"],
                            "punishment": finalization_result["punishment_applied"]
                        })
                        
                        self.logger.info(f"Finalized case {case.case_id}: {finalization_result['verdict']}")
                        
                    except Exception as e:
                        self.logger.error(f"Error finalizing case {case.case_id}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error processing justice cases: {e}")
            results["error"] = str(e)
        
        return results
    
    def _process_caravan_system(self) -> Dict[str, Any]:
        """Process caravan generation and resolution."""
        results = {
            "new_caravans": 0,
            "resolved_caravans": 0,
            "active_caravans": 0,
            "trade_volume": 0
        }
        
        try:
            # Generate new caravans
            new_caravans = generate_caravans(self.settlements, self.state.current_day)
            self.active_caravans.extend(new_caravans)
            results["new_caravans"] = len(new_caravans)
            
            # Resolve completed caravans
            initial_count = len(self.active_caravans)
            resolve_caravans(self.active_caravans, self.settlements, self.state.current_day)
            
            # Count resolved caravans (those that changed status)
            resolved_count = len([c for c in self.active_caravans if c.status in ["delivered", "intercepted"]])
            results["resolved_caravans"] = resolved_count
            
            # Clean up delivered/intercepted caravans older than 7 days
            cutoff_day = self.state.current_day - 7
            self.active_caravans = [
                c for c in self.active_caravans 
                if c.status == "in_transit" or c.departure_day > cutoff_day
            ]
            
            results["active_caravans"] = len([c for c in self.active_caravans if c.status == "in_transit"])
            
            # Calculate total trade volume
            results["trade_volume"] = sum(
                sum(caravan.resource_manifest.values()) 
                for caravan in self.active_caravans 
                if caravan.status == "in_transit"
            )
            
            if new_caravans:
                self.logger.info(f"Generated {len(new_caravans)} new caravans")
            if resolved_count > 0:
                self.logger.info(f"Resolved {resolved_count} caravans")
                
        except Exception as e:
            self.logger.error(f"Error processing caravan system: {e}")
            results["error"] = str(e)
        
        return results
    
    def _update_state_statistics(self):
        """Update simulation state statistics."""
        self.state.active_npcs = len([npc for npc in self.npcs if npc.is_active])
        self.state.active_settlements = len([s for s in self.settlements if s.is_active])
        self.state.active_factions = len(self.factions)
        
        # Update guild statistics from guild system
        if hasattr(self, 'guild_system'):
            guild_status = self.guild_system.get_system_status()
            self.state.active_guilds = guild_status["guild_counts"]["total"]
        else:
            self.state.active_guilds = len(self.guilds)
        
        network_stats = self.rumor_network.get_network_stats()
        self.state.active_rumors = network_stats["total_rumors"]
        
        justice_stats = self.justice_engine.get_case_statistics()
        self.state.active_justice_cases = justice_stats["total_cases"]
        
        # Update caravan statistics
        self.state.active_caravans = len([c for c in self.active_caravans if c.status == "in_transit"])
    
    def get_simulation_status(self) -> Dict[str, Any]:
        """Get current simulation status for external interfaces."""
        return {
            "state": asdict(self.state),
            "config": asdict(self.config),
            "uptime_seconds": (datetime.now() - self.state.start_time).total_seconds() 
                             if self.state.start_time else 0,
            "performance": {
                "last_tick_ms": self.state.last_tick_duration_ms,
                "average_tick_ms": self.state.average_tick_duration_ms,
                "ticks_per_second": self.state.ticks_per_second
            }
        }
    
    def get_world_state(self) -> Dict[str, Any]:
        """Get complete world state for saving or API access."""
        return {
            "settlements": [s.get_status_summary() for s in self.settlements],
            "npcs": [
                {
                    "id": npc.character_id,
                    "name": npc.full_name,
                    "location": npc.location,
                    "faction": npc.faction_affiliation,
                    "archetype": npc.archetype,
                    "status": getattr(self.npc_controllers.get(npc.character_id), 'current_state', 'unknown')
                }
                for npc in self.npcs
            ],
            "factions": [
                {
                    "id": faction.faction_id,
                    "name": faction.name,
                    "ideology": faction.ideology,
                    "member_count": len(faction.members),
                    "influence": faction.influence_score
                }
                for faction in self.factions
            ],
            "rumors": self.rumor_network.get_network_stats(),
            "justice": self.justice_engine.get_case_statistics(),
            "guilds": self.guild_system.get_system_status() if hasattr(self, 'guild_system') else {},
            "caravans": {
                "active": len([c for c in self.active_caravans if c.status == "in_transit"]),
                "total": len(self.active_caravans),
                "trade_volume": sum(sum(c.resource_manifest.values()) for c in self.active_caravans if c.status == "in_transit")
            }
        }
    
    def set_simulation_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Update simulation parameters during runtime."""
        try:
            for key, value in parameters.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    self.logger.info(f"Updated parameter {key} to {value}")
                else:
                    self.logger.warning(f"Unknown parameter: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update parameters: {e}")
            return False
    
    def export_simulation_data(self, format_type: str = "json") -> str:
        """Export simulation data in specified format."""
        data = {
            "metadata": {
                "export_time": datetime.now().isoformat(),
                "simulation_day": self.state.current_day,
                "total_ticks": self.state.total_ticks
            },
            "world_state": self.get_world_state(),
            "simulation_status": self.get_simulation_status()
        }
        
        if format_type.lower() == "json":
            return json.dumps(data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def shutdown(self):
        """Clean shutdown of simulation manager."""
        self.stop_simulation()
        
        if hasattr(self, 'thread_pool'):
            self.thread_pool.shutdown(wait=True)
        
        self.logger.info("SimulationManager shutdown complete")


# Example usage and testing
if __name__ == "__main__":
    # Create sample world configuration
    settlements_config = [
        {
            "name": "Riverside",
            "population": 150,
            "location": [10.0, 20.0],
            "founding_year": 980
        },
        {
            "name": "Millbrook",
            "population": 450,
            "location": [15.0, 18.0],
            "founding_year": 960,
            "governing_faction": "merchants_guild"
        }
    ]
    
    factions_config = [
        {
            "name": "Merchants Guild",
            "ideology": {"trade": 0.8, "prosperity": 0.7, "regulation": 0.3},
            "size": "large",
            "influence": 75
        },
        {
            "name": "City Watch",
            "ideology": {"order": 0.9, "justice": 0.8, "authority": 0.7},
            "size": "medium",
            "influence": 60
        }
    ]
    
    npcs_config = [
        {
            "name": "Marcus the Merchant",
            "archetype": "merchant",
            "location": [15.0, 18.0],
            "faction": "merchants_guild"
        },
        {
            "name": "Captain Sarah",
            "archetype": "guardian",
            "location": [10.0, 20.0],
            "faction": "city_watch"
        }
    ]
    
    # Initialize and test simulation
    config = SimulationConfig(
        ticks_per_day=24,
        simulation_speed=1.0,
        multithreading_enabled=True,
        max_worker_threads=2
    )
    
    sim = SimulationManager(config)
    
    print("=== Age of Scribes Simulation Manager Test ===")
    print("Creating world...")
    if sim.create_world(settlements_config, npcs_config, factions_config):
        print("World created successfully!")
        
        print("\nStarting simulation...")
        if sim.start_simulation():
            print("Simulation started!")
            
            # Run for 10 ticks
            for i in range(10):
                result = sim.step_simulation()
                print(f"Tick {i+1}: {result['status']} "
                      f"({result.get('duration_ms', 0):.1f}ms)")
                
                if result.get("day_advanced"):
                    print(f"  Day advanced to {result['day']}")
                
                time.sleep(0.1)  # Small delay for demonstration
            
            # Get final status
            status = sim.get_simulation_status()
            print(f"\nFinal Status:")
            print(f"  Day: {status['state']['current_day']}")
            print(f"  Total ticks: {status['state']['total_ticks']}")
            print(f"  Active NPCs: {status['state']['active_npcs']}")
            print(f"  Avg tick time: {status['performance']['average_tick_ms']:.1f}ms")
            
            sim.shutdown()
    else:
        print("Failed to create world!")