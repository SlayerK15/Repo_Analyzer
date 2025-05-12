"""
Path matcher utility for the Technology Extraction System.

This module provides functionality for matching file paths against patterns,
similar to .gitignore rules.
"""
import fnmatch
import os
import re
from pathlib import Path
from typing import List, Optional, Set


class PathMatcher:
    """
    Utility for matching file paths against patterns.
    
    Supports glob patterns and gitignore-style rules:
    - * matches any number of characters except /
    - ** matches any number of characters including /
    - ? matches a single character except /
    - [abc] matches one character from the set
    - [!abc] matches one character not in the set
    - directories can end with /
    - patterns starting with ! are negations
    """
    
    def __init__(self, patterns: Optional[List[str]] = None, ignore_file_path: Optional[Path] = None):
        """
        Initialize the path matcher.
        
        Args:
            patterns: List of patterns to match
            ignore_file_path: Path to a file containing patterns (like .gitignore)
        """
        self.include_patterns = []
        self.exclude_patterns = []
        
        # Add patterns from list
        if patterns:
            for pattern in patterns:
                self._add_pattern(pattern)
        
        # Add patterns from file
        if ignore_file_path and ignore_file_path.exists():
            self._add_patterns_from_file(ignore_file_path)
    
    def _add_pattern(self, pattern: str):
        """
        Add a pattern to the appropriate list.
        
        Args:
            pattern: Pattern to add
        """
        pattern = pattern.strip()
        
        # Skip empty patterns and comments
        if not pattern or pattern.startswith('#'):
            return
        
        # Check if it's a negation
        if pattern.startswith('!'):
            self.include_patterns.append(pattern[1:])
        else:
            self.exclude_patterns.append(pattern)
    
    def _add_patterns_from_file(self, file_path: Path):
        """
        Add patterns from a file.
        
        Args:
            file_path: Path to the file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    self._add_pattern(line)
        except Exception as e:
            print(f"Error reading patterns from {file_path}: {e}")
    
    def _match_pattern(self, path: Path, pattern: str) -> bool:
        """
        Check if a path matches a pattern.
        
        Args:
            path: Path to check
            pattern: Pattern to match
            
        Returns:
            True if the path matches the pattern, False otherwise
        """
        # Convert path to string for pattern matching
        path_str = str(path)
        
        # If the pattern ends with /, it should only match directories
        if pattern.endswith('/'):
            if not path.is_dir():
                return False
            pattern = pattern[:-1]
        
        # Handle directory-only matches
        if '/' in pattern:
            # Specific path pattern
            return fnmatch.fnmatch(path_str, pattern)
        else:
            # Match any path component
            path_parts = path_str.split(os.sep)
            return any(fnmatch.fnmatch(part, pattern) for part in path_parts)
    
    def should_ignore(self, path: Path) -> bool:
        """
        Check if a path should be ignored.
        
        Args:
            path: Path to check
            
        Returns:
            True if the path should be ignored, False otherwise
        """
        # First check if explicitly included
        for pattern in self.include_patterns:
            if self._match_pattern(path, pattern):
                return False
        
        # Then check if explicitly excluded
        for pattern in self.exclude_patterns:
            if self._match_pattern(path, pattern):
                return True
        
        # Default to not ignoring
        return False