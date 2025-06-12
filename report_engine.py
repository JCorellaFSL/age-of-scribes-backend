#!/usr/bin/env python3
"""
Report Engine - Structured Daily Logging for Age of Scribes Simulation
======================================================================

This module provides the reporting infrastructure for the Age of Scribes
simulation engine. It aggregates and organizes key simulation outputs for
debugging, GUI dashboards, or long-term storage.
"""

from typing import Dict, Any, List
import json
import logging
from datetime import datetime


class SimulationReporter:
    """
    Aggregates and organizes key simulation outputs into structured daily reports.
    
    This class collects various types of simulation events and activities throughout
    each day, organizing them into categorized reports that can be used for:
    - Debugging and development
    - GUI dashboard displays
    - Long-term data storage and analysis
    - Player information systems
    """
    
    def __init__(self):
        """Initialize the simulation reporter."""
        self.daily_reports = {}
        self.logger = logging.getLogger(__name__)
        self.logger.info("SimulationReporter initialized")

    def start_new_day(self, day: int):
        """
        Initialize a new daily report structure.
        
        Args:
            day: The simulation day number to start reporting for
        """
        self.daily_reports[day] = {
            "npc_logs": [],
            "guild_events": [],
            "justice_outcomes": [],
            "caravan_activity": [],
            "notable_events": []
        }
        self.logger.info(f"Started new daily report for day {day}")

    def log_npc_activity(self, day: int, npc_id: str, summary: str):
        """
        Log NPC activity for a specific day.
        
        Args:
            day: The simulation day
            npc_id: Unique identifier for the NPC
            summary: Brief description of the NPC's activity
        """
        if day not in self.daily_reports:
            self.start_new_day(day)
        
        self.daily_reports[day]["npc_logs"].append({
            "npc_id": npc_id, 
            "summary": summary
        })

    def log_guild_event(self, day: int, event: Dict[str, Any]):
        """
        Log guild-related events for a specific day.
        
        Args:
            day: The simulation day
            event: Dictionary containing guild event details
        """
        if day not in self.daily_reports:
            self.start_new_day(day)
        
        self.daily_reports[day]["guild_events"].append(event)

    def log_justice_outcome(self, day: int, case_id: str, verdict: str, notes: str):
        """
        Log justice system outcomes for a specific day.
        
        Args:
            day: The simulation day
            case_id: Unique identifier for the justice case
            verdict: The verdict reached in the case
            notes: Additional notes or details about the outcome
        """
        if day not in self.daily_reports:
            self.start_new_day(day)
        
        self.daily_reports[day]["justice_outcomes"].append({
            "case_id": case_id,
            "verdict": verdict,
            "notes": notes
        })

    def log_caravan_activity(self, day: int, summary: str):
        """
        Log caravan-related activity for a specific day.
        
        Args:
            day: The simulation day
            summary: Brief description of caravan activity
        """
        if day not in self.daily_reports:
            self.start_new_day(day)
        
        self.daily_reports[day]["caravan_activity"].append(summary)

    def log_misc_event(self, day: int, description: str):
        """
        Log miscellaneous notable events for a specific day.
        
        Args:
            day: The simulation day
            description: Description of the notable event
        """
        if day not in self.daily_reports:
            self.start_new_day(day)
        
        self.daily_reports[day]["notable_events"].append(description)

    def get_report(self, day: int) -> Dict[str, Any]:
        """
        Retrieve the complete report for a specific day.
        
        Args:
            day: The simulation day to retrieve the report for
            
        Returns:
            Dictionary containing all logged events for the specified day
        """
        return self.daily_reports.get(day, {})

    def export_report(self, day: int) -> str:
        """
        Export a daily report as a JSON string.
        
        Args:
            day: The simulation day to export
            
        Returns:
            JSON-formatted string of the daily report
        """
        return json.dumps(self.get_report(day), indent=2)
    
    def get_all_reports(self) -> Dict[int, Dict[str, Any]]:
        """
        Get all daily reports.
        
        Returns:
            Dictionary mapping day numbers to their respective reports
        """
        return self.daily_reports.copy()
    
    def get_available_days(self) -> List[int]:
        """
        Get a list of all days that have reports available.
        
        Returns:
            Sorted list of day numbers with available reports
        """
        return sorted(self.daily_reports.keys())
    
    def get_summary_stats(self, day: int) -> Dict[str, int]:
        """
        Get summary statistics for a specific day's report.
        
        Args:
            day: The simulation day to get statistics for
            
        Returns:
            Dictionary containing counts of different event types
        """
        report = self.get_report(day)
        if not report:
            return {}
        
        return {
            "npc_activities": len(report.get("npc_logs", [])),
            "guild_events": len(report.get("guild_events", [])),
            "justice_outcomes": len(report.get("justice_outcomes", [])),
            "caravan_activities": len(report.get("caravan_activity", [])),
            "notable_events": len(report.get("notable_events", []))
        }
    
    def clear_old_reports(self, keep_days: int = 30):
        """
        Clear old reports to manage memory usage.
        
        Args:
            keep_days: Number of recent days to keep (default: 30)
        """
        if not self.daily_reports:
            return
        
        latest_day = max(self.daily_reports.keys())
        cutoff_day = latest_day - keep_days
        
        days_to_remove = [day for day in self.daily_reports.keys() if day < cutoff_day]
        
        for day in days_to_remove:
            del self.daily_reports[day]
        
        if days_to_remove:
            self.logger.info(f"Cleared {len(days_to_remove)} old reports (keeping last {keep_days} days)")


# Example usage and testing
if __name__ == "__main__":
    # Initialize reporter
    reporter = SimulationReporter()
    
    # Simulate some daily activity
    test_day = 1
    reporter.start_new_day(test_day)
    
    # Log various types of events
    reporter.log_npc_activity(test_day, "npc_001", "Completed daily patrol of market district")
    reporter.log_npc_activity(test_day, "npc_002", "Participated in guild meeting")
    
    reporter.log_guild_event(test_day, {
        "guild_id": "merchants_guild",
        "event_type": "election",
        "outcome": "New guildmaster elected",
        "participants": 15
    })
    
    reporter.log_justice_outcome(test_day, "case_001", "guilty", "Theft conviction, 30 days labor")
    
    reporter.log_caravan_activity(test_day, "3 caravans departed, 2 arrived, total trade volume: 1500 gold")
    
    reporter.log_misc_event(test_day, "Unusual weather patterns observed in eastern regions")
    
    # Display the report
    print("=== Age of Scribes Daily Report Test ===")
    print(f"Day {test_day} Report:")
    print(reporter.export_report(test_day))
    
    # Show summary statistics
    print(f"\nSummary Statistics for Day {test_day}:")
    stats = reporter.get_summary_stats(test_day)
    for category, count in stats.items():
        print(f"  {category}: {count}") 