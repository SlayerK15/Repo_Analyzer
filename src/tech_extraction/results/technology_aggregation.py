"""
Technology Aggregation for the Technology Extraction System.

This module provides functionality for aggregating detected technologies,
resolving versions, and creating a hierarchical technology representation.
"""
import logging
import re
from collections import Counter, defaultdict
from dataclasses import asdict
from typing import Dict, List, Optional, Set, Tuple, Union

import semver

from tech_extraction.evidence.confidence_scoring import ConfidenceScoringEngine
from tech_extraction.evidence.evidence_collection import EvidenceCollection
from tech_extraction.models.dependency import Dependency
from tech_extraction.models.evidence import Evidence, EvidenceType
from tech_extraction.models.technology import (
    Technology,
    TechnologyCategory,
    TechnologyStack,
    TechnologyGroup,
    TechnologyUsage,
)

logger = logging.getLogger(__name__)


class TechnologyAggregation:
    """
    System for aggregating and structuring detected technologies.
    
    The TechnologyAggregation performs the following operations:
    1. Resolve and consolidate detected technologies
    2. Determine technology categories and relationships
    3. Resolve version information from multiple sources
    4. Quantify usage and importance of technologies
    """
    
    # Technology category mappings
    CATEGORY_MAPPINGS = {
        # Languages
        "python": TechnologyCategory.LANGUAGE,
        "javascript": TechnologyCategory.LANGUAGE,
        "typescript": TechnologyCategory.LANGUAGE,
        "java": TechnologyCategory.LANGUAGE,
        "c#": TechnologyCategory.LANGUAGE,
        "go": TechnologyCategory.LANGUAGE,
        "ruby": TechnologyCategory.LANGUAGE,
        "php": TechnologyCategory.LANGUAGE,
        "rust": TechnologyCategory.LANGUAGE,
        "kotlin": TechnologyCategory.LANGUAGE,
        "swift": TechnologyCategory.LANGUAGE,
        
        # Frameworks
        "django": TechnologyCategory.FRAMEWORK,
        "flask": TechnologyCategory.FRAMEWORK,
        "fastapi": TechnologyCategory.FRAMEWORK,
        "react": TechnologyCategory.FRAMEWORK,
        "angular": TechnologyCategory.FRAMEWORK,
        "vue": TechnologyCategory.FRAMEWORK,
        "spring": TechnologyCategory.FRAMEWORK,
        "express": TechnologyCategory.FRAMEWORK,
        "rails": TechnologyCategory.FRAMEWORK,
        "laravel": TechnologyCategory.FRAMEWORK,
        "next.js": TechnologyCategory.FRAMEWORK,
        "gatsby": TechnologyCategory.FRAMEWORK,
        
        # Libraries
        "pandas": TechnologyCategory.LIBRARY,
        "numpy": TechnologyCategory.LIBRARY,
        "tensorflow": TechnologyCategory.LIBRARY,
        "pytorch": TechnologyCategory.LIBRARY,
        "lodash": TechnologyCategory.LIBRARY,
        "moment": TechnologyCategory.LIBRARY,
        "axios": TechnologyCategory.LIBRARY,
        "requests": TechnologyCategory.LIBRARY,
        "boto3": TechnologyCategory.LIBRARY,
        "junit": TechnologyCategory.LIBRARY,
        "jest": TechnologyCategory.LIBRARY,
        "pytest": TechnologyCategory.LIBRARY,
        
        # Database
        "postgresql": TechnologyCategory.DATABASE,
        "mysql": TechnologyCategory.DATABASE,
        "mongodb": TechnologyCategory.DATABASE,
        "redis": TechnologyCategory.DATABASE,
        "sqlite": TechnologyCategory.DATABASE,
        "elasticsearch": TechnologyCategory.DATABASE,
        
        # ORM
        "sqlalchemy": TechnologyCategory.ORM,
        "sequelize": TechnologyCategory.ORM,
        "mongoose": TechnologyCategory.ORM,
        "hibernate": TechnologyCategory.ORM,
        "typeorm": TechnologyCategory.ORM,
        
        # Build Tools
        "webpack": TechnologyCategory.BUILD_TOOL,
        "babel": TechnologyCategory.BUILD_TOOL,
        "gulp": TechnologyCategory.BUILD_TOOL,
        "gradle": TechnologyCategory.BUILD_TOOL,
        "maven": TechnologyCategory.BUILD_TOOL,
        "poetry": TechnologyCategory.BUILD_TOOL,
        "pip": TechnologyCategory.BUILD_TOOL,
        "npm": TechnologyCategory.BUILD_TOOL,
        "yarn": TechnologyCategory.BUILD_TOOL,
        
        # Testing
        "jest": TechnologyCategory.TESTING,
        "mocha": TechnologyCategory.TESTING,
        "pytest": TechnologyCategory.TESTING,
        "unittest": TechnologyCategory.TESTING,
        "jasmine": TechnologyCategory.TESTING,
        "karma": TechnologyCategory.TESTING,
        "selenium": TechnologyCategory.TESTING,
        "cypress": TechnologyCategory.TESTING,
        
        # UI
        "bootstrap": TechnologyCategory.UI,
        "material-ui": TechnologyCategory.UI,
        "tailwindcss": TechnologyCategory.UI,
        "semantic-ui": TechnologyCategory.UI,
        "bulma": TechnologyCategory.UI,
        "ant-design": TechnologyCategory.UI,
        "chakra-ui": TechnologyCategory.UI,
        
        # State Management
        "redux": TechnologyCategory.STATE_MANAGEMENT,
        "mobx": TechnologyCategory.STATE_MANAGEMENT,
        "vuex": TechnologyCategory.STATE_MANAGEMENT,
        "recoil": TechnologyCategory.STATE_MANAGEMENT,
        "jotai": TechnologyCategory.STATE_MANAGEMENT,
        "apollo-client": TechnologyCategory.STATE_MANAGEMENT,
        
        # Infrastructure
        "docker": TechnologyCategory.INFRASTRUCTURE,
        "kubernetes": TechnologyCategory.INFRASTRUCTURE,
        "aws": TechnologyCategory.INFRASTRUCTURE,
        "azure": TechnologyCategory.INFRASTRUCTURE,
        "gcp": TechnologyCategory.INFRASTRUCTURE,
        "terraform": TechnologyCategory.INFRASTRUCTURE,
        "ansible": TechnologyCategory.INFRASTRUCTURE,
        
        # API
        "graphql": TechnologyCategory.API,
        "rest": TechnologyCategory.API,
        "grpc": TechnologyCategory.API,
        "swagger": TechnologyCategory.API,
        "openapi": TechnologyCategory.API,
    }
    
    # Technology relationships
    TECHNOLOGY_RELATIONSHIPS = {
        # Format: parent -> [children]
        "react": ["react-dom", "react-router", "redux", "mobx", "material-ui", "styled-components", "chakra-ui"],
        "angular": ["angular-router", "angular-forms", "angular-material", "ngrx"],
        "vue": ["vue-router", "vuex", "vuetify", "nuxt.js"],
        "django": ["django-rest-framework", "django-allauth", "django-filter"],
        "flask": ["flask-sqlalchemy", "flask-restful", "flask-login"],
        "express": ["express-session", "express-validator", "body-parser"],
        "spring": ["spring-boot", "spring-mvc", "spring-data", "spring-security"],
        "aws": ["boto3", "aws-sdk", "aws-lambda", "aws-s3", "aws-dynamodb"],
        "typescript": ["ts-node", "tsc", "tsconfig"],
    }
    
    # Default categories for technologies not in the mapping
    DEFAULT_CATEGORY_PATTERNS = [
        (r".*-plugin", TechnologyCategory.PLUGIN),
        (r".*-extension", TechnologyCategory.PLUGIN),
        (r".*-cli", TechnologyCategory.TOOL),
        (r".*-tool", TechnologyCategory.TOOL),
        (r".*-ui", TechnologyCategory.UI),
        (r".*-test", TechnologyCategory.TESTING),
        (r".*-client", TechnologyCategory.LIBRARY),
        (r".*-sdk", TechnologyCategory.LIBRARY),
        (r".*-db", TechnologyCategory.DATABASE),
        (r".*-orm", TechnologyCategory.ORM),
        (r".*-api", TechnologyCategory.API),
    ]
    
    def __init__(
        self,
        evidence_collection: EvidenceCollection,
        scoring_engine: ConfidenceScoringEngine
    ):
        """
        Initialize the technology aggregation system.
        
        Args:
            evidence_collection: Evidence collection instance
            scoring_engine: Confidence scoring engine instance
        """
        self.evidence_collection = evidence_collection
        self.scoring_engine = scoring_engine
        
        # Store aggregated technologies
        self.technologies = {}
        self.tech_stacks = {}
        self.primary_technologies = []
        self.tech_groups = {}
    
    def determine_category(self, technology_name: str) -> TechnologyCategory:
        """
        Determine the category of a technology.
        
        Args:
            technology_name: Technology name
            
        Returns:
            Technology category
        """
        # Check direct mappings first
        tech_lower = technology_name.lower()
        if tech_lower in self.CATEGORY_MAPPINGS:
            return self.CATEGORY_MAPPINGS[tech_lower]
        
        # Check for parent technologies that might define the category
        for parent, children in self.TECHNOLOGY_RELATIONSHIPS.items():
            if technology_name in children:
                parent_category = self.determine_category(parent)
                # Usually children are the same category as parents, with some exceptions
                if parent_category != TechnologyCategory.FRAMEWORK:
                    return parent_category
                return TechnologyCategory.LIBRARY  # Framework children are usually libraries
        
        # Try pattern matching
        for pattern, category in self.DEFAULT_CATEGORY_PATTERNS:
            if re.match(pattern, tech_lower):
                return category
        
        # Default to library for most unknown technologies
        return TechnologyCategory.LIBRARY
    
    def resolve_technology_version(self, technology_name: str) -> Optional[str]:
        """
        Resolve the version of a technology from evidence.
        
        Args:
            technology_name: Technology name
            
        Returns:
            Resolved version or None if unavailable
        """
        evidence_list = self.evidence_collection.get_evidence_for_technology(technology_name)
        
        # Extract version information from evidence
        versions = []
        
        for evidence in evidence_list:
            # Extract from manifest entry
            if evidence.type == EvidenceType.MANIFEST_ENTRY and evidence.details:
                version_match = re.search(r"Version:\s*([\d\.]+)", evidence.details)
                if version_match:
                    versions.append(version_match.group(1))
            
            # Extract from snippet (import statements sometimes include version)
            if evidence.snippet and re.search(r"[\d\.]+", evidence.snippet):
                version_match = re.search(r"[\d\.]+", evidence.snippet)
                if version_match:
                    versions.append(version_match.group(0))
        
        # No versions found
        if not versions:
            return None
        
        # Count version occurrences
        version_counts = Counter(versions)
        most_common = version_counts.most_common(1)[0][0]
        
        # Try to normalize the version
        try:
            # Check if it's a valid semantic version
            semver.parse(most_common)
            return most_common
        except ValueError:
            # If not a valid semver, return as is
            return most_common
    
    def calculate_technology_usage(self, technology_name: str) -> TechnologyUsage:
        """
        Calculate usage metrics for a technology.
        
        Args:
            technology_name: Technology name
            
        Returns:
            Technology usage information
        """
        evidence_list = self.evidence_collection.get_evidence_for_technology(technology_name)
        
        # Count unique files where the technology is used
        files = set(e.file_path for e in evidence_list if e.file_path)
        
        # Calculate usage frequency
        usage_frequency = len(evidence_list)
        
        # Calculate criticality based on evidence and confidence
        confidence = self.scoring_engine.calculate_confidence(technology_name)
        
        # Higher confidence and more files = more critical
        criticality = min(100, (confidence * 0.7) + (len(files) * 2))
        
        return TechnologyUsage(
            file_count=len(files),
            frequency=usage_frequency,
            criticality=criticality
        )
    
    def determine_parent_technology(self, technology_name: str) -> Optional[str]:
        """
        Determine the parent technology for a given technology.
        
        Args:
            technology_name: Technology name
            
        Returns:
            Parent technology name or None if no parent
        """
        for parent, children in self.TECHNOLOGY_RELATIONSHIPS.items():
            if technology_name in children:
                return parent
        
        # Check for naming patterns
        if '-' in technology_name:
            prefix = technology_name.split('-')[0]
            if prefix in self.technologies:
                return prefix
        
        return None
    
    def aggregate_technologies(self, confidence_threshold: float = 50.0) -> List[Technology]:
        """
        Aggregate technologies from collected evidence.
        
        Args:
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            List of aggregated technology objects
        """
        logger.info("Aggregating technologies from evidence")
        
        # Get technologies above threshold
        tech_names = self.scoring_engine.get_technologies_above_threshold(confidence_threshold)
        
        # Process each technology
        for name in tech_names:
            # Normalize the technology name
            normalized_name = name.strip()
            
            # Skip empty names
            if not normalized_name:
                continue
            
            # Determine category
            category = self.determine_category(normalized_name)
            
            # Resolve version
            version = self.resolve_technology_version(normalized_name)
            
            # Calculate usage
            usage = self.calculate_technology_usage(normalized_name)
            
            # Get confidence score
            confidence = self.scoring_engine.calculate_confidence(normalized_name)
            
            # Get supporting evidence
            evidence = self.scoring_engine.get_supporting_evidence(normalized_name)
            
            # Create technology object
            technology = Technology(
                name=normalized_name,
                category=category,
                version=version,
                confidence=confidence,
                usage=usage,
                evidence=[asdict(e) for e in evidence]
            )
            
            self.technologies[normalized_name] = technology
        
        logger.info(f"Aggregated {len(self.technologies)} technologies")
        return list(self.technologies.values())
    
    def group_technologies(self) -> Dict[str, List[Technology]]:
        """
        Group technologies by category.
        
        Returns:
            Dictionary mapping category names to lists of technologies
        """
        groups = defaultdict(list)
        
        for tech in self.technologies.values():
            groups[tech.category.name].append(tech)
        
        # Sort technologies in each group by confidence
        for category, techs in groups.items():
            groups[category] = sorted(techs, key=lambda t: t.confidence, reverse=True)
        
        self.tech_groups = {k: TechnologyGroup(name=k, technologies=v) for k, v in groups.items()}
        return {k: v for k, v in groups.items()}
    
    def create_technology_stacks(self) -> Dict[str, TechnologyStack]:
        """
        Create technology stacks by identifying primary technologies and their dependencies.
        
        Returns:
            Dictionary mapping stack names to TechnologyStack objects
        """
        stacks = {}
        
        # Identify primary technologies (frameworks and languages)
        primary_techs = [
            tech for tech in self.technologies.values()
            if tech.category in [TechnologyCategory.FRAMEWORK, TechnologyCategory.LANGUAGE]
            and tech.confidence >= 70  # Higher threshold for primary technologies
        ]
        
        # Sort by confidence
        primary_techs.sort(key=lambda t: t.confidence, reverse=True)
        
        # Create a stack for each primary technology
        for primary in primary_techs:
            # Find related technologies
            related = []
            
            # Check children in relationships
            if primary.name in self.TECHNOLOGY_RELATIONSHIPS:
                children = self.TECHNOLOGY_RELATIONSHIPS[primary.name]
                for child in children:
                    if child in self.technologies:
                        related.append(self.technologies[child])
            
            # Check for technologies that might be related by naming
            prefix = primary.name.lower() + "-"
            for tech_name, tech in self.technologies.items():
                if tech_name.lower().startswith(prefix) and tech not in related:
                    related.append(tech)
            
            # Create stack
            stack = TechnologyStack(
                name=f"{primary.name} Stack",
                primary_technology=primary,
                related_technologies=related
            )
            
            stacks[primary.name] = stack
        
        self.tech_stacks = stacks
        self.primary_technologies = primary_techs
        
        logger.info(f"Created {len(stacks)} technology stacks")
        return stacks
    
    def get_technologies_by_category(self, category: TechnologyCategory) -> List[Technology]:
        """
        Get technologies filtered by category.
        
        Args:
            category: Technology category to filter by
            
        Returns:
            List of technologies in the specified category
        """
        return [tech for tech in self.technologies.values() if tech.category == category]
    
    def get_primary_technologies(self) -> List[Technology]:
        """
        Get the primary technologies identified in the codebase.
        
        Returns:
            List of primary technologies
        """
        return self.primary_technologies
    
    def get_technology_stack(self, primary_name: str) -> Optional[TechnologyStack]:
        """
        Get a technology stack by primary technology name.
        
        Args:
            primary_name: Name of the primary technology
            
        Returns:
            TechnologyStack or None if not found
        """
        return self.tech_stacks.get(primary_name)
    
    def get_all_technology_stacks(self) -> List[TechnologyStack]:
        """
        Get all identified technology stacks.
        
        Returns:
            List of technology stacks
        """
        return list(self.tech_stacks.values())
    
    def get_technology_groups(self) -> List[TechnologyGroup]:
        """
        Get technology groups.
        
        Returns:
            List of technology groups
        """
        return list(self.tech_groups.values())
    
    def get_all_technologies(self) -> List[Technology]:
        """
        Get all aggregated technologies.
        
        Returns:
            List of all technologies
        """
        return list(self.technologies.values())