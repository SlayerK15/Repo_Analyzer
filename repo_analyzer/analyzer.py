"""
Enhanced RepoAnalyzer main class that orchestrates the complete repository analysis.

This enhanced version provides better integration of detectors, more rigorous
validation, and additional context-aware analysis to reduce false positives.
"""

import os
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Union

# Import enhanced detectors
from repo_analyzer.detectors.language_detector import LanguageDetector
from repo_analyzer.detectors.framework_detector import FrameworkDetector
from repo_analyzer.detectors.database_detector import DatabaseDetector
from repo_analyzer.detectors.build_detector import BuildDetector
from repo_analyzer.detectors.frontend_detector import FrontendDetector
from repo_analyzer.detectors.devops_detector import DevOpsDetector
from repo_analyzer.detectors.architecture_detector import ArchitectureDetector
from repo_analyzer.detectors.testing_detector import TestingDetector

# Import utilities
from repo_analyzer.utils.file_utils import get_all_files, load_files_content
from repo_analyzer.config import RepoAnalyzerConfig

logger = logging.getLogger(__name__)

class RepoAnalyzer:
    """
    Enhanced main class for analyzing code repositories.
    
    This class coordinates the repository analysis process by:
    1. Scanning all files in the repository
    2. Detecting programming languages
    3. Identifying frameworks
    4. Discovering database technologies
    5. Recognizing build systems and package managers
    6. Detecting frontend technologies
    7. Identifying DevOps tools
    8. Recognizing architecture patterns
    9. Discovering testing frameworks
    
    The enhanced version provides better integration between detectors,
    more context-aware analysis, and mechanisms to reduce false positives.
    """
    
    def __init__(self, repo_path: str, exclude_dirs: Optional[Set[str]] = None, 
                 max_file_size: int = 5 * 1024 * 1024, verbose: bool = False,
                 config_path: Optional[str] = None):
        """
        Initialize the RepoAnalyzer.
        
        Args:
            repo_path: Path to the repository to analyze
            exclude_dirs: Set of directory names to exclude from analysis
                         (defaults to common directories to ignore)
            max_file_size: Maximum file size in bytes to analyze (default: 5MB)
            verbose: Whether to print verbose output during analysis
            config_path: Path to configuration file (optional)
        """
        self.repo_path = os.path.abspath(repo_path)
        if not os.path.isdir(self.repo_path):
            raise ValueError(f"Repository path does not exist: {self.repo_path}")
        
        # Load configuration
        self.config = RepoAnalyzerConfig(config_path)
        
        # Set excluded directories
        self.exclude_dirs = exclude_dirs or self.config.get_exclude_dirs()
        
        self.max_file_size = max_file_size
        self.verbose = verbose
        
        # Configure logging based on verbosity
        log_level = logging.INFO if verbose else logging.WARNING
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Initialize result dictionary
        self.tech_stack = {
            "languages": {},
            "frameworks": {},
            "databases": {},
            "build_systems": {},
            "package_managers": {},
            "frontend": {},
            "devops": {},
            "architecture": {},
            "testing": {}
        }
        
        # Initialize detectors
        self.language_detector = LanguageDetector()
        self.framework_detector = FrameworkDetector()
        self.database_detector = DatabaseDetector()
        self.build_detector = BuildDetector()
        self.frontend_detector = FrontendDetector()
        self.devops_detector = DevOpsDetector()
        self.architecture_detector = ArchitectureDetector()
        self.testing_detector = TestingDetector()
        
        # Store analysis metadata
        self.analyze_duration = 0
        self.files_analyzed = 0
        self.files_with_content_analyzed = 0
        
        # Cache results for cross-detector analysis
        self._cache = {}
    
    def analyze(self) -> Dict[str, Any]:
        """
        Analyze the repository to identify its tech stack.
        
        This method orchestrates the complete analysis process by:
        1. Finding all relevant files in the repository
        2. Loading content of files that require deeper analysis
        3. Running specialized detectors for each aspect of the tech stack
        4. Determining primary technologies
        5. Cross-validating detections to reduce false positives
        6. Adding metadata about the analysis
        
        Returns:
            Dict containing the complete tech stack analysis results
        """
        logger.info(f"Starting analysis of repository: {self.repo_path}")
        start_time = datetime.now()
        
        # Step 1: Get all files in the repository
        all_files = get_all_files(self.repo_path, self.exclude_dirs)
        self.files_analyzed = len(all_files)
        logger.info(f"Found {self.files_analyzed} files to analyze")
        
        # Step 2: Detect programming languages (file extension based)
        self.tech_stack["languages"] = self.language_detector.detect(all_files)
        logger.info(f"Detected {len(self.tech_stack['languages'])} programming languages")
        
        # Cache primary languages for cross-detector validation
        self._cache["primary_languages"] = self._determine_primary_languages()
        
        # Step 3: Load content of relevant files for deeper analysis
        files_content = load_files_content(self.repo_path, all_files, self.max_file_size)
        self.files_with_content_analyzed = len(files_content)
        logger.info(f"Loaded content of {self.files_with_content_analyzed} files for deeper analysis")
        
        # Step 4: Detect frameworks
        self.tech_stack["frameworks"] = self.framework_detector.detect(all_files, files_content)
        logger.info(f"Detected {len(self.tech_stack['frameworks'])} frameworks")
        
        # Cache primary frameworks for cross-detector validation
        self._cache["primary_frameworks"] = self._get_highest_confidence_items("frameworks", 1)
        
        # Step 5: Detect databases
        self.tech_stack["databases"] = self.database_detector.detect(files_content)
        logger.info(f"Detected {len(self.tech_stack['databases'])} database technologies")
        
        # Step 6: Detect build systems and package managers
        build_systems, package_managers = self.build_detector.detect(all_files, files_content)
        self.tech_stack["build_systems"] = build_systems
        self.tech_stack["package_managers"] = package_managers
        logger.info(f"Detected {len(build_systems)} build systems and {len(package_managers)} package managers")
        
        # Step 7: Detect frontend technologies
        self.tech_stack["frontend"] = self.frontend_detector.detect(all_files, files_content)
        logger.info(f"Detected {len(self.tech_stack['frontend'])} frontend technologies")
        
        # Step 8: Detect DevOps tools
        self.tech_stack["devops"] = self.devops_detector.detect(all_files, files_content)
        logger.info(f"Detected {len(self.tech_stack['devops'])} DevOps tools")
        
        # Step 9: Detect architecture patterns
        self.tech_stack["architecture"] = self.architecture_detector.detect(all_files, files_content)
        logger.info(f"Detected {len(self.tech_stack['architecture'])} architecture patterns")
        
        # Step 10: Detect testing frameworks
        self.tech_stack["testing"] = self.testing_detector.detect(all_files, files_content)
        logger.info(f"Detected {len(self.tech_stack['testing'])} testing frameworks")
        
        # Step 11: Cross-validate and refine detections
        self._cross_validate_detections()
        logger.info("Performed cross-validation of detections")
        
        # Step 12: Determine primary technologies
        self.tech_stack["primary_technologies"] = self._determine_primary_technologies()
        logger.info("Determined primary technologies")
        
        # Step 13: Add metadata
        end_time = datetime.now()
        self.analyze_duration = (end_time - start_time).total_seconds()
        self.tech_stack["metadata"] = {
            "repo_path": self.repo_path,
            "file_count": self.files_analyzed,
            "content_analyzed_count": self.files_with_content_analyzed,
            "analysis_time_seconds": self.analyze_duration,
            "analyzed_at": str(end_time)
        }
        
        logger.info(f"Analysis completed in {self.analyze_duration:.2f} seconds")
        
        return self.tech_stack
    
    def _determine_primary_languages(self) -> List[str]:
        """
        Determine primary languages based on confidence scores and usage.
        
        Returns:
            List of primary language names
        """
        if not self.tech_stack["languages"]:
            return []
        
        # Find languages with confidence scores
        langs_with_confidence = []
        for lang, data in self.tech_stack["languages"].items():
            if isinstance(data, dict) and "confidence" in data:
                langs_with_confidence.append((lang, data["confidence"]))
        
        # Sort by confidence (highest first)
        if langs_with_confidence:
            langs_with_confidence.sort(key=lambda x: x[1], reverse=True)
            
            # Get languages with at least 50% of the confidence of the top language
            top_confidence = langs_with_confidence[0][1]
            threshold = top_confidence * 0.5
            
            return [lang for lang, conf in langs_with_confidence if conf >= threshold]
        
        return []
    
    def _get_highest_confidence_items(self, category: str, count: int = 3) -> List[str]:
        """
        Get the top N items with highest confidence from a category.
        
        Args:
            category: Technology category
            count: Number of top items to return
            
        Returns:
            List of top technology names
        """
        if category not in self.tech_stack or not self.tech_stack[category]:
            return []
        
        # Find items with confidence scores
        items_with_confidence = []
        for item, data in self.tech_stack[category].items():
            if isinstance(data, dict) and "confidence" in data:
                items_with_confidence.append((item, data["confidence"]))
        
        # Sort by confidence (highest first)
        if items_with_confidence:
            items_with_confidence.sort(key=lambda x: x[1], reverse=True)
            
            # Return top N items
            return [item for item, _ in items_with_confidence[:count]]
        
        return []
    
    def _cross_validate_detections(self) -> None:
        """
        Cross-validate detections across categories to reduce false positives.
        
        This method applies additional context-aware validation by checking
        relationships between different technologies.
        """
        # Get primary languages and frameworks
        primary_languages = self._cache.get("primary_languages", [])
        primary_frameworks = self._cache.get("primary_frameworks", [])
        
        # Map between languages and expected technologies
        language_framework_map = {
            "Python": ["Django", "Flask", "FastAPI", "PyTorch", "TensorFlow", "Pandas", "NumPy"],
            "JavaScript": ["React", "Vue.js", "Angular", "Express", "Next.js", "Node.js", "jQuery"],
            "TypeScript": ["React", "Vue.js", "Angular", "Express", "Next.js", "Node.js"],
            "Java": ["Spring", "Hibernate", "Jakarta EE", "Maven", "Gradle"],
            "C#": ["ASP.NET", "Entity Framework", ".NET", "Blazor"],
            "PHP": ["Laravel", "Symfony", "CodeIgniter", "Composer"],
            "Ruby": ["Rails", "Sinatra", "RubyGems", "Bundler"],
            "Go": ["Gin", "Echo", "Fiber", "Gorilla", "Go Modules"],
        }
        
        # Map between languages and build systems/package managers
        language_build_map = {
            "Python": ["setuptools", "pip", "Poetry", "Pipenv", "Conda"],
            "JavaScript": ["npm", "Yarn", "Webpack", "Babel", "Rollup", "esbuild", "swc"],
            "TypeScript": ["npm", "Yarn", "Webpack", "Babel", "Rollup", "tsc", "esbuild", "swc"],
            "Java": ["Maven", "Gradle", "Ant"],
            "C#": ["MSBuild", "NuGet"],
            "PHP": ["Composer"],
            "Ruby": ["Bundler", "RubyGems", "Rake"],
            "Go": ["Go Modules"],
        }
        
        # Validate frameworks against languages
        for framework, details in list(self.tech_stack["frameworks"].items()):
            is_valid = False
            
            # Check if framework is compatible with any primary language
            for lang in primary_languages:
                if lang in language_framework_map and framework in language_framework_map[lang]:
                    is_valid = True
                    break
            
            # If framework is incompatible with all primary languages, reduce confidence
            if not is_valid and primary_languages:
                if details["confidence"] < 80:  # Allow high confidence frameworks to remain
                    # Either reduce confidence or remove if already low
                    if details["confidence"] > 40:
                        self.tech_stack["frameworks"][framework]["confidence"] = details["confidence"] / 2
                        self.tech_stack["frameworks"][framework]["evidence"].append(
                            f"Warning: Framework may not be compatible with detected languages: {', '.join(primary_languages)}"
                        )
                    else:
                        del self.tech_stack["frameworks"][framework]
                        logger.debug(f"Removed {framework} - incompatible with languages {primary_languages}")
        
        # Validate build systems and package managers against languages
        for build_system, details in list(self.tech_stack["build_systems"].items()):
            is_valid = False
            
            # Check if build system is compatible with any primary language
            for lang in primary_languages:
                if lang in language_build_map and build_system in language_build_map[lang]:
                    is_valid = True
                    break
            
            # If build system is incompatible with all primary languages, reduce confidence
            if not is_valid and primary_languages:
                if details["confidence"] < 80:  # Allow high confidence build systems to remain
                    # Either reduce confidence or remove if already low
                    if details["confidence"] > 40:
                        self.tech_stack["build_systems"][build_system]["confidence"] = details["confidence"] / 2
                        self.tech_stack["build_systems"][build_system]["evidence"].append(
                            f"Warning: Build system may not be compatible with detected languages: {', '.join(primary_languages)}"
                        )
                    else:
                        del self.tech_stack["build_systems"][build_system]
                        logger.debug(f"Removed {build_system} - incompatible with languages {primary_languages}")
        
        # Similar validation for package managers
        for pkg_manager, details in list(self.tech_stack["package_managers"].items()):
            is_valid = False
            
            # Check if package manager is compatible with any primary language
            for lang in primary_languages:
                if lang in language_build_map and pkg_manager in language_build_map[lang]:
                    is_valid = True
                    break
            
            # If package manager is incompatible with all primary languages, reduce confidence
            if not is_valid and primary_languages:
                if details["confidence"] < 80:  # Allow high confidence package managers to remain
                    # Either reduce confidence or remove if already low
                    if details["confidence"] > 40:
                        self.tech_stack["package_managers"][pkg_manager]["confidence"] = details["confidence"] / 2
                        self.tech_stack["package_managers"][pkg_manager]["evidence"].append(
                            f"Warning: Package manager may not be compatible with detected languages: {', '.join(primary_languages)}"
                        )
                    else:
                        del self.tech_stack["package_managers"][pkg_manager]
                        logger.debug(f"Removed {pkg_manager} - incompatible with languages {primary_languages}")
        
        # Validate databases based on frameworks
        # For example, Django often uses PostgreSQL or SQLite
        framework_db_map = {
            "Django": ["PostgreSQL", "SQLite", "MySQL"],
            "Rails": ["PostgreSQL", "SQLite", "MySQL"],
            "Laravel": ["MySQL", "PostgreSQL"],
            "Express": ["MongoDB", "MySQL", "PostgreSQL"],
            "Spring": ["PostgreSQL", "MySQL", "Oracle", "SQL Server"],
            "Flask": ["SQLite", "PostgreSQL", "MySQL"],
        }
        
        # Boost confidence for databases that align with detected frameworks
        for framework in primary_frameworks:
            if framework in framework_db_map:
                for db in framework_db_map[framework]:
                    if db in self.tech_stack["databases"]:
                        # Boost confidence for aligned databases
                        current_confidence = self.tech_stack["databases"][db]["confidence"]
                        self.tech_stack["databases"][db]["confidence"] = min(100, current_confidence * 1.2)
                        self.tech_stack["databases"][db]["evidence"].append(
                            f"Compatible with detected framework: {framework}"
                        )
        
        # Final step: remove any technologies with confidence below threshold
        min_confidence = self.config.get("min_confidence", 15)
        
        for category in self.tech_stack:
            if category in ["metadata", "primary_technologies"]:
                continue
                
            # Filter technologies by confidence
            self.tech_stack[category] = {
                tech: details for tech, details in self.tech_stack[category].items()
                if isinstance(details, dict) and details.get("confidence", 0) >= min_confidence
            }
    
    def _determine_primary_technologies(self) -> Dict[str, str]:
        """
        Determine primary technologies in each category based on confidence scores.
        
        For each category (languages, frameworks, etc.), this method identifies
        the technology with the highest confidence score and designates it as
        the primary technology for that category.
        
        Returns:
            Dict mapping categories to their primary technologies
        """
        primary_tech = {}
        
        for category in self.tech_stack:
            # Skip metadata and primary_technologies itself
            if category in ["metadata", "primary_technologies"]:
                continue
                
            if isinstance(self.tech_stack[category], dict) and self.tech_stack[category]:
                # Find technologies with confidence scores
                techs_with_confidence = []
                for tech, data in self.tech_stack[category].items():
                    if isinstance(data, dict) and "confidence" in data:
                        techs_with_confidence.append((tech, data["confidence"]))
                
                # Sort by confidence (highest first)
                if techs_with_confidence:
                    techs_with_confidence.sort(key=lambda x: x[1], reverse=True)
                    primary_tech[category] = techs_with_confidence[0][0]
        
        return primary_tech
    
    def save_results(self, output_file: str = None) -> str:
        """
        Save analysis results to a JSON file.
        
        Args:
            output_file: Path to the output file (default: repo_analysis.json in current directory)
            
        Returns:
            Path to the saved file
        """
        if not output_file:
            output_file = "repo_analysis.json"
            
        # Ensure results exist
        if not self.tech_stack.get("metadata"):
            raise ValueError("No analysis results to save. Run analyze() first.")
            
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(self.tech_stack, f, indent=2)
            
        logger.info(f"Analysis results saved to {output_file}")
        return output_file
            
    def print_summary(self) -> None:
        """
        Print a human-readable summary of the analysis results.
        """
        if not self.tech_stack.get("metadata"):
            raise ValueError("No analysis results to print. Run analyze() first.")
            
        print("\n===== REPOSITORY ANALYSIS SUMMARY =====\n")
        
        # Print metadata
        print(f"Repository: {self.tech_stack['metadata']['repo_path']}")
        print(f"Files analyzed: {self.tech_stack['metadata']['file_count']}")
        print(f"Analysis time: {self.tech_stack['metadata']['analysis_time_seconds']:.2f} seconds")
        print(f"Analyzed at: {self.tech_stack['metadata']['analyzed_at']}")
        print("")
        
        # Print primary technologies
        print("Primary Technologies:")
        for category, tech in self.tech_stack.get("primary_technologies", {}).items():
            print(f"  - {category.replace('_', ' ').title()}: {tech}")
        print("")
        
        # Print details for each category
        for category in ["languages", "frameworks", "databases", "build_systems", 
                        "package_managers", "frontend", "devops", 
                        "architecture", "testing"]:
            techs = self.tech_stack.get(category, {})
            if techs:
                print(f"{category.replace('_', ' ').title()}:")
                # Sort by confidence
                sorted_techs = []
                for tech, details in techs.items():
                    confidence = details.get("confidence", 0) if isinstance(details, dict) else 0
                    sorted_techs.append((tech, confidence))
                
                sorted_techs.sort(key=lambda x: x[1], reverse=True)
                
                for tech, confidence in sorted_techs:
                    print(f"  - {tech} ({confidence:.1f}%)")
                print("")
                
        print("=======================================")