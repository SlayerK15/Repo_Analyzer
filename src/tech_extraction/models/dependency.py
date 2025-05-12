"""
Dependency-related data models for the Technology Extraction System.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Union


class DependencyType(Enum):
    """Types of dependencies."""
    RUNTIME = auto()      # Required at runtime
    DEVELOPMENT = auto()  # Required for development only
    OPTIONAL = auto()     # Optional dependency
    PEER = auto()         # Peer dependency
    BUNDLED = auto()      # Bundled dependency
    UNKNOWN = auto()      # Unknown dependency type


class DependencyScope(Enum):
    """Scope of dependencies."""
    DIRECT = auto()      # Directly declared in project
    TRANSITIVE = auto()  # Included via another dependency
    PEER = auto()        # Peer dependency
    UNKNOWN = auto()     # Unknown scope


@dataclass
class Dependency:
    """Information about a dependency."""
    name: str                                # Dependency name
    version: str = ""                        # Version specification
    type: DependencyType = DependencyType.UNKNOWN  # Type of dependency
    scope: DependencyScope = DependencyScope.UNKNOWN  # Scope of dependency
    optional: bool = False                   # Whether the dependency is optional
    source: str = ""                         # Source file where dependency was found
    group: Optional[str] = None              # Dependency group (e.g., Maven groupId)
    is_project_reference: bool = False       # Whether this is a reference to another project


@dataclass
class ManifestInfo:
    """Information about a package manifest file."""
    path: str                      # Path to the manifest file
    ecosystem: str                 # Package ecosystem (npm, pip, etc.)
    dependencies: List[Dependency] = field(default_factory=list)  # List of dependencies
    parse_error: Optional[str] = None  # Error message if parsing failed


@dataclass
class ImportInfo:
    """Information about an import statement."""
    path: str              # Import path
    line: int              # Line number
    type: str              # Type of import (e.g., "standard", "from")
    category: str          # Category of import (standard_library, third_party, relative)
    package_name: str      # Normalized package name
    file_path: str = ""    # Path to the file containing the import