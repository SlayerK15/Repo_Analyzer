"""
Architecture Detector module for repository analysis.

This module identifies software architecture patterns in a repository by
analyzing directory structures, file naming patterns, and code organization.
It can detect common patterns like MVC, MVVM, microservices, layered architecture,
and domain-driven design.
"""

import os
import re
from collections import defaultdict, Counter
from typing import Dict, List, Any, Set

class ArchitectureDetector:
    """
    Detector for software architecture patterns used in a repository.
    
    This class identifies architectural patterns by examining directory
    structures, file organization, naming conventions, and code organization
    patterns that indicate specific architectural approaches.
    """
    
    def __init__(self):
        """Initialize the Architecture Detector with detection patterns."""
        # Directory patterns for different architectures
        self.directory_patterns = {
            "MVC": [
                ("models/", "views/", "controllers/"),  # Classic MVC
                ("model/", "view/", "controller/"),
                ("app/models/", "app/views/", "app/controllers/"),
                ("src/models/", "src/views/", "src/controllers/"),
                ("Models/", "Views/", "Controllers/"),  # .NET style
            ],
            "MVVM": [
                ("models/", "views/", "viewmodels/"),
                ("model/", "view/", "viewmodel/"),
                ("app/models/", "app/views/", "app/viewmodels/"),
                ("src/models/", "src/views/", "src/viewmodels/"),
                ("Models/", "Views/", "ViewModels/"),
            ],
            "MVP": [
                ("models/", "views/", "presenters/"),
                ("model/", "view/", "presenter/"),
                ("app/models/", "app/views/", "app/presenters/"),
                ("src/models/", "src/views/", "src/presenters/"),
                ("Models/", "Views/", "Presenters/"),
            ],
            "Layered Architecture": [
                ("presentation/", "business/", "data/"),
                ("presentation/", "service/", "repository/"),
                ("ui/", "core/", "data/"),
                ("ui/", "domain/", "data/"),
                ("frontend/", "backend/", "database/"),
                ("api/", "services/", "repositories/"),
                ("controllers/", "services/", "repositories/"),
                ("web/", "service/", "persistence/"),
            ],
            "Clean Architecture": [
                ("entities/", "usecases/", "adapters/", "frameworks/"),
                ("domain/", "application/", "infrastructure/", "presentation/"),
                ("core/domain/", "core/application/", "infrastructure/", "ui/"),
                ("domain/entities/", "domain/usecases/", "data/", "presentation/"),
            ],
            "Hexagonal Architecture": [
                ("domain/", "ports/", "adapters/"),
                ("core/", "ports/", "adapters/"),
                ("domain/", "application/ports/", "infrastructure/adapters/"),
                ("internal/", "interfaces/", "external/"),
            ],
            "Microservices": [
                ("services/", "discovery/", "gateway/"),
                ("microservices/", "api-gateway/", "service-registry/"),
                ("ms-", "api-gateway/", "eureka/"),
                ("svc-", "gateway/", "registry/"),
            ],
            "Event-Driven Architecture": [
                ("events/", "handlers/", "publishers/"),
                ("events/", "subscribers/", "publishers/"),
                ("events/", "consumers/", "producers/"),
                ("messages/", "handlers/", "dispatchers/"),
            ],
            "Domain-Driven Design": [
                ("domain/entities/", "domain/valueobjects/", "domain/repositories/"),
                ("domain/aggregates/", "domain/services/", "domain/events/"),
                ("domain/model/", "domain/service/", "infrastructure/persistence/"),
                ("core/aggregates/", "core/repositories/", "infrastructure/"),
            ],
            "CQRS": [
                ("commands/", "queries/", "handlers/"),
                ("write/", "read/", "models/"),
                ("command/", "query/", "projections/"),
                ("commands/", "queries/", "events/"),
            ],
            "REST API": [
                ("controllers/", "services/", "repositories/"),
                ("resources/", "services/", "repositories/"),
                ("api/v1/", "services/", "repositories/"),
                ("endpoints/", "services/", "data/"),
            ],
            "GraphQL API": [
                ("graphql/", "resolvers/", "schema/"),
                ("graphql/resolvers/", "graphql/types/", "graphql/schema/"),
                ("graphql/", "resolvers/", "models/"),
                ("schema/", "resolvers/", "models/"),
            ],
            "Feature-based architecture": [
                ("features/", "shared/", "utils/"),
                ("modules/", "shared/", "common/"),
                ("features/", "common/", "core/"),
                ("modules/", "common/", "core/"),
            ],
        }
        
        # File naming patterns for different architectures
        self.file_patterns = {
            "MVC": [
                r"(\w+)Controller\.\w+", r"(\w+)View\.\w+", r"(\w+)Model\.\w+",
                r"controllers/(\w+)\.\w+", r"views/(\w+)\.\w+", r"models/(\w+)\.\w+"
            ],
            "MVVM": [
                r"(\w+)ViewModel\.\w+", r"(\w+)View\.\w+", r"(\w+)Model\.\w+",
                r"viewmodels/(\w+)\.\w+", r"views/(\w+)\.\w+", r"models/(\w+)\.\w+"
            ],
            "Clean Architecture": [
                r"(\w+)UseCase\.\w+", r"(\w+)Entity\.\w+", r"(\w+)Repository\.\w+",
                r"usecases/(\w+)\.\w+", r"entities/(\w+)\.\w+", r"repositories/(\w+)\.\w+"
            ],
            "Hexagonal Architecture": [
                r"(\w+)Port\.\w+", r"(\w+)Adapter\.\w+", r"(\w+)Service\.\w+",
                r"ports/(\w+)\.\w+", r"adapters/(\w+)\.\w+", r"domain/(\w+)\.\w+"
            ],
            "Domain-Driven Design": [
                r"(\w+)Entity\.\w+", r"(\w+)ValueObject\.\w+", r"(\w+)Aggregate\.\w+",
                r"(\w+)Repository\.\w+", r"(\w+)Factory\.\w+", r"(\w+)Service\.\w+"
            ],
            "CQRS": [
                r"(\w+)Command\.\w+", r"(\w+)Query\.\w+", r"(\w+)Handler\.\w+",
                r"commands/(\w+)\.\w+", r"queries/(\w+)\.\w+", r"handlers/(\w+)\.\w+"
            ],
            "Microservices": [
                r"(\w+)Service\.\w+", r"(\w+)Client\.\w+", r"(\w+)Api\.\w+",
                r"services/(\w+)/", r"clients/(\w+)\.\w+", r"apis/(\w+)\.\w+"
            ],
        }
        
        # Code patterns that indicate specific architectures
        self.code_patterns = {
            "MVC": [
                r"class\s+\w+Controller", r"class\s+\w+Model", r"extends\s+Controller",
                r"@Controller", r"@RequestMapping", r"render\(\s*['\"][\w/]+['\"]\s*,"
            ],
            "MVVM": [
                r"class\s+\w+ViewModel", r"extends\s+ViewModel", r"@BindingAdapter",
                r"LiveData<", r"Observable<", r"setState\("
            ],
            "Clean Architecture": [
                r"class\s+\w+UseCase", r"class\s+\w+Interactor", r"class\s+\w+Gateway",
                r"@UseCase", r"@Entity", r"@Repository", r"implements\s+UseCase"
            ],
            "Hexagonal Architecture": [
                r"interface\s+\w+Port", r"class\s+\w+Adapter", r"implements\s+\w+Port",
                r"@Port", r"@Adapter", r"@InboundPort", r"@OutboundPort"
            ],
            "Domain-Driven Design": [
                r"class\s+\w+Entity", r"class\s+\w+ValueObject", r"class\s+\w+Aggregate",
                r"class\s+\w+Repository", r"class\s+\w+Factory", r"class\s+\w+Service",
                r"@Entity", r"@AggregateRoot", r"@ValueObject", r"@DomainService"
            ],
            "CQRS": [
                r"class\s+\w+Command", r"class\s+\w+Query", r"class\s+\w+Handler",
                r"class\s+\w+CommandHandler", r"class\s+\w+QueryHandler",
                r"@CommandHandler", r"@QueryHandler", r"@EventHandler"
            ],
            "Event-Driven Architecture": [
                r"class\s+\w+Event", r"class\s+\w+EventHandler", r"class\s+\w+Publisher",
                r"class\s+\w+Subscriber", r"@EventListener", r"@Subscribe", r"emit\("
            ],
            "REST API": [
                r"@RestController", r"@GetMapping", r"@PostMapping", r"@RequestBody",
                r"@PathVariable", r"@RequestParam", r"app\.get\(", r"app\.post\("
            ],
            "GraphQL API": [
                r"type\s+\w+\s*{", r"input\s+\w+\s*{", r"interface\s+\w+\s*{",
                r"@Query", r"@Mutation", r"@Resolver", r"gql`", r"graphql`"
            ],
        }
        
        # Framework-specific architecture indicators
        self.framework_architecture_mapping = {
            "rails": "MVC",  # Ruby on Rails uses MVC
            "django": "MVC",  # Django uses MVT which is similar to MVC
            "laravel": "MVC",  # Laravel uses MVC
            "asp.net mvc": "MVC",  # ASP.NET MVC uses MVC
            "spring mvc": "MVC",  # Spring MVC uses MVC
            "angular": "MVVM",  # Angular uses component architecture with MVVM influence
            "vue": "MVVM",  # Vue.js uses MVVM
            "react-redux": "Flux-like",  # React with Redux follows Flux-like pattern
            "spring boot": "Layered Architecture",  # Spring Boot often uses layered architecture
            "nestjs": "Layered Architecture",  # NestJS uses modules pattern
            "express": "REST API",  # Express.js is commonly used for REST APIs
            "flask": "REST API",  # Flask is commonly used for REST APIs
            "graphql": "GraphQL API",  # GraphQL frameworks for GraphQL APIs
            "apollo": "GraphQL API",  # Apollo framework for GraphQL
            "kubernetes": "Microservices",  # Kubernetes often indicates microservices
            "docker-compose": "Microservices",  # docker-compose can indicate microservices
            "kafka": "Event-Driven Architecture",  # Kafka is used for event-driven architecture
            "rabbitmq": "Event-Driven Architecture"  # RabbitMQ is used for event-driven architecture
        }
        
        # Configuration files indicating specific architectures
        self.config_architecture_mapping = {
            "docker-compose.yml": "Microservices",
            "kubernetes": "Microservices",
            "k8s": "Microservices",
            "istio": "Microservices",
            "consul": "Microservices",
            "eureka": "Microservices",
            "zuul": "Microservices",
            "gateway": "Microservices",
            "kafka": "Event-Driven Architecture",
            "rabbitmq": "Event-Driven Architecture",
            "activemq": "Event-Driven Architecture",
            "graphql": "GraphQL API",
            "swagger": "REST API",
            "openapi": "REST API"
        }
    
    def _apply_context_validation(self, architecture_matches, architecture_evidence, files, files_content=None):
        """
        Apply additional validation to reduce false positives in architecture detection.
        
        Args:
            architecture_matches: Dict of architecture matches
            architecture_evidence: Dict of evidence for each architecture
            files: List of file paths
            files_content: Dict of file contents (optional)
        """
        # Check for specific file counts to validate architecture patterns
        
        # For MVC, check for balance between models, views, and controllers
        if "MVC" in architecture_matches:
            models_count = sum(1 for f in files if 'model' in f.lower() or '/models/' in f.lower())
            views_count = sum(1 for f in files if 'view' in f.lower() or '/views/' in f.lower())
            controllers_count = sum(1 for f in files if 'controller' in f.lower() or '/controllers/' in f.lower())
            
            # In a true MVC architecture, we should have a reasonable balance
            # between models, views, and controllers
            if models_count < 2 or views_count < 2 or controllers_count < 2:
                # If one of the components is missing or very small, reduce confidence
                architecture_matches["MVC"] = architecture_matches["MVC"] // 2
                architecture_evidence["MVC"].append(f"Imbalance in MVC components: Models ({models_count}), Views ({views_count}), Controllers ({controllers_count})")
        
        # For MVVM, check for balance between models, views, and viewmodels
        if "MVVM" in architecture_matches:
            models_count = sum(1 for f in files if 'model' in f.lower() or '/models/' in f.lower())
            views_count = sum(1 for f in files if 'view' in f.lower() or '/views/' in f.lower())
            viewmodels_count = sum(1 for f in files if 'viewmodel' in f.lower() or '/viewmodels/' in f.lower())
            
            # In a true MVVM architecture, we should have a reasonable balance
            if models_count < 2 or views_count < 2 or viewmodels_count < 2:
                architecture_matches["MVVM"] = architecture_matches["MVVM"] // 2
                architecture_evidence["MVVM"].append(f"Imbalance in MVVM components: Models ({models_count}), Views ({views_count}), ViewModels ({viewmodels_count})")
        
        # For Clean Architecture, check for proper layering
        if "Clean Architecture" in architecture_matches:
            entities_count = sum(1 for f in files if 'entity' in f.lower() or '/entities/' in f.lower() or '/domain/model' in f.lower())
            usecases_count = sum(1 for f in files if 'usecase' in f.lower() or '/usecases/' in f.lower() or '/application/' in f.lower())
            adapters_count = sum(1 for f in files if 'adapter' in f.lower() or '/adapters/' in f.lower() or '/infrastructure/' in f.lower())
            
            if entities_count < 2 or usecases_count < 2 or adapters_count < 2:
                architecture_matches["Clean Architecture"] = architecture_matches["Clean Architecture"] // 2
                architecture_evidence["Clean Architecture"].append(
                    f"Imbalance in Clean Architecture components: Entities ({entities_count}), UseCases ({usecases_count}), Adapters ({adapters_count})"
                )
        
        # For Microservices, validate with stronger evidence
        if "Microservices" in architecture_matches:
            # Strong indicators of microservices
            strong_indicators = [
                "docker-compose.yml", "docker-compose.yaml", 
                "kubernetes", "k8s", "helm", "istio",
                "api-gateway", "service-discovery", "eureka", "consul"
            ]
            
            # Check for presence of these indicators
            has_strong_indicator = any(any(ind in f for f in files) for ind in strong_indicators)
            
            # Check for multiple service directories
            service_dirs = set()
            for file_path in files:
                parts = file_path.split('/')
                if len(parts) >= 2 and (parts[0] == 'services' or parts[0] == 'microservices'):
                    service_dirs.add(parts[1])
            
            many_services = len(service_dirs) >= 3
            
            if not (has_strong_indicator or many_services):
                architecture_matches["Microservices"] = architecture_matches["Microservices"] // 2
                architecture_evidence["Microservices"].append("Limited evidence for true microservices architecture")
        
        # For Event-Driven Architecture, look for specific evidence
        if "Event-Driven Architecture" in architecture_matches:
            event_indicators = [
                "kafka", "rabbitmq", "activemq", "nats",
                "eventbus", "event-bus", "event_bus", "events"
            ]
            
            has_event_indicator = any(any(ind in f.lower() for f in files) for ind in event_indicators)
            
            if not has_event_indicator:
                architecture_matches["Event-Driven Architecture"] = architecture_matches["Event-Driven Architecture"] // 2
                architecture_evidence["Event-Driven Architecture"].append("Limited evidence for true event-driven architecture")
        
        # Enhanced detection for REST API architecture
        if "REST API" in architecture_matches:
            rest_indicators = [
                "swagger", "openapi", "endpoints", "controllers", 
                "api/v1", "api/v2", "resources"
            ]
            
            has_rest_indicator = any(any(ind in f.lower() for f in files) for ind in rest_indicators)
            
            # If there are REST indicators, boost the score
            if has_rest_indicator:
                architecture_matches["REST API"] += 10
                architecture_evidence["REST API"].append("Found strong REST API indicators")
        
        # Check for overlapping architectures and resolve conflicts
        # Some architectures are complementary, others are mutually exclusive
        
        # MVC and MVVM are generally mutually exclusive
        if "MVC" in architecture_matches and "MVVM" in architecture_matches:
            # Keep the one with the higher score
            if architecture_matches["MVC"] > architecture_matches["MVVM"]:
                architecture_matches["MVVM"] = architecture_matches["MVVM"] // 3
            else:
                architecture_matches["MVC"] = architecture_matches["MVC"] // 3
        
        # Feature-based can coexist with others, but check if it's a strong match
        if "Feature-based architecture" in architecture_matches:
            # Check if there are actual feature modules
            feature_dirs = sum(1 for f in files if '/features/' in f or '/modules/' in f)
            if feature_dirs < 5:  # Arbitrary threshold: at least 5 files in feature directories
                architecture_matches["Feature-based architecture"] = architecture_matches["Feature-based architecture"] // 2
                architecture_evidence["Feature-based architecture"].append(f"Only found {feature_dirs} files in feature directories")
    
    def detect(self, files: List[str], files_content: Dict[str, str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Detect architecture patterns used in the repository.
        
        This method examines file paths and directory structures to identify
        software architecture patterns used in the project.
        
        Args:
            files: List of file paths in the repository
            files_content: Dict mapping file paths to their content (optional)
            
        Returns:
            Dict mapping architecture pattern names to dicts containing:
                - matches: Number of pattern matches found
                - confidence: Confidence score (0-100)
                - evidence: List of evidence found
        """
        # Track matches for architecture patterns
        architecture_matches = defaultdict(int)
        architecture_evidence = defaultdict(list)
        
        # Step 1: Analyze directory structure
        directories = set()
        for file_path in files:
            # Extract all directories in the path
            path_components = file_path.split(os.sep)
            for i in range(len(path_components)):
                if i > 0:  # Skip the first component (which is empty or the repo root)
                    dir_path = os.sep.join(path_components[:i])
                    if dir_path and not dir_path.startswith("."):  # Skip hidden directories
                        directories.add(dir_path)
        
        # Check for directory pattern matches
        for architecture, pattern_sets in self.directory_patterns.items():
            for pattern_set in pattern_sets:
                # Count how many directories from the pattern exist
                matching_dirs = []
                for pattern in pattern_set:
                    matching = [d for d in directories if d.endswith(pattern) or pattern in d.split(os.sep)]
                    if matching:
                        matching_dirs.append((pattern, matching[0]))
                
                # If we found all patterns in the set, it's a strong match
                if len(matching_dirs) == len(pattern_set):
                    architecture_matches[architecture] += 20  # High weight for complete match
                    dirs_found = ", ".join([f"{pattern} ({dir})" for pattern, dir in matching_dirs])
                    architecture_evidence[architecture].append(f"Found complete directory pattern: {dirs_found}")
                # If we found most patterns in the set, it's a partial match
                elif len(matching_dirs) >= len(pattern_set) * 0.7:
                    architecture_matches[architecture] += 10  # Medium weight for partial match
                    dirs_found = ", ".join([f"{pattern} ({dir})" for pattern, dir in matching_dirs])
                    architecture_evidence[architecture].append(f"Found partial directory pattern: {dirs_found}")
                # If we found some patterns in the set, it's a weak match
                elif matching_dirs:
                    architecture_matches[architecture] += len(matching_dirs) * 2  # Lower weight for few matches
                    dirs_found = ", ".join([f"{pattern} ({dir})" for pattern, dir in matching_dirs])
                    architecture_evidence[architecture].append(f"Found some directories: {dirs_found}")
        
        # Step 2: Analyze file naming patterns
        for architecture, patterns in self.file_patterns.items():
            for pattern in patterns:
                for file_path in files:
                    filename = os.path.basename(file_path)
                    if re.search(pattern, file_path):
                        architecture_matches[architecture] += 5
                        architecture_evidence[architecture].append(f"Found file pattern: {filename}")
                        break  # Count each pattern only once
        
        # Step 3: Check for special framework-specific conventions that imply architectures
        
        # Rails follows MVC
        rails_indicators = ["app/models/", "app/controllers/", "app/views/", "config/routes.rb"]
        if any(any(ind in file_path for file_path in files) for ind in rails_indicators):
            if all(any(ind in file_path for file_path in files) for ind in rails_indicators[:3]):
                architecture_matches["MVC"] += 30
                architecture_evidence["MVC"].append("Found Ruby on Rails MVC structure")
        
        # Django follows MTV (Model-Template-View, similar to MVC)
        django_indicators = ["models.py", "views.py", "urls.py", "templates/"]
        if any(any(ind in file_path for file_path in files) for ind in django_indicators):
            if all(any(ind in file_path for file_path in files) for ind in django_indicators[:3]):
                architecture_matches["MVC"] += 30  # We classify MTV as MVC for simplicity
                architecture_evidence["MVC"].append("Found Django MTV structure")
        
        # Laravel follows MVC
        laravel_indicators = ["app/Models/", "app/Http/Controllers/", "resources/views/", "routes/web.php"]
        if any(any(ind in file_path for file_path in files) for ind in laravel_indicators):
            if all(any(ind in file_path for file_path in files) for ind in laravel_indicators[:3]):
                architecture_matches["MVC"] += 30
                architecture_evidence["MVC"].append("Found Laravel MVC structure")
        
        # Spring Boot often follows layered architecture
        spring_indicators = ["controller/", "service/", "repository/", "model/", "entity/"]
        if any(any(ind in file_path for file_path in files) for ind in spring_indicators):
            spring_layers = sum(1 for ind in spring_indicators if any(ind in file_path for file_path in files))
            if spring_layers >= 3:
                architecture_matches["Layered Architecture"] += 25
                architecture_evidence["Layered Architecture"].append("Found Spring Boot layered architecture")
        
        # Angular follows component-based architecture with MVVM influence
        angular_indicators = ["app.module.ts", "app.component.ts", "app.component.html", "app.service.ts"]
        if any(any(ind in file_path for file_path in files) for ind in angular_indicators):
            architecture_matches["MVVM"] += 20
            architecture_evidence["MVVM"].append("Found Angular MVVM-influenced structure")
        
        # React + Redux often implies Flux architecture (similar to MVVM)
        react_redux_indicators = ["reducers/", "actions/", "store.js", "App.jsx", "App.tsx"]
        if any(any(ind in file_path for file_path in files) for ind in react_redux_indicators):
            react_redux_count = sum(1 for ind in react_redux_indicators if any(ind in file_path for file_path in files))
            if react_redux_count >= 3:
                architecture_matches["MVVM"] += 20
                architecture_evidence["MVVM"].append("Found React with Redux structure")
        
        # ASP.NET MVC
        aspnet_mvc_indicators = ["Controllers/", "Views/", "Models/", "ViewModels/"]
        if any(any(ind in file_path for file_path in files) for ind in aspnet_mvc_indicators):
            aspnet_mvc_count = sum(1 for ind in aspnet_mvc_indicators if any(ind in file_path for file_path in files))
            if aspnet_mvc_count >= 3:
                architecture_matches["MVC"] += 30
                architecture_evidence["MVC"].append("Found ASP.NET MVC structure")
        
        # Microservices architecture indicators
        microservice_indicators = [
            "docker-compose.yml", "kubernetes/", "k8s/", "helm/", "service-discovery/",
            "api-gateway/", "gateway/", "eureka/", "consul/", "services/"
        ]
        microservice_count = sum(1 for ind in microservice_indicators if any(ind in file_path for file_path in files))
        if microservice_count >= 3:
            architecture_matches["Microservices"] += 25
            architecture_evidence["Microservices"].append(f"Found {microservice_count} microservice indicators")
        
        # Step 4: Analyze directory statistics for module-based architectures
        dir_counter = Counter()
        for file_path in files:
            path_parts = file_path.split(os.sep)
            for i in range(1, min(4, len(path_parts))):  # Look at first few directory levels
                if path_parts[i-1]:  # Skip empty parts
                    dir_counter[path_parts[i-1]] += 1
        
        # Feature modules pattern: many directories at the same level with similar structure
        potential_feature_dirs = []
        for dirname, count in dir_counter.items():
            # Potential feature/module directories have more than a few files
            if count > 5 and dirname not in ["src", "app", "test", "tests", "build", "dist", "node_modules"]:
                potential_feature_dirs.append(dirname)
        
        if len(potential_feature_dirs) >= 3:
            # Check if these directories have similar structure (indicating modules/features)
            similar_structure = True
            # Get the structure of the first directory
            first_dir = potential_feature_dirs[0]
            first_dir_files = [f for f in files if f.split(os.sep)[0] == first_dir]
            first_dir_extensions = Counter([os.path.splitext(f)[1] for f in first_dir_files])
            
            for feature_dir in potential_feature_dirs[1:]:
                dir_files = [f for f in files if f.split(os.sep)[0] == feature_dir]
                dir_extensions = Counter([os.path.splitext(f)[1] for f in dir_files])
                
                # Check if the extension distribution is similar
                if not any(ext in dir_extensions for ext in first_dir_extensions):
                    similar_structure = False
                    break
            
            if similar_structure:
                architecture_matches["Feature-based architecture"] += 25
                architecture_evidence["Feature-based architecture"].append(
                    f"Found {len(potential_feature_dirs)} potential feature modules: {', '.join(potential_feature_dirs[:5])}..."
                )
        
        # Step 5: Check for code patterns if files_content is provided
        if files_content:
            for file_path, content in files_content.items():
                # Skip large files
                if len(content) > 500000:  # Skip files over 500KB
                    continue
                
                # Look for code patterns in file content
                for architecture, patterns in self.code_patterns.items():
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            architecture_matches[architecture] += len(matches) * 2
                            architecture_evidence[architecture].append(
                                f"Code pattern in {os.path.basename(file_path)}: {pattern}"
                            )
        
        # Step 6: Apply additional context validation
        self._apply_context_validation(architecture_matches, architecture_evidence, files, files_content)
        
        # Step 7: Calculate confidence scores
        architectures = {}
        
        if architecture_matches:
            # Find maximum number of matches for normalization
            max_matches = max(architecture_matches.values())
            
            for arch, matches in architecture_matches.items():
                # Calculate confidence score (0-100)
                confidence = min(100, (matches / max_matches) * 100)
                
                # Only include architectures with reasonable confidence
                # Increased threshold from 20 to 35 to reduce false positives
                if confidence >= 35:
                    # Keep only unique evidence and limit to 5 examples
                    unique_evidence = list(dict.fromkeys(architecture_evidence[arch]))[:5]
                    
                    architectures[arch] = {
                        "matches": matches,
                        "confidence": round(confidence, 2),
                        "evidence": unique_evidence
                    }
        
        return architectures