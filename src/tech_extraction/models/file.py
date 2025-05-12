"""
File-related data models for the Technology Extraction System.
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Union


class FileType(Enum):
    """Types of files in a codebase."""
    SOURCE = auto()  # Source code files
    MARKUP = auto()  # Markup files (HTML, XML, etc.)
    CONFIG = auto()  # Configuration files
    DATA = auto()    # Data files
    ASSET = auto()   # Asset files (images, fonts, etc.)
    DOC = auto()     # Documentation files
    BUILD = auto()   # Build files
    SCRIPT = auto()  # Script files
    TEST = auto()    # Test files
    UNKNOWN = auto() # Unknown file type
    
    @classmethod
    def from_extension(cls, extension: str) -> 'FileType':
        """
        Determine file type from extension.
        
        Args:
            extension: File extension (including dot)
            
        Returns:
            FileType enum value
        """
        extension = extension.lower()
        
        # Source code
        if extension in ['.py', '.java', '.js', '.jsx', '.ts', '.tsx', '.rb', '.go', '.php', 
                         '.c', '.cpp', '.h', '.hpp', '.cs', '.swift', '.kt', '.rs', '.scala', 
                         '.clj', '.ex', '.exs', '.erl', '.hrl', '.hs', '.fs', '.fsx']:
            return cls.SOURCE
        
        # Markup
        if extension in ['.html', '.htm', '.xml', '.svg', '.xhtml', '.md', '.markdown', 
                         '.rst', '.adoc', '.jade', '.pug', '.haml', '.slim', '.erb', 
                         '.hbs', '.mustache', '.twig', '.liquid', '.tsx', '.jsx']:
            return cls.MARKUP
        
        # Configuration
        if extension in ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', 
                         '.properties', '.env', '.editorconfig', '.gitignore', '.dockerignore',
                         '.eslintrc', '.prettierrc', '.stylelintrc', '.babelrc', '.browserslistrc']:
            return cls.CONFIG
        
        # Data
        if extension in ['.csv', '.tsv', '.dat', '.db', '.sqlite', '.sql', '.json', '.xml', 
                         '.yaml', '.yml', '.toml', '.proto', '.avro', '.parquet']:
            return cls.DATA
        
        # Assets
        if extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.ico', '.webp', 
                         '.mp3', '.wav', '.ogg', '.mp4', '.webm', '.ttf', '.woff', '.woff2', 
                         '.eot', '.otf']:
            return cls.ASSET
        
        # Documentation
        if extension in ['.md', '.markdown', '.rst', '.adoc', '.txt', '.pdf', '.doc', '.docx', 
                         '.rtf', '.wiki', '.epub']:
            return cls.DOC
        
        # Build files
        if extension in ['.gradle', '.gradle.kts', '.sbt', '.maven', '.pom', '.xml', '.make', 
                         '.mk', '.cmake', '.msbuild', '.proj', '.pbxproj', '.vcxproj']:
            return cls.BUILD
        
        # Scripts
        if extension in ['.sh', '.bash', '.zsh', '.fish', '.bat', '.cmd', '.ps1', '.psm1', 
                         '.py', '.rb', '.pl', '.awk', '.sed']:
            return cls.SCRIPT
        
        # Test files (could be source, but categorized as test)
        if extension in ['.test.js', '.spec.js', '.test.ts', '.spec.ts', '.test.py', '.spec.py', 
                         '.test.rb', '.spec.rb', 'Test.java', 'Tests.cs']:
            return cls.TEST
        
        # Default
        return cls.UNKNOWN


@dataclass
class FileInfo:
    """Information about a file in the codebase."""
    path: str          # Relative path to the file
    full_path: str     # Absolute path to the file
    size: int          # File size in bytes
    hash: str          # Hash of the file content
    file_type: FileType = FileType.UNKNOWN  # Type of file


@dataclass
class LanguageInfo:
    """Information about a programming language."""
    name: str                     # Language name
    confidence: float             # Confidence level (0-100)
    lines_of_code: int = 0        # Lines of code in this language