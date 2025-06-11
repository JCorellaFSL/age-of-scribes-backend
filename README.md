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

### Core Simulation Systems

**🏘️ Settlement System**
- Five-tier settlement hierarchy (Hamlet → Village → Town → Small City → Large City)
- Dynamic population growth and resource management
- Organic settlement evolution and potential collapse
- Complex governance structures with faction control

**🤖 NPC AI System**
- Autonomous character behavior with daily routines
- Personality-driven decision making
- Memory-based learning and emotional responses
- Social relationship tracking and interaction systems

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
- Legal framework with crime investigation
- Multi-party conflict resolution
- Reputation-based social consequences
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

### Emergent Gameplay
- **Dynamic Story Generation**: Character-driven events create unique narrative experiences
- **Persistent Consequences**: Actions have lasting effects on NPCs, settlements, and factions
- **Organic World Evolution**: Settlements grow, factions rise and fall, economies shift over time
- **Realistic Social Pressure**: Characters respond to stress, memory, and social dynamics

### Technical Excellence
- **Modular Architecture**: Easy integration with existing game engines and frameworks
- **Performance Optimized**: Handles hundreds of NPCs and dozens of settlements efficiently
- **Event-Driven Design**: Clean separation of concerns with observable state changes
- **Extensible Framework**: Add new systems, resources, or mechanics without core modifications

### Rich Simulation Depth
- **Multi-layered Relationships**: Characters track complex social connections and grudges
- **Economic Interdependence**: Settlement success depends on trade networks and resource management
- **Political Intrigue**: Faction machinations create opportunities for player involvement
- **Character Growth**: NPCs learn, adapt, and change based on their experiences

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Basic understanding of object-oriented programming
- Familiarity with game development or simulation concepts (helpful but not required)

### Quick Start
```python
from settlement_system import SettlementManager
from npc_ai import NPCBehaviorController
from faction_generator import create_faction

# Create a living world
world = SettlementManager()
world.create_settlement("Millbrook", initial_population=150)

# Add autonomous NPCs
from npc_profile import generate_npc_profile
character = generate_npc_profile("Elara the Merchant")
ai_controller = NPCBehaviorController(character)

# Simulate time passage
world.simulate_day()
ai_controller.simulate_tick(memory_bank, rumor_network)
```

### Integration Examples
- **Unity/Unreal**: Use as backend service for world state management
- **Web Games**: REST API wrapper for browser-based experiences  
- **Discord Bots**: Create living campaign worlds for tabletop groups
- **Procedural Content**: Generate quest content based on faction conflicts and NPC needs

## 📚 Documentation

Comprehensive documentation is available in the repository:
- `Age_of_Scribes_Master_Documentation.txt` - Complete technical specifications
- Individual system documentation in Python docstrings
- Example implementations and usage patterns
- Integration guides for popular game engines

## 📈 Roadmap

- **Multi-threading Support**: Parallel processing for large simulations
- **Save/Load System**: Persistent world state management
- **Visual Analytics**: Real-time simulation monitoring and debugging tools
- **Mod Framework**: Plugin system for custom content and mechanics
- **Cloud Deployment**: Scalable simulation hosting for multiplayer experiences

## 📄 License

Licensed under MIT License - see LICENSE file for details.

---

*Age of Scribes transforms static game worlds into living societies where every character has a story, every choice matters, and every playthrough creates unique emergent narratives.*
