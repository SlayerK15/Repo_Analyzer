"""
Import Statement Analyzer for the Technology Extraction System.

This module provides functionality for analyzing import statements in source code files
to identify dependencies and their usage patterns.
"""
import logging
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from tech_extraction.models.dependency import (
    DependencyType,
    DependencyScope,
    ImportInfo,
)
from tech_extraction.models.file import FileInfo, LanguageInfo

logger = logging.getLogger(__name__)


class ImportStatementAnalyzer:
    """
    Analyzer for detecting and processing import statements in source code.
    
    The ImportStatementAnalyzer performs the following operations:
    1. Detect language-specific import statements in source files
    2. Map imports to package names and identify standard library imports
    3. Analyze import usage patterns across files
    """
    
    # Mapping of language-specific import patterns to regex patterns
    IMPORT_PATTERNS = {
        # JavaScript/TypeScript
        "JavaScript": [
            (r'(?:import|export)(?:\s+(?:\*\s+as\s+)?[{\w\s,}]+\s+from\s+)?[\'\"]([^\'"]+)[\'"]', "ES modules"),
            (r'require\s*\(\s*[\'\"]([^\'"]+)[\'\"]', "CommonJS"),
            (r'import\s*\(\s*[\'\"]([^\'"]+)[\'\"]', "Dynamic import"),
            (r'define\s*\(\s*\[[\'\"]([^\'"]+)[\'\"]', "AMD"),
        ],
        "TypeScript": [
            (r'(?:import|export)(?:\s+(?:\*\s+as\s+)?[{\w\s,}]+\s+from\s+)?[\'\"]([^\'"]+)[\'"]', "ES modules"),
            (r'require\s*\(\s*[\'\"]([^\'"]+)[\'\"]', "CommonJS"),
            (r'import\s*\(\s*[\'\"]([^\'"]+)[\'\"]', "Dynamic import"),
        ],
        "JavaScript (React)": [
            (r'(?:import|export)(?:\s+(?:\*\s+as\s+)?[{\w\s,}]+\s+from\s+)?[\'\"]([^\'"]+)[\'"]', "ES modules"),
            (r'require\s*\(\s*[\'\"]([^\'"]+)[\'\"]', "CommonJS"),
        ],
        "TypeScript (React)": [
            (r'(?:import|export)(?:\s+(?:\*\s+as\s+)?[{\w\s,}]+\s+from\s+)?[\'\"]([^\'"]+)[\'"]', "ES modules"),
            (r'require\s*\(\s*[\'\"]([^\'"]+)[\'\"]', "CommonJS"),
        ],
        
        # Python
        "Python": [
            (r'^\s*import\s+([\w.]+)(?:\s+as\s+[\w.]+)?', "Standard import"),
            (r'^\s*from\s+([\w.]+)\s+import', "From import"),
            (r'__import__\s*\(\s*[\'\"]([^\'"]+)[\'\"]', "Dynamic import"),
        ],
        
        # Java
        "Java": [
            (r'^\s*import\s+([\w.]+)(?:\s*\.\s*\*)?;', "Java import"),
        ],
        
        # Ruby
        "Ruby": [
            (r'^\s*require\s+[\'\"]([^\'"]+)[\'\"]', "Require"),
            (r'^\s*require_relative\s+[\'\"]([^\'"]+)[\'\"]', "Require relative"),
            (r'^\s*load\s+[\'\"]([^\'"]+)[\'\"]', "Load"),
            (r'^\s*include\s+([\w:]+)', "Include"),
            (r'^\s*extend\s+([\w:]+)', "Extend"),
        ],
        
        # Go
        "Go": [
            (r'^\s*import\s+\(\s*(?:[\w._]+\s+)?[\"\']([^\"\']+)[\"\']', "Go import block"),
            (r'^\s*import\s+(?:[\w._]+\s+)?[\"\']([^\"\']+)[\"\']', "Go import"),
        ],
        
        # C/C++
        "C": [
            (r'^\s*#include\s+[<\"]([^>\"]+)[>\"]', "C include"),
        ],
        "C++": [
            (r'^\s*#include\s+[<\"]([^>\"]+)[>\"]', "C++ include"),
        ],
        "C/C++ Header": [
            (r'^\s*#include\s+[<\"]([^>\"]+)[>\"]', "Header include"),
        ],
        
        # PHP
        "PHP": [
            (r'^\s*(?:require|include)(?:_once)?\s*\(\s*[\'\"]([^\'"]+)[\'\"]', "PHP require/include"),
            (r'^\s*(?:require|include)(?:_once)?\s+[\'\"]([^\'"]+)[\'\"]', "PHP require/include"),
            (r'^\s*use\s+([\w\\]+)(?:\s+as\s+[\w]+)?', "PHP namespace"),
        ],
    }
    
    # Standard library modules by language
    STANDARD_LIBS = {
        # JavaScript/TypeScript (Node.js built-ins)
        "JavaScript": {
            "fs", "path", "http", "https", "url", "querystring", "os", "util",
            "crypto", "stream", "zlib", "child_process", "cluster", "dgram",
            "dns", "events", "net", "readline", "repl", "tls", "buffer",
            "string_decoder", "timers", "tty", "assert", "console",
        },
        "TypeScript": {
            "fs", "path", "http", "https", "url", "querystring", "os", "util",
            "crypto", "stream", "zlib", "child_process", "cluster", "dgram",
            "dns", "events", "net", "readline", "repl", "tls", "buffer",
            "string_decoder", "timers", "tty", "assert", "console",
        },
        
        # Python standard library
        "Python": {
            "abc", "argparse", "array", "ast", "asyncio", "base64", "bisect",
            "calendar", "collections", "concurrent", "contextlib", "copy",
            "csv", "datetime", "decimal", "difflib", "enum", "errno", "functools",
            "glob", "gzip", "hashlib", "heapq", "hmac", "html", "http", "importlib",
            "inspect", "io", "itertools", "json", "logging", "math", "multiprocessing",
            "operator", "os", "pathlib", "pickle", "platform", "pprint", "queue",
            "random", "re", "shutil", "signal", "socket", "sqlite3", "string",
            "struct", "subprocess", "sys", "tempfile", "threading", "time",
            "traceback", "types", "typing", "unittest", "urllib", "uuid", "warnings",
            "weakref", "xml", "zipfile",
        },
        
        # Java standard packages
        "Java": {
            "java.lang", "java.util", "java.io", "java.nio", "java.math",
            "java.time", "java.text", "java.net", "java.security", "java.sql",
            "javax.swing", "javax.servlet", "java.awt", "java.beans",
        },
        
        # Ruby standard libraries
        "Ruby": {
            "abbrev", "base64", "benchmark", "bigdecimal", "cgi", "csv", "date",
            "digest", "erb", "fileutils", "forwardable", "io", "ipaddr", "json",
            "logger", "net", "open-uri", "optparse", "ostruct", "pathname", "pp",
            "prettyprint", "prime", "set", "shellwords", "singleton", "socket",
            "stringio", "strscan", "tempfile", "time", "timeout", "tmpdir",
            "tsort", "uri", "yaml", "zlib",
        },
        
        # Go standard packages
        "Go": {
            "archive", "bufio", "builtin", "bytes", "compress", "container",
            "context", "crypto", "database", "debug", "encoding", "errors",
            "expvar", "flag", "fmt", "go", "hash", "html", "image", "index",
            "io", "log", "math", "mime", "net", "os", "path", "plugin",
            "reflect", "regexp", "runtime", "sort", "strconv", "strings",
            "sync", "syscall", "testing", "text", "time", "unicode", "unsafe",
        },
    }
    
    # Package name normalization by language
    # Maps import statements to the actual package names
    PACKAGE_MAPPINGS = {
        # JavaScript/TypeScript common package name mappings
        "JavaScript": {
            # React ecosystem
            "react": "react",
            "react-dom": "react-dom",
            "react-router": "react-router",
            "react-router-dom": "react-router-dom",
            "@reduxjs/toolkit": "redux-toolkit",
            "redux": "redux",
            "react-redux": "react-redux",
            
            # Angular ecosystem
            "@angular/core": "angular-core",
            "@angular/common": "angular-common",
            "@angular/platform-browser": "angular-platform-browser",
            "@angular/router": "angular-router",
            
            # Vue ecosystem
            "vue": "vue",
            "vue-router": "vue-router",
            "vuex": "vuex",
            "@vue/cli": "vue-cli",
            
            # Other common libraries
            "lodash": "lodash",
            "axios": "axios",
            "express": "express",
            "next": "next",
            "gatsby": "gatsby",
            "@material-ui/core": "material-ui",
            "@mui/material": "mui",
            "styled-components": "styled-components",
            "tailwindcss": "tailwindcss",
        },
        
        # Python mappings
        "Python": {
            # Django ecosystem
            "django": "django",
            "django.contrib": "django",
            "django.db": "django",
            "django.http": "django",
            "django.views": "django",
            "django.urls": "django",
            "django.test": "django",
            "django.conf": "django",
            
            # Flask ecosystem
            "flask": "flask",
            "flask_sqlalchemy": "flask-sqlalchemy",
            "flask_migrate": "flask-migrate",
            "flask_login": "flask-login",
            
            # FastAPI ecosystem
            "fastapi": "fastapi",
            "starlette": "starlette",
            "pydantic": "pydantic",
            
            # ORM libraries
            "sqlalchemy": "sqlalchemy",
            "peewee": "peewee",
            "tortoise": "tortoise-orm",
            "mongoengine": "mongoengine",
            
            # Data science ecosystem
            "numpy": "numpy",
            "pandas": "pandas",
            "matplotlib": "matplotlib",
            "seaborn": "seaborn",
            "sklearn": "scikit-learn",
            "tensorflow": "tensorflow",
            "torch": "pytorch",
            "keras": "keras",
        },
    }
    
    def __init__(self):
        """Initialize the import statement analyzer."""
        self.import_counts = Counter()  # Counts of imports across files
        self.global_imports = Counter()  # Imports that appear in multiple files
        self.local_imports = defaultdict(list)  # File-specific imports
        
        self.standard_lib_imports = Counter()  # Standard library imports
        self.third_party_imports = Counter()  # Third-party package imports
        self.relative_imports = Counter()  # Relative (local) imports
        
        self.import_line_numbers = defaultdict(list)  # Line numbers for imports
    
    def analyze_file(self, file_path: Path, language_info: LanguageInfo) -> List[ImportInfo]:
        """
        Analyze a file for import statements.
        
        Args:
            file_path: Path to the file to analyze
            language_info: Language information for the file
            
        Returns:
            List of ImportInfo objects representing imports found in the file
        """
        imports = []
        language = language_info.name
        
        # Skip if we don't have patterns for this language
        if language not in self.IMPORT_PATTERNS:
            return imports
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Extract imports using language-specific patterns
            patterns = self.IMPORT_PATTERNS.get(language, [])
            
            for line_num, line in enumerate(lines, 1):
                for pattern, import_type in patterns:
                    for match in re.finditer(pattern, line):
                        import_path = match.group(1)
                        
                        # Skip empty imports
                        if not import_path:
                            continue
                        
                        # Determine if this is a standard library, third-party, or relative import
                        import_category = self._categorize_import(import_path, language)
                        
                        # Normalize the package name
                        package_name = self._normalize_package_name(import_path, language)
                        
                        # Create ImportInfo object
                        import_info = ImportInfo(
                            path=import_path,
                            line=line_num,
                            type=import_type,
                            category=import_category,
                            package_name=package_name
                        )
                        
                        imports.append(import_info)
                        
                        # Update counters
                        self.import_counts[import_path] += 1
                        self.import_line_numbers[import_path].append((str(file_path), line_num))
                        
                        if import_category == "standard_library":
                            self.standard_lib_imports[import_path] += 1
                        elif import_category == "third_party":
                            self.third_party_imports[import_path] += 1
                        elif import_category == "relative":
                            self.relative_imports[import_path] += 1
            
            # Store local imports for this file
            self.local_imports[str(file_path)] = imports
            
            return imports
        
        except Exception as e:
            logger.warning(f"Error analyzing imports in {file_path}: {e}")
            return []
    
    def analyze_files(self, files: List[Tuple[Path, LanguageInfo]]) -> Dict[str, List[ImportInfo]]:
        """
        Analyze multiple files for import statements.
        
        Args:
            files: List of tuples containing file paths and language info
            
        Returns:
            Dictionary mapping file paths to lists of imports
        """
        logger.info(f"Analyzing imports in {len(files)} files")
        
        results = {}
        for file_path, language_info in files:
            imports = self.analyze_file(file_path, language_info)
            if imports:
                results[str(file_path)] = imports
        
        # Update global imports (imports that appear in multiple files)
        for import_path, count in self.import_counts.items():
            if count > 1:
                self.global_imports[import_path] = count
        
        return results
    
    def _categorize_import(self, import_path: str, language: str) -> str:
        """
        Categorize an import as standard library, third-party, or relative.
        
        Args:
            import_path: The import path or name
            language: The programming language
            
        Returns:
            Category of the import: 'standard_library', 'third_party', or 'relative'
        """
        # Check for relative imports first
        if import_path.startswith('.') or import_path.startswith('/'):
            return "relative"
        
        # Check if this is a standard library import
        if language in self.STANDARD_LIBS:
            # For Python, we need to check the first part of dotted imports
            if language == "Python" and "." in import_path:
                root_module = import_path.split('.')[0]
                if root_module in self.STANDARD_LIBS[language]:
                    return "standard_library"
            
            # For other languages, check the full import path
            elif import_path in self.STANDARD_LIBS[language]:
                return "standard_library"
            
            # For Java, check if the import starts with java. or javax.
            elif language == "Java" and (import_path.startswith("java.") or import_path.startswith("javax.")):
                return "standard_library"
            
            # For Go, check if the import is in the standard library
            elif language == "Go":
                root_package = import_path.split('/')[0]
                if root_package in self.STANDARD_LIBS[language]:
                    return "standard_library"
        
        # Default to third-party if not relative or standard library
        return "third_party"
    
    def _normalize_package_name(self, import_path: str, language: str) -> str:
        """
        Normalize an import path to a standard package name.
        
        Args:
            import_path: The import path or name
            language: The programming language
            
        Returns:
            Normalized package name
        """
        # Handle relative imports
        if import_path.startswith('.') or import_path.startswith('/'):
            return f"relative:{import_path}"
        
        # Check language-specific mappings
        if language in self.PACKAGE_MAPPINGS:
            mappings = self.PACKAGE_MAPPINGS[language]
            
            # JavaScript/TypeScript: Handle scoped packages
            if language in ("JavaScript", "TypeScript", "JavaScript (React)", "TypeScript (React)"):
                # For @org/package format
                if import_path.startswith('@'):
                    parts = import_path.split('/')
                    if len(parts) >= 2:
                        scope_package = f"{parts[0]}/{parts[1]}"
                        if scope_package in mappings:
                            return mappings[scope_package]
                
                # For path imports like './components'
                if import_path.startswith('.'):
                    return f"relative:{import_path}"
                
                # For imports without paths
                if import_path in mappings:
                    return mappings[import_path]
                
                # Handle subpackages
                for prefix, mapped in mappings.items():
                    if import_path.startswith(f"{prefix}/"):
                        return f"{mapped}:{import_path[len(prefix) + 1:]}"
                
                # For node_modules, only keep the package name (before any /)
                if '/' in import_path and not import_path.startswith('@'):
                    return import_path.split('/')[0]
            
            # Python: Handle namespace packages
            elif language == "Python":
                # Check for full match first
                if import_path in mappings:
                    return mappings[import_path]
                
                # Check for namespace packages
                for prefix, mapped in mappings.items():
                    if import_path.startswith(f"{prefix}."):
                        return mapped
                
                # If no mapping found, use the first part of the dotted path
                if '.' in import_path:
                    return import_path.split('.')[0]
        
        # Default to the original import path
        return import_path
    
    def get_import_statistics(self) -> Dict[str, Dict]:
        """
        Generate statistics about imports.
        
        Returns:
            Dictionary containing various import statistics
        """
        return {
            "total_imports": len(self.import_counts),
            "unique_imports": len(set(self.import_counts.keys())),
            "global_imports": {k: v for k, v in self.global_imports.most_common(20)},
            "standard_lib_imports": {k: v for k, v in self.standard_lib_imports.most_common(20)},
            "third_party_imports": {k: v for k, v in self.third_party_imports.most_common(20)},
            "relative_imports": {k: v for k, v in self.relative_imports.most_common(20)},
        }
    
    def get_top_packages(self, top_n: int = 20) -> List[Tuple[str, int]]:
        """
        Get the most frequently imported third-party packages.
        
        Args:
            top_n: Number of top packages to return
            
        Returns:
            List of (package_name, count) tuples
        """
        # Convert import paths to package names
        package_counts = Counter()
        
        for import_path, count in self.third_party_imports.items():
            # Skip relative imports
            if import_path.startswith('.') or import_path.startswith('/'):
                continue
            
            # Try to determine the package name
            for language, patterns in self.IMPORT_PATTERNS.items():
                normalized = self._normalize_package_name(import_path, language)
                if normalized != import_path:
                    package_counts[normalized] += count
                    break
            else:
                # If no normalization occurred, use the import path
                package_counts[import_path] += count
        
        return package_counts.most_common(top_n)
    
    def find_imports_by_package(self, package_name: str) -> List[Tuple[str, int]]:
        """
        Find all occurrences of a package import.
        
        Args:
            package_name: The package name to search for
            
        Returns:
            List of (file_path, line_number) tuples
        """
        results = []
        
        for import_path, locations in self.import_line_numbers.items():
            # Check if this import corresponds to the package
            for language, patterns in self.IMPORT_PATTERNS.items():
                normalized = self._normalize_package_name(import_path, language)
                if normalized == package_name or import_path == package_name:
                    results.extend(locations)
                    break
        
        return results