"""
Framework Detector module for identifying frameworks used in a repository.

This module analyzes file names, directory structures, and file contents
to detect frameworks used in a code repository. It examines both filename
patterns and code patterns to identify frameworks with confidence scores.
"""

import os
import re
from collections import defaultdict
from typing import Dict, List, Any, Tuple

class FrameworkDetector:
    """
    Detector for frameworks used in a repository.
    
    This class analyzes file names, directory structures, and file contents
    to identify frameworks used in the repository. It looks for framework-specific
    files, directory patterns, and code patterns.
    """
    
    def __init__(self):
        """Initialize the Framework Detector with framework detection patterns."""
        # Framework detection patterns
        # Each framework has a list of patterns that might indicate its presence
        # Patterns can be filenames, directory names, or code patterns
        self.framework_patterns = {
            # Python frameworks
            "Django": [
                "django", "settings.py", "wsgi.py", "asgi.py", 
                "urls.py", "manage.py", "django.contrib", 
                "from django", "import django"
            ],
            "Flask": [
                "flask", "Flask(__name__", "app = Flask", 
                "from flask import", "import flask"
            ],
            "FastAPI": [
                "fastapi", "from fastapi import", "FastAPI(", 
                "app = FastAPI", "import fastapi"
            ],
            "Pyramid": [
                "pyramid", "from pyramid", "import pyramid",
                "config.add_route", "config.add_view"
            ],
            "Tornado": [
                "tornado", "tornado.web", "tornado.ioloop",
                "class MainHandler(tornado.web.RequestHandler)",
                "from tornado import"
            ],
            "SQLAlchemy": [
                "sqlalchemy", "from sqlalchemy import", "import sqlalchemy",
                "Base = declarative_base()", "Column(", "relationship("
            ],
            "Celery": [
                "celery", "from celery import", "import celery",
                "@app.task", "@shared_task", "celery.contrib"
            ],
            
            # JavaScript/TypeScript frameworks
            "React": [
                "react", "import React", "from 'react'", 
                "from \"react\"", "React.Component", "useState", 
                "useEffect", "jsx", "tsx"
            ],
            "Vue.js": [
                "vue", "import Vue", "new Vue", "createApp", 
                "<template>", "vue-router", ".vue"
            ],
            "Angular": [
                "angular", "@angular/core", "Component({", 
                "NgModule", "app.module.ts", "angular.module",
                "@Component", "@Injectable"
            ],
            "Next.js": [
                "next", "import next", "next.config.js", 
                "getStaticProps", "getServerSideProps",
                "pages/", "_app.js", "_document.js"
            ],
            "Express": [
                "express", "app.get(", "app.post(", "app.use(", 
                "express.Router()", "app.listen(", "import express",
                "require('express')", "require(\"express\")"
            ],
            "NestJS": [
                "nestjs", "@nestjs", "@Controller", "@Injectable", 
                "nest-cli.json", "@Module", "@Resolver"
            ],
            "Svelte": [
                "svelte", ".svelte", "onMount", "onDestroy",
                "svelte.config.js", "import { onMount }"
            ],
            "jQuery": [
                "jquery", "$.", "jQuery", "$(document).ready",
                "$.ajax", "$('#", "require('jquery')"
            ],
            
            # Java frameworks
            "Spring": [
                "spring", "springframework", "@Service", 
                "@Controller", "@RestController", "@Repository", 
                "@SpringBootApplication", "@Autowired"
            ],
            "Quarkus": [
                "quarkus", "io.quarkus", "@QuarkusTest",
                "application.properties", "@ConfigProperty"
            ],
            "Micronaut": [
                "micronaut", "io.micronaut", "@Controller",
                "@Inject", "@Client", "application.yml"
            ],
            "Jakarta EE": [
                "jakarta", "javax.servlet", "@WebServlet",
                "@EJB", "@Entity", "persistence.xml"
            ],
            
            # Go frameworks
            "Gin": [
                "gin-gonic/gin", "gin.Engine", "gin.Context",
                "gin.Default()", "r := gin."
            ],
            "Echo": [
                "labstack/echo", "echo.New()", "echo.Context",
                "e := echo.", "e.GET(", "e.POST("
            ],
            "Fiber": [
                "gofiber/fiber", "fiber.New()", "fiber.App",
                "app := fiber.", "app.Get(", "app.Post("
            ],
            "Gorilla": [
                "gorilla/mux", "gorilla/websocket", "mux.NewRouter()",
                "r := mux.", "r.HandleFunc("
            ],
            
            # Ruby frameworks
            "Rails": [
                "rails", "config/routes.rb", "ActiveRecord", 
                "gemfile", "gem 'rails'", "app/controllers/",
                "app/models/", "app/views/"
            ],
            "Sinatra": [
                "sinatra", "require 'sinatra'", "get '/'",
                "post '/'", "Sinatra::Base"
            ],
            
            # PHP frameworks
            "Laravel": [
                "laravel", "artisan", "Illuminate\\",
                "app/Http/Controllers/", "composer.json",
                "routes/web.php", "public/index.php"
            ],
            "Symfony": [
                "symfony", "symfony.lock", "bin/console",
                "Symfony\\Component", "Symfony\\Bundle",
                "config/services.yaml"
            ],
            "CodeIgniter": [
                "codeigniter", "system/core/CodeIgniter.php",
                "application/controllers/", "application/models/"
            ],
            
            # .NET frameworks
            "ASP.NET": [
                "aspnet", "Microsoft.AspNetCore", "IActionResult", 
                "Controller", ".csproj", ".sln", "Startup.cs",
                "Program.cs", "appsettings.json"
            ],
            "Blazor": [
                "blazor", "@page", "Microsoft.AspNetCore.Components",
                "_Imports.razor", "App.razor", "@code"
            ],
            "Entity Framework": [
                "EntityFramework", "Microsoft.EntityFrameworkCore",
                "DbContext", "OnModelCreating", "DbSet<"
            ],
            
            # Frontend frameworks
            "Electron": [
                "electron", "main.js", "preload.js", "renderer.js",
                "app.whenReady()", "BrowserWindow", "electron-builder"
            ],
            
            # Mobile frameworks
            "React Native": [
                "react-native", "import { View, Text } from 'react-native'",
                "AppRegistry", "StyleSheet", "expo"
            ],
            "Flutter": [
                "flutter", "pubspec.yaml", "dart", "Widget build",
                "MaterialApp", "StatelessWidget", "StatefulWidget"
            ],
            
            # Data science/ML frameworks
            "TensorFlow": [
                "tensorflow", "import tensorflow as tf", "tf.",
                "keras", "tf.keras", "tensorflow.keras"
            ],
            "PyTorch": [
                "pytorch", "torch", "import torch", "nn.Module",
                "torch.nn", "torch.optim"
            ],
            "Pandas": [
                "pandas", "import pandas as pd", "pd.DataFrame",
                "pd.read_csv", "pd.Series"
            ],
            "NumPy": [
                "numpy", "import numpy as np", "np.array",
                "np.zeros", "np.ones"
            ],
            
            # Cloud/serverless frameworks
            "AWS CDK": [
                "aws-cdk", "cdk.Stack", "cdk.Construct",
                "cdk.app", "cdk.json", "@aws-cdk"
            ],
            "Serverless Framework": [
                "serverless.yml", "serverless.yaml", 
                "serverless framework", "sls deploy"
            ],
            "Pulumi": [
                "pulumi", "Pulumi.yaml", "pulumi.Config",
                "pulumi up", "import * as pulumi"
            ]
        }
    
    def detect(self, files: List[str], files_content: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """
        Detect frameworks used in the repository.
        
        This method examines file names, paths, and contents to identify frameworks
        used in the repository and calculates confidence scores based on the number
        and strength of pattern matches.
        
        Args:
            files: List of file paths in the repository
            files_content: Dict mapping file paths to their content
            
        Returns:
            Dict mapping framework names to dicts containing:
                - matches: Number of pattern matches found
                - confidence: Confidence score (0-100)
        """
        # Track matches for each framework
        framework_matches = defaultdict(int)
        
        # Step 1: Check file paths for framework-specific files and directories
        for file_path in files:
            filename = os.path.basename(file_path)
            
            for framework, patterns in self.framework_patterns.items():
                for pattern in patterns:
                    # Check if pattern is in filename (exact match)
                    if pattern == filename:
                        framework_matches[framework] += 10  # High weight for exact filename match
                    # Check if pattern is in filename (partial match)
                    elif pattern in filename:
                        framework_matches[framework] += 5  # Medium weight for partial filename match
                    # Check if pattern is in file path
                    elif pattern in file_path:
                        framework_matches[framework] += 2  # Lower weight for path match
        
        # Step 2: Check file content for framework patterns
        for file_path, content in files_content.items():
            # Skip checking large files for performance reasons
            if len(content) > 500000:  # Skip files larger than 500KB
                continue
                
            # Extract file extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            for framework, patterns in self.framework_patterns.items():
                for pattern in patterns:
                    # Skip very short patterns (< 4 chars) for content search to reduce false positives
                    if len(pattern) < 4:
                        continue
                        
                    # Check if pattern is in file content
                    if pattern in content:
                        # Count multiple occurrences
                        occurrences = content.count(pattern)
                        
                        # Additional weight for patterns that look like imports or includes
                        if (("import " + pattern) in content or 
                            ("require(" + pattern) in content or 
                            ("include " + pattern) in content):
                            framework_matches[framework] += occurrences * 2
                        else:
                            framework_matches[framework] += occurrences
        
        # Calculate confidence scores and prepare results
        frameworks = {}
        
        if framework_matches:
            # Find the maximum number of matches to normalize scores
            max_matches = max(framework_matches.values())
            
            for framework, matches in framework_matches.items():
                # Calculate confidence score (0-100)
                # Higher match count relative to max matches means higher confidence
                confidence = min(100, (matches / max_matches) * 100)
                
                # Only include frameworks with reasonable confidence
                if confidence >= 10:
                    frameworks[framework] = {
                        "matches": matches,
                        "confidence": round(confidence, 2)
                    }
        
        return frameworks