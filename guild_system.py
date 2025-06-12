#!/usr/bin/env python3
"""
Guild System - Centralized Management for Guilds and Events
==========================================================

This module provides a centralized system to manage active guilds and their
ongoing events, integrating with the guild event engine to provide seamless
simulation coordination and logging capabilities.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

# Import guild-related classes
from guild_event_engine import GuildEvent, LocalGuild, RegionalGuild, generate_guild_events, apply_guild_events
from guild_formation_system import GuildFormationProposal
from guild_elections_system import GuildElection
from guild_summits_system import GuildSummit


class GuildSystem:
    """
    Centralized management system for all guild operations and events.
    
    This class coordinates guild activities, manages event lifecycles, and provides
    logging and reporting capabilities for simulation integration and debugging.
    """
    
    def __init__(self):
        """Initialize the guild system."""
        # Core guild storage
        self.guilds: List[Union[LocalGuild, RegionalGuild]] = []
        
        # Event management
        self.events: List[GuildEvent] = []
        self.resolved_events: List[GuildEvent] = []
        
        # Special guild processes
        self.active_formations: List[GuildFormationProposal] = []
        self.active_elections: List[GuildElection] = []
        self.active_summits: List[GuildSummit] = []
        
        # System state
        self.current_day = 0
        self.total_events_processed = 0
        self.last_event_generation = 0
        
        # Logging
        self.logger = logging.getLogger(__name__)
        self.daily_logs: List[str] = []
        self.system_stats = {
            'events_resolved_today': 0,
            'new_events_today': 0,
            'guilds_created_today': 0,
            'guilds_disbanded_today': 0
        }
    
    def add_guild(self, guild: Union[LocalGuild, RegionalGuild]) -> bool:
        """
        Add a guild to the system.
        
        Args:
            guild: The guild to add
            
        Returns:
            True if added successfully, False if guild ID already exists
        """
        # Check for duplicate IDs
        for existing_guild in self.guilds:
            if existing_guild.guild_id == guild.guild_id:
                self.logger.warning(f"Guild ID {guild.guild_id} already exists")
                return False
        
        self.guilds.append(guild)
        self.logger.info(f"Added guild: {guild.name} ({guild.guild_id})")
        self.system_stats['guilds_created_today'] += 1
        return True
    
    def remove_guild(self, guild_id: str, reason: str = "disbanded") -> bool:
        """
        Remove a guild from the system.
        
        Args:
            guild_id: ID of the guild to remove
            reason: Reason for removal
            
        Returns:
            True if removed successfully, False if not found
        """
        for i, guild in enumerate(self.guilds):
            if guild.guild_id == guild_id:
                guild_name = guild.name
                del self.guilds[i]
                
                # Clean up related events
                self._cleanup_guild_events(guild_id, reason)
                
                self.logger.info(f"Removed guild: {guild_name} ({guild_id}) - {reason}")
                self.system_stats['guilds_disbanded_today'] += 1
                return True
        
        self.logger.warning(f"Guild {guild_id} not found for removal")
        return False
    
    def get_guild_by_id(self, guild_id: str) -> Optional[Union[LocalGuild, RegionalGuild]]:
        """
        Get a guild by its ID.
        
        Args:
            guild_id: The guild ID to search for
            
        Returns:
            The guild if found, None otherwise
        """
        for guild in self.guilds:
            if guild.guild_id == guild_id:
                return guild
        return None
    
    def add_event(self, event: GuildEvent) -> bool:
        """
        Add a new guild event to the system.
        
        Args:
            event: The event to add
            
        Returns:
            True if added successfully
        """
        self.events.append(event)
        self.logger.info(f"Added event: {event.event_type} for guild {event.guild_id}")
        self.system_stats['new_events_today'] += 1
        return True
    
    def tick(self, current_day: int) -> List[str]:
        """
        Advance all guild events and systems by one day.
        
        Args:
            current_day: The current simulation day
            
        Returns:
            List of log messages describing what happened
        """
        self.current_day = current_day
        log = []
        
        # Reset daily stats
        self.system_stats = {
            'events_resolved_today': 0,
            'new_events_today': 0,
            'guilds_created_today': 0,
            'guilds_disbanded_today': 0
        }
        
        # Process active guild events
        log.extend(self._process_active_events(current_day))
        
        # Update all guild daily states
        log.extend(self._update_guild_states(current_day))
        
        # Process special guild activities
        log.extend(self._process_formations(current_day))
        log.extend(self._process_elections(current_day))
        log.extend(self._process_summits(current_day))
        
        # Generate new events periodically
        if current_day - self.last_event_generation >= 3:  # Every 3 days
            log.extend(self._generate_new_events(current_day))
            self.last_event_generation = current_day
        
        # Store daily logs
        self.daily_logs = log
        
        return log
    
    def _process_active_events(self, current_day: int) -> List[str]:
        """Process all active guild events."""
        log = []
        
        for event in list(self.events):  # Copy to allow removal
            result = event.advance_day()
            
            if result["status"] == "concluded":
                # Event has concluded
                self.resolved_events.append(event)
                self.events.remove(event)
                self.total_events_processed += 1
                self.system_stats['events_resolved_today'] += 1
                
                # Apply resolution effects to guild
                self._apply_event_resolution(event, result)
                
                log.append(f"Event resolved: {event.event_type} in guild {event.guild_id} - {result.get('outcome', 'unknown')}")
                
            elif result["status"] == "ongoing":
                # Event continues
                daily_effects = result.get('daily_effects', {})
                if daily_effects:
                    self._apply_daily_effects(event, daily_effects)
                
                log.append(f"Day {current_day}: {event.event_type} ongoing in guild {event.guild_id} ({result['days_remaining']} days left)")
            
            elif result["status"] == "inactive":
                # Event became inactive somehow
                log.append(f"Event {event.event_type} in guild {event.guild_id} became inactive")
        
        return log
    
    def _update_guild_states(self, current_day: int) -> List[str]:
        """Update daily state for all guilds."""
        log = []
        
        for guild in self.guilds:
            if hasattr(guild, 'update_daily_state'):
                changes = guild.update_daily_state(current_day)
                
                # Log significant changes
                if abs(changes.get('influence_change', 0)) > 1.0:
                    log.append(f"{guild.name} influence changed by {changes['influence_change']:+.1f}")
                
                if changes.get('conflict_status_changed'):
                    log.append(f"{guild.name} conflict status changed to {guild.conflict_status.value}")
                
                if changes.get('member_count_change', 0) != 0:
                    change = changes['member_count_change']
                    action = "gained" if change > 0 else "lost"
                    log.append(f"{guild.name} {action} {abs(change)} member(s)")
        
        return log
    
    def _process_formations(self, current_day: int) -> List[str]:
        """Process active guild formation proposals."""
        log = []
        
        for formation in list(self.active_formations):
            if hasattr(formation, 'advance_day'):
                result = formation.advance_day()
                
                if result.get('status') == 'completed':
                    if result.get('success'):
                        # New guild formed
                        new_guild = result.get('guild')
                        if new_guild:
                            self.add_guild(new_guild)
                            log.append(f"New guild formed: {new_guild.name}")
                    
                    self.active_formations.remove(formation)
                    log.append(f"Guild formation proposal resolved: {result.get('outcome', 'unknown')}")
        
        return log
    
    def _process_elections(self, current_day: int) -> List[str]:
        """Process active guild elections."""
        log = []
        
        for election in list(self.active_elections):
            if hasattr(election, 'advance_day'):
                result = election.advance_day()
                
                if result.get('status') == 'completed':
                    self.active_elections.remove(election)
                    log.append(f"Guild election completed in {election.guild_id}: {result.get('winner', 'unknown')} elected")
        
        return log
    
    def _process_summits(self, current_day: int) -> List[str]:
        """Process active guild summits."""
        log = []
        
        for summit in list(self.active_summits):
            if hasattr(summit, 'advance_day'):
                result = summit.advance_day()
                
                if result.get('status') == 'completed':
                    self.active_summits.remove(summit)
                    log.append(f"Guild summit concluded: {result.get('outcome', 'unknown')}")
        
        return log
    
    def _generate_new_events(self, current_day: int) -> List[str]:
        """Generate new events for guilds."""
        log = []
        
        # Only generate events for LocalGuilds (RegionalGuilds handle their own)
        local_guilds = [g for g in self.guilds if isinstance(g, LocalGuild)]
        
        if local_guilds:
            new_events = generate_guild_events(local_guilds, current_day)
            
            for event in new_events:
                self.add_event(event)
                log.append(f"New event generated: {event.event_type} for {event.guild_id}")
        
        return log
    
    def _apply_event_resolution(self, event: GuildEvent, result: Dict[str, Any]) -> None:
        """Apply the resolution effects of an event to the affected guild."""
        guild = self.get_guild_by_id(event.guild_id)
        if guild and hasattr(guild, 'apply_event_effects'):
            # Apply final resolution effects
            resolution_effects = self._calculate_resolution_effects(event, result)
            guild.apply_event_effects(event, resolution_effects)
    
    def _apply_daily_effects(self, event: GuildEvent, effects: Dict[str, float]) -> None:
        """Apply daily effects of an ongoing event to the affected guild."""
        guild = self.get_guild_by_id(event.guild_id)
        if guild and hasattr(guild, 'apply_event_effects'):
            guild.apply_event_effects(event, effects)
    
    def _calculate_resolution_effects(self, event: GuildEvent, result: Dict[str, Any]) -> Dict[str, float]:
        """Calculate the final effects of an event resolution."""
        outcome = result.get('outcome', 'status_quo')
        severity = result.get('final_severity', event.severity)
        
        # Base resolution effects by outcome type
        resolution_effects = {
            'leadership_change': {'influence_change': 5.0, 'stability_change': -10.0},
            'compromise': {'stability_change': 5.0},
            'schism': {'influence_change': -15.0, 'stability_change': -20.0, 'member_loyalty': -15.0},
            'status_quo': {},
            'monopoly_established': {'influence_change': 20.0, 'wealth_level': 15.0},
            'competition_emerges': {'influence_change': -5.0},
            'government_intervention': {'influence_change': -10.0, 'stability_change': -5.0},
            'market_collapse': {'influence_change': -25.0, 'wealth_level': -20.0},
            'new_alliance': {'influence_change': 10.0, 'stability_change': 5.0},
            'deeper_conflict': {'influence_change': -8.0, 'stability_change': -12.0},
            'ban_upheld': {'influence_change': -30.0, 'trade_efficiency': -0.5},
            'ban_overturned': {'influence_change': 5.0, 'stability_change': 10.0},
            'complete_dissolution': {'influence_change': -100.0},  # This would disband the guild
            'reorganization': {'stability_change': 10.0, 'member_loyalty': 5.0},
            'decisive_victory': {'influence_change': 25.0, 'wealth_level': 10.0},
            'mutual_destruction': {'influence_change': -40.0, 'wealth_level': -30.0}
        }
        
        effects = resolution_effects.get(outcome, {})
        
        # Scale effects by severity
        scaled_effects = {}
        for effect, value in effects.items():
            scaled_effects[effect] = value * severity
        
        return scaled_effects
    
    def _cleanup_guild_events(self, guild_id: str, reason: str) -> None:
        """Clean up events related to a removed guild."""
        # Mark guild events as concluded
        for event in list(self.events):
            if event.guild_id == guild_id:
                event.active = False
                event.resolved = True
                event.resolution_outcome = f"guild_disbanded_{reason}"
                self.resolved_events.append(event)
                self.events.remove(event)
    
    def get_guild_summary(self, guild_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a comprehensive summary of a guild's current state.
        
        Args:
            guild_id: The guild ID to summarize
            
        Returns:
            Dictionary containing guild summary, or None if not found
        """
        guild = self.get_guild_by_id(guild_id)
        if not guild:
            return None
        
        summary = guild.get_summary() if hasattr(guild, 'get_summary') else {}
        
        # Add event information
        active_events = [e for e in self.events if e.guild_id == guild_id]
        recent_resolved = [e for e in self.resolved_events 
                          if e.guild_id == guild_id and 
                          (self.current_day - e.start_day) <= 30]  # Last 30 days
        
        summary.update({
            'active_events': len(active_events),
            'recent_events_resolved': len(recent_resolved),
            'event_details': {
                'active': [{'type': e.event_type, 'days_remaining': e.days_remaining, 
                           'severity': e.severity} for e in active_events],
                'recent_resolved': [{'type': e.event_type, 'outcome': e.resolution_outcome,
                                   'severity': e.severity} for e in recent_resolved]
            }
        })
        
        return summary
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status and statistics.
        
        Returns:
            Dictionary containing system-wide information
        """
        local_guilds = [g for g in self.guilds if isinstance(g, LocalGuild)]
        regional_guilds = [g for g in self.guilds if isinstance(g, RegionalGuild)]
        
        return {
            'current_day': self.current_day,
            'guild_counts': {
                'total': len(self.guilds),
                'local': len(local_guilds),
                'regional': len(regional_guilds)
            },
            'event_counts': {
                'active': len(self.events),
                'resolved_total': len(self.resolved_events),
                'total_processed': self.total_events_processed
            },
            'special_activities': {
                'active_formations': len(self.active_formations),
                'active_elections': len(self.active_elections),
                'active_summits': len(self.active_summits)
            },
            'daily_stats': self.system_stats.copy(),
            'last_event_generation': self.last_event_generation
        }
    
    def get_daily_report(self) -> str:
        """
        Generate a formatted daily report.
        
        Returns:
            Formatted string containing the day's activities
        """
        status = self.get_system_status()
        
        report = [
            f"=== Guild System Daily Report - Day {self.current_day} ===",
            f"Active Guilds: {status['guild_counts']['total']} ({status['guild_counts']['local']} local, {status['guild_counts']['regional']} regional)",
            f"Active Events: {status['event_counts']['active']}",
            f"Events Resolved Today: {status['daily_stats']['events_resolved_today']}",
            f"New Events Today: {status['daily_stats']['new_events_today']}",
            "",
            "Daily Activity Log:"
        ]
        
        if self.daily_logs:
            for log_entry in self.daily_logs:
                report.append(f"  - {log_entry}")
        else:
            report.append("  - No significant activity")
        
        return "\n".join(report)
    
    def get_guild_list(self, guild_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a list of all guilds with basic information.
        
        Args:
            guild_type: Optional filter by guild type
            
        Returns:
            List of guild summaries
        """
        guild_list = []
        
        for guild in self.guilds:
            if guild_type and hasattr(guild, 'guild_type') and guild.guild_type.value != guild_type:
                continue
            
            guild_info = {
                'guild_id': guild.guild_id,
                'name': guild.name,
                'type': guild.guild_type.value if hasattr(guild, 'guild_type') else 'unknown',
                'influence_score': getattr(guild, 'influence_score', 0),
                'member_count': getattr(guild, 'member_count', 0),
                'active_events': len([e for e in self.events if e.guild_id == guild.guild_id])
            }
            
            guild_list.append(guild_info)
        
        return guild_list


# Example usage and testing
if __name__ == "__main__":
    print("=== Guild System Test ===")
    
    # Create guild system
    guild_system = GuildSystem()
    
    # Create some test guilds
    from guild_event_engine import LocalGuild, GuildType
    
    guild1 = LocalGuild(
        name="Riverside Merchants",
        guild_type=GuildType.MERCHANTS,
        base_settlement="Riverside",
        member_count=25,
        influence_score=60.0
    )
    
    guild2 = LocalGuild(
        name="Ironhold Craftsmen",
        guild_type=GuildType.CRAFTSMEN,
        base_settlement="Ironhold",
        member_count=18,
        influence_score=45.0
    )
    
    # Add guilds to system
    guild_system.add_guild(guild1)
    guild_system.add_guild(guild2)
    
    print(f"Added {len(guild_system.guilds)} guilds to system")
    
    # Create a test event
    test_event = GuildEvent(
        guild_id=guild1.guild_id,
        event_type="power_struggle",
        severity=0.6,
        duration=5,
        start_day=1
    )
    
    guild_system.add_event(test_event)
    print(f"Added test event: {test_event.event_type}")
    
    # Simulate several days
    print("\n=== Simulation ===")
    for day in range(1, 8):
        log = guild_system.tick(day)
        if log:
            print(f"\nDay {day}:")
            for entry in log:
                print(f"  {entry}")
    
    # Get final report
    print("\n" + guild_system.get_daily_report())
    
    # Get system status
    status = guild_system.get_system_status()
    print(f"\nFinal system status:")
    print(f"  Total events processed: {status['event_counts']['total_processed']}")
    print(f"  Active events: {status['event_counts']['active']}")
    print(f"  Resolved events: {status['event_counts']['resolved_total']}") 