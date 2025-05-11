"""
Language Detector module for identifying programming languages used in a repository.

This module analyzes file extensions and specific patterns to detect
programming languages used in a code repository. It calculates confidence
scores based on the frequency of each language's files.
"""

import os
from collections import Counter
from typing import Dict, List, Any

class LanguageDetector:
    """
    Detector for programming languages used in a repository.
    
    This class analyzes file extensions and specific patterns to identify
    programming languages and calculates confidence scores based on their
    frequency in the repository.
    """
    
    def __init__(self):
        """Initialize the Language Detector."""
        # Mapping of file extensions to programming languages
        self.language_extensions = {
            # General purpose languages
            ".py": "Python",
            ".ipynb": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "React/JavaScript",
            ".tsx": "React/TypeScript",
            ".java": "Java",
            ".class": "Java",
            ".jar": "Java",
            ".cs": "C#",
            ".csproj": "C#",
            ".vb": "Visual Basic",
            ".go": "Go",
            ".rb": "Ruby",
            ".php": "PHP",
            ".rs": "Rust",
            ".c": "C",
            ".h": "C",
            ".cpp": "C++",
            ".hpp": "C++",
            ".cc": "C++",
            ".hh": "C++",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".clj": "Clojure",
            ".erl": "Erlang",
            ".ex": "Elixir",
            ".exs": "Elixir",
            ".elm": "Elm",
            ".fs": "F#",
            ".fsx": "F#",
            ".hs": "Haskell",
            ".lhs": "Haskell",
            ".pl": "Perl",
            ".r": "R",
            ".lua": "Lua",
            ".m": "Objective-C", # Also used for MATLAB
            ".mm": "Objective-C++",
            ".jl": "Julia",
            
            # Shell/scripting languages
            ".sh": "Shell",
            ".bash": "Bash",
            ".zsh": "Zsh",
            ".ps1": "PowerShell",
            ".psm1": "PowerShell",
            ".bat": "Batch",
            ".cmd": "Batch",
            
            # Web languages
            ".html": "HTML",
            ".htm": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".sass": "Sass",
            ".less": "LESS",
            ".vue": "Vue.js",
            ".svelte": "Svelte",
            ".php": "PHP",
            ".jsp": "JSP",
            ".asp": "ASP",
            ".aspx": "ASP.NET",
            
            # Database languages
            ".sql": "SQL",
            ".hql": "HQL",
            
            # Markup/config languages
            ".xml": "XML",
            ".xsl": "XSL",
            ".xslt": "XSLT",
            ".json": "JSON",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".toml": "TOML",
            ".ini": "INI",
            ".md": "Markdown",
            ".rst": "reStructuredText",
            ".tex": "LaTeX",
            
            # Other languages
            ".proto": "Protocol Buffers",
            ".gradle": "Gradle",
            ".groovy": "Groovy",
            ".dart": "Dart",
            ".d": "D",
            ".coffee": "CoffeeScript",
            ".ts": "TypeScript",
            ".tf": "Terraform",
            ".hcl": "HCL",
        }
        
        # Special files that indicate a programming language
        self.special_files = {
            "package.json": "JavaScript/Node.js",
            "tsconfig.json": "TypeScript",
            "requirements.txt": "Python",
            "setup.py": "Python",
            "Pipfile": "Python",
            "pyproject.toml": "Python",
            "Gemfile": "Ruby",
            "Rakefile": "Ruby",
            "pom.xml": "Java",
            "build.gradle": "Java/Kotlin",
            "composer.json": "PHP",
            "Cargo.toml": "Rust",
            "go.mod": "Go",
            "build.sbt": "Scala",
            "mix.exs": "Elixir",
            "cabal.project": "Haskell",
            "stack.yaml": "Haskell",
            "dub.json": "D",
            "CMakeLists.txt": "C/C++",
            "Makefile": "Make",
            "pubspec.yaml": "Dart",
        }
    
    def detect(self, files: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Detect programming languages used in the repository.
        
        This method analyzes file extensions and special files to identify
        programming languages and calculates confidence scores based on their
        frequency in the repository.
        
        Args:
            files: List of file paths in the repository
            
        Returns:
            Dict mapping language names to dicts containing:
                - count: Number of files of this language
                - percentage: Percentage of files of this language
                - confidence: Confidence score (0-100)
        """
        # Count language occurrences based on file extensions
        language_counts = Counter()
        
        for file_path in files:
            # Check for special files
            filename = os.path.basename(file_path)
            if filename in self.special_files:
                language = self.special_files[filename]
                language_counts[language] += 3  # Give higher weight to special files
                continue
            
            # Check file extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()  # Normalize extension
            
            if ext in self.language_extensions:
                language = self.language_extensions[ext]
                language_counts[language] += 1
        
        # Calculate confidence scores based on frequency
        total_weighted_count = sum(language_counts.values())
        languages = {}
        
        if total_weighted_count > 0:
            for language, count in language_counts.items():
                percentage = (count / total_weighted_count) * 100
                
                # Calculate confidence (scale percentage to make it more meaningful)
                # Languages that make up a significant portion of the codebase get high confidence
                confidence = min(100, percentage * 2)  # Cap at 100%
                
                languages[language] = {
                    "count": count,
                    "percentage": round(percentage, 2),
                    "confidence": round(confidence, 2)
                }
        
        return languages