#!/usr/bin/env python3
"""
REST API for Age of Scribes Simulation Engine
==============================================

Flask-based REST API wrapper for the SimulationManager, designed to interface
with Flutter mobile/desktop applications. Provides endpoints for simulation
control, parameter adjustment, and real-time data access.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import threading
import time

from simulation_manager import SimulationManager, SimulationConfig


class SimulationAPI:
    """REST API wrapper for the simulation engine."""
    
    def __init__(self, port: int = 5000, debug: bool = False):
        """Initialize the Flask API server."""
        self.app = Flask(__name__)
        CORS(self.app)  # Enable cross-origin requests for Flutter
        
        self.port = port
        self.debug = debug
        self.simulation_manager: Optional[SimulationManager] = None
        self.auto_tick_thread: Optional[threading.Thread] = None
        self.auto_tick_running = False
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register all API endpoints."""
        
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Get current simulation status."""
            if not self.simulation_manager:
                return jsonify({"error": "Simulation not initialized"}), 400
            
            status = self.simulation_manager.get_simulation_status()
            return jsonify(status)
        
        @self.app.route('/api/world', methods=['GET'])
        def get_world_state():
            """Get complete world state."""
            if not self.simulation_manager:
                return jsonify({"error": "Simulation not initialized"}), 400
            
            world_state = self.simulation_manager.get_world_state()
            return jsonify(world_state)
        
        @self.app.route('/api/initialize', methods=['POST'])
        def initialize_simulation():
            """Initialize a new simulation world."""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "No configuration provided"}), 400
                
                # Extract configuration
                config_data = data.get('config', {})
                config = SimulationConfig(**config_data)
                
                # Initialize simulation manager
                self.simulation_manager = SimulationManager(config)
                
                # Create world if data provided
                settlements = data.get('settlements', [])
                npcs = data.get('npcs', [])
                factions = data.get('factions', [])
                
                if settlements or npcs or factions:
                    success = self.simulation_manager.create_world(settlements, npcs, factions)
                    if not success:
                        return jsonify({"error": "Failed to create world"}), 500
                
                return jsonify({
                    "status": "success",
                    "message": "Simulation initialized successfully"
                })
                
            except Exception as e:
                self.logger.error(f"Error initializing simulation: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/start', methods=['POST'])
        def start_simulation():
            """Start the simulation."""
            if not self.simulation_manager:
                return jsonify({"error": "Simulation not initialized"}), 400
            
            success = self.simulation_manager.start_simulation()
            if success:
                return jsonify({"status": "success", "message": "Simulation started"})
            else:
                return jsonify({"error": "Failed to start simulation"}), 500
        
        @self.app.route('/api/pause', methods=['POST'])
        def pause_simulation():
            """Pause the simulation."""
            if not self.simulation_manager:
                return jsonify({"error": "Simulation not initialized"}), 400
            
            self.simulation_manager.pause_simulation()
            return jsonify({"status": "success", "message": "Simulation paused"})
        
        @self.app.route('/api/resume', methods=['POST'])
        def resume_simulation():
            """Resume the simulation."""
            if not self.simulation_manager:
                return jsonify({"error": "Simulation not initialized"}), 400
            
            self.simulation_manager.resume_simulation()
            return jsonify({"status": "success", "message": "Simulation resumed"})
        
        @self.app.route('/api/stop', methods=['POST'])
        def stop_simulation():
            """Stop the simulation."""
            if not self.simulation_manager:
                return jsonify({"error": "Simulation not initialized"}), 400
            
            self.simulation_manager.stop_simulation()
            self._stop_auto_tick()
            return jsonify({"status": "success", "message": "Simulation stopped"})
        
        @self.app.route('/api/step', methods=['POST'])
        def step_simulation():
            """Execute one simulation tick."""
            if not self.simulation_manager:
                return jsonify({"error": "Simulation not initialized"}), 400
            
            result = self.simulation_manager.step_simulation()
            return jsonify(result)
        
        @self.app.route('/api/auto-tick/start', methods=['POST'])
        def start_auto_tick():
            """Start automatic ticking at specified interval."""
            if not self.simulation_manager:
                return jsonify({"error": "Simulation not initialized"}), 400
            
            data = request.get_json() or {}
            interval_ms = data.get('interval_ms', 1000)  # Default 1 second
            
            self._start_auto_tick(interval_ms / 1000.0)
            return jsonify({
                "status": "success", 
                "message": "Auto-tick started",
                "interval_ms": interval_ms
            })
        
        @self.app.route('/api/auto-tick/stop', methods=['POST'])
        def stop_auto_tick():
            """Stop automatic ticking."""
            self._stop_auto_tick()
            return jsonify({"status": "success", "message": "Auto-tick stopped"})
        
        @self.app.route('/api/parameters', methods=['GET'])
        def get_parameters():
            """Get current simulation parameters."""
            if not self.simulation_manager:
                return jsonify({"error": "Simulation not initialized"}), 400
            
            from dataclasses import asdict
            return jsonify(asdict(self.simulation_manager.config))
        
        @self.app.route('/api/parameters', methods=['POST'])
        def set_parameters():
            """Update simulation parameters."""
            if not self.simulation_manager:
                return jsonify({"error": "Simulation not initialized"}), 400
            
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "No parameters provided"}), 400
                
                success = self.simulation_manager.set_simulation_parameters(data)
                if success:
                    return jsonify({"status": "success", "message": "Parameters updated"})
                else:
                    return jsonify({"error": "Failed to update parameters"}), 500
                    
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/export', methods=['GET'])
        def export_data():
            """Export simulation data."""
            if not self.simulation_manager:
                return jsonify({"error": "Simulation not initialized"}), 400
            
            format_type = request.args.get('format', 'json')
            
            try:
                data = self.simulation_manager.export_simulation_data(format_type)
                
                if format_type.lower() == 'json':
                    return Response(data, mimetype='application/json')
                else:
                    return Response(data, mimetype='text/plain')
                    
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/settlements', methods=['GET'])
        def get_settlements():
            """Get detailed settlement information."""
            if not self.simulation_manager:
                return jsonify({"error": "Simulation not initialized"}), 400
            
            settlements_data = []
            for settlement in self.simulation_manager.settlements:
                settlement_info = settlement.get_status_summary()
                settlement_info['resources'] = settlement.get_resource_summary()
                settlements_data.append(settlement_info)
            
            return jsonify(settlements_data)
        
        @self.app.route('/api/npcs', methods=['GET'])
        def get_npcs():
            """Get detailed NPC information."""
            if not self.simulation_manager:
                return jsonify({"error": "Simulation not initialized"}), 400
            
            npc_data = []
            for npc in self.simulation_manager.npcs:
                npc_info = {
                    "id": npc.character_id,
                    "name": npc.full_name,
                    "archetype": npc.archetype,
                    "location": npc.location,
                    "faction": npc.faction_affiliation,
                    "personality": npc.personality_traits,
                    "beliefs": npc.belief_system,
                    "is_active": npc.is_active
                }
                
                # Add AI state if available
                if npc.character_id in self.simulation_manager.npc_controllers:
                    controller = self.simulation_manager.npc_controllers[npc.character_id]
                    npc_info.update({
                        "current_state": controller.current_state,
                        "stress_level": controller.stress_level,
                        "daily_routine": controller.daily_routine
                    })
                
                npc_data.append(npc_info)
            
            return jsonify(npc_data)
        
        @self.app.route('/api/factions', methods=['GET'])
        def get_factions():
            """Get detailed faction information."""
            if not self.simulation_manager:
                return jsonify({"error": "Simulation not initialized"}), 400
            
            faction_data = []
            for faction in self.simulation_manager.factions:
                faction_info = {
                    "id": faction.faction_id,
                    "name": faction.name,
                    "ideology": faction.ideology,
                    "goals": faction.goals,
                    "members": faction.members,
                    "influence_score": faction.influence_score,
                    "resources": faction.resources
                }
                
                # Add AI state if available
                if faction.faction_id in self.simulation_manager.faction_controllers:
                    controller = self.simulation_manager.faction_controllers[faction.faction_id]
                    faction_info.update({
                        "member_satisfaction": controller.member_satisfaction,
                        "internal_pressure": controller.internal_pressure,
                        "external_pressure": controller.external_pressure
                    })
                
                faction_data.append(faction_info)
            
            return jsonify(faction_data)
        
        @self.app.route('/api/rumors', methods=['GET'])
        def get_rumors():
            """Get current rumors in the network."""
            if not self.simulation_manager:
                return jsonify({"error": "Simulation not initialized"}), 400
            
            rumor_stats = self.simulation_manager.rumor_network.get_network_stats()
            
            # Get sample of recent rumors
            recent_rumors = []
            for rumor in self.simulation_manager.rumor_network.active_rumors[:20]:  # Last 20
                recent_rumors.append({
                    "id": rumor.rumor_id,
                    "content": rumor.content,
                    "confidence": rumor.confidence_level,
                    "spread_count": rumor.spread_count,
                    "originator": rumor.originator_id,
                    "location": rumor.location_origin
                })
            
            return jsonify({
                "stats": rumor_stats,
                "recent_rumors": recent_rumors
            })
        
        @self.app.route('/api/justice', methods=['GET'])
        def get_justice_cases():
            """Get justice system information."""
            if not self.simulation_manager:
                return jsonify({"error": "Simulation not initialized"}), 400
            
            justice_stats = self.simulation_manager.justice_engine.get_case_statistics()
            return jsonify(justice_stats)
        
        @self.app.route('/api/scenarios/list', methods=['GET'])
        def list_scenarios():
            """List available pre-built scenarios."""
            scenarios = [
                {
                    "id": "merchant_guild_conflict",
                    "name": "Merchant Guild Power Struggle",
                    "description": "Economic tensions lead to political upheaval",
                    "duration_days": 30,
                    "npcs": 25,
                    "settlements": 3,
                    "factions": 4
                },
                {
                    "id": "false_accusation",
                    "name": "False Accusation Crisis",
                    "description": "Justice system tested by false allegations",
                    "duration_days": 14,
                    "npcs": 15,
                    "settlements": 1,
                    "factions": 3
                },
                {
                    "id": "resource_shortage",
                    "name": "Regional Resource Crisis",
                    "description": "Economic collapse threatens multiple settlements",
                    "duration_days": 60,
                    "npcs": 50,
                    "settlements": 5,
                    "factions": 6
                }
            ]
            return jsonify(scenarios)
        
        @self.app.route('/api/scenarios/<scenario_id>/load', methods=['POST'])
        def load_scenario(scenario_id: str):
            """Load a pre-built scenario."""
            scenarios = self._get_scenario_configs()
            
            if scenario_id not in scenarios:
                return jsonify({"error": "Scenario not found"}), 404
            
            try:
                scenario_config = scenarios[scenario_id]
                
                # Initialize with scenario config
                config = SimulationConfig(**scenario_config.get('simulation_config', {}))
                self.simulation_manager = SimulationManager(config)
                
                # Create world
                success = self.simulation_manager.create_world(
                    scenario_config['settlements'],
                    scenario_config['npcs'],
                    scenario_config['factions']
                )
                
                if success:
                    return jsonify({
                        "status": "success",
                        "message": f"Scenario '{scenario_id}' loaded successfully"
                    })
                else:
                    return jsonify({"error": "Failed to load scenario"}), 500
                    
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "simulation_initialized": self.simulation_manager is not None,
                "auto_tick_running": self.auto_tick_running
            })
    
    def _start_auto_tick(self, interval_seconds: float):
        """Start automatic simulation ticking."""
        if self.auto_tick_running:
            self._stop_auto_tick()
        
        self.auto_tick_running = True
        
        def tick_loop():
            while self.auto_tick_running:
                if self.simulation_manager and self.simulation_manager.state.is_running:
                    try:
                        self.simulation_manager.step_simulation()
                    except Exception as e:
                        self.logger.error(f"Error in auto-tick: {e}")
                
                time.sleep(interval_seconds)
        
        self.auto_tick_thread = threading.Thread(target=tick_loop, daemon=True)
        self.auto_tick_thread.start()
        self.logger.info(f"Auto-tick started with interval {interval_seconds}s")
    
    def _stop_auto_tick(self):
        """Stop automatic simulation ticking."""
        self.auto_tick_running = False
        if self.auto_tick_thread and self.auto_tick_thread.is_alive():
            self.auto_tick_thread.join(timeout=1.0)
        self.logger.info("Auto-tick stopped")
    
    def _get_scenario_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get predefined scenario configurations."""
        return {
            "merchant_guild_conflict": {
                "simulation_config": {
                    "ticks_per_day": 24,
                    "max_npcs": 100,
                    "economy_enabled": True,
                    "faction_ai_enabled": True
                },
                "settlements": [
                    {
                        "name": "Tradehaven",
                        "population": 800,
                        "location": [50.0, 50.0],
                        "governing_faction": "merchants_guild"
                    },
                    {
                        "name": "Craftsburg",
                        "population": 400,
                        "location": [75.0, 30.0]
                    }
                ],
                "factions": [
                    {
                        "name": "Merchants Guild",
                        "ideology": {"trade": 0.9, "profit": 0.8, "regulation": 0.2},
                        "size": "large",
                        "influence": 85
                    },
                    {
                        "name": "Artisans Union",
                        "ideology": {"craftsmanship": 0.9, "fair_wages": 0.8, "tradition": 0.7},
                        "size": "medium",
                        "influence": 65
                    }
                ],
                "npcs": [
                    {
                        "name": "Guildmaster Aldric",
                        "archetype": "leader",
                        "location": [50.0, 50.0],
                        "faction": "merchants_guild"
                    },
                    {
                        "name": "Master Craftswoman Elena",
                        "archetype": "artisan",
                        "location": [75.0, 30.0],
                        "faction": "artisans_union"
                    }
                ]
            }
        }
    
    def run(self):
        """Start the Flask development server."""
        self.logger.info(f"Starting Age of Scribes API server on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=self.debug, threaded=True)
    
    def shutdown(self):
        """Shutdown the API server and clean up resources."""
        self._stop_auto_tick()
        if self.simulation_manager:
            self.simulation_manager.shutdown()
        self.logger.info("API server shutdown complete")


# Production WSGI application
def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    """Factory function to create Flask app for production deployment."""
    api = SimulationAPI()
    return api.app


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Age of Scribes API Server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run server on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    api = SimulationAPI(port=args.port, debug=args.debug)
    
    try:
        api.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        api.shutdown()