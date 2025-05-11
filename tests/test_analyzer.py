#!/usr/bin/env python3
"""
Basic tests for the RepoAnalyzer library.

This module contains unit tests and integration tests for the RepoAnalyzer library.
It verifies that the key functionality works as expected.
"""

import os
import sys
import json
import unittest
import tempfile
import shutil
from typing import Dict, Any

# Import RepoAnalyzer
from repo_analyzer import RepoAnalyzer
from repo_analyzer.config import RepoAnalyzerConfig

class TestRepoAnalyzer(unittest.TestCase):
    """Test cases for the RepoAnalyzer library."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test repositories
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test repository
        self.test_repo = os.path.join(self.test_dir, "test_repo")
        os.makedirs(self.test_repo)
        
        # Create test files
        self._create_test_files()
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def _create_test_files(self):
        """Create test files for the repository."""
        # Python files
        os.makedirs(os.path.join(self.test_repo, "app"))
        with open(os.path.join(self.test_repo, "app", "main.py"), "w") as f:
            f.write("""
import flask
from flask import Flask, request, jsonify
from models import User

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

if __name__ == '__main__':
    app.run(debug=True)
""")
        
        # Create models.py
        os.makedirs(os.path.join(self.test_repo, "app", "models"))
        with open(os.path.join(self.test_repo, "app", "models", "__init__.py"), "w") as f:
            f.write("""
from .user import User
""")
            
        with open(os.path.join(self.test_repo, "app", "models", "user.py"), "w") as f:
            f.write("""
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email
        }
""")
        
        # Create requirements.txt
        with open(os.path.join(self.test_repo, "requirements.txt"), "w") as f:
            f.write("""
flask==2.0.1
sqlalchemy==1.4.23
psycopg2-binary==2.9.1
pytest==6.2.5
pylint==2.9.6
""")
        
        # Create test directory
        os.makedirs(os.path.join(self.test_repo, "tests"))
        with open(os.path.join(self.test_repo, "tests", "test_app.py"), "w") as f:
            f.write("""
import pytest
from app.main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Hello, World!' in response.data
""")
        
        # Create Dockerfile
        with open(os.path.join(self.test_repo, "Dockerfile"), "w") as f:
            f.write("""
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app/main.py"]
""")
        
        # Create docker-compose.yml
        with open(os.path.join(self.test_repo, "docker-compose.yml"), "w") as f:
            f.write("""
version: '3'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
    depends_on:
      - db
      
  db:
    image: postgres:13
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=testdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
volumes:
  postgres_data:
""")
        
        # Create .github/workflows for CI/CD
        os.makedirs(os.path.join(self.test_repo, ".github", "workflows"))
        with open(os.path.join(self.test_repo, ".github", "workflows", "ci.yml"), "w") as f:
            f.write("""
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Test with pytest
      run: |
        pytest
""")
    
    def test_repo_analyzer_initialization(self):
        """Test that RepoAnalyzer initializes properly."""
        analyzer = RepoAnalyzer(self.test_repo)
        self.assertEqual(analyzer.repo_path, os.path.abspath(self.test_repo))
    
    def test_config_initialization(self):
        """Test that RepoAnalyzerConfig initializes properly."""
        config = RepoAnalyzerConfig()
        self.assertIn("exclude_dirs", config.config)
        self.assertIn(".git", config.get_exclude_dirs())
    
    def test_repo_analysis(self):
        """Test repository analysis."""
        analyzer = RepoAnalyzer(self.test_repo)
        tech_stack = analyzer.analyze()
        
        # Check that basic categories exist
        self.assertIn("languages", tech_stack)
        self.assertIn("frameworks", tech_stack)
        self.assertIn("databases", tech_stack)
        self.assertIn("devops", tech_stack)
        self.assertIn("primary_technologies", tech_stack)
        
        # Check that Python was detected
        self.assertIn("Python", tech_stack["languages"])
        
        # Check that Flask was detected
        self.assertIn("Flask", tech_stack["frameworks"])
        
        # Check that PostgreSQL was detected
        self.assertIn("PostgreSQL", tech_stack["databases"])
        
        # Check that Docker was detected
        self.assertIn("Docker", tech_stack["devops"])
        
        # Check that GitHub Actions was detected
        self.assertIn("GitHub Actions", tech_stack["devops"])
        
        # Check that SQLAlchemy was detected
        self.assertIn("SQLAlchemy", tech_stack["frameworks"])
        
        # Check that pytest was detected
        self.assertIn("PyTest", tech_stack["testing"])
    
    def test_primary_technologies(self):
        """Test that primary technologies are correctly identified."""
        analyzer = RepoAnalyzer(self.test_repo)
        tech_stack = analyzer.analyze()
        
        primary_tech = tech_stack["primary_technologies"]
        
        # Primary language should be Python
        self.assertEqual(primary_tech["languages"], "Python")
        
        # Primary framework should be Flask
        self.assertEqual(primary_tech["frameworks"], "Flask")
        
        # Primary database should be PostgreSQL
        self.assertEqual(primary_tech["databases"], "PostgreSQL")
    
    def test_confidence_scores(self):
        """Test that confidence scores are calculated correctly."""
        analyzer = RepoAnalyzer(self.test_repo)
        tech_stack = analyzer.analyze()
        
        # Check that Python has a confidence score
        self.assertIn("confidence", tech_stack["languages"]["Python"])
        
        # Check that Flask has a confidence score
        self.assertIn("confidence", tech_stack["frameworks"]["Flask"])
        
        # Confidence scores should be between 0 and 100
        self.assertGreaterEqual(tech_stack["languages"]["Python"]["confidence"], 0)
        self.assertLessEqual(tech_stack["languages"]["Python"]["confidence"], 100)
    
    def test_metadata(self):
        """Test that metadata is correctly included."""
        analyzer = RepoAnalyzer(self.test_repo)
        tech_stack = analyzer.analyze()
        
        # Check that metadata exists
        self.assertIn("metadata", tech_stack)
        
        # Check metadata fields
        metadata = tech_stack["metadata"]
        self.assertIn("repo_path", metadata)
        self.assertIn("file_count", metadata)
        self.assertIn("analyzed_at", metadata)
        
        # Check that file count is reasonable
        self.assertGreater(metadata["file_count"], 5)

class TestRealWorld(unittest.TestCase):
    """Test cases using the RepoAnalyzer library on this repository itself."""
    
    def test_self_analysis(self):
        """Test analyzing the RepoAnalyzer repository itself."""
        # Get the path to this file
        this_file = os.path.abspath(__file__)
        
        # Get the parent directory (repository root)
        repo_path = os.path.dirname(os.path.dirname(this_file))
        
        # Skip if not running from the repository
        if not os.path.isdir(os.path.join(repo_path, "repo_analyzer")):
            self.skipTest("Not running from the repository")
        
        # Analyze the repository
        analyzer = RepoAnalyzer(repo_path)
        tech_stack = analyzer.analyze()
        
        # Check that Python was detected
        self.assertIn("Python", tech_stack["languages"])
        
        # Check that the primary language is Python
        self.assertEqual(tech_stack["primary_technologies"]["languages"], "Python")

if __name__ == "__main__":
    unittest.main()