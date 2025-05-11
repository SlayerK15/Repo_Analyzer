"""
Main RepoAnalyzer class that orchestrates the complete repository analysis.

This module contains the primary RepoAnalyzer class, which coordinates 
the analysis process by utilizing specialized detectors for different 
aspects of the technology stack.
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Union

# Import detectors
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

logger = logging.getLogger(__name__)

class RepoAnalyzer:
    """
    Main class for analyzing code repositories.
    
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
    
    The analysis results include confidence scores for each detected technology
    and determine the primary technologies in each category.
    """
    
    def __init__(self, repo_path: str, exclude_dirs: Optional[Set[str]] = None, 
                 max_file_size: int = 5 * 1024 * 1024, verbose: bool = False):
        """
        Initialize the RepoAnalyzer.
        
        Args:
            repo_path: Path to the repository to analyze
            exclude_dirs: Set of directory names to exclude from analysis
                         (defaults to common directories to ignore)
            max_file_size: Maximum file size in bytes to analyze (default: 5MB)
            verbose: Whether to print verbose output during analysis
        """
        self.repo_path = os.path.abspath(repo_path)
        if not os.path.isdir(self.repo_path):
            raise ValueError(f"Repository path does not exist: {self.repo_path}")
        
        # Set default excluded directories if none provided
        self.exclude_dirs = exclude_dirs or {
            '.git', 'node_modules', 'venv', '.venv', '__pycache__', 
            'build', 'dist', 'target', 'bin', 'obj'
        }
        
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
    
    def analyze(self) -> Dict[str, Any]:
        """
        Analyze the repository to identify its tech stack.
        
        This method orchestrates the complete analysis process by:
        1. Finding all relevant files in the repository
        2. Loading content of files that require deeper analysis
        3. Running specialized detectors for each aspect of the tech stack
        4. Determining primary technologies
        5. Adding metadata about the analysis
        
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
        
        # Step 3: Load content of relevant files for deeper analysis
        files_content = load_files_content(self.repo_path, all_files, self.max_file_size)
        self.files_with_content_analyzed = len(files_content)
        logger.info(f"Loaded content of {self.files_with_content_analyzed} files for deeper analysis")
        
        # Step 4: Detect frameworks
        self.tech_stack["frameworks"] = self.framework_detector.detect(all_files, files_content)
        logger.info(f"Detected {len(self.tech_stack['frameworks'])} frameworks")
        
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
        self.tech_stack["architecture"] = self.architecture_detector.detect(all_files)
        logger.info(f"Detected {len(self.tech_stack['architecture'])} architecture patterns")
        
        # Step 10: Detect testing frameworks
        self.tech_stack["testing"] = self.testing_detector.detect(all_files, files_content)
        logger.info(f"Detected {len(self.tech_stack['testing'])} testing frameworks")
        
        # Step 11: Determine primary technologies
        self.tech_stack["primary_technologies"] = self._determine_primary_technologies()
        logger.info("Determined primary technologies")
        
        # Step 12: Add metadata
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


if __name__ == "__main__":
    import sys
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Analyze a code repository to identify its tech stack")
    parser.add_argument("repo_path", help="Path to the repository to analyze")
    parser.add_argument("--output", "-o", help="Path to save the analysis results (JSON format)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    try:
        # Create and run analyzer
        analyzer = RepoAnalyzer(args.repo_path, verbose=args.verbose)
        analyzer.analyze()
        
        # Print summary
        analyzer.print_summary()
        
        # Save results if output file specified
        if args.output:
            output_file = analyzer.save_results(args.output)
            print(f"\nAnalysis results saved to: {output_file}")
        
    except Exception as e:
        print(f"Error analyzing repository: {str(e)}")
        sys.exit(1)