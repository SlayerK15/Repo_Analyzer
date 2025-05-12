"""
Framework-related data models for the Technology Extraction System.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Union


class PatternType(Enum):
    """Types of framework signature patterns."""
    REGEX = auto()      # Regular expression pattern
    AST = auto()        # Abstract syntax tree pattern
    SEMANTIC = auto()   # Semantic pattern
    LEXICAL = auto()    # Lexical pattern
    CUSTOM = auto()     # Custom pattern


class SignatureCategory(Enum):
    """Categories of framework signatures."""
    SYNTAX = auto()             # Language syntax feature
    CLASS_DEFINITION = auto()   # Class definition pattern
    FUNCTION_DEFINITION = auto() # Function definition pattern
    FUNCTION_CALL = auto()      # Function call pattern
    DECORATOR = auto()          # Decorator pattern
    IMPORT = auto()             # Import pattern
    TEMPLATE = auto()           # Template pattern
    FILE_FORMAT = auto()        # File format pattern
    DIRECTIVE = auto()          # Directive pattern
    COMPONENT_USAGE = auto()    # Component usage pattern
    INSTANTIATION = auto()      # Class instantiation pattern
    STATIC_CALL = auto()        # Static method call pattern
    QUERY = auto()              # Query pattern
    SCHEMA = auto()             # Schema definition pattern
    OBJECT_DEFINITION = auto()  # Object definition pattern
    VARIABLE_DEFINITION = auto() # Variable definition pattern
    UNKNOWN = auto()            # Unknown pattern category


@dataclass
class FrameworkSignature:
    """Signature pattern for framework detection."""
    name: str                       # Name of the signature
    pattern: str                    # Pattern to match
    file_patterns: List[str] = field(default_factory=list)  # File patterns to check
    type: PatternType = PatternType.REGEX  # Type of pattern
    category: SignatureCategory = SignatureCategory.UNKNOWN  # Category of signature
    is_definitive: bool = False     # Whether the signature is definitive
    weight: float = 1.0             # Weight of the signature for confidence scoring
    example: Optional[str] = None   # Example of the pattern


@dataclass
class PatternMatch:
    """A match of a framework signature pattern."""
    framework: str                    # Framework name
    signature_name: str               # Name of the matched signature
    file_path: str                    # Path to the file with the match
    line_number: int                  # Line number of the match
    context: str                      # Context around the match
    confidence: float                 # Confidence level (0-1)
    is_definitive: bool = False       # Whether the match is definitive
    category: SignatureCategory = SignatureCategory.UNKNOWN  # Category of the signature