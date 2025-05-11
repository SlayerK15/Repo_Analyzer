"""
Technology Recommendation Engine for RepoAnalyzer.

This module provides intelligent recommendations for repository technologies
based on detected patterns, best practices, and common technology combinations.
It leverages both rule-based recommendations and AI-powered suggestions.
"""

import logging
from typing import Dict, List, Any, Optional, Set

from repo_analyzer.ai.ai_integration import AIIntegration

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """
    Technology recommendation engine for repository analysis.
    
    This class provides intelligent recommendations for improving a repository's
    technology stack based on detected patterns, best practices, and common
    technology combinations.
    """
    
    def __init__(self, ai_integration: Optional[AIIntegration] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the recommendation engine.
        
        Args:
            ai_integration: AIIntegration instance (optional, will create one if not provided)
            config: Configuration dictionary with settings (optional)
        """
        # Initialize AI integration
        self.ai = ai_integration or AIIntegration(config)
        
        # Initialize technology recommendation rules
        self._init_recommendation_rules()
    
    def _init_recommendation_rules(self):
        """Initialize recommendation rules for common technology stacks."""
        # Common recommended technology combinations
        self.tech_combinations = {
            # Frontend frameworks and their ecosystem
            "React": [
                {"name": "React Router", "reason": "Navigation management", "severity": "medium"},
                {"name": "Redux", "reason": "State management", "severity": "medium"},
                {"name": "TypeScript", "reason": "Type safety", "severity": "medium"},
                {"name": "Jest", "reason": "Testing framework", "severity": "high"},
                {"name": "ESLint", "reason": "Code quality", "severity": "high"},
                {"name": "Prettier", "reason": "Code formatting", "severity": "medium"}
            ],
            "Angular": [
                {"name": "TypeScript", "reason": "Type safety (Angular requires TypeScript)", "severity": "high"},
                {"name": "RxJS", "reason": "Reactive programming", "severity": "high"},
                {"name": "NgRx", "reason": "State management", "severity": "medium"},
                {"name": "Angular Material", "reason": "UI component library", "severity": "medium"},
                {"name": "Jasmine", "reason": "Testing framework", "severity": "high"},
                {"name": "Karma", "reason": "Test runner", "severity": "high"}
            ],
            "Vue.js": [
                {"name": "Vue Router", "reason": "Navigation management", "severity": "medium"},
                {"name": "Vuex", "reason": "State management", "severity": "medium"},
                {"name": "TypeScript", "reason": "Type safety", "severity": "medium"},
                {"name": "Jest", "reason": "Testing framework", "severity": "high"},
                {"name": "ESLint", "reason": "Code quality", "severity": "high"},
                {"name": "Vite", "reason": "Build tool", "severity": "medium"}
            ],
            
            # Backend frameworks and their ecosystem
            "Django": [
                {"name": "Django REST framework", "reason": "API development", "severity": "medium"},
                {"name": "Celery", "reason": "Task queue", "severity": "medium"},
                {"name": "pytest", "reason": "Testing framework", "severity": "high"},
                {"name": "Black", "reason": "Code formatting", "severity": "medium"},
                {"name": "django-debug-toolbar", "reason": "Debugging", "severity": "low"}
            ],
            "Flask": [
                {"name": "SQLAlchemy", "reason": "ORM", "severity": "high"},
                {"name": "Alembic", "reason": "Database migrations", "severity": "medium"},
                {"name": "Marshmallow", "reason": "Serialization", "severity": "medium"},
                {"name": "pytest", "reason": "Testing framework", "severity": "high"},
                {"name": "Black", "reason": "Code formatting", "severity": "medium"}
            ],
            "Express": [
                {"name": "Mongoose", "reason": "MongoDB ORM", "severity": "medium"},
                {"name": "Sequelize", "reason": "SQL ORM", "severity": "medium"},
                {"name": "JWT", "reason": "Authentication", "severity": "medium"},
                {"name": "Mocha", "reason": "Testing framework", "severity": "high"},
                {"name": "Chai", "reason": "Assertion library", "severity": "high"},
                {"name": "ESLint", "reason": "Code quality", "severity": "high"}
            ],
            "Spring": [
                {"name": "Spring Boot", "reason": "Simplified configuration", "severity": "high"},
                {"name": "Spring Data JPA", "reason": "Database access", "severity": "medium"},
                {"name": "Spring Security", "reason": "Authentication and authorization", "severity": "medium"},
                {"name": "JUnit", "reason": "Testing framework", "severity": "high"},
                {"name": "Mockito", "reason": "Mocking library", "severity": "high"},
                {"name": "SLF4J", "reason": "Logging", "severity": "medium"}
            ],
            "FastAPI": [
                {"name": "SQLAlchemy", "reason": "ORM", "severity": "high"},
                {"name": "Pydantic", "reason": "Data validation", "severity": "high"},
                {"name": "Alembic", "reason": "Database migrations", "severity": "medium"},
                {"name": "pytest", "reason": "Testing framework", "severity": "high"},
                {"name": "Black", "reason": "Code formatting", "severity": "medium"}
            ],
            
            # Programming languages and their ecosystem
            "Python": [
                {"name": "pytest", "reason": "Testing framework", "severity": "high"},
                {"name": "Black", "reason": "Code formatting", "severity": "medium"},
                {"name": "mypy", "reason": "Type checking", "severity": "medium"},
                {"name": "pylint", "reason": "Code quality", "severity": "medium"},
                {"name": "Poetry", "reason": "Dependency management", "severity": "medium"}
            ],
            "JavaScript": [
                {"name": "ESLint", "reason": "Code quality", "severity": "high"},
                {"name": "Prettier", "reason": "Code formatting", "severity": "medium"},
                {"name": "Jest", "reason": "Testing framework", "severity": "high"},
                {"name": "TypeScript", "reason": "Type safety", "severity": "medium"},
                {"name": "Webpack", "reason": "Module bundling", "severity": "medium"}
            ],
            "TypeScript": [
                {"name": "TSLint", "reason": "Code quality", "severity": "high"},
                {"name": "Prettier", "reason": "Code formatting", "severity": "medium"},
                {"name": "Jest", "reason": "Testing framework", "severity": "high"},
                {"name": "tsc", "reason": "TypeScript compiler", "severity": "high"}
            ],
            "Java": [
                {"name": "JUnit", "reason": "Testing framework", "severity": "high"},
                {"name": "Mockito", "reason": "Mocking library", "severity": "high"},
                {"name": "SLF4J", "reason": "Logging", "severity": "medium"},
                {"name": "Gradle", "reason": "Build tool", "severity": "medium"},
                {"name": "Checkstyle", "reason": "Code quality", "severity": "medium"}
            ],
            "Go": [
                {"name": "Go Modules", "reason": "Dependency management", "severity": "high"},
                {"name": "Go Test", "reason": "Testing framework", "severity": "high"},
                {"name": "golint", "reason": "Code quality", "severity": "medium"},
                {"name": "go fmt", "reason": "Code formatting", "severity": "high"}
            ],
            
            # Architecture patterns and their requirements
            "Microservices": [
                {"name": "Docker", "reason": "Containerization", "severity": "high"},
                {"name": "Kubernetes", "reason": "Container orchestration", "severity": "medium"},
                {"name": "API Gateway", "reason": "Service aggregation", "severity": "medium"},
                {"name": "Service Discovery", "reason": "Service location", "severity": "medium"},
                {"name": "Distributed Tracing", "reason": "Observability", "severity": "medium"},
                {"name": "Circuit Breaker", "reason": "Resilience", "severity": "medium"}
            ],
            "Event-Driven Architecture": [
                {"name": "Kafka", "reason": "Event streaming", "severity": "high"},
                {"name": "RabbitMQ", "reason": "Message broker", "severity": "high"},
                {"name": "Event Store", "reason": "Event persistence", "severity": "medium"},
                {"name": "CQRS", "reason": "Command-query separation", "severity": "medium"}
            ],
            "Serverless": [
                {"name": "AWS Lambda", "reason": "Function execution", "severity": "high"},
                {"name": "API Gateway", "reason": "API management", "severity": "high"},
                {"name": "Serverless Framework", "reason": "Deployment management", "severity": "medium"},
                {"name": "CloudFormation", "reason": "Infrastructure as code", "severity": "medium"}
            ]
        }
        
        # Problematic technology combinations that should be flagged
        self.problematic_combinations = [
            {
                "condition": lambda ts: "jQuery" in ts.get("frameworks", {}) and "React" in ts.get("frameworks", {}),
                "text": "Consider migrating from jQuery to use React's built-in DOM manipulation capabilities",
                "reason": "jQuery and React often lead to conflicting approaches to DOM manipulation",
                "severity": "medium"
            },
            {
                "condition": lambda ts: "SQLite" in ts.get("databases", {}) and ts.get("architecture", {}).get("Microservices", {"confidence": 0})["confidence"] > 70,
                "text": "Consider using a more robust database solution for a microservices architecture",
                "reason": "SQLite is generally not recommended for distributed microservices architectures",
                "severity": "medium"
            },
            {
                "condition": lambda ts: "Django" in ts.get("frameworks", {}) and "React" in ts.get("frameworks", {}) and not any("webpack" in t.lower() for t in ts.get("build_systems", {})),
                "text": "Consider adding Webpack or another build system to better integrate React with Django",
                "reason": "React with Django often benefits from a dedicated build pipeline",
                "severity": "medium"
            },
            {
                "condition": lambda ts: "MongoDB" in ts.get("databases", {}) and "Mongoose" not in ts.get("frameworks", {}) and "Express" in ts.get("frameworks", {}),
                "text": "Consider using Mongoose as an ODM for MongoDB with Express",
                "reason": "Mongoose provides a more structured approach to MongoDB in Express applications",
                "severity": "medium"
            },
            {
                "condition": lambda ts: "Flask" in ts.get("frameworks", {}) and "SQLAlchemy" not in ts.get("frameworks", {}),
                "text": "Consider adding SQLAlchemy for database access in your Flask application",
                "reason": "SQLAlchemy is the recommended ORM for Flask applications",
                "severity": "medium"
            }
        ]
        
        # Best practices that should always be checked
        self.best_practices = [
            {
                "condition": lambda files, ts: not any(".git" in f for f in files),
                "text": "Consider using Git for version control",
                "reason": "Version control is essential for modern software development",
                "severity": "high"
            },
            {
                "condition": lambda files, ts: not ts.get("testing", {}),
                "text": "Consider adding a testing framework to your project",
                "reason": "Testing frameworks are crucial for maintaining code quality",
                "severity": "high"
            },
            {
                "condition": lambda files, ts: "Docker" not in ts.get("devops", {}),
                "text": "Consider containerizing your application with Docker",
                "reason": "Containerization improves deployment consistency",
                "severity": "medium"
            },
            {
                "condition": lambda files, ts: not any(f.endswith((".md", ".rst")) for f in files),
                "text": "Consider adding documentation files (README.md)",
                "reason": "Documentation is important for project understanding",
                "severity": "medium"
            },
            {
                "condition": lambda files, ts: not any(".github/workflows" in f for f in files) and not any("jenkins" in f.lower() for f in files) and not any("gitlab-ci" in f.lower() for f in files),
                "text": "Consider adding a CI/CD pipeline",
                "reason": "Continuous integration and deployment improve development workflow",
                "severity": "medium"
            }
        ]
    
    def generate_recommendations(self, tech_stack: Dict[str, Any], files: List[str]) -> List[Dict[str, Any]]:
        """
        Generate technology recommendations for a repository.
        
        Args:
            tech_stack: Repository analysis results
            files: List of file paths in the repository
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Check if AI is enabled for more advanced recommendations
        ai_enabled = self.ai.config["enabled"]
        
        # Get primary technologies
        primary_tech = tech_stack.get("primary_technologies", {})
        
        # Check for missing technologies based on common combinations
        for category, tech_name in primary_tech.items():
            if tech_name in self.tech_combinations:
                recommended_techs = self.tech_combinations[tech_name]
                
                # Check which technologies are missing
                for rec_tech in recommended_techs:
                    is_present = False
                    
                    # Check across all categories
                    for cat in ["frameworks", "frontend", "testing", "build_systems", "package_managers"]:
                        if cat in tech_stack:
                            if rec_tech["name"] in tech_stack[cat]:
                                is_present = True
                                break
                    
                    # If technology is not present, recommend it
                    if not is_present:
                        recommendations.append({
                            "text": f"Consider adding {rec_tech['name']} to your project, which is commonly used with {tech_name}",
                            "severity": rec_tech["severity"],
                            "reason": f"{rec_tech['reason']} for {tech_name}",
                            "source": "stack_analysis"
                        })
        
        # Check for problematic technology combinations
        for combo in self.problematic_combinations:
            if combo["condition"](tech_stack):
                recommendations.append({
                    "text": combo["text"],
                    "severity": combo["severity"],
                    "reason": combo["reason"],
                    "source": "compatibility_analysis"
                })
        
        # Check best practices
        for practice in self.best_practices:
            if practice["condition"](files, tech_stack):
                recommendations.append({
                    "text": practice["text"],
                    "severity": practice["severity"],
                    "reason": practice["reason"],
                    "source": "best_practices"
                })
        
        # If AI is enabled, generate AI-powered recommendations
        if ai_enabled:
            try:
                ai_recommendations = self._generate_ai_recommendations(tech_stack)
                
                # Merge AI recommendations with rule-based ones
                for rec in ai_recommendations:
                    # Check for duplicates
                    is_duplicate = False
                    for existing_rec in recommendations:
                        if rec["text"].lower() == existing_rec["text"].lower():
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        rec["source"] = "ai_analysis"
                        recommendations.append(rec)
            except Exception as e:
                logger.error(f"Error generating AI recommendations: {str(e)}")
        
        # Sort recommendations by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        return recommendations
    
    def _generate_ai_recommendations(self, tech_stack: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate AI-powered recommendations.
        
        Args:
            tech_stack: Repository analysis results
            
        Returns:
            List of AI-generated recommendation dictionaries
        """
        if not self.ai.config["enabled"]:
            return []
        
        # Format tech stack data for AI prompt
        tech_stack_summary = {}
        
        # Include primary technologies
        tech_stack_summary["primary_technologies"] = tech_stack.get("primary_technologies", {})
        
        # Include top technologies from each category
        for category in ["languages", "frameworks", "databases", "build_systems", 
                        "package_managers", "frontend", "devops", "architecture", "testing"]:
            if category in tech_stack:
                techs = tech_stack[category]
                # Sort by confidence
                sorted_techs = sorted(
                    [(tech, details.get("confidence", 0)) for tech, details in techs.items()],
                    key=lambda x: x[1],
                    reverse=True
                )
                # Include top 3
                tech_stack_summary[category] = [tech for tech, _ in sorted_techs[:3]]
        
        # Convert to string for AI prompt
        tech_stack_str = json.dumps(tech_stack_summary, indent=2)
        
        # Create prompt for recommendations
        prompt = f"""
        Please analyze this technology stack and provide recommendations for improvements
        or additional technologies that would enhance the project.
        
        Technology Stack:
        ```json
        {tech_stack_str}
        ```
        
        Provide 3-5 specific, actionable recommendations that would improve this 
        technology stack. For each recommendation, include:
        1. A clear suggestion
        2. The severity (high, medium, or low)
        3. A brief reason for the recommendation
        
        Format your response as a JSON object with the following structure:
        ```json
        [
          {{
            "text": "Clear recommendation text",
            "severity": "high|medium|low",
            "reason": "Brief reason for this recommendation"
          }}
        ]
        ```
        
        Focus on practical, commonly-accepted best practices rather than personal preferences.
        """
        
        # Call AI to generate recommendations
        try:
            import json
            
            result = self.ai._call_llm_api(
                prompt=prompt,
                system_message="You are a software architecture advisor specializing in technology stack optimization and best practices."
            )
            
            # Parse JSON response
            if isinstance(result, dict) and "error" not in result:
                # Try to find recommendations in the response
                if isinstance(result, list):
                    # Response is already a list of recommendations
                    return result
                
                # Check if there's a recommendations field
                for field in ["recommendations", "response", "suggestions", "result"]:
                    if field in result and isinstance(result[field], list):
                        return result[field]
                
                # Try to parse the first list found in the result
                for value in result.values():
                    if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                        if "text" in value[0] or "recommendation" in value[0]:
                            return value
                
                # If we can't find a list of recommendations, return an empty list
                logger.warning("Could not parse AI recommendations from result")
                return []
            else:
                logger.warning(f"Error in AI recommendation generation: {result.get('error', 'Unknown error')}")
                return []
                
        except Exception as e:
            logger.error(f"Error generating AI recommendations: {str(e)}")
            return []