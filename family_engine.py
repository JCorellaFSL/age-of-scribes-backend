"""
Family Engine Module for Age of Scribes SSE

This module handles generational simulation and family structure for NPCs.
It enables NPCs to form marriages based on compatibility, class, status, and proximity
while respecting cultural and statistical constraints.

Note: This module assumes the NPCProfile class has been extended with the following attributes:
- gender: str ("male" or "female")
- social_class: str (social class identifier)
- character_id: str (unique character identifier, could use npc_id)
- relationship_status: str ("single", "courting", "married", "div.single", "div.courting")
- partner_id: Optional[str] (character_id of current partner/spouse)
"""

import random
from typing import List, Tuple, Optional, Dict, Any
from npc_profile import NPCProfile


class FamilyEngine:
    """
    Engine for managing family relationships and marriage simulation among NPCs.
    
    This class handles the formation of marriages based on various compatibility
    factors including age, social class, faction affiliation, and personality traits.
    """
    
    def __init__(self, npcs: List[NPCProfile]):
        """
        Initialize the Family Engine with a list of NPCs.
        
        Args:
            npcs: List of NPC profiles to manage
        """
        self.npcs = npcs
        self.marriages = []  # Each as (partner1_id, partner2_id, start_day)
        self.courtships = []  # Each as (partner1_id, partner2_id, start_day)
        
        # Marriage probability modifiers
        self.base_marriage_chance = 0.1  # Base chance per eligible pairing
        self.base_courtship_chance = 0.3  # Higher chance for courting
        self.courtship_to_marriage_chance = 0.2  # Chance per day for courting couples to marry
        self.age_preference_weight = 0.3  # How much age difference matters
        self.class_compatibility_weight = 0.4  # How much social class matters
        self.faction_compatibility_weight = 0.3  # How much faction alignment matters
        
        # Divorce settings
        self.divorce_reputation_penalty = -0.1  # Reputation penalty for divorce
        
        # Childbirth settings
        self.default_fertility_rate = 0.05  # 5% chance per day for eligible couples
        self.infant_mortality_rate = 0.2  # 20% chance of death at birth
        self.min_mother_age = 18
        self.max_mother_age = 40
        
    def process_relationships(self, current_day: int) -> Dict[str, List[Tuple[str, str, int]]]:
        """
        Process all relationship changes including courtships, marriages, and breakups.
        
        Args:
            current_day: Current simulation day
            
        Returns:
            Dictionary with lists of new courtships, marriages, and breakups
        """
        results = {
            "new_courtships": [],
            "new_marriages": [],
            "breakups": []
        }
        
        # First, attempt new courtships
        results["new_courtships"] = self._attempt_courtships(current_day)
        
        # Then, attempt marriages from existing courtships
        results["new_marriages"] = self._attempt_marriages_from_courtships(current_day)
        
        # Finally, attempt direct marriages for those not courting
        results["new_marriages"].extend(self._attempt_direct_marriages(current_day))
        
        return results
    
    def _attempt_courtships(self, current_day: int) -> List[Tuple[str, str, int]]:
        """
        Attempt to create new courtships between eligible NPCs.
        
        Args:
            current_day: Current simulation day
            
        Returns:
            List of new courtships formed as (partner1_id, partner2_id, start_day)
        """
        new_courtships = []
        
        # Filter eligible singles (including divorced singles)
        singles = [npc for npc in self.npcs 
                  if self._is_relationship_eligible(npc)]
        
        available_singles = singles.copy()
        
        for npc in singles:
            if not self._is_relationship_eligible(npc):
                continue
                
            # Males initiate
            if not hasattr(npc, 'gender') or npc.gender != "male":
                continue
            
            candidates = [
                other for other in available_singles
                if self._are_compatible_for_relationship(npc, other)
            ]
            
            if candidates:
                partner = self._select_relationship_partner(npc, candidates)
                
                if partner and self._attempt_courtship_proposal(npc, partner, current_day):
                    self._formalize_courtship(npc, partner, current_day)
                    new_courtships.append((
                        self._get_character_id(npc), 
                        self._get_character_id(partner), 
                        current_day
                    ))
                    
                    if npc in available_singles:
                        available_singles.remove(npc)
                    if partner in available_singles:
                        available_singles.remove(partner)
        
        return new_courtships
    
    def _attempt_marriages_from_courtships(self, current_day: int) -> List[Tuple[str, str, int]]:
        """
        Attempt to convert existing courtships to marriages.
        
        Args:
            current_day: Current simulation day
            
        Returns:
            List of new marriages formed from courtships
        """
        new_marriages = []
        courtships_to_remove = []
        
        for courtship in self.courtships:
            partner1_id, partner2_id, start_day = courtship
            
            # Find the NPCs
            npc1 = next((npc for npc in self.npcs if self._get_character_id(npc) == partner1_id), None)
            npc2 = next((npc for npc in self.npcs if self._get_character_id(npc) == partner2_id), None)
            
            if npc1 and npc2:
                # Check if they want to marry (random chance)
                if random.random() < self.courtship_to_marriage_chance:
                    self._formalize_marriage(npc1, npc2, current_day)
                    new_marriages.append((partner1_id, partner2_id, current_day))
                    courtships_to_remove.append(courtship)
        
        # Remove courtships that became marriages
        for courtship in courtships_to_remove:
            self.courtships.remove(courtship)
        
        return new_marriages
    
    def _attempt_direct_marriages(self, current_day: int) -> List[Tuple[str, str, int]]:
        """
        Attempt direct marriages for NPCs not in courtships.
        
        Args:
            current_day: Current simulation day
            
        Returns:
            List of new marriages formed directly
        """
        new_marriages = []
        
        # Filter eligible singles not in courtships
        singles = [npc for npc in self.npcs 
                  if self._is_marriage_eligible(npc)]
        
        available_singles = singles.copy()
        
        for npc in singles:
            if not self._is_marriage_eligible(npc):
                continue
                
            if not hasattr(npc, 'gender') or npc.gender != "male":
                continue
            
            candidates = [
                other for other in available_singles
                if self._are_compatible_for_marriage(npc, other)
            ]
            
            if candidates:
                partner = self._select_relationship_partner(npc, candidates)
                
                if partner and self._attempt_marriage_proposal(npc, partner, current_day):
                    self._formalize_marriage(npc, partner, current_day)
                    new_marriages.append((
                        self._get_character_id(npc), 
                        self._get_character_id(partner), 
                        current_day
                    ))
                    
                    if npc in available_singles:
                        available_singles.remove(npc)
                    if partner in available_singles:
                        available_singles.remove(partner)
        
        return new_marriages
    
    def _is_relationship_eligible(self, npc: NPCProfile) -> bool:
        """
        Check if an NPC is eligible for starting a relationship (courtship).
        
        Args:
            npc: NPC to check
            
        Returns:
            True if eligible for courtship
        """
        # Age requirement
        if npc.age < 16:
            return False
            
        # Check relationship status - single or divorced singles can start courting
        relationship_status = getattr(npc, 'relationship_status', 'single')
        if relationship_status in ['single', 'div.single']:
            return True
            
        return False
    
    def _is_marriage_eligible(self, npc: NPCProfile) -> bool:
        """
        Check if an NPC is eligible for marriage (direct marriage, not courting).
        
        Args:
            npc: NPC to check
            
        Returns:
            True if eligible for marriage
        """
        # Age requirement
        if npc.age < 16:
            return False
            
        # Check relationship status - only singles (not courting, not married, not divorced courting)
        relationship_status = getattr(npc, 'relationship_status', 'single')
        if relationship_status in ['single', 'div.single']:
            return True
            
        return False
    
    def _are_compatible_for_relationship(self, npc1: NPCProfile, npc2: NPCProfile) -> bool:
        """
        Check if two NPCs are compatible for a relationship (courtship or marriage).
        
        Args:
            npc1: First NPC (male initiator)
            npc2: Second NPC (potential female partner)
            
        Returns:
            True if they are compatible for a relationship
        """
        # Gender compatibility (heterosexual relationships)
        if not hasattr(npc2, 'gender') or npc2.gender != "female":
            return False
            
        # Same NPC check
        if self._get_character_id(npc1) == self._get_character_id(npc2):
            return False
            
        # Relationship status check
        if not self._is_relationship_eligible(npc2):
            return False
            
        # Social class compatibility (avoid cross-class for now)
        if hasattr(npc1, 'social_class') and hasattr(npc2, 'social_class'):
            if npc1.social_class != npc2.social_class:
                return False
        
        # Age compatibility (within 10 years)
        if abs(npc2.age - npc1.age) > 10:
            return False
            
        # Faction affiliation compatibility
        if (npc1.faction_affiliation and npc2.faction_affiliation and 
            npc1.faction_affiliation != npc2.faction_affiliation):
            return False
            
        return True
    
    def _are_compatible_for_marriage(self, npc1: NPCProfile, npc2: NPCProfile) -> bool:
        """
        Check if two NPCs are compatible for direct marriage.
        
        Args:
            npc1: First NPC (male initiator)
            npc2: Second NPC (potential female partner)
            
        Returns:
            True if they are compatible for marriage
        """
        # Use relationship compatibility as base
        if not self._are_compatible_for_relationship(npc1, npc2):
            return False
            
        # Additional marriage-specific checks
        if not self._is_marriage_eligible(npc2):
            return False
            
        return True
    
    def _select_relationship_partner(self, npc: NPCProfile, candidates: List[NPCProfile]) -> Optional[NPCProfile]:
        """
        Select the best relationship partner from candidates.
        
        Args:
            npc: NPC looking for a partner
            candidates: List of potential partners
            
        Returns:
            Selected partner or None
        """
        if not candidates:
            return None
            
        # Calculate compatibility scores
        scored_candidates = []
        for candidate in candidates:
            score = self._calculate_marriage_compatibility_score(npc, candidate)
            scored_candidates.append((candidate, score))
        
        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Use weighted random selection favoring higher scores
        weights = [score for _, score in scored_candidates]
        
        # Add some randomness to prevent always picking the highest score
        if weights:
            selected_candidate = random.choices(
                [candidate for candidate, _ in scored_candidates],
                weights=weights
            )[0]
            return selected_candidate
            
        return candidates[0] if candidates else None
    
    def _calculate_marriage_compatibility_score(self, npc1: NPCProfile, npc2: NPCProfile) -> float:
        """
        Calculate marriage compatibility score between two NPCs.
        
        Args:
            npc1: First NPC
            npc2: Second NPC
            
        Returns:
            Compatibility score (0.0 to 1.0)
        """
        base_score = npc1.compatibility_score(npc2)
        
        # Age compatibility bonus/penalty
        age_diff = abs(npc1.age - npc2.age)
        age_score = max(0.0, 1.0 - (age_diff / 20.0))  # Penalty increases with age gap
        
        # Social status compatibility (if available)
        class_score = 1.0
        if hasattr(npc1, 'social_class') and hasattr(npc2, 'social_class'):
            class_score = 1.0 if npc1.social_class == npc2.social_class else 0.5
        
        # Faction compatibility
        faction_score = 1.0
        if npc1.faction_affiliation and npc2.faction_affiliation:
            faction_score = 1.0 if npc1.faction_affiliation == npc2.faction_affiliation else 0.3
        elif npc1.faction_affiliation or npc2.faction_affiliation:
            faction_score = 0.7  # Slight penalty for faction mismatch
            
        # Weighted final score
        final_score = (
            base_score * 0.4 +
            age_score * self.age_preference_weight +
            class_score * self.class_compatibility_weight +
            faction_score * self.faction_compatibility_weight
        )
        
        return min(1.0, max(0.0, final_score))
    
    def _attempt_courtship_proposal(self, proposer: NPCProfile, candidate: NPCProfile, current_day: int) -> bool:
        """
        Attempt a courtship proposal between two NPCs.
        
        Args:
            proposer: NPC making the proposal
            candidate: NPC receiving the proposal
            current_day: Current simulation day
            
        Returns:
            True if proposal is accepted
        """
        # Base acceptance chance (higher than marriage)
        compatibility = self._calculate_marriage_compatibility_score(proposer, candidate)
        
        # Personality-based modifiers
        acceptance_chance = compatibility * self.base_courtship_chance
        
        # Trait-based modifiers
        if "cautious" in candidate.personality_traits:
            acceptance_chance *= 0.8  # Less penalty for courting than marriage
        if "impulsive" in candidate.personality_traits:
            acceptance_chance *= 1.2
        if "romantic" in candidate.personality_traits:  # If this trait exists
            acceptance_chance *= 1.3
            
        # Age-based modifiers
        if candidate.age > 20:
            acceptance_chance *= 1.05
        if candidate.age > 30:
            acceptance_chance *= 1.1
            
        return random.random() < acceptance_chance
    
    def _attempt_marriage_proposal(self, proposer: NPCProfile, candidate: NPCProfile, current_day: int) -> bool:
        """
        Attempt a direct marriage proposal between two NPCs.
        
        Args:
            proposer: NPC making the proposal
            candidate: NPC receiving the proposal
            current_day: Current simulation day
            
        Returns:
            True if proposal is accepted
        """
        # Base acceptance chance (lower than courtship)
        compatibility = self._calculate_marriage_compatibility_score(proposer, candidate)
        
        # Personality-based modifiers
        acceptance_chance = compatibility * self.base_marriage_chance
        
        # Trait-based modifiers
        if "cautious" in candidate.personality_traits:
            acceptance_chance *= 0.6  # More penalty for direct marriage
        if "impulsive" in candidate.personality_traits:
            acceptance_chance *= 1.4
        if "romantic" in candidate.personality_traits:
            acceptance_chance *= 1.1
            
        # Age-based modifiers (older NPCs more likely to accept direct marriage)
        if candidate.age > 25:
            acceptance_chance *= 1.2
        if candidate.age > 35:
            acceptance_chance *= 1.4
            
        return random.random() < acceptance_chance
    
    def _formalize_courtship(self, npc1: NPCProfile, npc2: NPCProfile, current_day: int) -> None:
        """
        Formalize the courtship between two NPCs.
        
        Args:
            npc1: First NPC
            npc2: Second NPC
            current_day: Current simulation day
        """
        # Update relationship status
        if hasattr(npc1, 'relationship_status'):
            npc1.relationship_status = "courting"
        if hasattr(npc2, 'relationship_status'):
            npc2.relationship_status = "courting"
            
        # Set partner IDs
        npc1_id = self._get_character_id(npc1)
        npc2_id = self._get_character_id(npc2)
        
        if hasattr(npc1, 'partner_id'):
            npc1.partner_id = npc2_id
        if hasattr(npc2, 'partner_id'):
            npc2.partner_id = npc1_id
            
        # Record the courtship
        self.courtships.append((npc1_id, npc2_id, current_day))
        
        # Update social circles
        if npc1_id not in npc2.social_circle:
            npc2.social_circle.append(npc1_id)
        if npc2_id not in npc1.social_circle:
            npc1.social_circle.append(npc2_id)
            
        # Update relationships (moderate trust)
        npc1.add_relationship(npc2_id, 0.6)
        npc2.add_relationship(npc1_id, 0.6)
    
    def _formalize_marriage(self, npc1: NPCProfile, npc2: NPCProfile, current_day: int) -> None:
        """
        Formalize the marriage between two NPCs.
        
        Args:
            npc1: First NPC
            npc2: Second NPC
            current_day: Current simulation day
        """
        # Update relationship status
        if hasattr(npc1, 'relationship_status'):
            npc1.relationship_status = "married"
        if hasattr(npc2, 'relationship_status'):
            npc2.relationship_status = "married"
            
        # Set partner IDs (now spouse)
        npc1_id = self._get_character_id(npc1)
        npc2_id = self._get_character_id(npc2)
        
        if hasattr(npc1, 'partner_id'):
            npc1.partner_id = npc2_id
        if hasattr(npc2, 'partner_id'):
            npc2.partner_id = npc1_id
            
        # Record the marriage
        self.marriages.append((npc1_id, npc2_id, current_day))
        
        # Update social circles
        if npc1_id not in npc2.social_circle:
            npc2.social_circle.append(npc1_id)
        if npc2_id not in npc1.social_circle:
            npc1.social_circle.append(npc2_id)
            
        # Update relationships (high trust)
        npc1.add_relationship(npc2_id, 0.8)
        npc2.add_relationship(npc1_id, 0.8)
    
    def _get_character_id(self, npc: NPCProfile) -> str:
        """
        Get the character ID from an NPC, using npc_id as fallback.
        
        Args:
            npc: NPC profile
            
        Returns:
            Character ID string
        """
        return getattr(npc, 'character_id', npc.npc_id)
    
    def _get_npc_by_id(self, npc_id: str) -> Optional[NPCProfile]:
        """
        Get an NPC by their character ID.
        
        Args:
            npc_id: Character ID to search for
            
        Returns:
            NPCProfile if found, None otherwise
        """
        return next((npc for npc in self.npcs if self._get_character_id(npc) == npc_id), None)
    
    def break_up_courtship(self, npc1_id: str, npc2_id: str, current_day: int) -> bool:
        """
        Break up a courtship between two NPCs.
        
        Args:
            npc1_id: ID of first NPC
            npc2_id: ID of second NPC
            current_day: Current simulation day
            
        Returns:
            True if courtship was successfully broken up
        """
        # Find the courtship record
        courtship_to_remove = None
        for courtship in self.courtships:
            if ((courtship[0] == npc1_id and courtship[1] == npc2_id) or
                (courtship[0] == npc2_id and courtship[1] == npc1_id)):
                courtship_to_remove = courtship
                break
                
        if not courtship_to_remove:
            return False
            
        # Remove courtship record
        self.courtships.remove(courtship_to_remove)
        
        # Update NPC statuses
        npc1 = next((npc for npc in self.npcs if self._get_character_id(npc) == npc1_id), None)
        npc2 = next((npc for npc in self.npcs if self._get_character_id(npc) == npc2_id), None)
        
        if npc1:
            if hasattr(npc1, 'relationship_status'):
                npc1.relationship_status = "single"
            if hasattr(npc1, 'partner_id'):
                npc1.partner_id = None
                
        if npc2:
            if hasattr(npc2, 'relationship_status'):
                npc2.relationship_status = "single"
            if hasattr(npc2, 'partner_id'):
                npc2.partner_id = None
                
        # Small relationship adjustment (breakups hurt but not as much as divorce)
        if npc1:
            npc1.adjust_relationship(npc2_id, -0.2)
        if npc2:
            npc2.adjust_relationship(npc1_id, -0.2)
                
        return True
    
    def divorce_marriage(self, npc1_id: str, npc2_id: str, current_day: int) -> bool:
        """
        Divorce a marriage between two NPCs with reputation penalties.
        
        Args:
            npc1_id: ID of first NPC
            npc2_id: ID of second NPC
            current_day: Current simulation day
            
        Returns:
            True if marriage was successfully dissolved
        """
        # Find the marriage record
        marriage_to_remove = None
        for marriage in self.marriages:
            if ((marriage[0] == npc1_id and marriage[1] == npc2_id) or
                (marriage[0] == npc2_id and marriage[1] == npc1_id)):
                marriage_to_remove = marriage
                break
                
        if not marriage_to_remove:
            return False
            
        # Remove marriage record
        self.marriages.remove(marriage_to_remove)
        
        # Update NPC statuses with divorce status
        npc1 = next((npc for npc in self.npcs if self._get_character_id(npc) == npc1_id), None)
        npc2 = next((npc for npc in self.npcs if self._get_character_id(npc) == npc2_id), None)
        
        if npc1:
            if hasattr(npc1, 'relationship_status'):
                npc1.relationship_status = "div.single"
            if hasattr(npc1, 'partner_id'):
                npc1.partner_id = None
            # Apply reputation penalty
            if hasattr(npc1, 'update_reputation'):
                npc1.update_reputation(npc1.region, self.divorce_reputation_penalty, 
                                     f"Divorced from {npc2.name if npc2 else 'unknown'}")
                
        if npc2:
            if hasattr(npc2, 'relationship_status'):
                npc2.relationship_status = "div.single"
            if hasattr(npc2, 'partner_id'):
                npc2.partner_id = None
            # Apply reputation penalty
            if hasattr(npc2, 'update_reputation'):
                npc2.update_reputation(npc2.region, self.divorce_reputation_penalty, 
                                     f"Divorced from {npc1.name if npc1 else 'unknown'}")
                
        # Significant relationship damage
        if npc1:
            npc1.adjust_relationship(npc2_id, -0.5)
        if npc2:
            npc2.adjust_relationship(npc1_id, -0.5)
                
        return True
    
    def get_courting_couples(self) -> List[Tuple[str, str, int]]:
        """
        Get all courting couples.
        
        Returns:
            List of courtships as (partner1_id, partner2_id, courtship_day)
        """
        return self.courtships.copy()
    
    def get_married_couples(self) -> List[Tuple[str, str, int]]:
        """
        Get all married couples.
        
        Returns:
            List of marriages as (partner1_id, partner2_id, marriage_day)
        """
        return self.marriages.copy()
    
    def get_relationship_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive relationship statistics.
        
        Returns:
            Dictionary with relationship statistics
        """
        total_npcs = len(self.npcs)
        status_counts = {
            "single": 0,
            "courting": 0,
            "married": 0,
            "div.single": 0,
            "div.courting": 0
        }
        
        for npc in self.npcs:
            status = getattr(npc, 'relationship_status', 'single')
            if status in status_counts:
                status_counts[status] += 1
            else:
                status_counts["single"] += 1  # Default unknown statuses to single
        
        return {
            "total_npcs": total_npcs,
            "status_breakdown": status_counts,
            "total_courtships": len(self.courtships),
            "total_marriages": len(self.marriages),
            "marriage_rate": status_counts["married"] / total_npcs if total_npcs > 0 else 0.0,
                         "relationship_rate": (status_counts["courting"] + status_counts["married"]) / total_npcs if total_npcs > 0 else 0.0
         }
    
    def simulate_childbirth(self, current_day: int, fertility_rate: Optional[float] = None) -> List[str]:
        """
        Simulate childbirth between married NPCs with realistic birth odds and mortality.
        
        Args:
            current_day: Current simulation day
            fertility_rate: Daily fertility rate (defaults to class setting)
            
        Returns:
            List of character IDs for successfully born children
        """
        if fertility_rate is None:
            fertility_rate = self.default_fertility_rate
            
        births = []
        
        for (parent1_id, parent2_id, marriage_day) in self.marriages:
            parent1 = self._get_npc_by_id(parent1_id)
            parent2 = self._get_npc_by_id(parent2_id)
            
            if not parent1 or not parent2:
                continue
                
            # Only female NPCs can give birth
            mother = parent1 if getattr(parent1, 'gender', None) == "female" else parent2
            father = parent2 if mother == parent1 else parent1
            
            # Verify mother is female
            if getattr(mother, 'gender', None) != "female":
                continue
                
            # Age and time filter
            if mother.age < self.min_mother_age or mother.age > self.max_mother_age:
                continue
                
            # Random chance based on fertility
            if random.random() > fertility_rate:
                continue
                
            # Child creation
            child = self._generate_child_profile(mother, father, current_day)
            
            # 1-in-5 chance of death at birth
            if random.random() < self.infant_mortality_rate:
                # Mark child as deceased
                if hasattr(child, 'is_active'):
                    child.is_active = False
                if hasattr(child, 'cause_of_death'):
                    child.cause_of_death = "infant_mortality"
                if hasattr(child, 'death_day'):
                    child.death_day = current_day
                    
                # Still add to NPC list for record keeping but mark as inactive
                self.npcs.append(child)
            else:
                # Child survives
                if hasattr(child, 'is_active'):
                    child.is_active = True
                self.npcs.append(child)
                births.append(self._get_character_id(child))
                
        return births
    
    def _generate_child_profile(self, mother: NPCProfile, father: NPCProfile, birth_day: int) -> NPCProfile:
        """
        Generate a child NPC profile from two parents.
        
        Args:
            mother: Mother NPC
            father: Father NPC
            birth_day: Day of birth
            
        Returns:
            New child NPCProfile
        """
        # Generate child name (simple approach)
        father_surname = getattr(father, 'last_name', father.name.split()[-1] if ' ' in father.name else father.name)
        child_name = self._generate_child_name(father_surname)
        
        # Create child with random gender
        child_gender = random.choice(["male", "female"])
        
        # Use father's region and basic info
        child = NPCProfile.generate_random(
            name=child_name,
            region=father.region,
            age_range=(0, 0),  # Newborn
            num_traits=2,  # Fewer traits for children
            archetype=None,  # Random traits
            gender=child_gender,
            social_class=getattr(father, 'social_class', None),
            parent_ids=[self._get_character_id(mother), self._get_character_id(father)]
        )
        
        # Set child-specific attributes
        child.birth_day = birth_day
        child.faction_affiliation = father.faction_affiliation
            
        # Add relationships with parents
        mother_id = self._get_character_id(mother)
        father_id = self._get_character_id(father)
        child_id = self._get_character_id(child)
        
        child.add_relationship(mother_id, 1.0)  # Perfect trust with mother
        child.add_relationship(father_id, 1.0)  # Perfect trust with father
        
        # Parents add relationship with child
        mother.add_relationship(child_id, 1.0)
        father.add_relationship(child_id, 1.0)
        
        # Add to social circles
        if mother_id not in child.social_circle:
            child.social_circle.append(mother_id)
        if father_id not in child.social_circle:
            child.social_circle.append(father_id)
        if child_id not in mother.social_circle:
            mother.social_circle.append(child_id)
        if child_id not in father.social_circle:
            father.social_circle.append(child_id)
            
        return child
    
    def _generate_child_name(self, surname: str) -> str:
        """
        Generate a simple child name with the given surname.
        
        Args:
            surname: Family surname to use
            
        Returns:
            Generated full name
        """
        # Simple name lists - you could expand these or make them region-specific
        male_names = ["Alexander", "William", "James", "Robert", "John", "Michael", "David", "Richard", "Charles", "Thomas"]
        female_names = ["Elizabeth", "Mary", "Catherine", "Margaret", "Anne", "Sarah", "Emily", "Isabella", "Victoria", "Charlotte"]
        
        # For now, just pick a random name
        first_name = random.choice(male_names + female_names)
        return f"{first_name} {surname}"
    
    def get_children_by_parents(self, parent1_id: str, parent2_id: str) -> List[NPCProfile]:
        """
        Get all children of two specific parents.
        
        Args:
            parent1_id: First parent's ID
            parent2_id: Second parent's ID
            
        Returns:
            List of child NPCs
        """
        children = []
        for npc in self.npcs:
            parent_ids = getattr(npc, 'parent_ids', [])
            if (parent1_id in parent_ids and parent2_id in parent_ids):
                children.append(npc)
        return children
    
    def get_family_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive family statistics including births and deaths.
        
        Returns:
            Dictionary with family statistics
        """
        total_npcs = len(self.npcs)
        children = [npc for npc in self.npcs if npc.age < 16]
        adults = [npc for npc in self.npcs if npc.age >= 16]
        deceased_children = [npc for npc in self.npcs 
                           if npc.age == 0 and getattr(npc, 'cause_of_death', None) == "infant_mortality"]
        
        return {
            "total_npcs": total_npcs,
            "total_children": len(children),
            "total_adults": len(adults),
            "deceased_infants": len(deceased_children),
            "infant_survival_rate": 1.0 - (len(deceased_children) / max(1, len(children) + len(deceased_children))),
            "families_with_children": len(set(
                tuple(sorted(getattr(npc, 'parent_ids', []))) 
                for npc in children 
                if getattr(npc, 'parent_ids', [])
            ))
        }
    
 