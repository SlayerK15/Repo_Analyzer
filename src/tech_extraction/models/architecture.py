"""
Architecture-related data models for the Technology Extraction System.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Union, Any


class ArchitectureType(Enum):
    """Types of architectural patterns."""
    DESIGN_PATTERN = auto()       # Design pattern (MVC, MVVM, etc.)
    SYSTEM_ARCHITECTURE = auto()  # System architecture (microservices, serverless, etc.)
    CODE_ORGANIZATION = auto()    # Code organization pattern
    UNKNOWN = auto()              # Unknown architecture type


@dataclass
class ArchitecturalPattern:
    """Information about an architectural pattern."""
    name: str                        # Pattern name
    type: ArchitectureType           # Type of pattern
    confidence: float                # Confidence level (0-100)
    evidence: Dict[str, List[Any]]   # Evidence supporting the pattern


@dataclass
class DatabaseIntegration:
    """Information about a database integration."""
    name: str                    # Name of the integration
    type: str                    # Type of integration (ORM, query builder, raw SQL)
    confidence: float            # Confidence level (0-100)
    evidence: List[Dict]         # Evidence supporting the integration


@dataclass
class ApiPattern:
    """Information about an API implementation pattern."""
    name: str                    # Name of the pattern (REST, GraphQL, etc.)
    confidence: float            # Confidence level (0-100)
    evidence: List[Dict]         # Evidence supporting the pattern