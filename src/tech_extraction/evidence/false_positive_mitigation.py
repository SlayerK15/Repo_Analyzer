"""
False Positive Mitigation for the Technology Extraction System.

This module provides functionality for reducing false positives
in technology detection through validation rules and checks.
"""
import logging
import re
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple

from tech_extraction.evidence.confidence_scoring import ConfidenceScoringEngine
from tech_extraction.evidence.evidence_collection import EvidenceCollection
from tech_extraction.models.evidence import Evidence, EvidenceType, EvidenceSource
from tech_extraction.models.technology import Technology, TechnologyCategory

logger = logging.getLogger(__name__)


class FalsePositiveMitigation:
    """
    System for mitigating false positives in technology detection.
    
    The FalsePositiveMitigation performs the following operations:
    1. Apply validation rules to filter out unreliable detections
    2. Check for consistency across multiple detection methods
    3. Detect and filter statistical anomalies
    4. Adjust confidence scores based on validation results
    """
    
    # Confidence threshold below which we consider a detection potentially false
    LOW_CONFIDENCE_THRESHOLD = 40.0
    
    # Minimum evidence count for reliable detection
    MIN_EVIDENCE_COUNT = 2
    
    # List of technologies that often cause false positives
    HIGH_FALSE_POSITIVE_TECHNOLOGIES = {
        # JavaScript ecosystem
        "lodash": {"case_sensitive": True, "min_evidence": 3},
        "react": {"case_sensitive": True, "min_evidence": 3},
        "jquery": {"case_sensitive": False, "min_evidence": 4},
        "express": {"case_sensitive": False, "min_evidence": 4},
        "moment": {"case_sensitive": False, "min_evidence": 3},
        
        # Python ecosystem
        "flask": {"case_sensitive": True, "min_evidence": 3},
        "django": {"case_sensitive": True, "min_evidence": 3},
        "pandas": {"case_sensitive": True, "min_evidence": 3},
        "requests": {"case_sensitive": False, "min_evidence": 3},
        
        # Java ecosystem
        "spring": {"case_sensitive": False, "min_evidence": 3},
        "hibernate": {"case_sensitive": False, "min_evidence": 3},
        
        # Common utility names that might be used for other purposes
        "utils": {"case_sensitive": False, "min_evidence": 5},
        "common": {"case_sensitive": False, "min_evidence": 5},
        "helpers": {"case_sensitive": False, "min_evidence": 5},
        "core": {"case_sensitive": False, "min_evidence": 5},
    }
    
    # List of technology naming conflicts that need disambiguation
    AMBIGUOUS_TECHNOLOGIES = {
        # Format: ambiguous_name -> [actual technologies that might be confused]
        "bootstrap": ["bootstrap-css", "bootstrap-js", "bootstrap-vue", "bootstrap-react"],
        "router": ["vue-router", "react-router", "angular-router", "express-router"],
        "dom": ["react-dom", "jsdom"],
        "test": ["jest", "mocha", "pytest", "unittest"],
        "ui": ["material-ui", "semantic-ui", "element-ui", "ant-design"],
    }
    
    def __init__(
        self, 
        evidence_collection: EvidenceCollection,
        scoring_engine: ConfidenceScoringEngine
    ):
        """
        Initialize the false positive mitigation system.
        
        Args:
            evidence_collection: Evidence collection instance
            scoring_engine: Confidence scoring engine instance
        """
        self.evidence_collection = evidence_collection
        self.scoring_engine = scoring_engine
        
        # Track mitigated technologies
        self.mitigated_technologies = set()
        self.confidence_adjustments = {}
    
    def apply_technology_specific_rules(self, technology_name: str) -> bool:
        """
        Apply technology-specific validation rules.
        
        Args:
            technology_name: Name of the technology to validate
            
        Returns:
            True if the technology passes validation, False otherwise
        """
        # Check if this is a technology with high false positive rate
        if technology_name.lower() in self.HIGH_FALSE_POSITIVE_TECHNOLOGIES:
            rules = self.HIGH_FALSE_POSITIVE_TECHNOLOGIES[technology_name.lower()]
            
            # Apply case sensitivity rule
            name_to_check = technology_name if rules["case_sensitive"] else technology_name.lower()
            compare_func = (lambda x, y: x == y) if rules["case_sensitive"] else (lambda x, y: x.lower() == y.lower())
            
            # Get evidence with matching name (respecting case sensitivity)
            evidence = [
                e for e in self.evidence_collection.get_evidence_for_technology(technology_name)
                if compare_func(e.technology_name, name_to_check)
            ]
            
            # Check minimum evidence count
            if len(evidence) < rules["min_evidence"]:
                logger.info(f"Mitigating '{technology_name}' due to insufficient evidence: {len(evidence)} < {rules['min_evidence']}")
                return False
        
        return True
    
    def disambiguate_technology(self, technology_name: str) -> Optional[str]:
        """
        Attempt to disambiguate an ambiguous technology name.
        
        Args:
            technology_name: Potentially ambiguous technology name
            
        Returns:
            Disambiguated technology name, or None if unable to disambiguate
        """
        tech_lower = technology_name.lower()
        
        # Check if this is an ambiguous technology
        if tech_lower not in self.AMBIGUOUS_TECHNOLOGIES:
            return technology_name
        
        potential_matches = self.AMBIGUOUS_TECHNOLOGIES[tech_lower]
        
        # Check if any of the specific technologies have evidence
        best_match = None
        best_evidence_count = 0
        
        for specific_tech in potential_matches:
            evidence_count = len(self.evidence_collection.get_evidence_for_technology(specific_tech))
            
            if evidence_count > best_evidence_count:
                best_match = specific_tech
                best_evidence_count = evidence_count
        
        # If we found a better match, use it
        if best_match and best_evidence_count >= self.MIN_EVIDENCE_COUNT:
            logger.info(f"Disambiguated '{technology_name}' to '{best_match}' with {best_evidence_count} evidence items")
            return best_match
        
        # If the original technology has sufficient evidence, keep it
        original_evidence_count = len(self.evidence_collection.get_evidence_for_technology(technology_name))
        if original_evidence_count >= self.MIN_EVIDENCE_COUNT:
            return technology_name
        
        # Otherwise, unable to disambiguate
        logger.info(f"Unable to disambiguate '{technology_name}'")
        return None
    
    def validate_by_evidence_types(self, technology_name: str) -> bool:
        """
        Validate a technology by checking for diverse evidence types.
        
        Args:
            technology_name: Name of the technology to validate
            
        Returns:
            True if the technology has diverse evidence, False otherwise
        """
        evidence_list = self.evidence_collection.get_evidence_for_technology(technology_name)
        
        if len(evidence_list) < self.MIN_EVIDENCE_COUNT:
            return False
        
        # Check for diversity of evidence types
        evidence_types = Counter(e.type for e in evidence_list)
        
        # We want at least 2 different types of evidence for strong validation
        if len(evidence_types) >= 2:
            return True
        
        # Special case: if we have manifest evidence, that's strong enough on its own
        if evidence_types.get(EvidenceType.MANIFEST_ENTRY, 0) > 0:
            return True
        
        # Special case: multiple import statements are also strong evidence
        if evidence_types.get(EvidenceType.IMPORT_STATEMENT, 0) >= 3:
            return True
        
        # For single evidence type with few occurrences, require higher confidence
        single_type = list(evidence_types.keys())[0]
        confidence = self.scoring_engine.calculate_confidence(technology_name)
        
        if confidence > self.LOW_CONFIDENCE_THRESHOLD:
            return True
        
        return False
    
    def check_for_statistical_anomalies(self, technology_name: str) -> bool:
        """
        Check if a technology detection is a statistical anomaly.
        
        Args:
            technology_name: Name of the technology to check
            
        Returns:
            True if the technology is valid, False if it's an anomaly
        """
        evidence_list = self.evidence_collection.get_evidence_for_technology(technology_name)
        
        # Skip if we don't have enough evidence
        if not evidence_list:
            return False
        
        # Check for suspicious patterns
        
        # 1. All evidence from single file
        file_paths = set(e.file_path for e in evidence_list if e.file_path)
        if len(file_paths) == 1 and len(evidence_list) > 1:
            # Single file source is suspicious for some technologies
            # For utility libraries, they might be referenced in many files
            if technology_name.lower() in ["utils", "helpers", "common", "util"]:
                return False
        
        # 2. All evidence from AI detection only
        ai_evidence = [e for e in evidence_list if e.source == EvidenceSource.AI_MODEL]
        if len(ai_evidence) == len(evidence_list) and len(evidence_list) > 1:
            # All evidence from AI without corroboration is less reliable
            logger.info(f"Technology '{technology_name}' has only AI-based evidence")
            
            # Check confidence level
            confidence = self.scoring_engine.calculate_confidence(technology_name)
            if confidence < 60:  # Higher threshold for AI-only detections
                return False
        
        # 3. Conflicting evidence
        confidence_values = [e.confidence for e in evidence_list if e.confidence is not None]
        if confidence_values:
            max_confidence = max(confidence_values)
            min_confidence = min(confidence_values)
            
            # Wide range of confidence values can indicate uncertainty
            if max_confidence - min_confidence > 50 and len(evidence_list) >= 3:
                # Adjust confidence rather than reject completely
                self.confidence_adjustments[technology_name] = 0.8  # 20% reduction
        
        return True
    
    def cross_validate_evidence(self, technology_name: str) -> float:
        """
        Cross-validate evidence from multiple sources for consistency.
        
        Args:
            technology_name: Name of the technology to validate
            
        Returns:
            Validation score (0.0-1.0)
        """
        evidence_list = self.evidence_collection.get_evidence_for_technology(technology_name)
        
        if len(evidence_list) < 2:
            return 0.5  # Neutral score for limited evidence
        
        # Group evidence by source
        evidence_by_source = {}
        for evidence in evidence_list:
            if evidence.source not in evidence_by_source:
                evidence_by_source[evidence.source] = []
            evidence_by_source[evidence.source].append(evidence)
        
        # More diverse sources means more reliable detection
        source_count = len(evidence_by_source)
        source_score = min(1.0, source_count / 3)  # Max score at 3+ sources
        
        # Check consistency of evidence confidence
        confidence_values = [e.confidence for e in evidence_list if e.confidence is not None]
        confidence_score = 0.5  # Default neutral
        
        if confidence_values:
            # Calculate consistency using coefficient of variation
            mean_confidence = sum(confidence_values) / len(confidence_values)
            if mean_confidence > 0:
                variance = sum((x - mean_confidence) ** 2 for x in confidence_values) / len(confidence_values)
                std_dev = variance ** 0.5
                cv = std_dev / mean_confidence if mean_confidence > 0 else 0
                
                # Lower CV means more consistent confidence values
                consistency = max(0, 1 - cv)
                confidence_score = min(1.0, consistency)
        
        # Combine scores (weighted average)
        validation_score = (source_score * 0.7) + (confidence_score * 0.3)
        
        return validation_score
    
    def adjust_confidence_scores(self) -> Dict[str, float]:
        """
        Adjust confidence scores based on validation results.
        
        Returns:
            Dictionary mapping technology names to adjusted confidence scores
        """
        # Get current confidence scores
        current_scores = self.scoring_engine.calculate_all_confidences()
        adjusted_scores = {}
        
        for tech_name, score in current_scores.items():
            # Skip if already mitigated
            if tech_name in self.mitigated_technologies:
                adjusted_scores[tech_name] = 0.0
                continue
            
            # Apply confidence adjustment factor if any
            adjustment_factor = self.confidence_adjustments.get(tech_name, 1.0)
            
            # Apply cross-validation score
            validation_score = self.cross_validate_evidence(tech_name)
            
            # Calculate adjusted score
            adjusted_score = score * adjustment_factor * validation_score
            
            # Apply minimum threshold
            if adjusted_score < self.LOW_CONFIDENCE_THRESHOLD:
                adjusted_score = 0.0
            
            adjusted_scores[tech_name] = adjusted_score
        
        return adjusted_scores
    
    def mitigate_false_positives(self) -> Tuple[Set[str], Dict[str, float]]:
        """
        Apply false positive mitigation to detected technologies.
        
        Returns:
            Tuple of (mitigated_technologies, adjusted_confidence_scores)
        """
        logger.info("Starting false positive mitigation")
        
        # Get all technologies with evidence
        technologies = self.evidence_collection.get_technologies_with_evidence()
        
        # Apply mitigation rules
        for tech_name in technologies:
            # 1. Apply technology-specific validation rules
            if not self.apply_technology_specific_rules(tech_name):
                self.mitigated_technologies.add(tech_name)
                continue
            
            # 2. Try to disambiguate ambiguous technologies
            disambiguated = self.disambiguate_technology(tech_name)
            if disambiguated is None or disambiguated != tech_name:
                self.mitigated_technologies.add(tech_name)
                continue
            
            # 3. Validate by evidence types
            if not self.validate_by_evidence_types(tech_name):
                self.mitigated_technologies.add(tech_name)
                continue
            
            # 4. Check for statistical anomalies
            if not self.check_for_statistical_anomalies(tech_name):
                self.mitigated_technologies.add(tech_name)
                continue
        
        # Adjust confidence scores
        adjusted_scores = self.adjust_confidence_scores()
        
        logger.info(f"Mitigated {len(self.mitigated_technologies)} potential false positives")
        return self.mitigated_technologies, adjusted_scores
    
    def get_mitigated_technologies(self) -> Set[str]:
        """
        Get the set of mitigated technologies.
        
        Returns:
            Set of technology names that were mitigated
        """
        return self.mitigated_technologies