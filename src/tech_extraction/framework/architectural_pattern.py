"""
Architectural Pattern Recognition for the Technology Extraction System.

This module provides functionality for detecting architectural patterns
in codebases, such as MVC, microservices, and database integration patterns.
"""
import json
import logging
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from tech_extraction.models.architecture import (
    ArchitecturalPattern,
    ArchitectureType,
    DatabaseIntegration,
    ApiPattern,
)
from tech_extraction.models.file import FileInfo
from tech_extraction.models.framework import PatternMatch

logger = logging.getLogger(__name__)


class ArchitecturalPatternRecognition:
    """
    System for recognizing architectural patterns in codebases.
    
    The ArchitecturalPatternRecognition performs the following operations:
    1. Detect design patterns like MVC, MVVM, microservices
    2. Identify database integration patterns and ORM usage
    3. Recognize API pattern implementations (REST, GraphQL, etc.)
    """
    
    # Patterns for directory structures
    DIRECTORY_PATTERNS = {
        "mvc": [
            (r"controllers?/?$", "Controller directory"),
            (r"views?/?$", "View directory"),
            (r"models?/?$", "Model directory"),
        ],
        "mvvm": [
            (r"models?/?$", "Model directory"),
            (r"views?/?$", "View directory"),
            (r"viewmodels?/?$", "ViewModel directory"),
        ],
        "microservices": [
            (r"services?/?$", "Services directory"),
            (r"api-gateway/?$", "API Gateway"),
            (r"(?:micro)?services?/[^/]+/?$", "Individual service"),
        ],
        "serverless": [
            (r"functions?/?$", "Functions directory"),
            (r"lambdas?/?$", "Lambda functions"),
            (r"handlers?/?$", "Event handlers"),
        ],
    }
    
    # File naming patterns for architectural components
    FILE_PATTERNS = {
        "mvc": [
            (r".*controller\.(?:py|rb|php|java|js|ts|cs)$", "Controller file"),
            (r".*model\.(?:py|rb|php|java|js|ts|cs)$", "Model file"),
            (r".*view\.(?:py|rb|php|java|js|ts|cs)$", "View file"),
        ],
        "mvvm": [
            (r".*model\.(?:py|rb|php|java|js|ts|cs)$", "Model file"),
            (r".*view\.(?:py|rb|php|java|js|ts|cs)$", "View file"),
            (r".*viewmodel\.(?:py|rb|php|java|js|ts|cs)$", "ViewModel file"),
        ],
        "repository_pattern": [
            (r".*repository\.(?:py|rb|php|java|js|ts|cs)$", "Repository file"),
            (r".*repo\.(?:py|rb|php|java|js|ts|cs)$", "Repository file"),
        ],
        "service_layer": [
            (r".*service\.(?:py|rb|php|java|js|ts|cs)$", "Service file"),
        ],
    }
    
    # Database ORM patterns
    ORM_PATTERNS = {
        "sqlalchemy": [
            (r"from\s+sqlalchemy(?:\.\w+)?\s+import", "SQLAlchemy import"),
            (r"class\s+\w+\s*\(\s*(?:Base|db\.Model)\s*\)", "SQLAlchemy model"),
            (r"(?:Column|db\.Column)\s*\(", "SQLAlchemy column"),
        ],
        "django_orm": [
            (r"from\s+django\.db\s+import\s+models", "Django models import"),
            (r"class\s+\w+\s*\(\s*models\.Model\s*\)", "Django model class"),
            (r"models\.\w+Field\s*\(", "Django model field"),
        ],
        "sequelize": [
            (r"(?:const|let|var)\s+\w+\s*=\s*sequelize\.define\s*\(", "Sequelize model definition"),
            (r"(?:const|let|var)\s+\w+\s*=\s*DataTypes", "Sequelize DataTypes"),
            (r"(?:const|let|var)\s+\w+\s*=\s*\w+\.belongsTo\s*\(", "Sequelize relationship"),
        ],
        "hibernate": [
            (r"@Entity", "Hibernate entity annotation"),
            (r"@Table\s*\(\s*name\s*=", "Hibernate table annotation"),
            (r"@Column\s*\(", "Hibernate column annotation"),
        ],
        "active_record": [
            (r"class\s+\w+\s*<\s*ApplicationRecord", "ActiveRecord model"),
            (r"class\s+\w+\s*<\s*ActiveRecord::Base", "ActiveRecord model"),
            (r"has_many\s+:", "ActiveRecord relationship"),
            (r"belongs_to\s+:", "ActiveRecord relationship"),
        ],
        "mongoose": [
            (r"(?:const|let|var)\s+\w+Schema\s*=\s*new\s+(?:mongoose\.)?Schema", "Mongoose schema"),
            (r"mongoose\.model\s*\(", "Mongoose model"),
        ],
        "typeorm": [
            (r"@Entity\s*\(", "TypeORM entity decorator"),
            (r"@Column\s*\(", "TypeORM column decorator"),
            (r"@OneToMany\s*\(", "TypeORM relationship decorator"),
        ],
        "entity_framework": [
            (r"class\s+\w+\s*:\s*DbContext", "Entity Framework DbContext"),
            (r"DbSet<\w+>\s+\w+\s*{\s*get;\s*set;\s*}", "Entity Framework DbSet"),
        ],
    }
    
    # Query builder patterns
    QUERY_BUILDER_PATTERNS = {
        "knex": [
            (r"knex\s*\(", "Knex query builder"),
            (r"knex\.\w+\s*\(", "Knex table query"),
            (r"\.where\s*\(", "Knex where clause"),
        ],
        "jooq": [
            (r"create\.select", "JOOQ query"),
            (r"dsl\.\w+\s*\(", "JOOQ DSL"),
        ],
        "ecto": [
            (r"Ecto\.Query", "Ecto query"),
            (r"from\s+\w+\s+in\s+\w+", "Ecto query expression"),
        ],
        "prisma": [
            (r"prisma\.\w+\.\(?:find|create|update|delete)", "Prisma client operation"),
        ],
    }
    
    # Raw SQL patterns
    SQL_PATTERNS = {
        "raw_sql": [
            (r"(?:SELECT|INSERT|UPDATE|DELETE)\s+.+?\s+(?:FROM|INTO|SET)\s+\w+", "SQL query"),
            (r"execute\s*\(\s*[\"'](?:SELECT|INSERT|UPDATE|DELETE)", "SQL execution"),
            (r"query\s*\(\s*[\"'](?:SELECT|INSERT|UPDATE|DELETE)", "SQL query execution"),
            (r"executeQuery\s*\(\s*[\"'](?:SELECT|INSERT|UPDATE|DELETE)", "JDBC query execution"),
        ],
    }
    
    # API patterns
    REST_API_PATTERNS = {
        "rest_api": [
            (r"@(?:Get|Post|Put|Delete|Patch)Mapping", "Spring REST mapping"),
            (r"@RestController", "Spring REST controller"),
            (r"app\.(get|post|put|delete|patch)\s*\(\s*['\"][^'\"]*['\"]", "Express route handler"),
            (r"@app\.(?:get|post|put|delete|patch)\s*\(\s*['\"][^'\"]*['\"]", "Flask route handler"),
            (r"router\.(?:get|post|put|delete|patch)\s*\(\s*['\"][^'\"]*['\"]", "Router method"),
            (r"@router\.(?:get|post|put|delete|patch)\s*\(\s*['\"][^'\"]*['\"]", "FastAPI route"),
            (r"class\s+\w+ViewSet\s*\(", "Django REST viewset"),
            (r"class\s+\w+APIView\s*\(", "Django REST API view"),
            (r"resources\s+:[a-zA-Z0-9_]+\s+do", "Rails API resources"),
        ],
    }
    
    GRAPHQL_API_PATTERNS = {
        "graphql_api": [
            (r"type\s+\w+\s*{", "GraphQL type definition"),
            (r"input\s+\w+\s*{", "GraphQL input type"),
            (r"interface\s+\w+\s*{", "GraphQL interface"),
            (r"Query\s*:\s*{", "GraphQL query resolvers"),
            (r"Mutation\s*:\s*{", "GraphQL mutation resolvers"),
            (r"(?:const|let|var)\s+\w+\s*=\s*(?:gql|graphql)`", "GraphQL query template"),
            (r"(?:new\s+ApolloServer|ApolloServer\s*\(\s*\{)", "Apollo server"),
            (r"class\s+\w+\s*\(\s*ObjectType\s*\)", "Graphene type"),
        ],
    }
    
    RPC_API_PATTERNS = {
        "grpc_api": [
            (r"syntax\s*=\s*[\"']proto[23][\"']", "Protocol buffer definition"),
            (r"service\s+\w+\s*{", "gRPC service definition"),
            (r"rpc\s+\w+\s*\(\s*\w+\s*\)\s*returns\s*\(\s*\w+\s*\)", "gRPC method definition"),
            (r"(?:const|let|var)\s+\w+\s*=\s*grpc\.loadPackageDefinition", "gRPC package loading"),
            (r"(?:new\s+\w+Client|grpc\.(?:unary|serverStreaming|clientStreaming|bidiStreaming))", "gRPC client instantiation"),
        ],
        "json_rpc": [
            (r"jsonrpc[\"']\s*:\s*[\"']2\.0[\"']", "JSON-RPC 2.0 format"),
            (r"method[\"']\s*:\s*[\"']\w+[\"']", "JSON-RPC method"),
            (r"params[\"']\s*:", "JSON-RPC params"),
        ],
    }
    
    def __init__(self, root_path: Path):
        """
        Initialize the architectural pattern recognition system.
        
        Args:
            root_path: Path to the root of the codebase
        """
        self.root_path = Path(root_path)
        
        # Collected evidence
        self.directory_evidence = {}
        self.file_pattern_evidence = {}
        self.content_pattern_evidence = defaultdict(list)
        
        # Detected patterns
        self.detected_architectures = []
        self.detected_db_integrations = []
        self.detected_api_patterns = []
    
    def analyze_directory_structure(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        Analyze the directory structure for architectural patterns.
        
        Returns:
            Dictionary mapping pattern types to lists of (path, description) tuples
        """
        logger.info(f"Analyzing directory structure at {self.root_path}")
        
        evidence = defaultdict(list)
        
        # Walk directory tree
        for root, dirs, files in os.walk(self.root_path):
            rel_path = Path(root).relative_to(self.root_path)
            path_str = str(rel_path)
            
            # Check each pattern set
            for pattern_type, patterns in self.DIRECTORY_PATTERNS.items():
                for pattern, description in patterns:
                    if re.search(pattern, path_str, re.IGNORECASE):
                        evidence[pattern_type].append((path_str, description))
        
        self.directory_evidence = dict(evidence)
        return self.directory_evidence
    
    def analyze_file_patterns(self, files: List[FileInfo]) -> Dict[str, List[Tuple[str, str]]]:
        """
        Analyze file patterns for architectural components.
        
        Args:
            files: List of files to analyze
            
        Returns:
            Dictionary mapping pattern types to lists of (path, description) tuples
        """
        logger.info(f"Analyzing file patterns for {len(files)} files")
        
        evidence = defaultdict(list)
        
        for file_info in files:
            file_path = file_info.path
            
            # Check each pattern set
            for pattern_type, patterns in self.FILE_PATTERNS.items():
                for pattern, description in patterns:
                    if re.search(pattern, file_path, re.IGNORECASE):
                        evidence[pattern_type].append((file_path, description))
        
        self.file_pattern_evidence = dict(evidence)
        return self.file_pattern_evidence
    
    def analyze_content_patterns(self, files: List[FileInfo]) -> Dict[str, List[Dict]]:
        """
        Analyze file contents for ORM, query builder, and API patterns.
        
        Args:
            files: List of files to analyze
            
        Returns:
            Dictionary mapping pattern types to lists of evidence
        """
        logger.info(f"Analyzing content patterns for {len(files)} files")
        
        # Combine all pattern sets
        all_patterns = {}
        all_patterns.update(self.ORM_PATTERNS)
        all_patterns.update(self.QUERY_BUILDER_PATTERNS)
        all_patterns.update(self.SQL_PATTERNS)
        all_patterns.update(self.REST_API_PATTERNS)
        all_patterns.update(self.GRAPHQL_API_PATTERNS)
        all_patterns.update(self.RPC_API_PATTERNS)
        
        for file_info in files:
            try:
                with open(file_info.full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Check each pattern set
                for pattern_type, patterns in all_patterns.items():
                    for pattern, description in patterns:
                        for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                            # Get line number
                            line_number = content[:match.start()].count('\n') + 1
                            
                            # Get context (line containing the match)
                            line_start = content.rfind('\n', 0, match.start()) + 1
                            line_end = content.find('\n', match.start())
                            if line_end == -1:
                                line_end = len(content)
                            
                            line_content = content[line_start:line_end].strip()
                            
                            self.content_pattern_evidence[pattern_type].append({
                                "file_path": file_info.path,
                                "line_number": line_number,
                                "line_content": line_content,
                                "description": description,
                            })
            
            except Exception as e:
                logger.warning(f"Error analyzing file content for {file_info.path}: {e}")
        
        return dict(self.content_pattern_evidence)
    
    def _evidence_to_confidence(self, evidence_count: int, is_strong: bool = False) -> float:
        """
        Convert evidence count to a confidence score.
        
        Args:
            evidence_count: Number of evidence items
            is_strong: Whether this is strong evidence
            
        Returns:
            Confidence score (0-100)
        """
        if evidence_count == 0:
            return 0
        
        # Base confidence
        base_confidence = 30 if is_strong else 20
        
        # Evidence scaling factor
        evidence_factor = min(1.0, (evidence_count / 5) if is_strong else (evidence_count / 10))
        
        # Calculate confidence
        confidence = base_confidence + (evidence_factor * (70 if is_strong else 50))
        
        return min(confidence, 100)
    
    def detect_architectural_patterns(self) -> List[ArchitecturalPattern]:
        """
        Detect architectural patterns based on collected evidence.
        
        Returns:
            List of detected architectural patterns
        """
        patterns = []
        
        # MVC Pattern
        mvc_dir_evidence = self.directory_evidence.get("mvc", [])
        mvc_file_evidence = self.file_pattern_evidence.get("mvc", [])
        
        # Check if we have significant MVC evidence
        if len(mvc_dir_evidence) >= 2 or len(mvc_file_evidence) >= 3:
            # Calculate confidence based on evidence
            confidence = self._evidence_to_confidence(
                len(mvc_dir_evidence) * 2 + len(mvc_file_evidence),
                is_strong=True
            )
            
            patterns.append(
                ArchitecturalPattern(
                    name="Model-View-Controller (MVC)",
                    type=ArchitectureType.DESIGN_PATTERN,
                    confidence=confidence,
                    evidence={
                        "directory_structure": mvc_dir_evidence,
                        "file_patterns": mvc_file_evidence,
                    }
                )
            )
        
        # MVVM Pattern
        mvvm_dir_evidence = self.directory_evidence.get("mvvm", [])
        mvvm_file_evidence = self.file_pattern_evidence.get("mvvm", [])
        
        if len(mvvm_dir_evidence) >= 2 or len(mvvm_file_evidence) >= 3:
            confidence = self._evidence_to_confidence(
                len(mvvm_dir_evidence) * 2 + len(mvvm_file_evidence),
                is_strong=True
            )
            
            patterns.append(
                ArchitecturalPattern(
                    name="Model-View-ViewModel (MVVM)",
                    type=ArchitectureType.DESIGN_PATTERN,
                    confidence=confidence,
                    evidence={
                        "directory_structure": mvvm_dir_evidence,
                        "file_patterns": mvvm_file_evidence,
                    }
                )
            )
        
        # Microservices Architecture
        microservices_evidence = self.directory_evidence.get("microservices", [])
        
        if len(microservices_evidence) >= 2:
            confidence = self._evidence_to_confidence(
                len(microservices_evidence) * 3,
                is_strong=True
            )
            
            patterns.append(
                ArchitecturalPattern(
                    name="Microservices Architecture",
                    type=ArchitectureType.SYSTEM_ARCHITECTURE,
                    confidence=confidence,
                    evidence={
                        "directory_structure": microservices_evidence,
                    }
                )
            )
        
        # Serverless Architecture
        serverless_evidence = self.directory_evidence.get("serverless", [])
        
        if len(serverless_evidence) >= 1:
            confidence = self._evidence_to_confidence(
                len(serverless_evidence) * 3,
                is_strong=True
            )
            
            patterns.append(
                ArchitecturalPattern(
                    name="Serverless Architecture",
                    type=ArchitectureType.SYSTEM_ARCHITECTURE,
                    confidence=confidence,
                    evidence={
                        "directory_structure": serverless_evidence,
                    }
                )
            )
        
        # Repository Pattern
        repo_evidence = self.file_pattern_evidence.get("repository_pattern", [])
        
        if len(repo_evidence) >= 2:
            confidence = self._evidence_to_confidence(len(repo_evidence), is_strong=False)
            
            patterns.append(
                ArchitecturalPattern(
                    name="Repository Pattern",
                    type=ArchitectureType.DESIGN_PATTERN,
                    confidence=confidence,
                    evidence={
                        "file_patterns": repo_evidence,
                    }
                )
            )
        
        # Service Layer
        service_evidence = self.file_pattern_evidence.get("service_layer", [])
        
        if len(service_evidence) >= 2:
            confidence = self._evidence_to_confidence(len(service_evidence), is_strong=False)
            
            patterns.append(
                ArchitecturalPattern(
                    name="Service Layer",
                    type=ArchitectureType.DESIGN_PATTERN,
                    confidence=confidence,
                    evidence={
                        "file_patterns": service_evidence,
                    }
                )
            )
        
        self.detected_architectures = patterns
        return patterns
    
    def detect_database_integrations(self) -> List[DatabaseIntegration]:
        """
        Detect database integration patterns.
        
        Returns:
            List of detected database integrations
        """
        integrations = []
        
        # ORM integrations
        for orm_name, evidence_list in self.content_pattern_evidence.items():
            # Filter to only ORM patterns
            if orm_name not in self.ORM_PATTERNS:
                continue
            
            if evidence_list:
                # Calculate confidence based on evidence
                confidence = self._evidence_to_confidence(len(evidence_list), is_strong=True)
                
                integrations.append(
                    DatabaseIntegration(
                        name=orm_name.replace('_', ' ').title(),
                        type="ORM",
                        confidence=confidence,
                        evidence=evidence_list[:10]  # Limit to 10 examples
                    )
                )
        
        # Query builder integrations
        for builder_name, evidence_list in self.content_pattern_evidence.items():
            # Filter to only query builder patterns
            if builder_name not in self.QUERY_BUILDER_PATTERNS:
                continue
            
            if evidence_list:
                confidence = self._evidence_to_confidence(len(evidence_list), is_strong=False)
                
                integrations.append(
                    DatabaseIntegration(
                        name=builder_name.replace('_', ' ').title(),
                        type="Query Builder",
                        confidence=confidence,
                        evidence=evidence_list[:10]
                    )
                )
        
        # Raw SQL usage
        raw_sql_evidence = self.content_pattern_evidence.get("raw_sql", [])
        if raw_sql_evidence:
            confidence = self._evidence_to_confidence(len(raw_sql_evidence), is_strong=False)
            
            integrations.append(
                DatabaseIntegration(
                    name="Raw SQL",
                    type="Direct SQL",
                    confidence=confidence,
                    evidence=raw_sql_evidence[:10]
                )
            )
        
        self.detected_db_integrations = integrations
        return integrations
    
    def detect_api_patterns(self) -> List[ApiPattern]:
        """
        Detect API implementation patterns.
        
        Returns:
            List of detected API patterns
        """
        api_patterns = []
        
        # REST API
        rest_evidence = self.content_pattern_evidence.get("rest_api", [])
        if rest_evidence:
            confidence = self._evidence_to_confidence(len(rest_evidence), is_strong=True)
            
            api_patterns.append(
                ApiPattern(
                    name="REST API",
                    confidence=confidence,
                    evidence=rest_evidence[:10]
                )
            )
        
        # GraphQL API
        graphql_evidence = self.content_pattern_evidence.get("graphql_api", [])
        if graphql_evidence:
            confidence = self._evidence_to_confidence(len(graphql_evidence), is_strong=True)
            
            api_patterns.append(
                ApiPattern(
                    name="GraphQL API",
                    confidence=confidence,
                    evidence=graphql_evidence[:10]
                )
            )
        
        # gRPC API
        grpc_evidence = self.content_pattern_evidence.get("grpc_api", [])
        if grpc_evidence:
            confidence = self._evidence_to_confidence(len(grpc_evidence), is_strong=True)
            
            api_patterns.append(
                ApiPattern(
                    name="gRPC API",
                    confidence=confidence,
                    evidence=grpc_evidence[:10]
                )
            )
        
        # JSON-RPC API
        jsonrpc_evidence = self.content_pattern_evidence.get("json_rpc", [])
        if jsonrpc_evidence:
            confidence = self._evidence_to_confidence(len(jsonrpc_evidence), is_strong=False)
            
            api_patterns.append(
                ApiPattern(
                    name="JSON-RPC API",
                    confidence=confidence,
                    evidence=jsonrpc_evidence[:10]
                )
            )
        
        self.detected_api_patterns = api_patterns
        return api_patterns
    
    def analyze(self, files: List[FileInfo]) -> Dict:
        """
        Perform full architectural analysis.
        
        Args:
            files: List of files to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        logger.info("Starting architectural pattern analysis")
        
        # Analyze directory structure
        self.analyze_directory_structure()
        
        # Analyze file patterns
        self.analyze_file_patterns(files)
        
        # Analyze content patterns
        self.analyze_content_patterns(files)
        
        # Detect patterns
        architectures = self.detect_architectural_patterns()
        db_integrations = self.detect_database_integrations()
        api_patterns = self.detect_api_patterns()
        
        logger.info(f"Detected {len(architectures)} architectural patterns, "
                   f"{len(db_integrations)} database integrations, "
                   f"and {len(api_patterns)} API patterns")
        
        return {
            "architectural_patterns": architectures,
            "database_integrations": db_integrations,
            "api_patterns": api_patterns,
        }