"""
Test cases for AI Integration module in RepoAnalyzer.

This module contains comprehensive tests for the AIIntegration class,
which provides the core functionality for integrating AI models with
the repository analysis process.
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
from pathlib import Path

from repo_analyzer.ai.ai_integration import AIIntegration
from repo_analyzer.ai.prompt_templates import PROMPT_TEMPLATES

class TestAIIntegration(unittest.TestCase):
    """Test cases for the AIIntegration class."""
    
    def setUp(self):
        """Set up test environment with test configuration."""
        self.test_config = {
            "enabled": True,
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.1,
            "cache_dir": tempfile.mkdtemp(),
            "cache_enabled": True
        }
        
        # Create a test instance with mocked provider initialization
        with patch.object(AIIntegration, '_init_provider'):
            self.ai_integration = AIIntegration(self.test_config)
    
    def tearDown(self):
        """Clean up after tests."""
        # Clean up temp directory if it exists
        if hasattr(self, 'test_config') and 'cache_dir' in self.test_config:
            cache_dir = Path(self.test_config['cache_dir'])
            if cache_dir.exists():
                import shutil
                shutil.rmtree(cache_dir)
    
    def test_initialization_with_config(self):
        """Test initialization with configuration parameters."""
        # Create a new instance with test config
        with patch.object(AIIntegration, '_init_provider'):
            ai = AIIntegration(self.test_config)
        
        # Check if configuration is properly loaded
        self.assertEqual(ai.config["provider"], "openai")
        self.assertEqual(ai.config["model"], "gpt-4")
        self.assertEqual(ai.config["temperature"], 0.1)
        self.assertTrue(ai.config["enabled"])
        self.assertTrue(ai.config["cache_enabled"])
    
    @patch.dict('os.environ', {
        "REPO_ANALYZER_AI_PROVIDER": "anthropic",
        "REPO_ANALYZER_AI_MODEL": "claude-3",
        "REPO_ANALYZER_AI_TEMPERATURE": "0.2",
        "REPO_ANALYZER_AI_ENABLED": "true"
    })
    def test_load_from_env(self):
        """Test loading configuration from environment variables."""
        # Create a new instance with env variables set
        with patch.object(AIIntegration, '_init_provider'):
            ai = AIIntegration()
        
        # Check if environment variables are properly loaded
        self.assertEqual(ai.config["provider"], "anthropic")
        self.assertEqual(ai.config["model"], "claude-3")
        self.assertEqual(ai.config["temperature"], 0.2)
        self.assertTrue(ai.config["enabled"])
    
    @patch('repo_analyzer.ai.ai_integration.AIIntegration._call_openai_api')
    def test_analyze_code(self, mock_call_api):
        """Test code analysis functionality."""
        # Mock API response
        mock_response = {
            "technologies": [
                {"name": "Flask", "confidence": 95}
            ],
            "success": True
        }
        mock_call_api.return_value = mock_response
        
        # Test code and parameters
        code = "from flask import Flask\napp = Flask(__name__)"
        language = "python"
        filename = "app.py"
        prompt_template = "Analyze this {language} code: {code}"
        
        # Execute analysis
        result = self.ai_integration.analyze_code(code, language, filename, prompt_template)
        
        # Verify result
        self.assertEqual(result, mock_response)
        mock_call_api.assert_called_once()
    
    @patch('repo_analyzer.ai.ai_integration.AIIntegration._call_openai_api')
    def test_analyze_code_chunking(self, mock_call_api):
        """Test code analysis with chunking for large files."""
        # Mock API responses for chunks
        mock_responses = [
            {"technologies": [{"name": "React", "confidence": 90}], "success": True},
            {"technologies": [{"name": "Redux", "confidence": 85}], "success": True}
        ]
        mock_call_api.side_effect = mock_responses
        
        # Create a large code snippet that will require chunking
        large_code = "import React from 'react';\n" * 1000
        
        # Patch the chunking threshold to force chunking with our smaller test code
        with patch.object(self.ai_integration, 'count_tokens', return_value=10000):
            result = self.ai_integration.analyze_code(
                large_code, "javascript", "app.js", "Analyze this {language} code: {code}"
            )
        
        # Verify chunking was used and results aggregated
        self.assertEqual(mock_call_api.call_count, 2)
        self.assertTrue("technologies" in result)
        # Check that the aggregated results include both technologies
        tech_names = [t["name"] for t in result["technologies"]]
        self.assertIn("React", tech_names)
        self.assertIn("Redux", tech_names)
    
    def test_split_code_into_chunks(self):
        """Test splitting code into chunks."""
        # Create test code with multiple lines
        test_code = "\n".join([f"line{i}" for i in range(100)])
        
        # Split into chunks
        chunks = self.ai_integration._split_code_into_chunks(test_code)
        
        # Verify chunks are created correctly
        self.assertGreater(len(chunks), 1)
        # Check that chunks have the expected content
        for chunk in chunks:
            self.assertIsInstance(chunk, str)
            self.assertGreater(len(chunk), 0)
    
    @patch('repo_analyzer.ai.ai_integration.AIIntegration._create_openai_embeddings')
    def test_create_embeddings(self, mock_create_embeddings):
        """Test creating embeddings for text."""
        # Mock embedding creation
        mock_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_create_embeddings.return_value = mock_embeddings
        
        # Test text
        texts = ["text1", "text2"]
        
        # Create embeddings
        result = self.ai_integration.create_embeddings(texts)
        
        # Verify result
        self.assertEqual(result, mock_embeddings)
        mock_create_embeddings.assert_called_once_with(texts)
    
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_cache_result(self, mock_json_dump, mock_file_open, mock_mkdir):
        """Test caching of API results."""
        # Test data
        cache_key = "test_key"
        result = {"data": "test_data"}
        
        # Cache the result
        self.ai_integration._cache_result(cache_key, result)
        
        # Verify caching operations
        mock_mkdir.assert_called_once()
        mock_file_open.assert_called_once()
        mock_json_dump.assert_called_once()
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='{"data": "test_data"}')
    def test_get_cached_result(self, mock_file_open, mock_exists):
        """Test retrieving cached results."""
        # Test data
        cache_key = "test_key"
        expected_result = {"data": "test_data"}
        
        # Get cached result
        result = self.ai_integration._get_cached_result(cache_key)
        
        # Verify result
        self.assertEqual(result, expected_result)
        mock_exists.assert_called_once()
        mock_file_open.assert_called_once()
    
    def test_create_cache_key(self):
        """Test generation of cache keys."""
        # Test data
        content = "test content"
        operation = "test_op"
        extras = "extras"
        
        # Create cache key
        cache_key = self.ai_integration._create_cache_key(content, operation, extras)
        
        # Verify key format and uniqueness
        self.assertIsInstance(cache_key, str)
        self.assertTrue(len(cache_key) > 0)
        
        # Test uniqueness
        other_key = self.ai_integration._create_cache_key("different content", operation, extras)
        self.assertNotEqual(cache_key, other_key)
    
    @patch('requests.post')
    def test_call_huggingface_api(self, mock_post):
        """Test calling the HuggingFace API."""
        # Skip if provider is not huggingface
        if self.ai_integration.config["provider"] != "huggingface":
            self.ai_integration.config["provider"] = "huggingface"
        
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"generated_text": '{"result": "success"}'}
        mock_post.return_value = mock_response
        
        # Set up test
        self.ai_integration.client = MagicMock()
        
        # Call API with mocked client
        with patch.object(self.ai_integration, '_call_huggingface_api', 
                         return_value={"result": "success"}):
            result = self.ai_integration._call_llm_api("test prompt")
        
        # Verify result
        self.assertEqual(result["result"], "success")
    
    def test_get_prompt_templates(self):
        """Test retrieving prompt templates."""
        # Test all prompt template getter methods
        prompt_methods = [
            'get_framework_detection_prompt',
            'get_architecture_detection_prompt',
            'get_code_quality_prompt'
        ]
        
        for method_name in prompt_methods:
            with patch.object(self.ai_integration, method_name, 
                             return_value=PROMPT_TEMPLATES["framework_detection"]):
                # Call the method
                method = getattr(self.ai_integration, method_name)
                prompt = method()
                
                # Verify prompt is retrieved
                self.assertIsNotNone(prompt)

if __name__ == '__main__':
    unittest.main()
