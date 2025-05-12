"""
Confidence Scoring Engine for the Technology Extraction System.

This module provides functionality for calculating confidence scores
for detected technologies based on evidence quality and quantity.
"""
import logging
import math
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple, Union

from tech_extraction.models.evidence import Evidence, EvidenceType, EvidenceSource
from tech_extraction.models.technology import Technology, TechnologyCategory

logger = logging.getLogger(__name__)


class ConfidenceScoringEngine:
    """
    Engine for calculating confidence scores for detected technologies.
    
    The ConfidenceScoringEngine performs the following operations:
    1. Weight evidence based on type, source, and quality
    2. Aggregate evidence for each technology
    3. Calculate confidence scores using a multi-factor model
    4. Normalize scores for consistent reporting
    """
    
    # Evidence type weights (higher = stronger evidence)
    EVIDENCE_TYPE_WEIGHTS = {
        EvidenceType.IMPORT_STATEMENT: 8,
        EvidenceType.MANIFEST_ENTRY: 10,
        EvidenceType.FRAMEWORK_PATTERN: 7,
        EvidenceType.CLASS_DEFINITION: 7,
        EvidenceType.FUNCTION_CALL: 6,
        EvidenceType.CONFIGURATION: 9,
        EvidenceType.FILE_STRUCTURE: 5,
        EvidenceType.DEPENDENCY_USAGE: 8,
        EvidenceType.AI_DETECTION: 6,
        EvidenceType.UNKNOWN: 3
    }
    
    # Evidence source weights (higher = more reliable)
    EVIDENCE_SOURCE_WEIGHTS = {
        EvidenceSource.STATIC_ANALYSIS: 10,
        EvidenceSource.MANIFEST_PARSER: 10,
        EvidenceSource.IMPORT_ANALYZER: 9,
        EvidenceSource.PATTERN_MATCHING: 8,
        EvidenceSource.AI_MODEL: 7,
        EvidenceSource.USER_PROVIDED: 9,
        EvidenceSource.UNKNOWN: 5
    }
    
    # Minimum evidence threshold for confidence calculation
    MIN_EVIDENCE_COUNT = 1
    
    # Minimum confidence threshold for reporting
    MIN_CONFIDENCE_THRESHOLD = 10.0
    
    def __init__(self):
        """Initialize the confidence scoring engine."""
        # Map of technology name to list of evidence
        self.evidence_by_technology = defaultdict(list)
        
        # Cache of calculated confidence scores
        self.confidence_scores = {}
        
        # Normalizing factors
        self.max_raw_score = 0.0
    
    def add_evidence(self, technology_name: str, evidence: Evidence):
        """
        Add evidence for a technology.
        
        Args:
            technology_name: Name of the technology
            evidence: Evidence object
        """
        self.evidence_by_technology[technology_name].append(evidence)
        
        # Invalidate cached scores
        if technology_name in self.confidence_scores:
            del self.confidence_scores[technology_name]
    
    def add_evidence_batch(self, evidence_items: Dict[str, List[Evidence]]):
        """
        Add multiple evidence items for technologies.
        
        Args:
            evidence_items: Dictionary mapping technology names to lists of evidence
        """
        for tech_name, evidence_list in evidence_items.items():
            for evidence in evidence_list:
                self.add_evidence(tech_name, evidence)
    
    def _calculate_raw_score(self, evidence_list: List[Evidence]) -> float:
        """
        Calculate raw confidence score based on evidence.
        
        Args:
            evidence_list: List of evidence items
            
        Returns:
            Raw confidence score
        """
        if not evidence_list:
            return 0.0
        
        # Base score from evidence count with diminishing returns
        count_factor = math.log(len(evidence_list) + 1, 2)
        
        # Calculate weighted sum of evidence
        weighted_sum = 0.0
        for evidence in evidence_list:
            # Get weights for this evidence
            type_weight = self.EVIDENCE_TYPE_WEIGHTS.get(
                evidence.type, self.EVIDENCE_TYPE_WEIGHTS[EvidenceType.UNKNOWN]
            )
            source_weight = self.EVIDENCE_SOURCE_WEIGHTS.get(
                evidence.source, self.EVIDENCE_SOURCE_WEIGHTS[EvidenceSource.UNKNOWN]
            )
            
            # Calculate individual evidence score
            evidence_score = (type_weight * source_weight) / 10.0  # Normalize to 0-10 scale
            
            # Apply confidence modifier from the evidence
            if evidence.confidence > 0:
                evidence_score *= evidence.confidence / 100.0
            
            weighted_sum += evidence_score
        
        # Combine count factor and weighted sum
        raw_score = weighted_sum * count_factor
        
        return raw_score
    
    def _normalize_score(self, raw_score: float) -> float:
        """
        Normalize a raw score to a 0-100 scale.
        
        Args:
            raw_score: Raw confidence score
            
        Returns:
            Normalized confidence score (0-100)
        """
        # Update max raw score
        self.max_raw_score = max(self.max_raw_score, raw_score)
        
        # Apply sigmoid normalization for a more intuitive scale
        # This maps low raw scores to low confidence and high raw scores to high confidence
        # with a smooth transition in between
        if raw_score <= 0:
            return 0.0
        
        # Use a modified logistic function
        normalized = 100 / (1 + math.exp(-0.5 * (raw_score - 10)))
        
        return normalized
    
    def calculate_confidence(self, technology_name: str) -> float:
        """
        Calculate confidence score for a technology.
        
        Args:
            technology_name: Name of the technology
            
        Returns:
            Confidence score (0-100)
        """
        # Check cache first
        if technology_name in self.confidence_scores:
            return self.confidence_scores[technology_name]
        
        # Get evidence for this technology
        evidence_list = self.evidence_by_technology.get(technology_name, [])
        
        # Check minimum evidence threshold
        if len(evidence_list) < self.MIN_EVIDENCE_COUNT:
            self.confidence_scores[technology_name] = 0.0
            return 0.0
        
        # Calculate raw score
        raw_score = self._calculate_raw_score(evidence_list)
        
        # Normalize score
        normalized_score = self._normalize_score(raw_score)
        
        # Apply minimum threshold
        if normalized_score < self.MIN_CONFIDENCE_THRESHOLD:
            normalized_score = 0.0
        
        # Cache and return
        self.confidence_scores[technology_name] = normalized_score
        return normalized_score
    
    def calculate_all_confidences(self) -> Dict[str, float]:
        """
        Calculate confidence scores for all technologies.
        
        Returns:
            Dictionary mapping technology names to confidence scores
        """
        for tech_name in self.evidence_by_technology.keys():
            if tech_name not in self.confidence_scores:
                self.calculate_confidence(tech_name)
        
        return self.confidence_scores
    
    def get_supporting_evidence(self, technology_name: str, max_items: int = 5) -> List[Evidence]:
        """
        Get the most significant supporting evidence for a technology.
        
        Args:
            technology_name: Name of the technology
            max_items: Maximum number of evidence items to return
            
        Returns:
            List of the most significant evidence items
        """
        evidence_list = self.evidence_by_technology.get(technology_name, [])
        
        if not evidence_list:
            return []
        
        # Sort by weighted significance
        def evidence_significance(evidence):
            type_weight = self.EVIDENCE_TYPE_WEIGHTS.get(
                evidence.type, self.EVIDENCE_TYPE_WEIGHTS[EvidenceType.UNKNOWN]
            )
            source_weight = self.EVIDENCE_SOURCE_WEIGHTS.get(
                evidence.source, self.EVIDENCE_SOURCE_WEIGHTS[EvidenceSource.UNKNOWN]
            )
            confidence = evidence.confidence if evidence.confidence > 0 else 50
            
            return type_weight * source_weight * (confidence / 100)
        
        sorted_evidence = sorted(evidence_list, key=evidence_significance, reverse=True)
        
        # Return top items
        return sorted_evidence[:max_items]
    
    def get_technologies_above_threshold(self, threshold: float = 50.0) -> List[str]:
        """
        Get technologies with confidence scores above a threshold.
        
        Args:
            threshold: Confidence threshold (0-100)
            
        Returns:
            List of technology names above threshold
        """
        # Calculate all confidences
        self.calculate_all_confidences()
        
        # Filter by threshold
        return [
            tech_name for tech_name, score in self.confidence_scores.items()
            if score >= threshold
        ]
    
    def get_evidence_stats(self) -> Dict:
        """
        Get statistics about collected evidence.
        
        Returns:
            Dictionary with evidence statistics
        """
        total_evidence = sum(len(evidence) for evidence in self.evidence_by_technology.values())
        
        # Count by type and source
        type_counts = defaultdict(int)
        source_counts = defaultdict(int)
        
        for evidence_list in self.evidence_by_technology.values():
            for evidence in evidence_list:
                type_counts[evidence.type] += 1
                source_counts[evidence.source] += 1
        
        return {
            "total_technologies": len(self.evidence_by_technology),
            "total_evidence": total_evidence,
            "evidence_by_type": dict(type_counts),
            "evidence_by_source": dict(source_counts),
            "avg_evidence_per_technology": total_evidence / len(self.evidence_by_technology) if self.evidence_by_technology else 0,
        }