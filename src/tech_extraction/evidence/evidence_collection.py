"""
Evidence Collection for the Technology Extraction System.

This module provides functionality for collecting, storing, and categorizing
evidence of technology usage from various sources.
"""
import hashlib
import logging
from collections import defaultdict
from dataclasses import asdict
from typing import Dict, List, Optional, Set, Tuple, Union

from tech_extraction.models.dependency import Dependency, ImportInfo
from tech_extraction.models.evidence import Evidence, EvidenceType, EvidenceSource
from tech_extraction.models.framework import PatternMatch
from tech_extraction.models.technology import Technology, TechnologyCategory

logger = logging.getLogger(__name__)


class EvidenceCollection:
    """
    System for collecting and storing evidence of technology usage.
    
    The EvidenceCollection performs the following operations:
    1. Collect and store evidence from various sources
    2. Categorize evidence by type and source
    3. Map evidence to technologies
    4. Track evidence provenance
    """
    
    def __init__(self):
        """Initialize the evidence collection system."""
        # Storage for all evidence items
        self.evidence_items = []
        
        # Maps to organize evidence
        self.evidence_by_technology = defaultdict(list)
        self.evidence_by_file = defaultdict(list)
        self.evidence_by_source = defaultdict(list)
        self.evidence_by_type = defaultdict(list)
        
        # Set of unique evidence identifiers to avoid duplicates
        self.evidence_identifiers = set()
    
    def _generate_evidence_id(self, evidence: Evidence) -> str:
        """
        Generate a unique identifier for an evidence item.
        
        Args:
            evidence: Evidence item
            
        Returns:
            Unique identifier string
        """
        # Create a composite key from core evidence attributes
        key_parts = [
            str(evidence.type),
            str(evidence.source),
            evidence.technology_name,
            evidence.file_path or "",
            str(evidence.line_number or 0),
            evidence.snippet or "",
            evidence.details or "",
        ]
        
        key = ":".join(key_parts)
        evidence_id = hashlib.md5(key.encode()).hexdigest()
        
        return evidence_id
    
    def add_evidence(self, evidence: Evidence) -> bool:
        """
        Add an evidence item to the collection.
        
        Args:
            evidence: Evidence item to add
            
        Returns:
            True if the evidence was added, False if it was a duplicate
        """
        # Generate a unique identifier
        evidence_id = self._generate_evidence_id(evidence)
        
        # Check for duplicates
        if evidence_id in self.evidence_identifiers:
            return False
        
        # Add the identifier
        self.evidence_identifiers.add(evidence_id)
        
        # Store the evidence
        self.evidence_items.append(evidence)
        
        # Update maps
        self.evidence_by_technology[evidence.technology_name].append(evidence)
        
        if evidence.file_path:
            self.evidence_by_file[evidence.file_path].append(evidence)
        
        self.evidence_by_source[evidence.source].append(evidence)
        self.evidence_by_type[evidence.type].append(evidence)
        
        return True
    
    def create_from_dependency(self, dependency: Dependency) -> Evidence:
        """
        Create evidence from a dependency object.
        
        Args:
            dependency: Dependency object
            
        Returns:
            Created evidence object
        """
        evidence = Evidence(
            technology_name=dependency.name,
            type=EvidenceType.MANIFEST_ENTRY,
            source=EvidenceSource.MANIFEST_PARSER,
            file_path=dependency.source,
            details=f"Version: {dependency.version}" if dependency.version else None,
            snippet=None,
            line_number=None,
            confidence=90  # High confidence for manifest entries
        )
        
        return evidence
    
    def create_from_import(self, import_info: ImportInfo, technology_name: str) -> Evidence:
        """
        Create evidence from an import statement.
        
        Args:
            import_info: Import information
            technology_name: Mapped technology name
            
        Returns:
            Created evidence object
        """
        evidence = Evidence(
            technology_name=technology_name,
            type=EvidenceType.IMPORT_STATEMENT,
            source=EvidenceSource.IMPORT_ANALYZER,
            file_path=import_info.file_path,
            line_number=import_info.line,
            snippet=import_info.path,
            details=f"Import type: {import_info.type}, Category: {import_info.category}",
            confidence=80  # High confidence for imports
        )
        
        return evidence
    
    def create_from_pattern_match(self, pattern_match: PatternMatch) -> Evidence:
        """
        Create evidence from a framework pattern match.
        
        Args:
            pattern_match: Pattern match information
            
        Returns:
            Created evidence object
        """
        evidence = Evidence(
            technology_name=pattern_match.framework,
            type=EvidenceType.FRAMEWORK_PATTERN,
            source=EvidenceSource.PATTERN_MATCHING,
            file_path=pattern_match.file_path,
            line_number=pattern_match.line_number,
            snippet=pattern_match.context,
            details=f"Signature: {pattern_match.signature_name}, Category: {pattern_match.category}",
            confidence=pattern_match.confidence * 100  # Convert from 0-1 to 0-100
        )
        
        return evidence
    
    def create_from_ai_detection(
        self,
        technology_name: str,
        file_path: str,
        confidence: float,
        details: Optional[str] = None,
        snippet: Optional[str] = None,
        line_number: Optional[int] = None
    ) -> Evidence:
        """
        Create evidence from AI model detection.
        
        Args:
            technology_name: Detected technology name
            file_path: Path to the file where the technology was detected
            confidence: Confidence level (0-100)
            details: Additional details about the detection
            snippet: Code snippet showing the evidence
            line_number: Line number in the file
            
        Returns:
            Created evidence object
        """
        evidence = Evidence(
            technology_name=technology_name,
            type=EvidenceType.AI_DETECTION,
            source=EvidenceSource.AI_MODEL,
            file_path=file_path,
            line_number=line_number,
            snippet=snippet,
            details=details,
            confidence=confidence
        )
        
        return evidence
    
    def collect_from_dependencies(self, dependencies: List[Dependency]) -> int:
        """
        Collect evidence from dependencies.
        
        Args:
            dependencies: List of dependencies
            
        Returns:
            Number of evidence items added
        """
        added_count = 0
        
        for dependency in dependencies:
            evidence = self.create_from_dependency(dependency)
            if self.add_evidence(evidence):
                added_count += 1
        
        logger.info(f"Added {added_count} evidence items from {len(dependencies)} dependencies")
        return added_count
    
    def collect_from_imports(self, imports_by_file: Dict[str, List[ImportInfo]], package_mapping: Dict[str, str]) -> int:
        """
        Collect evidence from import statements.
        
        Args:
            imports_by_file: Dictionary mapping file paths to lists of imports
            package_mapping: Dictionary mapping import paths to technology names
            
        Returns:
            Number of evidence items added
        """
        added_count = 0
        
        for file_path, imports in imports_by_file.items():
            for import_info in imports:
                # Skip relative imports and standard library imports
                if import_info.category in ("relative", "standard_library"):
                    continue
                
                # Try to map import path to a technology name
                technology_name = package_mapping.get(import_info.path, import_info.package_name)
                
                # Update import_info with file path
                import_info.file_path = file_path
                
                evidence = self.create_from_import(import_info, technology_name)
                if self.add_evidence(evidence):
                    added_count += 1
        
        logger.info(f"Added {added_count} evidence items from imports")
        return added_count
    
    def collect_from_pattern_matches(self, matches_by_file: Dict[str, List[PatternMatch]]) -> int:
        """
        Collect evidence from framework pattern matches.
        
        Args:
            matches_by_file: Dictionary mapping file paths to lists of pattern matches
            
        Returns:
            Number of evidence items added
        """
        added_count = 0
        
        for file_path, matches in matches_by_file.items():
            for match in matches:
                evidence = self.create_from_pattern_match(match)
                if self.add_evidence(evidence):
                    added_count += 1
        
        logger.info(f"Added {added_count} evidence items from pattern matches")
        return added_count
    
    def collect_from_ai_detections(self, detections: List[Dict]) -> int:
        """
        Collect evidence from AI detections.
        
        Args:
            detections: List of AI detection results
            
        Returns:
            Number of evidence items added
        """
        added_count = 0
        
        for detection in detections:
            technology_name = detection.get("name")
            if not technology_name:
                continue
            
            file_path = detection.get("file_path", "")
            confidence = detection.get("confidence", 50.0)
            
            # Get detection evidence
            evidence_items = detection.get("evidence", [])
            
            if evidence_items:
                # Create separate evidence for each item
                for item in evidence_items:
                    snippet = item.get("snippet", "")
                    line_number = item.get("line_number")
                    details = item.get("details", "")
                    
                    evidence = self.create_from_ai_detection(
                        technology_name=technology_name,
                        file_path=file_path,
                        confidence=confidence,
                        details=details,
                        snippet=snippet,
                        line_number=line_number
                    )
                    
                    if self.add_evidence(evidence):
                        added_count += 1
            else:
                # Create a single general evidence
                evidence = self.create_from_ai_detection(
                    technology_name=technology_name,
                    file_path=file_path,
                    confidence=confidence,
                    details=detection.get("details", "")
                )
                
                if self.add_evidence(evidence):
                    added_count += 1
        
        logger.info(f"Added {added_count} evidence items from AI detections")
        return added_count
    
    def get_evidence_for_technology(self, technology_name: str) -> List[Evidence]:
        """
        Get all evidence for a specific technology.
        
        Args:
            technology_name: Name of the technology
            
        Returns:
            List of evidence items
        """
        return self.evidence_by_technology.get(technology_name, [])
    
    def get_evidence_for_file(self, file_path: str) -> List[Evidence]:
        """
        Get all evidence found in a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of evidence items
        """
        return self.evidence_by_file.get(file_path, [])
    
    def get_technologies_with_evidence(self) -> Set[str]:
        """
        Get the set of technologies that have evidence.
        
        Returns:
            Set of technology names
        """
        return set(self.evidence_by_technology.keys())
    
    def get_evidence_count_by_technology(self) -> Dict[str, int]:
        """
        Get the count of evidence items for each technology.
        
        Returns:
            Dictionary mapping technology names to evidence counts
        """
        return {tech: len(evidence) for tech, evidence in self.evidence_by_technology.items()}
    
    def get_total_evidence_count(self) -> int:
        """
        Get the total number of evidence items.
        
        Returns:
            Total evidence count
        """
        return len(self.evidence_items)
    
    def get_summary(self) -> Dict:
        """
        Get a summary of the evidence collection.
        
        Returns:
            Dictionary with summary information
        """
        return {
            "total_evidence": len(self.evidence_items),
            "unique_technologies": len(self.evidence_by_technology),
            "evidence_by_type": {str(t): len(e) for t, e in self.evidence_by_type.items()},
            "evidence_by_source": {str(s): len(e) for s, e in self.evidence_by_source.items()},
            "top_technologies": sorted(
                [(tech, len(evidence)) for tech, evidence in self.evidence_by_technology.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    
    def clear(self):
        """Clear all collected evidence."""
        self.evidence_items.clear()
        self.evidence_by_technology.clear()
        self.evidence_by_file.clear()
        self.evidence_by_source.clear()
        self.evidence_by_type.clear()
        self.evidence_identifiers.clear()