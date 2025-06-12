"""
Guild Registry Module for Age of Scribes SSE

This module manages the hierarchical structure of guilds and their sub-guilds,
including job classes and organizational information for the guild system.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class BaseGuild:
    """
    Dataclass representing a base guild with its organizational structure.
    
    Attributes:
        guild_id: Unique identifier for the guild
        name: Display name of the guild
        category: Guild category ("trade", "combat", etc.)
        prestige: Prestige level of the guild (0.0 to 1.0)
        allows_npc_membership: Whether NPCs can join this guild
        region_restricted: Whether membership is restricted to specific regions
        sub_guilds: Dictionary mapping sub-guild names to lists of job classes
    """
    guild_id: str
    name: str
    category: str
    prestige: float
    allows_npc_membership: bool
    region_restricted: bool
    sub_guilds: Dict[str, List[str]]


class GuildRegistry:
    """
    Registry for managing all base guilds and their hierarchical structures.
    
    This class initializes and manages the complete guild system including
    top-level guilds, their sub-guilds, and associated job classes.
    """
    
    def __init__(self):
        """Initialize the guild registry with all base guilds."""
        self.guilds: Dict[str, BaseGuild] = {}
        self._initialize_base_guilds()
    
    def _initialize_base_guilds(self) -> None:
        """Initialize all base guilds with their sub-guilds and job classes."""
        
        # 1. Smithing Guild
        smithing_guild = BaseGuild(
            guild_id="smithing_guild",
            name="Smithing Guild",
            category="trade",
            prestige=0.65,
            allows_npc_membership=True,
            region_restricted=False,
            sub_guilds={
                "Blacksmith": ["weaponsmith", "armorsmith"],
                "Jewelsmith": ["jeweler"],
                "Glasssmith": ["glassblower"]
            }
        )
        self.guilds["smithing_guild"] = smithing_guild
        
        # 2. Textile Guild
        textile_guild = BaseGuild(
            guild_id="textile_guild",
            name="Textile Guild",
            category="trade",
            prestige=0.58,
            allows_npc_membership=True,
            region_restricted=False,
            sub_guilds={
                "Weavers": ["linen weaver", "wool weaver", "loom artisan"],
                "Clothiers": ["tailor", "seamstress", "costumer"],
                "Leatherworkers": ["tanner", "leathersmith", "armor crafter"],
                "Cobblers": ["bootmaker", "shoemaker", "sandal crafter"],
                "Dyers": ["color mixer", "textile dyer", "pattern printer"]
            }
        )
        self.guilds["textile_guild"] = textile_guild
        
        # 3. Woodworking Guild
        woodworking_guild = BaseGuild(
            guild_id="woodworking_guild",
            name="Woodworking Guild",
            category="trade",
            prestige=0.6,
            allows_npc_membership=True,
            region_restricted=False,
            sub_guilds={
                "Carpenter": ["structural carpenter", "fine woodworker"],
                "Bowyer": ["bowmaker"],
                "Carver": ["decorative artisan"]
            }
        )
        self.guilds["woodworking_guild"] = woodworking_guild
        
        # 4. Animal Guild
        animal_guild = BaseGuild(
            guild_id="animal_guild",
            name="Animal Guild",
            category="trade",
            prestige=0.55,
            allows_npc_membership=True,
            region_restricted=False,
            sub_guilds={
                "Breeders": ["horse breeder", "hound breeder"],
                "Trainers": ["beast trainer", "war dog handler"],
                "Herders": ["sheep herder", "goatherd"]
            }
        )
        self.guilds["animal_guild"] = animal_guild
        
        # 5. Agricultural Guild
        agricultural_guild = BaseGuild(
            guild_id="agricultural_guild",
            name="Agricultural Guild",
            category="trade",
            prestige=0.5,
            allows_npc_membership=True,
            region_restricted=False,
            sub_guilds={
                "Farmers": ["grain farmer", "vegetable grower"],
                "Fishers": ["net fisher", "angler"],
                "Foragers": ["herbalist", "wild gatherer"]
            }
        )
        self.guilds["agricultural_guild"] = agricultural_guild
        
        # 6. Mercenary Guild
        mercenary_guild = BaseGuild(
            guild_id="mercenary_guild",
            name="Mercenary Guild",
            category="combat",
            prestige=0.8,
            allows_npc_membership=True,
            region_restricted=False,
            sub_guilds={
                "Adventurers": ["fighter", "rogue", "ranger"],
                "Spellcasters": ["wizard", "sorcerer", "cleric", "warlock", "druid", "bard"],
                "Martial Orders": ["paladin", "monk", "barbarian"],
                "Custom": ["custom"]
            }
        )
        self.guilds["mercenary_guild"] = mercenary_guild
    
    def get_guild(self, guild_id: str) -> BaseGuild:
        """
        Get a guild by its ID.
        
        Args:
            guild_id: The unique identifier of the guild
            
        Returns:
            BaseGuild instance if found
            
        Raises:
            KeyError: If guild_id is not found
        """
        if guild_id not in self.guilds:
            raise KeyError(f"Guild with ID '{guild_id}' not found")
        return self.guilds[guild_id]
    
    def get_all_guilds(self) -> Dict[str, BaseGuild]:
        """
        Get all registered guilds.
        
        Returns:
            Dictionary of all guilds keyed by guild_id
        """
        return self.guilds.copy()
    
    def get_guilds_by_category(self, category: str) -> Dict[str, BaseGuild]:
        """
        Get all guilds in a specific category.
        
        Args:
            category: Category to filter by ("trade", "combat", etc.)
            
        Returns:
            Dictionary of guilds in the specified category
        """
        return {
            guild_id: guild for guild_id, guild in self.guilds.items()
            if guild.category == category
        }
    
    def get_job_classes_for_guild(self, guild_id: str) -> List[str]:
        """
        Get all job classes available in a guild across all sub-guilds.
        
        Args:
            guild_id: The guild to get job classes for
            
        Returns:
            List of all job classes in the guild
        """
        guild = self.get_guild(guild_id)
        all_job_classes = []
        for job_classes in guild.sub_guilds.values():
            all_job_classes.extend(job_classes)
        return all_job_classes
    
    def get_sub_guild_for_job_class(self, guild_id: str, job_class: str) -> str:
        """
        Find which sub-guild contains a specific job class.
        
        Args:
            guild_id: The guild to search in
            job_class: The job class to find
            
        Returns:
            Sub-guild name that contains the job class
            
        Raises:
            ValueError: If job class is not found in any sub-guild
        """
        guild = self.get_guild(guild_id)
        for sub_guild_name, job_classes in guild.sub_guilds.items():
            if job_class in job_classes:
                return sub_guild_name
        raise ValueError(f"Job class '{job_class}' not found in guild '{guild_id}'")
    
    def get_guilds_for_npc_membership(self) -> Dict[str, BaseGuild]:
        """
        Get all guilds that allow NPC membership.
        
        Returns:
            Dictionary of guilds that allow NPC membership
        """
        return {
            guild_id: guild for guild_id, guild in self.guilds.items()
            if guild.allows_npc_membership
        }
    
    def get_guild_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the guild registry.
        
        Returns:
            Dictionary with registry statistics
        """
        total_guilds = len(self.guilds)
        total_sub_guilds = sum(len(guild.sub_guilds) for guild in self.guilds.values())
        total_job_classes = sum(
            len(job_classes) 
            for guild in self.guilds.values() 
            for job_classes in guild.sub_guilds.values()
        )
        
        categories = {}
        for guild in self.guilds.values():
            categories[guild.category] = categories.get(guild.category, 0) + 1
        
        return {
            "total_guilds": total_guilds,
            "total_sub_guilds": total_sub_guilds,
            "total_job_classes": total_job_classes,
            "categories": categories,
            "npc_accessible_guilds": len(self.get_guilds_for_npc_membership())
        }
    
    def add_custom_guild(self, guild: BaseGuild) -> None:
        """
        Add a custom guild to the registry.
        
        Args:
            guild: BaseGuild instance to add
            
        Raises:
            ValueError: If guild_id already exists
        """
        if guild.guild_id in self.guilds:
            raise ValueError(f"Guild with ID '{guild.guild_id}' already exists")
        self.guilds[guild.guild_id] = guild
    
    def remove_guild(self, guild_id: str) -> bool:
        """
        Remove a guild from the registry.
        
        Args:
            guild_id: ID of the guild to remove
            
        Returns:
            True if guild was removed, False if it didn't exist
        """
        if guild_id in self.guilds:
            del self.guilds[guild_id]
            return True
        return False
    
    def list_all_job_classes(self) -> List[str]:
        """
        Get a comprehensive list of all job classes across all guilds.
        
        Returns:
            Sorted list of all unique job classes
        """
        all_job_classes = set()
        for guild in self.guilds.values():
            for job_classes in guild.sub_guilds.values():
                all_job_classes.update(job_classes)
        return sorted(list(all_job_classes))
    
    def find_guilds_with_job_class(self, job_class: str) -> List[str]:
        """
        Find all guilds that contain a specific job class.
        
        Args:
            job_class: The job class to search for
            
        Returns:
            List of guild IDs that contain the job class
        """
        matching_guilds = []
        for guild_id, guild in self.guilds.items():
            for job_classes in guild.sub_guilds.values():
                if job_class in job_classes:
                    matching_guilds.append(guild_id)
                    break  # Don't add the same guild multiple times
        return matching_guilds 