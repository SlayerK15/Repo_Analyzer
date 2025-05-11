"""
Test cases for AI-enhanced detectors in RepoAnalyzer.

This module contains tests for the AI integration and AI-enhanced detectors in 
the RepoAnalyzer library, including tests with mocked API responses to ensure
functionality without requiring actual API credentials.
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from repo_analyzer.ai.ai_integration import AIIntegration
from repo_analyzer.ai.ai_detector import AIDetector

# Sample code for testing
PYTHON_CODE_SAMPLE = """
import flask
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    result = []
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
        result.append(user_data)
    return jsonify(result)

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    user = User(username=data['username'], email=data['email'])
    db.session.add(user)
    db.session.commit()
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email
    }), 201

if __name__ == '__main__':
    app.run(debug=True)
"""

JS_CODE_SAMPLE = """
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function UserList() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await axios.get('/api/users');
        setUsers(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch users');
        setLoading(false);
      }
    };
    
    fetchUsers();
  }, []);
  
  const handleAddUser = async (user) => {
    try {
      const response = await axios.post('/api/users', user);
      setUsers([...users, response.data]);
    } catch (err) {
      setError('Failed to add user');
    }
  };
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div className="user-list">
      <h2>Users</h2>
      <ul>
        {users.map(user => (
          <li key={user.id}>{user.username} - {user.email}</li>
        ))}
      </ul>
    </div>
  );
}

export default UserList;
"""

# Mock API responses
MOCK_FRAMEWORK_DETECTION_RESPONSE = {
    "technologies": [
        {
            "name": "Flask",
            "category": "framework",
            "confidence": 95,
            "evidence": ["Import statement 'import flask'", "Flask app initialization 'app = Flask(__name__)'"]
        },
        {
            "name": "SQLAlchemy",
            "category": "library",
            "confidence": 90,
            "evidence": ["Import 'from flask_sqlalchemy import SQLAlchemy'", "Database model definition"]
        },
        {
            "name": "SQLite",
            "category": "database",
            "confidence": 85,
            "evidence": ["Connection string 'sqlite:///test.db'"]
        }
    ],
    "suggestions": [
        {
            "text": "Consider adding request validation to ensure data integrity",
            "severity": "medium",
            "reason": "Missing validation in create_user route"
        }
    ],
    "success": True,
    "model": "gpt-4",
    "enabled": True,
    "provider": "openai"
}

MOCK_ARCHITECTURE_DETECTION_RESPONSE = {
    "patterns": [
        {
            "name": "MVC",
            "type": "architecture",
            "confidence": 80,
            "evidence": ["Model defined with User class", "Controller logic in route handlers"]
        },
        {
            "name": "REST API",
            "type": "architecture",
            "confidence": 90,
            "evidence": ["RESTful route definitions", "JSON responses", "HTTP methods usage"]
        }
    ],
    "suggestions": [
        {
            "text": "Consider separating routes into a dedicated module",
            "severity": "low",
            "reason": "Better code organization"
        }
    ],
    "success": True,
    "model": "gpt-4",
    "enabled": True,
    "provider": "openai"
}

MOCK_CODE_QUALITY_RESPONSE = {
    "quality_assessment": {
        "readability": {
            "score": 85,
            "strengths": ["Clear function names", "Consistent indentation"],
            "weaknesses": ["Limited comments"]
        },
        "maintainability": {
            "score": 75,
            "strengths": ["Modular design", "Clear separation of concerns"],
            "weaknesses": ["Hardcoded database URI", "No error handling"]
        },
        "performance": {
            "score": 80,
            "strengths": ["Efficient SQLAlchemy queries"],
            "weaknesses": ["Loading all users at once could be inefficient with large datasets"]
        }
    },
    "issues": [
        {
            "type": "security",
            "severity": "high",
            "description": "No input validation on user data",
            "location": "create_user function"
        },
        {
            "type": "code-smell",
            "severity": "medium",
            "description": "Hardcoded database URI",
            "location": "app configuration"
        }
    ],
    "suggestions": [
        {
            "text": "Add input validation for user data",
            "severity": "high",
            "reason": "Security vulnerability"
        },
        {
            "text": "Use environment variables for database configuration",
            "severity": "medium",
            "reason": "Better security and configuration management"
        }
    ],
    "success": True,
    "model": "gpt-4",
    "enabled": True,
    "provider": "openai"
}


class TestAIIntegration(unittest.TestCase):
    """Test cases for the AIIntegration class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary config for testing
        self.test_config = {
            "enabled": True,
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.1,
            "cache_enabled": False  # Disable caching for tests
        }
        
        # Create AIIntegration instance
        self.ai = AIIntegration(self.test_config)
    
    @patch('repo_analyzer.ai.ai_integration.AIIntegration._call_openai_api')
    def test_analyze_code(self, mock_call_api):
        """Test code analysis functionality."""
        # Setup mock response
        mock_call_api.return_value = MOCK_FRAMEWORK_DETECTION_RESPONSE
        
        # Call analyze_code
        result = self.ai.analyze_code(
            code=PYTHON_CODE_SAMPLE,
            language="Python",
            filename="app.py",
            prompt_template=self.ai.get_framework_detection_prompt(),
            system_message="You are a code analyzer."
        )
        
        # Verify result
        self.assertTrue(result["success"])
        self.assertEqual(len(result["technologies"]), 3)
        self.assertEqual(result["technologies"][0]["name"], "Flask")
        self.assertEqual(result["technologies"][0]["confidence"], 95)
        
        # Verify mock was called
        mock_call_api.assert_called_once()
    
    @patch('repo_analyzer.ai.ai_integration.AIIntegration._call_openai_api')
    def test_analyze_code_chunking(self, mock_call_api):
        """Test code analysis with chunking for large files."""
        # Setup test config with small max_file_tokens to force chunking
        small_chunk_config = self.test_config.copy()
        small_chunk_config["max_file_tokens"] = 100  # Force chunking
        small_chunk_config["chunk_size"] = 50
        ai = AIIntegration(small_chunk_config)
        
        # Setup mock responses for chunks
        mock_call_api.side_effect = [
            {"technologies": [{"name": "Flask", "category": "framework", "confidence": 90, "evidence": ["Evidence 1"]}], "success": True},
            {"technologies": [{"name": "SQLAlchemy", "category": "library", "confidence": 85, "evidence": ["Evidence 2"]}], "success": True}
        ]
        
        # Call analyze_code with large code sample
        result = ai.analyze_code(
            code=PYTHON_CODE_SAMPLE * 5,  # Make it larger
            language="Python",
            filename="large_app.py",
            prompt_template=ai.get_framework_detection_prompt(),
            system_message="You are a code analyzer."
        )
        
        # Verify result contains aggregated technologies
        self.assertTrue(result["success"])
        self.assertEqual(len(result["technologies"]), 2)
        
        # Verify mock was called multiple times (for each chunk)
        self.assertEqual(mock_call_api.call_count, 2)
    
    @patch('repo_analyzer.ai.ai_integration.AIIntegration._create_openai_embeddings')
    def test_create_embeddings(self, mock_create_embeddings):
        """Test embedding creation functionality."""
        # Setup mock response
        mock_create_embeddings.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ]
        
        # Call create_embeddings
        result = self.ai.create_embeddings(["text1", "text2"])
        
        # Verify result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], [0.1, 0.2, 0.3])
        self.assertEqual(result[1], [0.4, 0.5, 0.6])
        
        # Verify mock was called
        mock_create_embeddings.assert_called_once_with(["text1", "text2"])
    
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_cache_functionality(self, mock_json_dump, mock_file_open, mock_mkdir):
        """Test caching functionality."""
        # Setup test config with caching enabled
        cache_config = self.test_config.copy()
        cache_config["cache_enabled"] = True
        cache_config["cache_dir"] = ".test_cache"
        ai = AIIntegration(cache_config)
        
        # Mock _call_llm_api to return a simple result
        with patch.object(ai, '_call_llm_api', return_value={"result": "test"}) as mock_call_api:
            # Call analyze_code
            result = ai.analyze_code(
                code="test code",
                language="Python",
                filename="test.py",
                prompt_template="test prompt {code} {language} {filename}",
                system_message="test system message"
            )
            
            # Verify result
            self.assertEqual(result, {"result": "test"})
            
            # Verify mocks were called
            mock_mkdir.assert_called_once()
            mock_call_api.assert_called_once()
            mock_file_open.assert_called_once()
            mock_json_dump.assert_called_once()


class TestAIDetector(unittest.TestCase):
    """Test cases for the AIDetector class."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock AIIntegration
        self.mock_ai = MagicMock()
        self.mock_ai.config = {"enabled": True}
        self.mock_ai.get_framework_detection_prompt.return_value = "framework prompt"
        self.mock_ai.get_architecture_detection_prompt.return_value = "architecture prompt"
        self.mock_ai.get_code_quality_prompt.return_value = "code quality prompt"
        
        # Create AIDetector with mock AIIntegration
        self.detector = AIDetector(self.mock_ai)
        
        # Create test repository
        self.repo_path = "test_repo"
        self.files = [
            "app.py",
            "models.py",
            "static/style.css",
            "templates/index.html"
        ]
        self.files_content = {
            "app.py": PYTHON_CODE_SAMPLE,
            "models.py": "# Empty model file",
            "static/style.css": "body { color: black; }",
            "templates/index.html": "<html><body>Test</body></html>"
        }
    
    def test_analyze_file(self):
        """Test analysis of a single file."""
        # Setup mock response
        self.mock_ai.analyze_code.return_value = MOCK_FRAMEWORK_DETECTION_RESPONSE
        
        # Call analyze_file
        result = self.detector.analyze_file("app.py", PYTHON_CODE_SAMPLE, "Python")
        
        # Verify result
        self.assertEqual(result, MOCK_FRAMEWORK_DETECTION_RESPONSE)
        
        # Verify mock was called
        self.mock_ai.analyze_code.assert_called_once_with(
            code=PYTHON_CODE_SAMPLE,
            language="Python",
            filename="app.py",
            prompt_template="framework prompt",
            system_message="You are a code analyzer AI that specializes in identifying technologies, frameworks, and patterns in code repositories."
        )
    
    def test_analyze_repository(self):
        """Test analysis of a repository."""
        # Setup mock response for file analysis
        self.mock_ai.analyze_code.return_value = MOCK_FRAMEWORK_DETECTION_RESPONSE
        
        # Call analyze_repository
        result = self.detector.analyze_repository(self.repo_path, self.files, self.files_content)
        
        # Verify result
        self.assertTrue(result["enabled"])
        self.assertTrue("technologies" in result)
        
        # Verify mock was called at least once
        self.mock_ai.analyze_code.assert_called()
    
    def test_analyze_architecture(self):
        """Test architecture analysis."""
        # Setup mock response
        self.mock_ai.analyze_code.return_value = MOCK_ARCHITECTURE_DETECTION_RESPONSE
        
        # Call analyze_architecture
        result = self.detector.analyze_architecture(self.repo_path, self.files, self.files_content)
        
        # Verify result
        self.assertTrue(result["enabled"])
        self.assertTrue("patterns" in result)
        
        # Verify mock was called at least once
        self.mock_ai.analyze_code.assert_called()
    
    def test_analyze_code_quality(self):
        """Test code quality analysis."""
        # Setup mock response
        self.mock_ai.analyze_code.return_value = MOCK_CODE_QUALITY_RESPONSE
        
        # Call analyze_code_quality
        result = self.detector.analyze_code_quality(self.repo_path, self.files, self.files_content)
        
        # Verify result
        self.assertTrue(result["enabled"])
        self.assertTrue("quality_assessment" in result)
        self.assertTrue("issues" in result)
        
        # Verify mock was called at least once
        self.mock_ai.analyze_code.assert_called()
    
    def test_select_representative_files(self):
        """Test file selection for analysis."""
        # Call _select_representative_files
        selected_files = self.detector._select_representative_files(self.files, self.files_content)
        
        # Verify result
        self.assertIsInstance(selected_files, list)
        self.assertLessEqual(len(selected_files), 20)  # Max files should be 20 or less
        
        # Should include app.py as it's a priority file
        self.assertIn("app.py", selected_files)
    
    def test_detect_language_from_extension(self):
        """Test language detection from file extension."""
        # Test various extensions
        self.assertEqual(self.detector._detect_language_from_extension(".py"), "Python")
        self.assertEqual(self.detector._detect_language_from_extension(".js"), "JavaScript")
        self.assertEqual(self.detector._detect_language_from_extension(".unknown"), "unknown")
    
    def test_aggregation_methods(self):
        """Test result aggregation methods."""
        # Create test results
        file_results = {
            "app.py": {
                "technologies": [
                    {"name": "Flask", "category": "framework", "confidence": 90, "evidence": ["Evidence 1"]},
                    {"name": "SQLAlchemy", "category": "library", "confidence": 85, "evidence": ["Evidence 2"]}
                ],
                "suggestions": [
                    {"text": "Suggestion 1", "severity": "medium", "reason": "Reason 1"}
                ],
                "success": True
            },
            "models.py": {
                "technologies": [
                    {"name": "SQLAlchemy", "category": "library", "confidence": 95, "evidence": ["Evidence 3"]},
                    {"name": "SQLite", "category": "database", "confidence": 80, "evidence": ["Evidence 4"]}
                ],
                "suggestions": [
                    {"text": "Suggestion 2", "severity": "high", "reason": "Reason 2"}
                ],
                "success": True
            }
        }
        
        # Set file_results directly for testing
        self.detector.file_results = file_results
        self.detector.analyzed_file_count = len(file_results)
        
        # Call _aggregate_repository_results
        result = self.detector._aggregate_repository_results()
        
        # Verify result
        self.assertTrue(result["enabled"])
        self.assertEqual(result["file_count"], 2)
        
        # Should have aggregated technologies
        techs = result["technologies"]
        self.assertEqual(len(techs), 3)  # Flask, SQLAlchemy, SQLite
        
        # SQLAlchemy should have the highest confidence (95)
        sqlalchemy = next(tech for tech in techs if tech["name"] == "SQLAlchemy")
        self.assertEqual(sqlalchemy["confidence"], 95)
        
        # High severity suggestion should come first
        self.assertEqual(result["suggestions"][0]["severity"], "high")


if __name__ == '__main__':
    unittest.main()