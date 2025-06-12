# Age of Scribes - Social Simulation Engine (SSE)

**A comprehensive Python backend simulation engine for creating living, breathing social worlds with autonomous NPCs, dynamic settlements, emergent economies, and complex faction relationships.**

## 🌟 Overview

Age of Scribes SSE is a sophisticated social simulation engine designed to power narrative-driven games, interactive fiction, tabletop RPG campaigns, and educational simulations. The engine creates believable virtual societies where NPCs pursue their own goals, settlements evolve organically, economies respond to supply and demand, and factions vie for power - all without direct player intervention.

## 🎯 Core Philosophy

- **Emergent Storytelling**: Complex narratives emerge naturally from simple rules and character interactions
- **Autonomous Behavior**: NPCs make decisions based on personality, memories, relationships, and circumstances
- **Living World**: The simulation continues to evolve even when players aren't actively engaged
- **Realistic Social Dynamics**: Characters form relationships, spread rumors, hold grudges, and build reputations
- **Dynamic Economy**: Resource production, trade networks, and economic pressures drive settlement development

## 🏛️ System Architecture

### Master Orchestration

**🎛️ Simulation Manager**
- Master orchestration system coordinating all subsystems
- Sequential and parallel execution modes for optimal performance
- Real-time performance monitoring and optimization
- External API integration for dashboards and control interfaces
- Comprehensive world state management and persistence

**📊 Simulation Reporting**
- Structured daily event logging and analysis
- Categorized event tracking (NPCs, guilds, justice, caravans, notable events)
- JSON export capabilities for external analysis tools
- Memory management with configurable retention periods
- Integration hooks for dashboard systems and monitoring

### Core Simulation Systems

**🏘️ Settlement System**
- Five-tier settlement hierarchy (Hamlet → Village → Town → Small City → Large City)
- Dynamic population growth and resource management
- Organic settlement evolution and potential collapse
- Complex governance structures with faction control

**🤖 NPC AI System**
- Autonomous character behavior with daily routines and comprehensive career simulation
- Personality-driven decision making with dynamic career transitions
- Memory-based learning and emotional responses
- Social relationship tracking and interaction systems

**🏛️ Guild System**
- Dynamic professional organizations with autonomous management
- Comprehensive guild lifecycle (formation, elections, events, conflicts)
- NPC-driven guild membership and career progression
- Guild facilities, vaults, and resource sharing systems
- Equal opportunity mechanics for NPCs and player characters

**🏛️ Faction Dynamics**
- Political organizations with evolving ideologies
- Internal pressure and external threat response
- Dynamic goal adjustment and member satisfaction
- Leadership changes and organizational evolution

**💰 Economy Simulation**
- Eight-resource economy (Food, Ore, Cloth, Wood, Stone, Tools, Luxury, Magic Components)
- Supply chain management and trade network simulation
- Caravan system for inter-settlement commerce
- Economic pressure-driven narrative events

**⚖️ Justice System**
- Legal framework with crime investigation and case resolution
- Multi-party conflict resolution with reputation consequences
- Integrated punishment system with social impacts
- Integration with faction politics and character relationships

**🧠 Supporting Systems**
- **Memory Core**: Persistent character memory with emotional weighting
- **Rumor Engine**: Information spread and social influence simulation
- **Reputation Tracker**: Multi-dimensional social standing system
- **NPC Profile Generator**: Detailed character creation with backgrounds and motivations

## 🎮 Target Audience

### Game Developers
- **Indie RPG Studios**: Add depth to world simulation without building from scratch
- **Narrative Game Designers**: Create dynamic stories that respond to emergent character behavior
- **Strategy Game Developers**: Implement realistic civilian populations and political systems
- **Open World Developers**: Populate persistent worlds with believable, autonomous inhabitants

### Tabletop RPG Community
- **Game Masters**: Generate living campaign worlds with evolving NPCs and political situations
- **Campaign Managers**: Track complex political relationships and economic systems across sessions
- **World Builders**: Create detailed, self-sustaining fantasy or historical settings
- **Solo RPG Players**: Experience dynamic storytelling with minimal preparation

### Educational and Research Applications
- **Sociology Researchers**: Model social dynamics and organizational behavior
- **Game Design Students**: Study emergent narrative systems and AI behavior
- **History Educators**: Simulate historical societies and economic systems
- **Social Science**: Explore group dynamics, rumor propagation, and reputation systems

### Interactive Fiction Authors
- **Choose Your Own Adventure**: Create branching narratives with persistent character consequences
- **Interactive Novels**: Build stories where character relationships evolve based on reader choices
- **Procedural Storytelling**: Generate unique narrative experiences through character interactions

## ⚡ Key Features

### Production-Ready Architecture
- **Master Orchestration**: SimulationManager coordinates all subsystems with performance monitoring
- **Comprehensive Reporting**: Structured event logging with JSON export and analytics
- **Performance Optimized**: Handles 1000+ NPCs and dozens of settlements with multi-threading support
- **External Integration**: Built-in REST API for dashboards, monitoring, and control interfaces
- **Modular Design**: Easy integration with existing game engines and frameworks

### Emergent Gameplay
- **Dynamic Story Generation**: Character-driven events create unique narrative experiences
- **Guild-Driven Narratives**: Professional organizations create conflicts, opportunities, and career paths
- **Persistent Consequences**: Actions have lasting effects tracked through comprehensive reporting
- **Organic World Evolution**: Settlements grow, guilds form/dissolve, economies shift over time
- **Realistic Social Dynamics**: Characters respond to stress, memory, reputation, and career ambitions

### Rich Simulation Depth
- **Professional Career Simulation**: NPCs pursue realistic career paths with guild membership
- **Multi-layered Justice System**: Legal framework with reputation consequences and case tracking
- **Economic Interdependence**: Settlement success depends on trade networks and guild activities
- **Political Intrigue**: Faction and guild machinations create opportunities for player involvement
- **Character Growth**: NPCs learn, adapt, change careers, and form lasting relationships

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Basic understanding of object-oriented programming
- Familiarity with game development or simulation concepts (helpful but not required)

### Quick Start
```python
from simulation_manager import SimulationManager, SimulationConfig

# Create a complete simulation world
config = SimulationConfig(
    ticks_per_day=24,
    max_npcs=1000,
    guild_systems_enabled=True,
    justice_system_enabled=True
)

sim = SimulationManager(config)

# Define your world
settlements_config = [
    {
        "name": "Riverside",
        "population": 150,
        "location": [10.0, 20.0],
        "founding_year": 980
    }
]

npcs_config = [
    {
        "name": "Marcus the Merchant",
        "archetype": "merchant",
        "location": [10.0, 20.0]
    }
]

factions_config = [
    {
        "name": "Merchants Guild",
        "ideology": {"trade": 0.8, "prosperity": 0.7},
        "size": "large"
    }
]

# Initialize and run simulation
sim.create_world(settlements_config, npcs_config, factions_config)
sim.start_simulation()

# Run simulation steps
for day in range(10):
    for tick in range(24):
        results = sim.step_simulation()
        if results.get("day_advanced"):
            print(f"Day {results['day']} completed")
            # Access daily reports
            daily_report = sim.reporter.get_report(results['day'])
            print(f"Guild events: {len(daily_report.get('guild_events', []))}")
```

### Integration Examples
- **Unity/Unreal**: Use SimulationManager as backend service for world state management
- **Web Games**: Built-in REST API (`rest_api.py`) for browser-based experiences  
- **Discord Bots**: Create living campaign worlds with daily report integration
- **Dashboard Applications**: Real-time monitoring via SimulationReporter analytics
- **Procedural Content**: Generate quest content based on guild conflicts and justice system events

## 📚 Documentation

Comprehensive documentation is available in the repository:
- `Age_of_Scribes_Master_Documentation.txt` - Complete technical specifications
- Individual system documentation in Python docstrings
- Example implementations and usage patterns
- Integration guides for popular game engines

## 📈 Recent Updates

### Version 0.0.5.0 - Master Orchestration Edition
- ✅ **SimulationManager**: Complete master orchestration system with performance monitoring
- ✅ **SimulationReporter**: Structured daily event logging and analysis system
- ✅ **Guild System**: Comprehensive professional organizations with autonomous management
- ✅ **Enhanced NPC AI**: Career transitions and guild integration
- ✅ **Justice System Integration**: Automated case resolution with reporting
- ✅ **REST API**: Complete web interface for external applications

## 📈 Future Roadmap

- **Enhanced Multi-threading**: Advanced parallel processing optimizations
- **Persistent Storage**: Database integration for long-term world persistence  
- **Visual Analytics Dashboard**: Web-based real-time simulation monitoring
- **Mod Framework**: Plugin system for custom content and mechanics
- **Cloud Deployment**: Scalable simulation hosting for multiplayer experiences
- **AI-Driven Events**: Machine learning for dynamic story generation

## 📄 License

Licensed under MIT License - see LICENSE file for details.

---

*Age of Scribes transforms static game worlds into living societies where every character has a story, every choice matters, and every playthrough creates unique emergent narratives.*
