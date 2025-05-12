"""
Metadata models for the Technology Extraction System.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Union, Any


@dataclass
class LanguageDistribution:
    """Distribution information for a programming language."""
    language: str          # Language name
    file_count: int        # Number of files
    percentage: float      # Percentage of files
    lines_of_code: int     # Total lines of code
    loc_percentage: float  # Percentage of lines of code


@dataclass
class LanguageMetadata:
    """Metadata about programming languages in a codebase."""
    total_files: int                                # Total number of files
    total_loc: int                                  # Total lines of code
    primary_language: str                           # Primary language
    distribution: List[LanguageDistribution] = field(default_factory=list)  # Language distribution


@dataclass
class CodebaseMetadata:
    """Metadata about a codebase."""
    repository_name: Optional[str] = None            # Repository name
    repository_url: Optional[str] = None             # Repository URL
    commit_hash: Optional[str] = None                # Commit hash
    commit_date: Optional[str] = None                # Commit date
    file_count: int = 0                              # Total file count
    directory_count: int = 0                         # Total directory count
    size_bytes: int = 0                              # Total size in bytes
    languages: Optional[LanguageMetadata] = None     # Language metadata
    contributors: List[str] = field(default_factory=list)  # Contributors
    last_modified: Optional[str] = None              # Last modified date


@dataclass
class AnalysisMetadata:
    """Metadata about the analysis process."""
    start_time: str                                  # Analysis start time
    end_time: str                                    # Analysis end time
    duration_seconds: float                          # Analysis duration in seconds
    files_analyzed: int                              # Number of files analyzed
    technologies_detected: int                       # Number of technologies detected
    confidence_threshold: float                      # Confidence threshold used
    token_usage: Optional[Dict[str, int]] = None     # Token usage statistics
    cost_estimate: Optional[float] = None            # Cost estimate
    version: str = "0.1.0"                           # Technology Extraction version