"""
Language Detection Subsystem for the Technology Extraction System.

This module provides functionality for detecting programming languages
based on file extensions and content analysis, generating metadata about
the language distribution in a codebase.
"""
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tech_extraction.config import settings
from tech_extraction.models.file import FileInfo, LanguageInfo
from tech_extraction.models.metadata import LanguageDistribution, LanguageMetadata

logger = logging.getLogger(__name__)


class LanguageDetectionSubsystem:
    """
    Subsystem responsible for detecting programming languages in files.
    
    The LanguageDetectionSubsystem performs the following operations:
    1. Map file extensions to programming languages
    2. Analyze file content for additional language clues
    3. Generate metadata about language distribution in the codebase
    """
    
    # Extension to language mapping
    # This is a comprehensive mapping of file extensions to languages
    EXTENSION_MAP = {
        # Programming Languages
        ".py": "Python",
        ".pyi": "Python",
        ".ipynb": "Jupyter Notebook",
        ".js": "JavaScript",
        ".jsx": "JavaScript (React)",
        ".ts": "TypeScript",
        ".tsx": "TypeScript (React)",
        ".java": "Java",
        ".kt": "Kotlin",
        ".groovy": "Groovy",
        ".scala": "Scala",
        ".rb": "Ruby",
        ".rs": "Rust",
        ".go": "Go",
        ".c": "C",
        ".h": "C/C++ Header",
        ".cpp": "C++",
        ".hpp": "C++ Header",
        ".cc": "C++",
        ".cxx": "C++",
        ".cs": "C#",
        ".fs": "F#",
        ".vb": "Visual Basic",
        ".php": "PHP",
        ".swift": "Swift",
        ".m": "Objective-C",
        ".mm": "Objective-C++",
        ".pl": "Perl",
        ".pm": "Perl Module",
        ".r": "R",
        ".lua": "Lua",
        ".sh": "Shell",
        ".bash": "Bash",
        ".zsh": "Zsh",
        ".fish": "Fish",
        ".ps1": "PowerShell",
        ".psm1": "PowerShell Module",
        ".bat": "Batch",
        ".cmd": "Batch",
        ".jl": "Julia",
        ".ex": "Elixir",
        ".exs": "Elixir Script",
        ".erl": "Erlang",
        ".hrl": "Erlang Header",
        ".hs": "Haskell",
        ".lhs": "Haskell (Literate)",
        ".elm": "Elm",
        ".clj": "Clojure",
        ".cljs": "ClojureScript",
        ".cljc": "Clojure Common",
        ".dart": "Dart",
        ".d": "D",
        ".lisp": "Lisp",
        ".cl": "Common Lisp",
        ".scm": "Scheme",
        ".rkt": "Racket",
        
        # Markup and Templates
        ".html": "HTML",
        ".htm": "HTML",
        ".xhtml": "XHTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".sass": "Sass",
        ".less": "Less",
        ".md": "Markdown",
        ".markdown": "Markdown",
        ".rst": "reStructuredText",
        ".xml": "XML",
        ".svg": "SVG",
        ".xsl": "XSLT",
        ".xslt": "XSLT",
        ".mustache": "Mustache",
        ".handlebars": "Handlebars",
        ".hbs": "Handlebars",
        ".ejs": "EJS",
        ".pug": "Pug",
        ".jade": "Jade",
        ".haml": "Haml",
        ".slim": "Slim",
        ".jinja": "Jinja",
        ".jinja2": "Jinja2",
        ".j2": "Jinja2",
        ".twig": "Twig",
        ".liquid": "Liquid",
        
        # Configuration
        ".json": "JSON",
        ".jsonc": "JSON with Comments",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".toml": "TOML",
        ".ini": "INI",
        ".cfg": "Config",
        ".conf": "Config",
        ".config": "Config",
        ".properties": "Properties",
        ".env": "Environment Variables",
        ".tf": "Terraform",
        ".hcl": "HCL",
        ".dockerfile": "Dockerfile",
        ".editorconfig": "EditorConfig",
        ".gitignore": "Git Ignore",
        ".gitattributes": "Git Attributes",
        ".eslintrc": "ESLint Config",
        ".prettierrc": "Prettier Config",
        ".stylelintrc": "Stylelint Config",
        ".babelrc": "Babel Config",
        ".tsconfig": "TypeScript Config",
        
        # Data
        ".csv": "CSV",
        ".tsv": "TSV",
        ".sql": "SQL",
        ".graphql": "GraphQL",
        ".gql": "GraphQL",
        ".proto": "Protocol Buffers",
        
        # Documentation
        ".txt": "Plain Text",
        ".rtf": "Rich Text Format",
        ".pdf": "PDF",
        ".doc": "Word Document",
        ".docx": "Word Document",
        ".xls": "Excel Spreadsheet",
        ".xlsx": "Excel Spreadsheet",
        ".ppt": "PowerPoint Presentation",
        ".pptx": "PowerPoint Presentation",
    }
    
    # Multi-extension mapping for ambiguous cases
    MULTI_EXTENSION_MAP = {
        ".h": ["C", "C++", "Objective-C"],
        ".m": ["Objective-C", "Matlab"],
    }
    
    # Shebang patterns for script languages
    SHEBANG_PATTERNS = {
        r"^#!.*\bpython\b": "Python",
        r"^#!.*\bruby\b": "Ruby",
        r"^#!.*\bperl\b": "Perl",
        r"^#!.*\bnode\b": "JavaScript",
        r"^#!.*\bbash\b": "Bash",
        r"^#!.*\bzsh\b": "Zsh",
        r"^#!.*\bsh\b": "Shell",
        r"^#!.*\bfish\b": "Fish",
        r"^#!.*\btclsh\b": "Tcl",
        r"^#!.*\bphp\b": "PHP",
        r"^#!.*\br\b": "R",
    }
    
    # Content markers for specific languages
    CONTENT_MARKERS = {
        r"<\?php": "PHP",
        r"<\?=": "PHP",
        r"import\s+React": "JavaScript (React)",
        r"from\s+React\s+import": "JavaScript (React)",
        r"import\s+.*\s+from\s+['\"]react['\"]": "JavaScript (React)",
        r"@angular": "Angular",
        r"@Component": "Angular",
        r"@NgModule": "Angular",
        r"@Injectable": "Angular",
        r"Vue\.component": "Vue.js",
        r"new\s+Vue": "Vue.js",
        r"<template>.*</template>": "Vue.js",
        r"import\s+.*\s+from\s+['\"]vue['\"]": "Vue.js",
        r"django\.": "Django",
        r"from\s+django": "Django",
        r"rails": "Ruby on Rails",
        r"ActiveRecord": "Ruby on Rails",
        r"ActiveController": "Ruby on Rails",
        r"spring-boot": "Spring Boot",
        r"@SpringBootApplication": "Spring Boot",
        r"@RestController": "Spring Boot",
        r"@Controller": "Spring Boot",
        r"@Service": "Spring Boot",
        r"@Repository": "Spring Boot",
        r"@Autowired": "Spring Boot",
        r"express\(": "Express.js",
        r"require\(['\"]express['\"]": "Express.js",
        r"import\s+.*\s+from\s+['\"]express['\"]": "Express.js",
        r"flask\.": "Flask",
        r"from\s+flask": "Flask",
        r"laravel": "Laravel",
        r"namespace\s+App": "Laravel",
        r"use\s+Illuminate": "Laravel",
    }
    
    def __init__(self):
        """Initialize the language detection subsystem."""
        self.language_distribution = Counter()
        self.total_loc = 0
        self.language_to_loc = Counter()
    
    def detect_language(self, file_info: FileInfo) -> LanguageInfo:
        """
        Detect the programming language of a file.
        
        Args:
            file_info: Information about the file
            
        Returns:
            Language information including name and confidence
        """
        language = None
        confidence = 0.0
        path = Path(file_info.full_path)
        
        # 1. Extension-based detection
        if path.suffix.lower() in self.EXTENSION_MAP:
            language = self.EXTENSION_MAP[path.suffix.lower()]
            confidence = 0.8  # Good confidence but not absolute
        elif path.suffix.lower() in self.MULTI_EXTENSION_MAP:
            # Handle ambiguous extensions - need content analysis
            possible_languages = self.MULTI_EXTENSION_MAP[path.suffix.lower()]
            language = possible_languages[0]  # Default to first possibility
            confidence = 0.5  # Lower confidence due to ambiguity
        else:
            # Unknown extension
            language = "Unknown"
            confidence = 0.2
        
        # 2. Content-based detection for better accuracy
        try:
            # Read the first 1000 bytes of the file (enough for headers/shebang)
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content_start = f.read(1000)
                
                # Look for shebang in the first line
                first_line = content_start.split('\n')[0] if content_start else ""
                for pattern, lang in self.SHEBANG_PATTERNS.items():
                    if re.search(pattern, first_line):
                        language = lang
                        confidence = 0.9  # Shebang is a strong indicator
                        break
                
                # Look for content markers
                for pattern, lang in self.CONTENT_MARKERS.items():
                    if re.search(pattern, content_start, re.MULTILINE):
                        # If we already detected this language family from extension
                        # but now have a more specific framework, use the framework
                        # and increase confidence
                        if language in lang or lang in language:
                            language = lang  # More specific
                            confidence = 0.95  # Very high confidence
                        # Otherwise replace if our new confidence would be higher
                        elif confidence < 0.9:
                            language = lang
                            confidence = 0.9
                        break
                
                # Count lines of code for metrics
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        loc = sum(1 for line in f if line.strip())
                        self.language_to_loc[language] += loc
                        self.total_loc += loc
                except Exception as e:
                    logger.warning(f"Failed to count lines in {path}: {e}")
        
        except Exception as e:
            logger.warning(f"Error analyzing file content for {path}: {e}")
            # If content analysis fails, stay with extension-based detection
        
        # Update language distribution counter
        self.language_distribution[language] += 1
        
        return LanguageInfo(
            name=language,
            confidence=confidence,
            lines_of_code=self.language_to_loc.get(language, 0)
        )
    
    def generate_metadata(self) -> LanguageMetadata:
        """
        Generate metadata about the language distribution in the codebase.
        
        Returns:
            Language metadata including distribution and statistics
        """
        # Calculate total files
        total_files = sum(self.language_distribution.values())
        
        # Create language distribution
        distribution = []
        for language, count in self.language_distribution.most_common():
            percentage = (count / total_files) * 100 if total_files > 0 else 0
            loc_percentage = (self.language_to_loc[language] / self.total_loc) * 100 if self.total_loc > 0 else 0
            
            distribution.append(
                LanguageDistribution(
                    language=language,
                    file_count=count,
                    percentage=percentage,
                    lines_of_code=self.language_to_loc[language],
                    loc_percentage=loc_percentage
                )
            )
        
        # Calculate primary language
        primary_language = distribution[0].language if distribution else "Unknown"
        
        return LanguageMetadata(
            total_files=total_files,
            total_loc=self.total_loc,
            primary_language=primary_language,
            distribution=distribution
        )

    def process_files(self, files: List[FileInfo]) -> Dict[str, LanguageInfo]:
        """
        Process a list of files and detect their languages.
        
        Args:
            files: List of files to process
            
        Returns:
            Dictionary mapping file paths to language information
        """
        logger.info(f"Detecting languages for {len(files)} files")
        
        result = {}
        for file_info in files:
            language_info = self.detect_language(file_info)
            result[file_info.path] = language_info
        
        return result