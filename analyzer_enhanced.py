"""
Enhanced RepoAnalyzer main class that integrates AI capabilities.

This enhanced version adds AI-powered analysis to the standard repository analysis,
providing more accurate detection, intelligent recommendations, and deeper insights.
"""

import os
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Union

# Import original analyzer
from repo_analyzer.analyzer import RepoAnalyzer as BaseRepoAnalyzer

# Import AI components
from repo_analyzer.ai import AIIntegration, AIDetector

logger = logging.getLogger(__name__)

class RepoAnalyzer(BaseRepoAnalyzer):
    """
    Enhanced RepoAnalyzer with AI capabilities.
    
    This class extends the base RepoAnalyzer with AI-powered analysis,
    providing more accurate detection, intelligent recommendations,
    and deeper insights into the repository.
    """
    
    def __init__(self, repo_path: str, exclude_dirs: Optional[Set[str]] = None, 
                 max_file_size: int = 5 * 1024 * 1024, verbose: bool = False,
                 config_path: Optional[str] = None, ai_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the enhanced RepoAnalyzer.
        
        Args:
            repo_path: Path to the repository to analyze
            exclude_dirs: Set of directory names to exclude from analysis
                         (defaults to common directories to ignore)
            max_file_size: Maximum file size in bytes to analyze (default: 5MB)
            verbose: Whether to print verbose output during analysis
            config_path: Path to configuration file (optional)
            ai_config: Configuration for AI features (optional)
        """
        # Initialize the base analyzer
        super().__init__(repo_path, exclude_dirs, max_file_size, verbose, config_path)
        
        # Initialize AI components
        self.ai_config = ai_config or {}
        self.ai_integration = AIIntegration(self.ai_config)
        self.ai_detector = AIDetector(self.ai_integration)
        
        # Add AI results to tech stack
        self.tech_stack["ai_analysis"] = {}
    
    def analyze(self) -> Dict[str, Any]:
        """
        Analyze the repository with standard detectors and AI enhancement.
        
        This method orchestrates the complete analysis process, using both
        traditional detectors and AI-powered analysis to provide enhanced
        insights into the repository's technology stack.
        
        Returns:
            Dict containing the complete tech stack analysis results
        """
        # Run standard analysis first
        tech_stack = super().analyze()
        
        # Check if AI is enabled
        if not self.ai_integration.config["enabled"]:
            logger.info("AI analysis is disabled. Skipping AI-enhanced analysis.")
            tech_stack["ai_analysis"] = {"enabled": False, "message": "AI analysis is disabled"}
            return tech_stack
        
        try:
            # Start AI analysis
            logger.info("Starting AI-enhanced analysis...")
            ai_start_time = datetime.now()
            
            # Run AI technology detection
            tech_stack["ai_analysis"]["technologies"] = self.ai_detector.analyze_repository(
                self.repo_path, self.files, self.files_content
            )
            
            # Run AI architecture analysis
            tech_stack["ai_analysis"]["architecture"] = self.ai_detector.analyze_architecture(
                self.repo_path, self.files, self.files_content
            )
            
            # Run AI code quality assessment
            tech_stack["ai_analysis"]["code_quality"] = self.ai_detector.analyze_code_quality(
                self.repo_path, self.files, self.files_content
            )
            
            # Calculate AI analysis duration
            ai_end_time = datetime.now()
            ai_duration = (ai_end_time - ai_start_time).total_seconds()
            tech_stack["ai_analysis"]["analysis_time_seconds"] = ai_duration
            
            # Cross-validate results from standard detectors with AI results
            tech_stack = self._cross_validate_with_ai(tech_stack)
            
            logger.info(f"AI-enhanced analysis completed in {ai_duration:.2f} seconds")
            
            # Generate recommendations
            tech_stack["ai_analysis"]["recommendations"] = self._generate_recommendations(tech_stack)
            
            return tech_stack
            
        except Exception as e:
            logger.error(f"Error during AI-enhanced analysis: {str(e)}")
            tech_stack["ai_analysis"] = {
                "enabled": True,
                "error": str(e),
                "message": "AI analysis failed"
            }
            return tech_stack
    
    def _cross_validate_with_ai(self, tech_stack: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cross-validate results from standard detectors with AI results.
        
        This method compares the results from traditional pattern-based detectors
        with the AI-powered analysis to improve confidence scores and reduce
        false positives.
        
        Args:
            tech_stack: Dict containing tech stack analysis results
            
        Returns:
            Updated tech stack dict with validated results
        """
        # Only cross-validate if AI analysis was successful
        if not tech_stack.get("ai_analysis") or not tech_stack["ai_analysis"].get("technologies"):
            return tech_stack
        
        ai_technologies = tech_stack["ai_analysis"]["technologies"].get("technologies", [])
        ai_tech_names = {tech["name"].lower(): tech for tech in ai_technologies}
        
        # Cross-validate frameworks
        if "frameworks" in tech_stack:
            for framework, details in list(tech_stack["frameworks"].items()):
                framework_lower = framework.lower()
                
                # If AI detected this framework, increase confidence
                if framework_lower in ai_tech_names:
                    ai_confidence = ai_tech_names[framework_lower]["confidence"]
                    
                    # If AI is very confident but pattern detector is not, increase pattern detector confidence
                    if ai_confidence > 80 and details["confidence"] < 60:
                        tech_stack["frameworks"][framework]["confidence"] = min(100, details["confidence"] * 1.5)
                        tech_stack["frameworks"][framework]["evidence"].append(
                            f"AI analysis confirmed this framework with high confidence"
                        )
                    
                    # If AI detected with medium confidence, slightly increase pattern detector confidence
                    elif ai_confidence > 50:
                        tech_stack["frameworks"][framework]["confidence"] = min(100, details["confidence"] * 1.2)
                        tech_stack["frameworks"][framework]["evidence"].append(
                            f"AI analysis confirmed this framework"
                        )
                
                # If AI didn't detect a framework that pattern matcher found with low confidence, reduce confidence
                elif details["confidence"] < 50:
                    tech_stack["frameworks"][framework]["confidence"] = details["confidence"] * 0.8
                    tech_stack["frameworks"][framework]["evidence"].append(
                        f"AI analysis did not detect this framework"
                    )
        
        # Cross-validate databases
        if "databases" in tech_stack:
            for database, details in list(tech_stack["databases"].items()):
                database_lower = database.lower()
                
                # If AI detected this database, increase confidence
                if database_lower in ai_tech_names:
                    ai_confidence = ai_tech_names[database_lower]["confidence"]
                    
                    if ai_confidence > 80 and details["confidence"] < 60:
                        tech_stack["databases"][database]["confidence"] = min(100, details["confidence"] * 1.5)
                        tech_stack["databases"][database]["evidence"].append(
                            f"AI analysis confirmed this database with high confidence"
                        )
                    elif ai_confidence > 50:
                        tech_stack["databases"][database]["confidence"] = min(100, details["confidence"] * 1.2)
                        tech_stack["databases"][database]["evidence"].append(
                            f"AI analysis confirmed this database"
                        )
                
                # If AI didn't detect a database that pattern matcher found with low confidence, reduce confidence
                elif details["confidence"] < 50:
                    tech_stack["databases"][database]["confidence"] = details["confidence"] * 0.8
                    tech_stack["databases"][database]["evidence"].append(
                        f"AI analysis did not detect this database"
                    )
        
        # Add technologies detected by AI but missed by pattern matchers
        for tech_name, tech_details in ai_tech_names.items():
            # Skip technologies that are already detected by pattern matchers
            found_in_standard = False
            for category in ["frameworks", "databases", "frontend", "build_systems", "package_managers"]:
                if category in tech_stack:
                    for tech in tech_stack[category]:
                        if tech.lower() == tech_name:
                            found_in_standard = True
                            break
                    
                    if found_in_standard:
                        break
            
            # If not found and AI is confident, add it to the appropriate category
            if not found_in_standard and tech_details["confidence"] >= 70:
                category = tech_details["category"]
                
                # Map AI category to tech stack category
                if category == "framework":
                    stack_category = "frameworks"
                elif category == "database":
                    stack_category = "databases"
                elif category == "frontend":
                    stack_category = "frontend"
                elif category == "build_system":
                    stack_category = "build_systems"
                elif category == "package_manager":
                    stack_category = "package_managers"
                else:
                    # Default to frameworks for unknown categories
                    stack_category = "frameworks"
                
                # Ensure the category exists
                if stack_category not in tech_stack:
                    tech_stack[stack_category] = {}
                
                # Add the technology
                if tech_details["name"] not in tech_stack[stack_category]:
                    tech_stack[stack_category][tech_details["name"]] = {
                        "matches": 0,  # No pattern matches
                        "confidence": tech_details["confidence"] * 0.9,  # Slightly lower confidence than AI
                        "evidence": [f"Detected by AI with {tech_details['confidence']}% confidence"]
                    }
                    
                    # Add evidence from AI
                    if "evidence" in tech_details:
                        tech_stack[stack_category][tech_details["name"]]["evidence"].extend(
                            [f"AI evidence: {e}" for e in tech_details["evidence"][:3]]
                        )
        
        # Cross-validate architecture
        if "architecture" in tech_stack and "architecture" in tech_stack["ai_analysis"]:
            ai_patterns = tech_stack["ai_analysis"]["architecture"].get("patterns", [])
            ai_pattern_names = {pattern["name"].lower(): pattern for pattern in ai_patterns}
            
            for arch, details in list(tech_stack["architecture"].items()):
                arch_lower = arch.lower()
                
                # If AI detected this architecture, increase confidence
                if arch_lower in ai_pattern_names:
                    ai_confidence = ai_pattern_names[arch_lower]["confidence"]
                    
                    if ai_confidence > 80 and details["confidence"] < 60:
                        tech_stack["architecture"][arch]["confidence"] = min(100, details["confidence"] * 1.5)
                        tech_stack["architecture"][arch]["evidence"].append(
                            f"AI analysis confirmed this architecture with high confidence"
                        )
                    elif ai_confidence > 50:
                        tech_stack["architecture"][arch]["confidence"] = min(100, details["confidence"] * 1.2)
                        tech_stack["architecture"][arch]["evidence"].append(
                            f"AI analysis confirmed this architecture"
                        )
                
                # If AI didn't detect an architecture pattern that rule matcher found with low confidence, reduce confidence
                elif details["confidence"] < 50:
                    tech_stack["architecture"][arch]["confidence"] = details["confidence"] * 0.8
                    tech_stack["architecture"][arch]["evidence"].append(
                        f"AI analysis did not detect this architecture pattern"
                    )
        
        return tech_stack
    
    def _generate_recommendations(self, tech_stack: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate intelligent recommendations based on analysis results.
        
        Args:
            tech_stack: Dict containing tech stack analysis results
            
        Returns:
            List of recommendation dicts
        """
        recommendations = []
        
        # Add recommendations from AI analysis
        for section in ["technologies", "architecture", "code_quality"]:
            if section in tech_stack["ai_analysis"]:
                section_data = tech_stack["ai_analysis"][section]
                if "suggestions" in section_data:
                    for suggestion in section_data["suggestions"]:
                        # Avoid duplicates
                        is_duplicate = False
                        for rec in recommendations:
                            if suggestion["text"] == rec["text"]:
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            recommendations.append({
                                "text": suggestion["text"],
                                "severity": suggestion["severity"],
                                "reason": suggestion.get("reason", "AI-detected suggestion"),
                                "source": section
                            })
        
        # Add cross-validation recommendations
        primary_tech = tech_stack.get("primary_technologies", {})
        
        # Check for missing technologies based on common combinations
        tech_combinations = {
            "React": ["ESLint", "Prettier", "Jest", "React Router"],
            "Angular": ["TypeScript", "RxJS", "NgRx", "Angular Material"],
            "Vue.js": ["Vuex", "Vue Router", "ESLint", "Jest"],
            "Django": ["Django REST framework", "Celery", "pytest"],
            "Flask": ["SQLAlchemy", "Alembic", "pytest"],
            "Spring": ["Spring Boot", "Hibernate", "JUnit"],
            "Express": ["Mongoose", "JWT", "Mocha", "Chai"]
        }
        
        # Check if primary framework has recommended complementary technologies
        if "frameworks" in primary_tech:
            primary_framework = primary_tech["frameworks"]
            if primary_framework in tech_combinations:
                recommended_techs = tech_combinations[primary_framework]
                
                # Check which technologies are missing
                for rec_tech in recommended_techs:
                    is_present = False
                    
                    # Check across all categories
                    for category in ["frameworks", "frontend", "testing", "build_systems", "package_managers"]:
                        if category in tech_stack:
                            if rec_tech in tech_stack[category]:
                                is_present = True
                                break
                    
                    # If technology is not present, recommend it
                    if not is_present:
                        recommendations.append({
                            "text": f"Consider adding {rec_tech} to your project, which is commonly used with {primary_framework}",
                            "severity": "medium",
                            "reason": f"Common companion technology for {primary_framework}",
                            "source": "stack_analysis"
                        })
        
        # Check for outdated or problematic technology combinations
        problematic_combinations = [
            {
                "condition": lambda ts: "jQuery" in ts.get("frameworks", {}) and "React" in ts.get("frameworks", {}),
                "text": "Consider migrating from jQuery to use React's built-in DOM manipulation capabilities",
                "severity": "medium",
                "reason": "jQuery and React often lead to conflicting approaches to DOM manipulation"
            },
            {
                "condition": lambda ts: "SQLite" in ts.get("databases", {}) and ts.get("architecture", {}).get("Microservices", {"confidence": 0})["confidence"] > 70,
                "text": "Consider using a more robust database solution for a microservices architecture",
                "severity": "medium",
                "reason": "SQLite is generally not recommended for distributed microservices architectures"
            },
            {
                "condition": lambda ts: "Django" in ts.get("frameworks", {}) and "React" in ts.get("frameworks", {}) and not any("webpack" in t.lower() for t in ts.get("build_systems", {})),
                "text": "Consider adding Webpack or another build system to better integrate React with Django",
                "severity": "medium",
                "reason": "React with Django often benefits from a dedicated build pipeline"
            }
        ]
        
        # Check for problematic combinations
        for combo in problematic_combinations:
            if combo["condition"](tech_stack):
                recommendations.append({
                    "text": combo["text"],
                    "severity": combo["severity"],
                    "reason": combo["reason"],
                    "source": "compatibility_analysis"
                })
        
        # Check for version control
        has_git = any(".git" in f for f in self.files)
        if not has_git:
            recommendations.append({
                "text": "Consider using Git for version control",
                "severity": "high",
                "reason": "Version control is essential for modern software development",
                "source": "best_practices"
            })
        
        # Check for testing frameworks
        if not tech_stack.get("testing", {}):
            recommendations.append({
                "text": "Consider adding a testing framework to your project",
                "severity": "high",
                "reason": "Testing frameworks are crucial for maintaining code quality",
                "source": "best_practices"
            })
        
        # Sort recommendations by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        return recommendations
    
    def print_ai_summary(self) -> None:
        """
        Print a human-readable summary of the AI analysis results.
        """
        if not self.tech_stack.get("ai_analysis"):
            print("\nAI analysis was not performed.")
            return
            
        if not self.tech_stack["ai_analysis"].get("enabled", True):
            print("\nAI analysis was disabled.")
            return
        
        print("\n===== AI-ENHANCED ANALYSIS SUMMARY =====\n")
        
        # Print technologies detected by AI
        if "technologies" in self.tech_stack["ai_analysis"]:
            tech_analysis = self.tech_stack["ai_analysis"]["technologies"]
            
            if "technologies" in tech_analysis:
                print("Technologies detected by AI:")
                for tech in tech_analysis["technologies"]:
                    print(f"  - {tech['name']} ({tech['category']}, {tech['confidence']:.1f}% confidence)")
                print("")
        
        # Print architecture patterns detected by AI
        if "architecture" in self.tech_stack["ai_analysis"]:
            arch_analysis = self.tech_stack["ai_analysis"]["architecture"]
            
            if "patterns" in arch_analysis:
                print("Architecture patterns detected by AI:")
                for pattern in arch_analysis["patterns"]:
                    print(f"  - {pattern['name']} ({pattern['type']}, {pattern['confidence']:.1f}% confidence)")
                print("")
        
        # Print code quality assessment
        if "code_quality" in self.tech_stack["ai_analysis"]:
            quality_analysis = self.tech_stack["ai_analysis"]["code_quality"]
            
            if "quality_assessment" in quality_analysis:
                qa = quality_analysis["quality_assessment"]
                print("Code Quality Assessment:")
                for aspect in ["readability", "maintainability", "performance"]:
                    if aspect in qa:
                        print(f"  - {aspect.capitalize()}: {qa[aspect]['score']:.1f}/100")
                print("")
            
            if "issues" in quality_analysis and quality_analysis["issues"]:
                print("Top Code Issues:")
                for issue in quality_analysis["issues"][:5]:
                    print(f"  - [{issue['severity'].upper()}] {issue['description']}")
                print("")
        
        # Print recommendations
        if "recommendations" in self.tech_stack["ai_analysis"]:
            recommendations = self.tech_stack["ai_analysis"]["recommendations"]
            
            if recommendations:
                print("AI Recommendations:")
                for rec in recommendations[:5]:
                    print(f"  - [{rec['severity'].upper()}] {rec['text']}")
                if len(recommendations) > 5:
                    print(f"  (+ {len(recommendations) - 5} more recommendations)")
                print("")
        
        print("==========================================")
    
    def save_results(self, output_file: str = None) -> str:
        """
        Save analysis results to a JSON file.
        
        Args:
            output_file: Path to the output file (default: repo_analysis.json in current directory)
            
        Returns:
            Path to the saved file
        """
        # Use the original save_results method, just add a message if AI analysis was performed
        result_path = super().save_results(output_file)
        
        if self.tech_stack.get("ai_analysis") and self.tech_stack["ai_analysis"].get("enabled", False):
            logger.info("Results include AI-enhanced analysis")
        
        return result_path