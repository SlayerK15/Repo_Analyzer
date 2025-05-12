"""
Technology-related data models for the Technology Extraction System.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Union, Any


class TechnologyCategory(Enum):
    """Categories of technologies."""
    LANGUAGE = auto()          # Programming language
    FRAMEWORK = auto()         # Framework
    LIBRARY = auto()           # Library
    DATABASE = auto()          # Database
    ORM = auto()               # Object-Relational Mapper
    BUILD_TOOL = auto()        # Build tool
    TESTING = auto()           # Testing framework/library
    UI = auto()                # UI framework/library
    STATE_MANAGEMENT = auto()  # State management library
    INFRASTRUCTURE = auto()    # Infrastructure technology
    API = auto()               # API technology
    PLUGIN = auto()            # Plugin
    TOOL = auto()              # Tool
    UNKNOWN = auto()           # Unknown category


@dataclass
class TechnologyUsage:
    """Usage information for a technology."""
    file_count: int = 0          # Number of files using the technology
    frequency: int = 0           # Frequency of usage
    criticality: float = 0.0     # Criticality score (0-100)


@dataclass
class Technology:
    """Information about a detected technology."""
    name: str                              # Technology name
    category: TechnologyCategory           # Technology category
    confidence: float                      # Confidence level (0-100)
    version: Optional[str] = None          # Version information
    usage: Optional[TechnologyUsage] = None  # Usage information
    evidence: List[Dict] = field(default_factory=list)  # Supporting evidence


@dataclass
class TechnologyGroup:
    """Group of related technologies."""
    name: str                       # Group name
    technologies: List[Technology]  # Technologies in the group


@dataclass
class TechnologyStack:
    """Technology stack information."""
    name: str                              # Stack name
    primary_technology: Technology         # Primary technology
    related_technologies: List[Technology] # Related technologies