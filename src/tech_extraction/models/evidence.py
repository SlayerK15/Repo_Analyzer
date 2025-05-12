"""
Evidence-related data models for the Technology Extraction System.
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Union


class EvidenceType(Enum):
    """Types of evidence for technology detection."""
    IMPORT_STATEMENT = auto()    # Import/require statement
    MANIFEST_ENTRY = auto()      # Entry in package manifest
    FRAMEWORK_PATTERN = auto()   # Framework-specific pattern
    CLASS_DEFINITION = auto()    # Class definition
    FUNCTION_CALL = auto()       # Function call
    CONFIGURATION = auto()       # Configuration entry
    FILE_STRUCTURE = auto()      # File/directory structure
    DEPENDENCY_USAGE = auto()    # Usage of a dependency
    AI_DETECTION = auto()        # Detection by AI model
    UNKNOWN = auto()             # Unknown evidence type


class EvidenceSource(Enum):
    """Sources of evidence."""
    STATIC_ANALYSIS = auto()     # Static code analysis
    MANIFEST_PARSER = auto()     # Package manifest parser
    IMPORT_ANALYZER = auto()     # Import statement analyzer
    PATTERN_MATCHING = auto()    # Pattern matching
    AI_MODEL = auto()            # AI model detection
    USER_PROVIDED = auto()       # User-provided information
    UNKNOWN = auto()             # Unknown source


@dataclass
class Evidence:
    """Evidence of technology usage."""
    technology_name: str                 # Name of the technology
    type: EvidenceType                   # Type of evidence
    source: EvidenceSource               # Source of evidence
    file_path: Optional[str] = None      # Path to the file containing the evidence
    line_number: Optional[int] = None    # Line number in the file
    snippet: Optional[str] = None        # Code snippet showing the evidence
    details: Optional[str] = None        # Additional details
    confidence: float = 50.0             # Confidence level (0-100)