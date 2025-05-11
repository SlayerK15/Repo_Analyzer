"""
AI-Enhanced Detector module for repository analysis.

This module provides AI-powered detection of technologies, frameworks,
architectures, and other aspects of repository analysis. It uses LLMs to
complement traditional pattern-based detection with semantic understanding.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Set

from repo_analyzer.ai.ai_integration import AIIntegration

logger = logging.getLogger(__name__)

class AIDetector:
    """
    AI-enhanced detector for repository analysis.
    
    This class uses LLMs to analyze code repositories for technologies,
    frameworks, architectures, and other patterns that might be missed by
    traditional pattern-based detection methods.
    """
    
    def __init__(self, ai_integration: Optional[AIIntegration] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AI Detector.
        
        Args:
            ai_integration: AIIntegration instance (optional, will create one if not provided)
            config: Configuration dictionary with AI settings (optional)
        """
        # Initialize AI integration
        self.ai = ai_integration or AIIntegration(config)
        
        # Initialize analyzed file count for reporting
        self.analyzed_file_count = 0
        self.file_results = {}
    
    def analyze_repository(self, repo_path: str, files: List[str], 
                          files_content: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyze a repository using AI.
        
        This method examines a sample of files in the repository to identify
        technologies, frameworks, architectures, and other patterns.
        
        Args:
            repo_path: Path to the repository
            files: List of file paths to analyze
            files_content: Dict mapping file paths to their content
            
        Returns:
            Dict containing the AI analysis results
        """
        if not self.ai.config["enabled"]:
            logger.info("AI analysis is disabled. Skipping repository analysis.")
            return {"enabled": False, "message": "AI analysis is disabled"}
        
        # Select a representative sample of files to analyze
        selected_files = self._select_representative_files(files, files_content)
        logger.info(f"Selected {len(selected_files)} files for AI analysis")
        
        # Analyze each selected file
        self.analyzed_file_count = 0
        self.file_results = {}
        
        for file_path in selected_files:
            if file_path in files_content:
                relative_path = os.path.relpath(file_path, repo_path)
                filename = os.path.basename(file_path)
                extension = os.path.splitext(filename)[1].lower()
                
                # Detect language based on file extension
                language = self._detect_language_from_extension(extension)
                
                # Skip binary files and files without a recognized language
                if language == "unknown" or language == "binary":
                    continue
                
                logger.debug(f"Analyzing file with AI: {relative_path}")
                
                try:
                    # Analyze file content
                    result = self.analyze_file(file_path, files_content[file_path], language)
                    
                    if result.get("success", False):
                        self.file_results[relative_path] = result
                        self.analyzed_file_count += 1
                    
                except Exception as e:
                    logger.error(f"Error analyzing file {relative_path}: {str(e)}")
        
        # Aggregate results from all analyzed files
        return self._aggregate_repository_results()
    
    def analyze_file(self, file_path: str, content: str, language: str) -> Dict[str, Any]:
        """
        Analyze a single file using AI.
        
        Args:
            file_path: Path to the file
            content: Content of the file
            language: Programming language of the file
            
        Returns:
            Dict containing the AI analysis results for the file
        """
        filename = os.path.basename(file_path)
        
        # Get prompt for framework detection
        prompt = self.ai.get_framework_detection_prompt()
        
        # Use AI to analyze the file
        result = self.ai.analyze_code(
            code=content,
            language=language,
            filename=filename,
            prompt_template=prompt,
            system_message="You are a code analyzer AI that specializes in identifying technologies, frameworks, and patterns in code repositories."
        )
        
        return result
    
    def analyze_architecture(self, repo_path: str, files: List[str], 
                            files_content: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyze repository architecture using AI.
        
        Args:
            repo_path: Path to the repository
            files: List of file paths to analyze
            files_content: Dict mapping file paths to their content
            
        Returns:
            Dict containing the architecture analysis results
        """
        if not self.ai.config["enabled"]:
            logger.info("AI analysis is disabled. Skipping architecture analysis.")
            return {"enabled": False, "message": "AI analysis is disabled"}
        
        # Select a representative sample of files with focus on structure indicators
        selected_files = self._select_architecture_indicator_files(files, files_content)
        logger.info(f"Selected {len(selected_files)} files for architecture analysis")
        
        # Analyze each selected file
        architecture_results = {}
        
        for file_path in selected_files:
            if file_path in files_content:
                relative_path = os.path.relpath(file_path, repo_path)
                filename = os.path.basename(file_path)
                extension = os.path.splitext(filename)[1].lower()
                
                # Detect language based on file extension
                language = self._detect_language_from_extension(extension)
                
                # Skip binary files and files without a recognized language
                if language == "unknown" or language == "binary":
                    continue
                
                logger.debug(f"Analyzing architecture in file: {relative_path}")
                
                try:
                    # Get prompt for architecture detection
                    prompt = self.ai.get_architecture_detection_prompt()
                    
                    # Use AI to analyze the file
                    result = self.ai.analyze_code(
                        code=files_content[file_path],
                        language=language,
                        filename=filename,
                        prompt_template=prompt,
                        system_message="You are a software architecture analyst specializing in identifying architectural patterns, design patterns, and code organization principles."
                    )
                    
                    if result.get("success", False):
                        architecture_results[relative_path] = result
                    
                except Exception as e:
                    logger.error(f"Error analyzing architecture in {relative_path}: {str(e)}")
        
        # Aggregate architecture results
        return self._aggregate_architecture_results(architecture_results)
    
    def analyze_code_quality(self, repo_path: str, files: List[str], 
                           files_content: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyze code quality using AI.
        
        Args:
            repo_path: Path to the repository
            files: List of file paths to analyze
            files_content: Dict mapping file paths to their content
            
        Returns:
            Dict containing the code quality analysis results
        """
        if not self.ai.config["enabled"]:
            logger.info("AI analysis is disabled. Skipping code quality analysis.")
            return {"enabled": False, "message": "AI analysis is disabled"}
        
        # Select a representative sample of files for code quality analysis
        selected_files = self._select_code_quality_sample(files, files_content)
        logger.info(f"Selected {len(selected_files)} files for code quality analysis")
        
        # Analyze each selected file
        quality_results = {}
        
        for file_path in selected_files:
            if file_path in files_content:
                relative_path = os.path.relpath(file_path, repo_path)
                filename = os.path.basename(file_path)
                extension = os.path.splitext(filename)[1].lower()
                
                # Detect language based on file extension
                language = self._detect_language_from_extension(extension)
                
                # Skip binary files and files without a recognized language
                if language == "unknown" or language == "binary":
                    continue
                
                logger.debug(f"Analyzing code quality in file: {relative_path}")
                
                try:
                    # Get prompt for code quality assessment
                    prompt = self.ai.get_code_quality_prompt()
                    
                    # Use AI to analyze the file
                    result = self.ai.analyze_code(
                        code=files_content[file_path],
                        language=language,
                        filename=filename,
                        prompt_template=prompt,
                        system_message="You are a code quality analyst specializing in identifying best practices, code smells, and potential improvements in software code."
                    )
                    
                    if result.get("success", False):
                        quality_results[relative_path] = result
                    
                except Exception as e:
                    logger.error(f"Error analyzing code quality in {relative_path}: {str(e)}")
        
        # Aggregate code quality results
        return self._aggregate_quality_results(quality_results)
    
    def _select_representative_files(self, files: List[str], 
                                   files_content: Dict[str, str]) -> List[str]:
        """
        Select a representative sample of files for AI analysis.
        
        This method selects a subset of files that are most likely to contain
        useful information about the repository's technology stack.
        
        Args:
            files: List of all file paths in the repository
            files_content: Dict mapping file paths to their content
            
        Returns:
            List of selected file paths
        """
        # Define priority file patterns that are likely to indicate technologies
        priority_patterns = [
            # Configuration files
            "package.json", "requirements.txt", "Gemfile", "pom.xml", "build.gradle",
            "setup.py", "build.sbt", "composer.json", "Cargo.toml", "go.mod",
            "webpack.config.js", "tsconfig.json", "babel.config.js", "pyproject.toml",
            "config.py", "jest.config.js", "karma.conf.js", "gulpfile.js",
            
            # Framework-specific files
            "app.py", "app.js", "index.js", "main.py", "Main.java", "Program.cs",
            "Startup.cs", "web.config", "application.properties", "settings.py",
            
            # Structure-defining files
            "__init__.py", "README.md", "README.rst", "DESCRIPTION",
            "LICENSE", "Makefile", "Dockerfile", "docker-compose.yml",
            
            # Source code extensions by popularity
            ".py", ".js", ".ts", ".java", ".c", ".cpp", ".cs", ".rb", ".php", ".go"
        ]
        
        # Calculate maximum files to analyze
        max_files = 20  # Default
        
        # Adjust based on repository size
        if len(files) < 50:
            max_files = min(10, len(files))
        elif len(files) < 500:
            max_files = 20
        else:
            max_files = 30  # Cap at 30 files for very large repos
        
        # First, select priority files
        selected_files = []
        
        # Add files that match priority patterns
        for pattern in priority_patterns:
            for file_path in files:
                filename = os.path.basename(file_path)
                extension = os.path.splitext(file_path)[1].lower()
                
                if (filename == pattern or extension == pattern) and file_path in files_content:
                    # Check if file is not too large
                    if len(files_content[file_path]) < 100000:  # Skip files larger than ~100KB
                        selected_files.append(file_path)
                        
                    # Break if we've reached the maximum
                    if len(selected_files) >= max_files:
                        break
            
            # Break if we've reached the maximum
            if len(selected_files) >= max_files:
                break
                
        # If we still need more files, add some from different directories
        if len(selected_files) < max_files:
            # Group files by directory
            dir_files = {}
            for file_path in files:
                if file_path in files_content and file_path not in selected_files:
                    directory = os.path.dirname(file_path)
                    if directory not in dir_files:
                        dir_files[directory] = []
                    dir_files[directory].append(file_path)
            
            # Add one file from each directory until we reach max_files
            remaining_slots = max_files - len(selected_files)
            dirs_to_sample = sorted(dir_files.keys())[:remaining_slots]
            
            for directory in dirs_to_sample:
                if dir_files[directory]:
                    # Get the first file from this directory that's not too large
                    for file_path in dir_files[directory]:
                        if len(files_content[file_path]) < 50000:  # Skip files larger than ~50KB
                            selected_files.append(file_path)
                            break
        
        return selected_files
    
    def _select_architecture_indicator_files(self, files: List[str], 
                                           files_content: Dict[str, str]) -> List[str]:
        """
        Select files that are likely to indicate architectural patterns.
        
        Args:
            files: List of all file paths in the repository
            files_content: Dict mapping file paths to their content
            
        Returns:
            List of selected file paths
        """
        # Define patterns that indicate architectural structure
        architecture_patterns = [
            # Directory structure indicators
            "src/main", "app/controllers", "app/models", "app/views",
            "src/controllers", "src/models", "src/views",
            "src/services", "app/services", "src/repositories", "app/repositories",
            "domain", "infrastructure", "presentation", "application",
            "adapters", "ports", "usecases", "entities",
            
            # Configuration files
            "docker-compose.yml", "kubernetes", "k8s", "manifests",
            "serverless.yml", "terraform", "pulumi",
            
            # Architecture description files
            "architecture.md", "ARCHITECTURE", "DESIGN.md",
            
            # Common architecture files
            "ApplicationContext", "DependencyInjection", "Module",
            "Factory", "Repository", "Service", "Controller",
            "Provider", "Container", "Mediator", "Command",
            
            # File extensions
            ".kt", ".scala", ".clj", ".fs", ".ex", ".elm",
            ".xml", ".gradle", ".ts", ".rs"
        ]
        
        # Calculate maximum files to analyze
        max_files = 15  # Default
        
        # Adjust based on repository size
        if len(files) < 50:
            max_files = min(10, len(files))
        elif len(files) < 500:
            max_files = 15
        else:
            max_files = 20  # Cap at 20 files for very large repos
        
        # Select files that match architecture patterns
        selected_files = []
        
        for pattern in architecture_patterns:
            for file_path in files:
                if pattern in file_path and file_path in files_content:
                    # Check if file is not too large
                    if len(files_content[file_path]) < 100000:  # Skip files larger than ~100KB
                        selected_files.append(file_path)
                        
                    # Break if we've reached the maximum
                    if len(selected_files) >= max_files:
                        break
            
            # Break if we've reached the maximum
            if len(selected_files) >= max_files:
                break
        
        # Add some randomly selected files from different directories if needed
        if len(selected_files) < max_files:
            import random
            
            # Filter to files that are not too large
            eligible_files = [f for f in files if f in files_content 
                            and f not in selected_files 
                            and len(files_content[f]) < 50000]
            
            # Shuffle and select remaining files
            if eligible_files:
                random.shuffle(eligible_files)
                remaining_slots = max_files - len(selected_files)
                selected_files.extend(eligible_files[:remaining_slots])
        
        return selected_files
    
    def _select_code_quality_sample(self, files: List[str], 
                                  files_content: Dict[str, str]) -> List[str]:
        """
        Select a representative sample of files for code quality analysis.
        
        Args:
            files: List of all file paths in the repository
            files_content: Dict mapping file paths to their content
            
        Returns:
            List of selected file paths
        """
        # Define file extensions to analyze for code quality
        code_extensions = [
            ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".scala", 
            ".c", ".cpp", ".h", ".hpp", ".cs", ".go", ".rb", ".php", 
            ".swift", ".m", ".rs", ".dart", ".ex", ".exs", ".fs", ".fsx", 
            ".clj", ".cljs", ".groovy", ".sh", ".ps1", ".pl", ".lua"
        ]
        
        # Calculate maximum files to analyze
        max_files = 15  # Default
        
        # Adjust based on repository size
        if len(files) < 50:
            max_files = min(10, len(files))
        elif len(files) < 500:
            max_files = 15
        else:
            max_files = 20  # Cap at 20 files for very large repos
        
        # Filter files by extension and size
        eligible_files = []
        for file_path in files:
            if file_path in files_content:
                extension = os.path.splitext(file_path)[1].lower()
                if extension in code_extensions and len(files_content[file_path]) < 100000:
                    eligible_files.append(file_path)
        
        # If we have too few eligible files, return all of them
        if len(eligible_files) <= max_files:
            return eligible_files
        
        # Otherwise, select a diverse sample
        selected_files = []
        
        # Group by extension
        extension_files = {}
        for file_path in eligible_files:
            extension = os.path.splitext(file_path)[1].lower()
            if extension not in extension_files:
                extension_files[extension] = []
            extension_files[extension].append(file_path)
        
        # Calculate how many files to select from each extension
        total_extensions = len(extension_files)
        if total_extensions > 0:
            files_per_extension = max(1, max_files // total_extensions)
            
            # Select files from each extension
            for extension, files_list in extension_files.items():
                # Sort by file size (prefer smaller files for quicker analysis)
                sorted_files = sorted(files_list, key=lambda f: len(files_content[f]))
                
                # Take a sample from beginning, middle, and end to get diverse examples
                count = min(files_per_extension, len(files_list))
                if count == 1:
                    selected_files.append(files_list[0])
                elif count == 2:
                    selected_files.append(files_list[0])
                    selected_files.append(files_list[-1])
                else:
                    step = max(1, len(files_list) // count)
                    for i in range(0, len(files_list), step):
                        if len(selected_files) < max_files and i < len(files_list):
                            selected_files.append(files_list[i])
                
                # Break if we've reached the maximum
                if len(selected_files) >= max_files:
                    break
        
        return selected_files
    
    def _detect_language_from_extension(self, extension: str) -> str:
        """
        Detect programming language from file extension.
        
        Args:
            extension: File extension (including the dot)
            
        Returns:
            Language name or "unknown" if not recognized
        """
        # Mapping of file extensions to programming languages
        extension_map = {
            ".py": "Python",
            ".ipynb": "Python",
            ".js": "JavaScript",
            ".jsx": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".java": "Java",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".c": "C",
            ".cpp": "C++",
            ".h": "C",
            ".hpp": "C++",
            ".cs": "C#",
            ".vb": "Visual Basic",
            ".go": "Go",
            ".rb": "Ruby",
            ".php": "PHP",
            ".rs": "Rust",
            ".swift": "Swift",
            ".m": "Objective-C",
            ".mm": "Objective-C++",
            ".dart": "Dart",
            ".html": "HTML",
            ".htm": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".sass": "Sass",
            ".less": "Less",
            ".vue": "Vue",
            ".svelte": "Svelte",
            ".xml": "XML",
            ".json": "JSON",
            ".yml": "YAML",
            ".yaml": "YAML",
            ".md": "Markdown",
            ".sh": "Shell",
            ".bash": "Bash",
            ".ps1": "PowerShell",
            ".pl": "Perl",
            ".r": "R",
            ".lua": "Lua",
            ".ex": "Elixir",
            ".exs": "Elixir",
            ".clj": "Clojure",
            ".cljs": "ClojureScript",
            ".fs": "F#",
            ".fsx": "F#",
            ".hs": "Haskell",
            ".sql": "SQL",
            ".gradle": "Gradle",
            ".groovy": "Groovy",
            ".tf": "Terraform",
            ".proto": "Protocol Buffers",
            ".toml": "TOML",
            ".ini": "INI",
        }
        
        # Get lower case extension
        ext = extension.lower()
        
        # Return the language or "unknown" if not recognized
        return extension_map.get(ext, "unknown")
    
    def _aggregate_repository_results(self) -> Dict[str, Any]:
        """
        Aggregate AI analysis results from all analyzed files.
        
        Returns:
            Dict containing aggregated analysis results
        """
        # Initialize aggregated results
        aggregated = {
            "enabled": True,
            "file_count": self.analyzed_file_count,
            "technologies": {},
            "suggestions": []
        }
        
        # Aggregate technologies across all files
        for file_path, result in self.file_results.items():
            if "technologies" in result:
                for tech in result["technologies"]:
                    name = tech["name"]
                    
                    if name not in aggregated["technologies"]:
                        # Add new technology
                        aggregated["technologies"][name] = {
                            "name": name,
                            "category": tech["category"],
                            "confidence": tech["confidence"],
                            "evidence": tech["evidence"]
                        }
                    else:
                        # Update existing technology
                        existing = aggregated["technologies"][name]
                        
                        # Update confidence (use max confidence)
                        existing["confidence"] = max(existing["confidence"], tech["confidence"])
                        
                        # Add new evidence
                        for evidence in tech["evidence"]:
                            if evidence not in existing["evidence"]:
                                existing["evidence"].append(evidence)
            
            # Aggregate suggestions
            if "suggestions" in result:
                for suggestion in result["suggestions"]:
                    # Check if we already have a similar suggestion
                    is_duplicate = False
                    for existing in aggregated["suggestions"]:
                        if suggestion["text"] == existing["text"]:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        # Add source file info to suggestion
                        suggestion["file"] = file_path
                        aggregated["suggestions"].append(suggestion)
        
        # Convert technologies dict to list
        aggregated["technologies"] = list(aggregated["technologies"].values())
        
        # Sort technologies by confidence
        aggregated["technologies"].sort(key=lambda x: x["confidence"], reverse=True)
        
        # Limit evidence to keep response size reasonable
        for tech in aggregated["technologies"]:
            if len(tech["evidence"]) > 5:
                tech["evidence"] = tech["evidence"][:5]
        
        # Sort suggestions by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        aggregated["suggestions"].sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        # Limit suggestions to avoid overwhelming users
        if len(aggregated["suggestions"]) > 10:
            aggregated["suggestions"] = aggregated["suggestions"][:10]
        
        return aggregated
    
    def _aggregate_architecture_results(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate architecture analysis results.
        
        Args:
            results: Dict mapping file paths to architecture analysis results
            
        Returns:
            Dict containing aggregated architecture results
        """
        # Initialize aggregated results
        aggregated = {
            "enabled": True,
            "file_count": len(results),
            "patterns": {},
            "suggestions": []
        }
        
        # Aggregate patterns across all files
        for file_path, result in results.items():
            if "patterns" in result:
                for pattern in result["patterns"]:
                    name = pattern["name"]
                    
                    if name not in aggregated["patterns"]:
                        # Add new pattern
                        aggregated["patterns"][name] = {
                            "name": name,
                            "type": pattern["type"],
                            "confidence": pattern["confidence"],
                            "evidence": pattern["evidence"]
                        }
                    else:
                        # Update existing pattern
                        existing = aggregated["patterns"][name]
                        
                        # Update confidence (use max confidence)
                        existing["confidence"] = max(existing["confidence"], pattern["confidence"])
                        
                        # Add new evidence
                        for evidence in pattern["evidence"]:
                            if evidence not in existing["evidence"]:
                                existing["evidence"].append(evidence)
            
            # Aggregate suggestions
            if "suggestions" in result:
                for suggestion in result["suggestions"]:
                    # Check if we already have a similar suggestion
                    is_duplicate = False
                    for existing in aggregated["suggestions"]:
                        if suggestion["text"] == existing["text"]:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        # Add source file info to suggestion
                        suggestion["file"] = file_path
                        aggregated["suggestions"].append(suggestion)
        
        # Convert patterns dict to list
        aggregated["patterns"] = list(aggregated["patterns"].values())
        
        # Sort patterns by confidence
        aggregated["patterns"].sort(key=lambda x: x["confidence"], reverse=True)
        
        # Limit evidence to keep response size reasonable
        for pattern in aggregated["patterns"]:
            if len(pattern["evidence"]) > 5:
                pattern["evidence"] = pattern["evidence"][:5]
        
        # Sort suggestions by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        aggregated["suggestions"].sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        # Limit suggestions to avoid overwhelming users
        if len(aggregated["suggestions"]) > 10:
            aggregated["suggestions"] = aggregated["suggestions"][:10]
        
        return aggregated
    
    def _aggregate_quality_results(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate code quality analysis results.
        
        Args:
            results: Dict mapping file paths to code quality analysis results
            
        Returns:
            Dict containing aggregated quality results
        """
        # Initialize aggregated results
        aggregated = {
            "enabled": True,
            "file_count": len(results),
            "quality_assessment": {
                "readability": {"score": 0, "strengths": [], "weaknesses": []},
                "maintainability": {"score": 0, "strengths": [], "weaknesses": []},
                "performance": {"score": 0, "strengths": [], "weaknesses": []}
            },
            "issues": [],
            "suggestions": []
        }
        
        if not results:
            return aggregated
        
        # Track scores for averaging
        scores = {
            "readability": [],
            "maintainability": [],
            "performance": []
        }
        
        # Aggregate quality assessments across all files
        for file_path, result in results.items():
            if "quality_assessment" in result:
                qa = result["quality_assessment"]
                
                # Accumulate scores for averaging
                for aspect in ["readability", "maintainability", "performance"]:
                    if aspect in qa and "score" in qa[aspect]:
                        scores[aspect].append(qa[aspect]["score"])
                
                # Accumulate strengths and weaknesses
                for aspect in ["readability", "maintainability", "performance"]:
                    if aspect in qa:
                        # Add strengths
                        if "strengths" in qa[aspect]:
                            for strength in qa[aspect]["strengths"]:
                                if strength not in aggregated["quality_assessment"][aspect]["strengths"]:
                                    aggregated["quality_assessment"][aspect]["strengths"].append(strength)
                        
                        # Add weaknesses
                        if "weaknesses" in qa[aspect]:
                            for weakness in qa[aspect]["weaknesses"]:
                                if weakness not in aggregated["quality_assessment"][aspect]["weaknesses"]:
                                    aggregated["quality_assessment"][aspect]["weaknesses"].append(weakness)
            
            # Aggregate issues
            if "issues" in result:
                for issue in result["issues"]:
                    # Add source file info to issue
                    issue["file"] = file_path
                    aggregated["issues"].append(issue)
            
            # Aggregate suggestions
            if "suggestions" in result:
                for suggestion in result["suggestions"]:
                    # Check if we already have a similar suggestion
                    is_duplicate = False
                    for existing in aggregated["suggestions"]:
                        if suggestion["text"] == existing["text"]:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        # Add source file info to suggestion
                        suggestion["file"] = file_path
                        aggregated["suggestions"].append(suggestion)
        
        # Calculate average scores
        for aspect in ["readability", "maintainability", "performance"]:
            if scores[aspect]:
                aggregated["quality_assessment"][aspect]["score"] = sum(scores[aspect]) / len(scores[aspect])
        
        # Limit strengths and weaknesses to keep response size reasonable
        for aspect in ["readability", "maintainability", "performance"]:
            if len(aggregated["quality_assessment"][aspect]["strengths"]) > 5:
                aggregated["quality_assessment"][aspect]["strengths"] = aggregated["quality_assessment"][aspect]["strengths"][:5]
            
            if len(aggregated["quality_assessment"][aspect]["weaknesses"]) > 5:
                aggregated["quality_assessment"][aspect]["weaknesses"] = aggregated["quality_assessment"][aspect]["weaknesses"][:5]
        
        # Sort issues by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        aggregated["issues"].sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        # Limit issues to avoid overwhelming users
        if len(aggregated["issues"]) > 15:
            aggregated["issues"] = aggregated["issues"][:15]
        
        # Sort suggestions by severity
        aggregated["suggestions"].sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        # Limit suggestions to avoid overwhelming users
        if len(aggregated["suggestions"]) > 10:
            aggregated["suggestions"] = aggregated["suggestions"][:10]
        
        return aggregated