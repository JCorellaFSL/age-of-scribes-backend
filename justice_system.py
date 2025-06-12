import uuid
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict


class JusticeCase:
    """
    Represents a single legal case with evidence, witnesses, and resolution logic.
    
    Tracks all aspects of a legal case from initiation through resolution,
    including evidence evaluation, witness credibility, and punishment application.
    """
    
    def __init__(self,
                 crime_type: str,
                 accused_id: str,
                 region: str,
                 case_id: Optional[str] = None,
                 witness_ids: Optional[List[str]] = None,
                 evidence_strength: float = 0.5,
                 status: str = "open",
                 verdict: Optional[str] = None):
        """
        Initialize a justice case.
        
        Args:
            crime_type: Type of crime (e.g., "theft", "murder", "corruption")
            accused_id: ID of the accused entity
            region: Region where the crime occurred
            case_id: Unique case identifier (auto-generated if None)
            witness_ids: List of witness entity IDs
            evidence_strength: Strength of evidence (0.0 to 1.0)
            status: Current case status
            verdict: Final verdict (if resolved)
        """
        self.case_id = case_id or str(uuid.uuid4())
        self.crime_type = crime_type
        self.accused_id = accused_id
        self.witness_ids = witness_ids or []
        self.evidence_strength = max(0.0, min(1.0, evidence_strength))
        self.region = region
        self.status = status
        self.verdict = verdict
        
        # Case metadata
        self.creation_date = datetime.now()
        self.resolution_date: Optional[datetime] = None
        self.judge_id: Optional[str] = None
        self.punishment_applied: List[str] = []
        
        # Evidence and investigation details
        self.source_memories: List[str] = []  # Memory node IDs that created this case
        self.source_rumors: List[str] = []   # Rumor IDs that influenced this case
        self.investigation_notes: List[str] = []
        
        # Case outcome tracking
        self.reputation_changes: Dict[str, Dict[str, float]] = {}
        self.factional_impacts: Dict[str, float] = {}
        
    def add_evidence(self, evidence_source: str, strength_delta: float, notes: str = "") -> None:
        """
        Add evidence to the case.
        
        Args:
            evidence_source: Source of the evidence (memory_id, rumor_id, etc.)
            strength_delta: Change in evidence strength (-1.0 to 1.0)
            notes: Additional notes about the evidence
        """
        old_strength = self.evidence_strength
        self.evidence_strength = max(0.0, min(1.0, self.evidence_strength + strength_delta))
        
        self.investigation_notes.append(
            f"{datetime.now().isoformat()}: Evidence from {evidence_source} "
            f"changed strength by {strength_delta:.3f} ({old_strength:.3f} -> {self.evidence_strength:.3f})"
        )
        
        if notes:
            self.investigation_notes.append(f"  Notes: {notes}")
    
    def add_witness(self, witness_id: str, credibility: float = 0.5) -> None:
        """
        Add a witness to the case.
        
        Args:
            witness_id: ID of the witness
            credibility: Witness credibility (0.0 to 1.0)
        """
        if witness_id not in self.witness_ids:
            self.witness_ids.append(witness_id)
            self.investigation_notes.append(
                f"{datetime.now().isoformat()}: Added witness {witness_id} "
                f"with credibility {credibility:.3f}"
            )
    
    def evaluate_case(self, 
                     witness_credibility_map: Optional[Dict[str, float]] = None,
                     regional_bias: float = 0.0) -> Dict[str, Any]:
        """
        Evaluate the case to determine probable guilt.
        
        Args:
            witness_credibility_map: Map of witness_id -> credibility (0.0 to 1.0)
            regional_bias: Regional bias affecting evaluation (-1.0 to 1.0)
            
        Returns:
            Dictionary containing evaluation results
        """
        # Base guilt probability from evidence
        evidence_weight = self.evidence_strength
        
        # Calculate witness reliability
        witness_credibility_map = witness_credibility_map or {}
        witness_factor = 0.0
        
        if self.witness_ids:
            total_credibility = 0.0
            for witness_id in self.witness_ids:
                credibility = witness_credibility_map.get(witness_id, 0.5)  # Default neutral credibility
                total_credibility += credibility
            
            witness_factor = total_credibility / len(self.witness_ids)
        
        # Combine evidence and witness factors
        base_guilt_probability = (evidence_weight * 0.7) + (witness_factor * 0.3)
        
        # Apply regional bias
        biased_probability = base_guilt_probability + (regional_bias * 0.2)
        biased_probability = max(0.0, min(1.0, biased_probability))
        
        # Crime type modifiers
        crime_severity_multipliers = {
            "theft": 1.0,
            "assault": 1.1,
            "murder": 1.3,
            "corruption": 0.8,  # Harder to prove
            "treason": 1.4,
            "fraud": 0.9,
            "arson": 1.2,
            "smuggling": 0.85
        }
        
        severity_multiplier = crime_severity_multipliers.get(self.crime_type, 1.0)
        final_probability = min(1.0, biased_probability * severity_multiplier)
        
        evaluation = {
            'case_id': self.case_id,
            'evidence_strength': evidence_weight,
            'witness_factor': witness_factor,
            'witness_count': len(self.witness_ids),
            'base_guilt_probability': base_guilt_probability,
            'regional_bias': regional_bias,
            'crime_severity_multiplier': severity_multiplier,
            'final_guilt_probability': final_probability,
            'recommended_action': self._get_recommended_action(final_probability)
        }
        
        return evaluation
    
    def _get_recommended_action(self, guilt_probability: float) -> str:
        """Get recommended action based on guilt probability."""
        if guilt_probability >= 0.8:
            return "convict_high_confidence"
        elif guilt_probability >= 0.6:
            return "convict_moderate_confidence"
        elif guilt_probability >= 0.4:
            return "investigate_further"
        elif guilt_probability >= 0.2:
            return "insufficient_evidence"
        else:
            return "dismiss_case"
    
    def finalize_case(self, guilty_threshold: float = 0.6) -> Dict[str, Any]:
        """
        Finalize a case based on guilt probability and apply suitable punishment.
        
        This method provides a simplified case resolution that evaluates the case,
        determines a verdict based on the guilty threshold, and applies appropriate
        punishment without complex regional bias or corruption factors.
        
        Args:
            guilty_threshold: Probability threshold for guilty verdict (default 0.6)
            
        Returns:
            Dictionary containing finalization results
        """
        if self.status != "open":
            raise ValueError(f"Case {self.case_id} is not open for finalization")
        
        # Evaluate the case to get guilt probability
        eval_result = self.evaluate_case()
        
        # Determine verdict based on threshold
        self.verdict = "guilty" if eval_result["final_guilt_probability"] >= guilty_threshold else "innocent"
        self.status = "resolved"
        self.resolution_date = datetime.now()
        
        # Apply appropriate punishment based on verdict and crime type
        if self.verdict == "guilty":
            if self.crime_type in ["fraud", "corruption", "smuggling"]:
                self.punishment_applied.append("fine")
            elif self.crime_type in ["theft", "assault", "arson"]:
                self.punishment_applied.append("imprisonment")
            elif self.crime_type in ["murder", "treason"]:
                self.punishment_applied.append("execution")
            else:
                self.punishment_applied.append("sanctions")
        else:
            self.punishment_applied.append("released")
        
        # Create finalization result
        finalization_result = {
            'case_id': self.case_id,
            'crime_type': self.crime_type,
            'accused_id': self.accused_id,
            'verdict': self.verdict,
            'punishment_applied': self.punishment_applied.copy(),
            'guilt_probability': eval_result["final_guilt_probability"],
            'guilty_threshold': guilty_threshold,
            'evidence_strength': eval_result["evidence_strength"],
            'witness_count': eval_result["witness_count"],
            'resolution_date': self.resolution_date.isoformat(),
            'evaluation_details': eval_result
        }
        
        return finalization_result
    
    def resolve_case(self, 
                    bias_profile: Optional[Dict[str, Any]] = None,
                    judge_id: Optional[str] = None,
                    witness_credibility_map: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Resolve the case by applying regional justice logic and bias.
        
        Args:
            bias_profile: Regional bias configuration
            judge_id: ID of the judge handling the case
            witness_credibility_map: Witness credibility ratings
            
        Returns:
            Dictionary containing resolution details
        """
        if self.status != "open":
            raise ValueError(f"Case {self.case_id} is not open for resolution")
        
        bias_profile = bias_profile or {}
        self.judge_id = judge_id
        
        # Get case evaluation
        regional_bias = bias_profile.get('general_bias', 0.0)
        evaluation = self.evaluate_case(witness_credibility_map, regional_bias)
        
        # Apply specific biases
        crime_bias = bias_profile.get('crime_biases', {}).get(self.crime_type, 0.0)
        corruption_level = bias_profile.get('corruption_level', 0.0)
        political_influence = bias_profile.get('political_influence', 0.0)
        
        # Calculate final verdict probability
        guilt_probability = evaluation['final_guilt_probability']
        guilt_probability += crime_bias
        
        # Corruption can flip cases
        if corruption_level > 0.5 and random.random() < corruption_level:
            # Corrupt justice - might dismiss strong cases or convict weak ones
            if guilt_probability > 0.7 and random.random() < 0.3:
                guilt_probability *= 0.3  # Dismiss strong case due to corruption
                self.investigation_notes.append(f"Case influenced by corruption - evidence suppressed")
            elif guilt_probability < 0.3 and random.random() < 0.4:
                guilt_probability = 0.8  # False conviction
                self.investigation_notes.append(f"Case influenced by corruption - false evidence planted")
        
        # Political influence
        if political_influence != 0.0:
            guilt_probability += political_influence * 0.3
            self.investigation_notes.append(f"Case influenced by political pressure: {political_influence:.2f}")
        
        guilt_probability = max(0.0, min(1.0, guilt_probability))
        
        # Determine verdict
        verdict_threshold = random.uniform(0.45, 0.55)  # Some randomness in justice
        
        if guilt_probability >= verdict_threshold:
            possible_verdicts = ["guilty", "guilty_lesser_charge"]
            if guilt_probability >= 0.8:
                possible_verdicts.append("guilty_aggravated")
            self.verdict = random.choice(possible_verdicts)
        else:
            possible_verdicts = ["not_guilty", "insufficient_evidence"]
            if guilt_probability < 0.2:
                possible_verdicts.append("dismissed")
            self.verdict = random.choice(possible_verdicts)
        
        # Update case status
        self.status = "resolved"
        self.resolution_date = datetime.now()
        
        resolution_details = {
            'case_id': self.case_id,
            'verdict': self.verdict,
            'guilt_probability': guilt_probability,
            'verdict_threshold': verdict_threshold,
            'judge_id': self.judge_id,
            'bias_factors': {
                'regional_bias': regional_bias,
                'crime_bias': crime_bias,
                'corruption_level': corruption_level,
                'political_influence': political_influence
            },
            'evaluation': evaluation
        }
        
        return resolution_details
    
    def apply_punishment(self, 
                        reputation_engine: Any,
                        punishment_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Apply punishment based on verdict and regional law.
        
        Args:
            reputation_engine: ReputationEngine instance for applying reputation changes
            punishment_profile: Regional punishment configuration
            
        Returns:
            Dictionary containing punishment details
        """
        if self.verdict is None:
            raise ValueError(f"Case {self.case_id} has no verdict to apply")
        
        punishment_profile = punishment_profile or {}
        punishment_details = {
            'case_id': self.case_id,
            'verdict': self.verdict,
            'punishments_applied': [],
            'reputation_changes': {},
            'faction_impacts': {}
        }
        
        # Base punishment severity
        crime_severities = {
            "theft": 0.3,
            "assault": 0.5,
            "murder": 1.0,
            "corruption": 0.4,
            "treason": 1.2,
            "fraud": 0.4,
            "arson": 0.7,
            "smuggling": 0.4
        }
        
        base_severity = crime_severities.get(self.crime_type, 0.5)
        
        # Verdict modifiers
        verdict_multipliers = {
            "guilty": 1.0,
            "guilty_lesser_charge": 0.6,
            "guilty_aggravated": 1.4,
            "not_guilty": 0.0,
            "insufficient_evidence": 0.0,
            "dismissed": 0.0
        }
        
        severity_multiplier = verdict_multipliers.get(self.verdict, 0.0)
        final_severity = base_severity * severity_multiplier
        
        # Regional punishment modifiers
        regional_harshness = punishment_profile.get('harshness_multiplier', 1.0)
        final_severity *= regional_harshness
        
        # Apply punishments if guilty
        if "guilty" in self.verdict:
            # Reputation punishment
            reputation_penalty = -final_severity * 0.5
            
            # Regional reputation impact
            reputation_engine.update_reputation(
                self.accused_id,
                region=self.region,
                delta=reputation_penalty,
                reason=f"convicted_of_{self.crime_type}"
            )
            punishment_details['reputation_changes'][f"region_{self.region}"] = reputation_penalty
            
            # Law enforcement faction impact
            law_factions = punishment_profile.get('law_factions', ['city_guard', 'magistrates'])
            for faction in law_factions:
                faction_penalty = -final_severity * 0.4
                reputation_engine.update_reputation(
                    self.accused_id,
                    faction=faction,
                    delta=faction_penalty,
                    reason=f"convicted_of_{self.crime_type}"
                )
                punishment_details['faction_impacts'][faction] = faction_penalty
            
            # Criminal faction benefits (if applicable)
            if self.crime_type in ['theft', 'smuggling', 'fraud']:
                criminal_factions = punishment_profile.get('criminal_factions', ['thieves_guild'])
                for faction in criminal_factions:
                    faction_bonus = final_severity * 0.2  # Criminals respect successful crime (even if caught)
                    reputation_engine.update_reputation(
                        self.accused_id,
                        faction=faction,
                        delta=faction_bonus,
                        reason=f"criminal_reputation_from_{self.crime_type}"
                    )
                    punishment_details['faction_impacts'][faction] = faction_bonus
            
            # Determine specific punishments
            punishments = []
            if final_severity >= 0.8:
                punishments.extend(["exile", "heavy_fine"])
            elif final_severity >= 0.5:
                punishments.extend(["imprisonment", "fine"])
            elif final_severity >= 0.3:
                punishments.extend(["fine", "public_service"])
            else:
                punishments.append("warning")
            
            # Add punishment-specific effects
            for punishment in punishments:
                if punishment == "exile":
                    # Exile affects all regional reputation
                    for region in reputation_engine.region_registry:
                        if region != self.region:  # Don't double-penalize home region
                            reputation_engine.update_reputation(
                                self.accused_id,
                                region=region,
                                delta=-0.2,
                                reason=f"exiled_for_{self.crime_type}"
                            )
                elif punishment == "heavy_fine":
                    # Heavy fines affect merchant relations
                    reputation_engine.update_reputation(
                        self.accused_id,
                        faction="merchants_guild",
                        delta=-0.3,
                        reason="unable_to_pay_fine"
                    )
            
            self.punishment_applied = punishments
            punishment_details['punishments_applied'] = punishments
            
        else:
            # Not guilty - reputation restoration
            if self.verdict == "not_guilty":
                reputation_bonus = final_severity * 0.3  # Partial restoration
                reputation_engine.update_reputation(
                    self.accused_id,
                    region=self.region,
                    delta=reputation_bonus,
                    reason=f"acquitted_of_{self.crime_type}"
                )
                punishment_details['reputation_changes'][f"region_{self.region}"] = reputation_bonus
        
        # Record the punishment application
        self.reputation_changes = punishment_details['reputation_changes']
        self.factional_impacts = punishment_details['faction_impacts']
        
        return punishment_details


class JusticeEngine:
    """
    Manages the legal system across regions with configurable law profiles.
    
    Handles case creation, tracking, and resolution with support for
    regional variations, corruption, and political influence.
    """
    
    def __init__(self):
        """Initialize the justice engine."""
        self.active_cases: Dict[str, JusticeCase] = {}
        self.resolved_cases: Dict[str, JusticeCase] = {}
        self.regional_law_profiles: Dict[str, Dict[str, Any]] = {}
        
        # Integration tracking
        self.memory_case_triggers: Dict[str, str] = {}  # memory_id -> case_id
        self.rumor_case_triggers: Dict[str, str] = {}   # rumor_id -> case_id
        
        # Justice system statistics
        self.case_statistics: Dict[str, Any] = {
            'total_cases': 0,
            'convictions': 0,
            'acquittals': 0,
            'dismissals': 0,
            'by_crime_type': defaultdict(int),
            'by_region': defaultdict(int)
        }
        
        # Default regional profiles
        self._initialize_default_profiles()
    
    def _initialize_default_profiles(self) -> None:
        """Initialize default regional law profiles."""
        self.regional_law_profiles = {
            'law_abiding_city': {
                'general_bias': 0.1,  # Slight bias toward conviction
                'corruption_level': 0.1,
                'political_influence': 0.0,
                'harshness_multiplier': 1.0,
                'crime_biases': {
                    'theft': 0.1,
                    'murder': 0.2,
                    'corruption': -0.1  # Harder to convict officials
                },
                'law_factions': ['city_guard', 'magistrates'],
                'criminal_factions': ['thieves_guild']
            },
            'corrupt_port': {
                'general_bias': -0.2,  # Bias toward acquittal (corrupt)
                'corruption_level': 0.7,
                'political_influence': 0.3,
                'harshness_multiplier': 0.6,
                'crime_biases': {
                    'smuggling': -0.4,  # Very lenient on smuggling
                    'corruption': -0.5,
                    'theft': -0.1
                },
                'law_factions': ['harbor_patrol'],
                'criminal_factions': ['smugglers_guild', 'thieves_guild']
            },
            'harsh_frontier': {
                'general_bias': 0.3,  # Strong bias toward conviction
                'corruption_level': 0.2,
                'political_influence': -0.1,
                'harshness_multiplier': 1.8,
                'crime_biases': {
                    'murder': 0.3,
                    'theft': 0.2,
                    'assault': 0.3
                },
                'law_factions': ['frontier_militia'],
                'criminal_factions': ['bandit_clans']
            },
            'noble_district': {
                'general_bias': 0.0,
                'corruption_level': 0.4,
                'political_influence': 0.6,  # High political influence
                'harshness_multiplier': 0.8,
                'crime_biases': {
                    'corruption': -0.3,
                    'fraud': -0.2,
                    'theft': 0.1  # Harsh on common crimes
                },
                'law_factions': ['noble_guard', 'magistrates'],
                'criminal_factions': []
            }
        }
    
    def create_case_from_memory(self, 
                               memory_node: Any,
                               accused_id: str,
                               region: str,
                               crime_type: Optional[str] = None) -> Optional[JusticeCase]:
        """
        Create a case from a memory node.
        
        Args:
            memory_node: MemoryNode that triggered the case
            accused_id: ID of the accused
            region: Region where case should be tried
            crime_type: Specific crime type (auto-detected if None)
            
        Returns:
            JusticeCase instance if created, None if memory insufficient
        """
        # Extract memory properties
        memory_id = getattr(memory_node, 'event_id', str(uuid.uuid4()))
        context_tags = getattr(memory_node, 'context_tags', [])
        actor_ids = getattr(memory_node, 'actor_ids', [])
        strength = getattr(memory_node, 'strength', 0.5)
        description = getattr(memory_node, 'description', '')
        
        # Auto-detect crime type if not provided
        if crime_type is None:
            crime_type = self._detect_crime_type(context_tags, description)
        
        if crime_type is None:
            return None  # No crime detected
        
        # Memory strength influences evidence strength
        evidence_strength = min(1.0, strength * 1.2)  # Boost strong memories slightly
        
        # Find witnesses (actors other than accused)
        witnesses = [actor for actor in actor_ids if actor != accused_id]
        
        # Create the case
        case = JusticeCase(
            crime_type=crime_type,
            accused_id=accused_id,
            region=region,
            witness_ids=witnesses,
            evidence_strength=evidence_strength
        )
        
        case.source_memories.append(memory_id)
        case.add_evidence(
            evidence_source=f"memory_{memory_id}",
            strength_delta=0.0,  # Already applied in initialization
            notes=f"Case created from memory: {description[:100]}"
        )
        
        # Register case
        self.active_cases[case.case_id] = case
        self.memory_case_triggers[memory_id] = case.case_id
        self.case_statistics['total_cases'] += 1
        self.case_statistics['by_crime_type'][crime_type] += 1
        self.case_statistics['by_region'][region] += 1
        
        return case
    
    def create_case_from_rumor(self, 
                              rumor: Any,
                              accused_id: str,
                              region: str,
                              crime_type: Optional[str] = None) -> Optional[JusticeCase]:
        """
        Create a case from a rumor.
        
        Args:
            rumor: Rumor that triggered the case
            accused_id: ID of the accused
            region: Region where case should be tried
            crime_type: Specific crime type (auto-detected if None)
            
        Returns:
            JusticeCase instance if created, None if rumor insufficient
        """
        # Extract rumor properties
        rumor_id = getattr(rumor, 'rumor_id', str(uuid.uuid4()))
        content = getattr(rumor, 'content', '')
        confidence = getattr(rumor, 'confidence_level', 0.5)
        spread_count = getattr(rumor, 'spread_count', 1)
        originator_id = getattr(rumor, 'originator_id', None)
        
        # Auto-detect crime type if not provided
        if crime_type is None:
            crime_type = self._detect_crime_type([], content)
        
        if crime_type is None:
            return None  # No crime detected
        
        # Rumor confidence and spread influence evidence strength
        evidence_strength = confidence * min(1.0, spread_count / 5.0)  # More spread = more credible
        
        # Originator becomes witness if not the accused
        witnesses = [originator_id] if originator_id and originator_id != accused_id else []
        
        # Create the case
        case = JusticeCase(
            crime_type=crime_type,
            accused_id=accused_id,
            region=region,
            witness_ids=witnesses,
            evidence_strength=evidence_strength
        )
        
        case.source_rumors.append(rumor_id)
        case.add_evidence(
            evidence_source=f"rumor_{rumor_id}",
            strength_delta=0.0,  # Already applied in initialization
            notes=f"Case created from rumor: {content[:100]}"
        )
        
        # Register case
        self.active_cases[case.case_id] = case
        self.rumor_case_triggers[rumor_id] = case.case_id
        self.case_statistics['total_cases'] += 1
        self.case_statistics['by_crime_type'][crime_type] += 1
        self.case_statistics['by_region'][region] += 1
        
        return case
    
    def _detect_crime_type(self, context_tags: List[str], content: str) -> Optional[str]:
        """
        Detect crime type from context tags and content.
        
        Args:
            context_tags: List of context tags
            content: Text content to analyze
            
        Returns:
            Detected crime type or None
        """
        content_lower = content.lower()
        
        # Check context tags first
        tag_crime_map = {
            'theft': 'theft',
            'murder': 'murder',
            'assault': 'assault',
            'corruption': 'corruption',
            'fraud': 'fraud',
            'smuggling': 'smuggling',
            'arson': 'arson',
            'treason': 'treason'
        }
        
        for tag in context_tags:
            if tag in tag_crime_map:
                return tag_crime_map[tag]
        
        # Check content keywords
        content_crime_map = {
            'stole': 'theft',
            'stolen': 'theft',
            'theft': 'theft',
            'killed': 'murder',
            'murdered': 'murder',
            'murder': 'murder',
            'attacked': 'assault',
            'assault': 'assault',
            'bribe': 'corruption',
            'corrupt': 'corruption',
            'fraud': 'fraud',
            'cheated': 'fraud',
            'smuggle': 'smuggling',
            'contraband': 'smuggling',
            'fire': 'arson',
            'burned': 'arson',
            'treason': 'treason',
            'betrayed': 'treason'
        }
        
        for keyword, crime_type in content_crime_map.items():
            if keyword in content_lower:
                return crime_type
        
        return None
    
    def resolve_case(self, 
                    case_id: str,
                    region_profile: Optional[str] = None,
                    judge_id: Optional[str] = None,
                    witness_credibility_map: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Resolve a case using regional justice system.
        
        Args:
            case_id: ID of case to resolve
            region_profile: Regional law profile to use
            judge_id: Judge handling the case
            witness_credibility_map: Witness credibility ratings
            
        Returns:
            Resolution details
        """
        if case_id not in self.active_cases:
            raise ValueError(f"Case {case_id} not found in active cases")
        
        case = self.active_cases[case_id]
        
        # Get regional profile
        if region_profile is None:
            # Try to match region to a profile
            region_profile = self._match_region_profile(case.region)
        
        bias_profile = self.regional_law_profiles.get(region_profile, {})
        
        # Resolve the case
        resolution = case.resolve_case(bias_profile, judge_id, witness_credibility_map)
        
        # Move to resolved cases
        self.resolved_cases[case_id] = case
        del self.active_cases[case_id]
        
        # Update statistics
        if "guilty" in case.verdict:
            self.case_statistics['convictions'] += 1
        elif case.verdict in ["not_guilty", "insufficient_evidence"]:
            self.case_statistics['acquittals'] += 1
        elif case.verdict == "dismissed":
            self.case_statistics['dismissals'] += 1
        
        return resolution
    
    def _match_region_profile(self, region: str) -> str:
        """Match a region name to a law profile."""
        region_lower = region.lower()
        
        if 'port' in region_lower or 'harbor' in region_lower:
            return 'corrupt_port'
        elif 'frontier' in region_lower or 'border' in region_lower:
            return 'harsh_frontier'
        elif 'noble' in region_lower or 'upper' in region_lower:
            return 'noble_district'
        else:
            return 'law_abiding_city'
    
    def apply_case_punishment(self, 
                             case_id: str,
                             reputation_engine: Any,
                             region_profile: Optional[str] = None) -> Dict[str, Any]:
        """
        Apply punishment for a resolved case.
        
        Args:
            case_id: ID of resolved case
            reputation_engine: ReputationEngine instance
            region_profile: Regional punishment profile
            
        Returns:
            Punishment details
        """
        if case_id not in self.resolved_cases:
            raise ValueError(f"Case {case_id} not found in resolved cases")
        
        case = self.resolved_cases[case_id]
        
        if region_profile is None:
            region_profile = self._match_region_profile(case.region)
        
        punishment_profile = self.regional_law_profiles.get(region_profile, {})
        
        return case.apply_punishment(reputation_engine, punishment_profile)
    
    def get_case_statistics(self) -> Dict[str, Any]:
        """Get comprehensive case statistics."""
        active_count = len(self.active_cases)
        resolved_count = len(self.resolved_cases)
        
        conviction_rate = (self.case_statistics['convictions'] / 
                          max(1, resolved_count)) if resolved_count > 0 else 0.0
        
        return {
            'active_cases': active_count,
            'resolved_cases': resolved_count,
            'total_cases': self.case_statistics['total_cases'],
            'conviction_rate': conviction_rate,
            'convictions': self.case_statistics['convictions'],
            'acquittals': self.case_statistics['acquittals'],
            'dismissals': self.case_statistics['dismissals'],
            'by_crime_type': dict(self.case_statistics['by_crime_type']),
            'by_region': dict(self.case_statistics['by_region']),
            'regional_profiles': list(self.regional_law_profiles.keys())
        }
    
    def get_regional_justice_summary(self, region: str) -> Dict[str, Any]:
        """Get justice summary for a specific region."""
        regional_cases = [case for case in list(self.active_cases.values()) + list(self.resolved_cases.values())
                         if case.region == region]
        
        if not regional_cases:
            return {'region': region, 'case_count': 0}
        
        resolved_cases = [case for case in regional_cases if case.status == 'resolved']
        convictions = len([case for case in resolved_cases if 'guilty' in (case.verdict or '')])
        
        return {
            'region': region,
            'case_count': len(regional_cases),
            'active_cases': len([case for case in regional_cases if case.status == 'open']),
            'resolved_cases': len(resolved_cases),
            'conviction_rate': convictions / max(1, len(resolved_cases)),
            'crime_types': list(set(case.crime_type for case in regional_cases))
        }


# Test harness
if __name__ == "__main__":
    print("=== Justice System Test Harness ===\n")
    
    # Import reputation engine for testing
    # Note: In real implementation, this would import from reputation_tracker
    class MockReputationEngine:
        def __init__(self):
            self.reputation_updates = []
            self.region_registry = {'Westford', 'Corruptport', 'Frontier_Town'}
        
        def update_reputation(self, entity_id, region=None, faction=None, delta=0.0, reason=""):
            self.reputation_updates.append({
                'entity_id': entity_id, 'region': region, 'faction': faction,
                'delta': delta, 'reason': reason
            })
    
    # Initialize systems
    justice_engine = JusticeEngine()
    reputation_engine = MockReputationEngine()
    
    print("1. Creating cases from simulated memory and rumor data...")
    
    # Mock memory node class
    class MockMemory:
        def __init__(self, event_id, description, context_tags, actor_ids, strength):
            self.event_id = event_id
            self.description = description
            self.context_tags = context_tags
            self.actor_ids = actor_ids
            self.strength = strength
    
    # Mock rumor class
    class MockRumor:
        def __init__(self, rumor_id, content, confidence_level, spread_count, originator_id):
            self.rumor_id = rumor_id
            self.content = content
            self.confidence_level = confidence_level
            self.spread_count = spread_count
            self.originator_id = originator_id
    
    # Case 1: Theft case from strong memory
    theft_memory = MockMemory(
        event_id="mem_001",
        description="Saw merchant_bob steal bread from baker's stall",
        context_tags=["theft", "witnessed", "public"],
        actor_ids=["merchant_bob", "baker_alice", "witness_guard"],
        strength=0.9
    )
    
    case1 = justice_engine.create_case_from_memory(
        theft_memory, "merchant_bob", "Westford", "theft"
    )
    print(f"Created Case 1: {case1.case_id}")
    print(f"  Crime: {case1.crime_type}, Accused: {case1.accused_id}")
    print(f"  Evidence strength: {case1.evidence_strength:.2f}")
    print(f"  Witnesses: {case1.witness_ids}")
    
    # Case 2: Corruption case from rumor
    corruption_rumor = MockRumor(
        rumor_id="rum_001",
        content="Guard captain takes bribes from smugglers at the docks",
        confidence_level=0.6,
        spread_count=4,
        originator_id="dock_worker"
    )
    
    case2 = justice_engine.create_case_from_rumor(
        corruption_rumor, "guard_captain", "Corruptport", "corruption"
    )
    print(f"\nCreated Case 2: {case2.case_id}")
    print(f"  Crime: {case2.crime_type}, Accused: {case2.accused_id}")
    print(f"  Evidence strength: {case2.evidence_strength:.2f}")
    print(f"  Witnesses: {case2.witness_ids}")
    
    # Case 3: Murder case from memory
    murder_memory = MockMemory(
        event_id="mem_002",
        description="Found bandit_leader standing over dead merchant with bloody knife",
        context_tags=["murder", "crime", "violence"],
        actor_ids=["bandit_leader", "dead_merchant", "investigator"],
        strength=0.8
    )
    
    case3 = justice_engine.create_case_from_memory(
        murder_memory, "bandit_leader", "Frontier_Town", "murder"
    )
    print(f"\nCreated Case 3: {case3.case_id}")
    print(f"  Crime: {case3.crime_type}, Accused: {case3.accused_id}")
    print(f"  Evidence strength: {case3.evidence_strength:.2f}")
    print(f"  Witnesses: {case3.witness_ids}")
    
    print("\n2. Resolving cases under different regional justice systems...")
    
    # Resolve Case 1 in law-abiding city
    print(f"\nResolving theft case in law-abiding Westford:")
    witness_credibility = {
        "baker_alice": 0.8,  # Victim, high credibility
        "witness_guard": 0.9  # Official witness
    }
    
    resolution1 = justice_engine.resolve_case(
        case1.case_id,
        region_profile="law_abiding_city",
        judge_id="judge_fairman",
        witness_credibility_map=witness_credibility
    )
    print(f"  Verdict: {resolution1['verdict']}")
    print(f"  Guilt probability: {resolution1['guilt_probability']:.3f}")
    print(f"  Judge: {resolution1['judge_id']}")
    
    # Apply punishment for Case 1
    punishment1 = justice_engine.apply_case_punishment(
        case1.case_id, reputation_engine, "law_abiding_city"
    )
    print(f"  Punishments: {punishment1['punishments_applied']}")
    print(f"  Reputation changes: {punishment1['reputation_changes']}")
    
    # Resolve Case 2 in corrupt port
    print(f"\nResolving corruption case in corrupt Corruptport:")
    witness_credibility2 = {
        "dock_worker": 0.4  # Low credibility in corrupt system
    }
    
    resolution2 = justice_engine.resolve_case(
        case2.case_id,
        region_profile="corrupt_port",
        judge_id="judge_bribeson",
        witness_credibility_map=witness_credibility2
    )
    print(f"  Verdict: {resolution2['verdict']}")
    print(f"  Guilt probability: {resolution2['guilt_probability']:.3f}")
    print(f"  Corruption influence: {resolution2['bias_factors']['corruption_level']}")
    
    # Apply punishment for Case 2
    punishment2 = justice_engine.apply_case_punishment(
        case2.case_id, reputation_engine, "corrupt_port"
    )
    print(f"  Punishments: {punishment2['punishments_applied']}")
    print(f"  Reputation changes: {punishment2['reputation_changes']}")
    
    # Resolve Case 3 in harsh frontier
    print(f"\nResolving murder case in harsh Frontier_Town:")
    witness_credibility3 = {
        "investigator": 0.7
    }
    
    resolution3 = justice_engine.resolve_case(
        case3.case_id,
        region_profile="harsh_frontier",
        judge_id="sheriff_ironhand",
        witness_credibility_map=witness_credibility3
    )
    print(f"  Verdict: {resolution3['verdict']}")
    print(f"  Guilt probability: {resolution3['guilt_probability']:.3f}")
    print(f"  Harshness multiplier: Shows in punishment severity")
    
    # Apply punishment for Case 3
    punishment3 = justice_engine.apply_case_punishment(
        case3.case_id, reputation_engine, "harsh_frontier"
    )
    print(f"  Punishments: {punishment3['punishments_applied']}")
    print(f"  Reputation changes: {punishment3['reputation_changes']}")
    
    print("\n3. Justice system statistics...")
    
    stats = justice_engine.get_case_statistics()
    print(f"\nOverall Justice Statistics:")
    print(f"  Total cases processed: {stats['total_cases']}")
    print(f"  Convictions: {stats['convictions']}")
    print(f"  Acquittals: {stats['acquittals']}")
    print(f"  Dismissals: {stats['dismissals']}")
    print(f"  Conviction rate: {stats['conviction_rate']:.1%}")
    print(f"  Cases by crime type: {stats['by_crime_type']}")
    print(f"  Cases by region: {stats['by_region']}")
    
    print("\n4. Regional justice summaries...")
    
    for region in ['Westford', 'Corruptport', 'Frontier_Town']:
        summary = justice_engine.get_regional_justice_summary(region)
        print(f"\n{region} Justice Summary:")
        print(f"  Total cases: {summary['case_count']}")
        print(f"  Conviction rate: {summary.get('conviction_rate', 0):.1%}")
        print(f"  Crime types handled: {summary.get('crime_types', [])}")
    
    print("\n5. Reputation impact summary...")
    
    print(f"\nReputation changes applied:")
    for i, update in enumerate(reputation_engine.reputation_updates, 1):
        entity = update['entity_id']
        location = update['region'] or update['faction'] or 'unknown'
        delta = update['delta']
        reason = update['reason']
        print(f"  {i}. {entity} at {location}: {delta:+.3f} ({reason})")
    
    print("\n=== Test Complete ===") 