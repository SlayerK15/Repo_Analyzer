"""
AI Integration module for RepoAnalyzer.

This module provides the core functionality for integrating Large Language Models (LLMs)
and other AI capabilities into the RepoAnalyzer library. It handles API connections,
prompt engineering, caching, and unified interfaces for all AI-enhanced features.
"""

import os
import json
import time
import logging
import hashlib
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import requests

logger = logging.getLogger(__name__)

class AIIntegration:
    """
    Core class for AI integration in RepoAnalyzer.
    
    This class provides methods for connecting to LLM APIs, embedding code,
    caching results, and other core AI functionality. It serves as the foundation
    for all AI-enhanced features in RepoAnalyzer.
    """
    
    # Default configuration
    DEFAULT_CONFIG = {
        "enabled": False,
        "provider": "openai",
        "model": "gpt-4o",
        "embedding_model": "text-embedding-3-small",
        "temperature": 0.1,
        "max_tokens": 4000,
        "api_base": None,  # Use default for the provider
        "timeout": 60,  # seconds
        "cache_dir": ".repo_analyzer_cache",
        "cache_enabled": True,
        "max_file_tokens": 8000,  # Maximum tokens per file to analyze
        "max_context_tokens": 16000,  # Maximum tokens for context window
        "budget_limit": None,  # Maximum cost in USD
        "token_counter": "tiktoken",  # Library to use for token counting
        "chunk_size": 1500,  # Size of code chunks when splitting large files
        "chunk_overlap": 200,  # Overlap between chunks to maintain context
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AI integration.
        
        Args:
            config: Configuration dictionary with AI settings (optional)
        """
        # Load configuration (with fallbacks)
        self.config = self.DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
            
        # Environment variables override configuration
        self._load_from_env()
        
        # Initialize API client based on provider
        self.client = None
        
        # Create cache directory if needed
        if self.config["cache_enabled"]:
            cache_dir = Path(self.config["cache_dir"])
            cache_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize token counter
        self._init_token_counter()
        
        # Initialize provider if enabled
        if self.config["enabled"]:
            self._init_provider()
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        env_vars = {
            "REPO_ANALYZER_AI_ENABLED": ("enabled", lambda x: x.lower() in ('true', '1', 'yes')),
            "REPO_ANALYZER_AI_PROVIDER": ("provider", str),
            "REPO_ANALYZER_AI_MODEL": ("model", str),
            "REPO_ANALYZER_AI_EMBEDDING_MODEL": ("embedding_model", str),
            "REPO_ANALYZER_AI_TEMPERATURE": ("temperature", float),
            "REPO_ANALYZER_AI_MAX_TOKENS": ("max_tokens", int),
            "REPO_ANALYZER_AI_API_BASE": ("api_base", str),
            "REPO_ANALYZER_AI_TIMEOUT": ("timeout", int),
            "REPO_ANALYZER_AI_CACHE_DIR": ("cache_dir", str),
            "REPO_ANALYZER_AI_CACHE_ENABLED": ("cache_enabled", lambda x: x.lower() in ('true', '1', 'yes')),
            "REPO_ANALYZER_AI_BUDGET_LIMIT": ("budget_limit", lambda x: float(x) if x else None),
        }
        
        # API keys for different providers
        provider_keys = {
            "OPENAI_API_KEY": "openai",
            "ANTHROPIC_API_KEY": "anthropic", 
            "COHERE_API_KEY": "cohere",
            "HF_API_KEY": "huggingface",
        }
        
        # Process environment variables
        for env_var, (config_key, converter) in env_vars.items():
            if env_var in os.environ:
                try:
                    value = converter(os.environ[env_var])
                    self.config[config_key] = value
                    logger.debug(f"Loaded {config_key} from environment variable {env_var}")
                except Exception as e:
                    logger.warning(f"Failed to load {env_var}: {str(e)}")
        
        # Check if any provider API key is set
        for env_var, provider in provider_keys.items():
            if env_var in os.environ and os.environ[env_var]:
                # If API key is set and no provider is explicitly configured, use this provider
                if not self.config.get("provider_api_key"):
                    self.config["provider"] = provider
                    self.config["provider_api_key"] = os.environ[env_var]
                    logger.debug(f"Using {provider} as AI provider based on available API key")
                    # If no explicit enabled flag, enable AI if an API key is found
                    if "REPO_ANALYZER_AI_ENABLED" not in os.environ:
                        self.config["enabled"] = True
    
    def _init_token_counter(self):
        """Initialize token counting functionality."""
        if self.config["token_counter"] == "tiktoken":
            try:
                import tiktoken
                self.tokenizer = tiktoken.encoding_for_model(self.config["model"])
                self.count_tokens = lambda text: len(self.tokenizer.encode(text))
            except ImportError:
                logger.warning("Tiktoken not installed, falling back to rough token estimation")
                # Rough estimation: ~4 chars per token for English text
                self.count_tokens = lambda text: len(text) // 4
            except Exception as e:
                logger.warning(f"Failed to initialize tiktoken: {str(e)}")
                self.count_tokens = lambda text: len(text) // 4
        else:
            # Simple approximation
            self.count_tokens = lambda text: len(text) // 4
    
    def _init_provider(self):
        """Initialize the AI provider client."""
        provider = self.config["provider"].lower()
        
        if provider == "openai":
            try:
                import openai
                
                # Set API key from environment if not explicitly provided
                api_key = self.config.get("provider_api_key") or os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    logger.warning("OpenAI API key not found. AI features will be disabled.")
                    self.config["enabled"] = False
                    return
                
                # Set custom base URL if provided
                if self.config["api_base"]:
                    openai.base_url = self.config["api_base"]
                
                self.client = openai.OpenAI(api_key=api_key)
                logger.info("Initialized OpenAI client")
                
            except ImportError:
                logger.warning("OpenAI package not installed. Install it with 'pip install openai'")
                self.config["enabled"] = False
        
        elif provider == "anthropic":
            try:
                import anthropic
                
                # Set API key from environment if not explicitly provided
                api_key = self.config.get("provider_api_key") or os.environ.get("ANTHROPIC_API_KEY")
                if not api_key:
                    logger.warning("Anthropic API key not found. AI features will be disabled.")
                    self.config["enabled"] = False
                    return
                
                # Set custom base URL if provided
                if self.config["api_base"]:
                    self.client = anthropic.Anthropic(api_key=api_key, base_url=self.config["api_base"])
                else:
                    self.client = anthropic.Anthropic(api_key=api_key)
                    
                logger.info("Initialized Anthropic client")
                
            except ImportError:
                logger.warning("Anthropic package not installed. Install it with 'pip install anthropic'")
                self.config["enabled"] = False
        
        elif provider == "local":
            try:
                from llama_cpp import Llama
                
                # Set model path
                model_path = self.config.get("local_model_path")
                if not model_path or not os.path.exists(model_path):
                    logger.warning("Local model path not found. AI features will be disabled.")
                    self.config["enabled"] = False
                    return
                
                # Initialize Llama with the specified model
                self.client = Llama(
                    model_path=model_path,
                    n_ctx=self.config.get("max_context_tokens", 2048),
                    n_threads=self.config.get("n_threads", 4)
                )
                logger.info(f"Initialized local LLM client with model: {model_path}")
                
            except ImportError:
                logger.warning("llama-cpp-python package not installed. Install it with 'pip install llama-cpp-python'")
                self.config["enabled"] = False
        
        elif provider == "huggingface":
            try:
                import huggingface_hub
                
                # Set API key from environment if not explicitly provided
                api_key = self.config.get("provider_api_key") or os.environ.get("HF_API_KEY")
                if not api_key:
                    logger.warning("HuggingFace API key not found. AI features will be disabled.")
                    self.config["enabled"] = False
                    return
                
                # Initialize client with API token
                self.client = huggingface_hub.InferenceClient(token=api_key)
                logger.info("Initialized HuggingFace Inference client")
                
            except ImportError:
                logger.warning("huggingface_hub package not installed. Install it with 'pip install huggingface_hub'")
                self.config["enabled"] = False
        
        else:
            logger.warning(f"Unsupported AI provider: {provider}. AI features will be disabled.")
            self.config["enabled"] = False
    
    def analyze_code(self, code: str, language: str, filename: str, 
                    prompt_template: str, system_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze code using the configured LLM.
        
        Args:
            code: Code content to analyze
            language: Programming language of the code
            filename: Name of the file being analyzed
            prompt_template: Template for the prompt to send to the LLM
            system_message: Optional system message to set context for the LLM
            
        Returns:
            Dict containing the analysis results
        """
        if not self.config["enabled"]:
            logger.warning("AI features are disabled. Returning empty analysis.")
            return {"enabled": False, "message": "AI features are disabled"}
        
        # Check if result is in cache
        cache_key = self._create_cache_key(code, prompt_template, system_message)
        if self.config["cache_enabled"]:
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                logger.debug(f"Using cached AI analysis result for {filename}")
                return cached_result
        
        # Count tokens and check if we need to chunk the code
        code_tokens = self.count_tokens(code)
        
        if code_tokens > self.config["max_file_tokens"]:
            # Handle large files by chunking
            logger.debug(f"Code file {filename} is too large ({code_tokens} tokens). Chunking...")
            return self._analyze_code_chunked(code, language, filename, prompt_template, system_message)
        
        # Format the prompt
        formatted_prompt = prompt_template.format(
            code=code,
            language=language,
            filename=filename
        )
        
        # Call the LLM API based on the configured provider
        try:
            result = self._call_llm_api(formatted_prompt, system_message)
            
            # Cache the result
            if self.config["cache_enabled"]:
                self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error calling AI API: {str(e)}")
            return {
                "error": str(e),
                "message": "Failed to analyze code with AI",
                "enabled": True,
                "success": False
            }
    
    def _analyze_code_chunked(self, code: str, language: str, filename: str, 
                             prompt_template: str, system_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a large code file by splitting it into chunks.
        
        Args:
            code: Code content to analyze
            language: Programming language of the code
            filename: Name of the file being analyzed
            prompt_template: Template for the prompt to send to the LLM
            system_message: Optional system message to set context for the LLM
            
        Returns:
            Dict containing the aggregated analysis results
        """
        # Split code into chunks
        chunks = self._split_code_into_chunks(code)
        logger.debug(f"Split code into {len(chunks)} chunks for analysis")
        
        # Analyze each chunk
        chunk_results = []
        for i, chunk in enumerate(chunks):
            logger.debug(f"Analyzing chunk {i+1}/{len(chunks)} of {filename}")
            
            # Add chunk context to prompt template
            chunk_prompt = prompt_template.format(
                code=chunk,
                language=language,
                filename=f"{filename} (chunk {i+1}/{len(chunks)})",
                chunk_index=i+1,
                total_chunks=len(chunks)
            )
            
            # Call LLM API
            try:
                result = self._call_llm_api(chunk_prompt, system_message)
                chunk_results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing chunk {i+1}: {str(e)}")
                chunk_results.append({
                    "error": str(e),
                    "message": f"Failed to analyze chunk {i+1}/{len(chunks)}",
                    "enabled": True,
                    "success": False
                })
        
        # Aggregate results
        return self._aggregate_chunk_results(chunk_results, filename)
    
    def _split_code_into_chunks(self, code: str) -> List[str]:
        """
        Split code into chunks for processing large files.
        
        Args:
            code: Complete code content
            
        Returns:
            List of code chunks
        """
        chunk_size = self.config["chunk_size"]
        chunk_overlap = self.config["chunk_overlap"]
        
        # Split by lines first to avoid breaking in the middle of a line
        lines = code.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_tokens = self.count_tokens(line)
            
            # If adding this line would exceed chunk size, start a new chunk
            if current_size + line_tokens > chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                
                # Keep the last few lines for overlap
                overlap_lines = current_chunk[-chunk_overlap:] if chunk_overlap < len(current_chunk) else current_chunk
                current_chunk = overlap_lines
                current_size = sum(self.count_tokens(l) for l in current_chunk)
            
            current_chunk.append(line)
            current_size += line_tokens
        
        # Add the last chunk if not empty
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def _aggregate_chunk_results(self, chunk_results: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
        """
        Aggregate results from multiple code chunks.
        
        Args:
            chunk_results: List of results from individual chunks
            filename: Name of the file being analyzed
            
        Returns:
            Dict containing the aggregated analysis results
        """
        # Initialize aggregated result
        aggregated = {
            "enabled": True,
            "success": all(result.get("success", False) for result in chunk_results),
            "filename": filename,
            "message": f"Aggregated results from {len(chunk_results)} chunks"
        }
        
        # Merge analysis from chunks
        # The strategy depends on the structure of the results, which will vary based on prompt design
        # Here's a generic approach that should work for most cases
        all_technologies = []
        all_patterns = []
        all_suggestions = []
        
        for result in chunk_results:
            if "technologies" in result:
                all_technologies.extend(result.get("technologies", []))
            
            if "patterns" in result:
                all_patterns.extend(result.get("patterns", []))
            
            if "suggestions" in result:
                all_suggestions.extend(result.get("suggestions", []))
        
        # Remove duplicates and combine similar findings
        if all_technologies:
            # Use a set to deduplicate by name
            unique_tech = {}
            for tech in all_technologies:
                if tech["name"] not in unique_tech:
                    unique_tech[tech["name"]] = tech
                else:
                    # Combine confidence scores and evidence
                    existing = unique_tech[tech["name"]]
                    existing["confidence"] = max(existing["confidence"], tech["confidence"])
                    existing["evidence"].extend(tech["evidence"])
            
            aggregated["technologies"] = list(unique_tech.values())
        
        if all_patterns:
            # Deduplicate patterns
            unique_patterns = []
            pattern_names = set()
            for pattern in all_patterns:
                if pattern["name"] not in pattern_names:
                    pattern_names.add(pattern["name"])
                    unique_patterns.append(pattern)
            
            aggregated["patterns"] = unique_patterns
        
        if all_suggestions:
            # Deduplicate suggestions
            unique_suggestions = []
            suggestion_texts = set()
            for suggestion in all_suggestions:
                # Use the first sentence as a key for deduplication
                key = suggestion["text"].split(".")[0]
                if key not in suggestion_texts:
                    suggestion_texts.add(key)
                    unique_suggestions.append(suggestion)
            
            aggregated["suggestions"] = unique_suggestions
        
        return aggregated
    
    def _call_llm_api(self, prompt: str, system_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Call the LLM API with the provided prompt.
        
        Args:
            prompt: The prompt to send to the LLM
            system_message: Optional system message to set context for the LLM
            
        Returns:
            Dict containing the LLM response and metadata
        """
        provider = self.config["provider"].lower()
        
        if provider == "openai":
            return self._call_openai_api(prompt, system_message)
        elif provider == "anthropic":
            return self._call_anthropic_api(prompt, system_message)
        elif provider == "local":
            return self._call_local_llm(prompt, system_message)
        elif provider == "huggingface":
            return self._call_huggingface_api(prompt, system_message)
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
    
    def _call_openai_api(self, prompt: str, system_message: Optional[str] = None) -> Dict[str, Any]:
        """Call the OpenAI API."""
        if not system_message:
            system_message = "You are a code analyzer AI that specializes in identifying technologies, frameworks, and patterns in code repositories."
        
        try:
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"],
                response_format={"type": "json_object"}
            )
            
            # Parse JSON response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Add metadata to result
            result.update({
                "model": self.config["model"],
                "success": True,
                "enabled": True,
                "provider": "openai",
                "tokens": {
                    "prompt": response.usage.prompt_tokens,
                    "completion": response.usage.completion_tokens,
                    "total": response.usage.total_tokens
                }
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return {
                "error": str(e),
                "message": "Failed to analyze code with OpenAI",
                "success": False,
                "enabled": True,
                "provider": "openai"
            }
    
    def _call_anthropic_api(self, prompt: str, system_message: Optional[str] = None) -> Dict[str, Any]:
        """Call the Anthropic API."""
        if not system_message:
            system_message = "You are a code analyzer AI that specializes in identifying technologies, frameworks, and patterns in code repositories."
        
        try:
            response = self.client.messages.create(
                model=self.config["model"],
                system=system_message,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"],
                response_format={"type": "json_object"}
            )
            
            # Parse JSON response
            content = response.content[0].text
            result = json.loads(content)
            
            # Add metadata to result
            result.update({
                "model": self.config["model"],
                "success": True,
                "enabled": True,
                "provider": "anthropic",
                "tokens": {
                    "prompt": 0,  # Anthropic doesn't provide token counts in the same way
                    "completion": 0,
                    "total": 0
                }
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {str(e)}")
            return {
                "error": str(e),
                "message": "Failed to analyze code with Anthropic",
                "success": False,
                "enabled": True,
                "provider": "anthropic"
            }
    
    def _call_local_llm(self, prompt: str, system_message: Optional[str] = None) -> Dict[str, Any]:
        """Call a local LLM using llama-cpp."""
        if system_message:
            full_prompt = f"{system_message}\n\nUser: {prompt}\n\nAssistant:"
        else:
            full_prompt = f"User: {prompt}\n\nAssistant:"
        
        try:
            response = self.client(
                prompt=full_prompt,
                max_tokens=self.config["max_tokens"],
                temperature=self.config["temperature"],
                stop=["User:"],  # Stop at next user turn
                echo=False
            )
            
            # Parse response as JSON if possible
            content = response["choices"][0]["text"].strip()
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # If not valid JSON, wrap it in a simple structure
                result = {
                    "analysis": content,
                    "message": "Response wasn't valid JSON, returning raw text"
                }
            
            # Add metadata to result
            result.update({
                "model": "local",
                "success": True,
                "enabled": True,
                "provider": "local",
                "tokens": {
                    "prompt": response["usage"]["prompt_tokens"],
                    "completion": response["usage"]["completion_tokens"],
                    "total": response["usage"]["total_tokens"]
                }
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error calling local LLM: {str(e)}")
            return {
                "error": str(e),
                "message": "Failed to analyze code with local LLM",
                "success": False,
                "enabled": True,
                "provider": "local"
            }
    
    def _call_huggingface_api(self, prompt: str, system_message: Optional[str] = None) -> Dict[str, Any]:
        """Call the HuggingFace Inference API."""
        if system_message:
            full_prompt = f"{system_message}\n\nUser: {prompt}\n\nAssistant:"
        else:
            full_prompt = f"User: {prompt}\n\nAssistant:"
        
        try:
            # Call the text generation API
            model_id = self.config["model"]
            response = self.client.text_generation(
                prompt=full_prompt,
                model=model_id,
                max_new_tokens=self.config["max_tokens"],
                temperature=self.config["temperature"],
                return_full_text=False
            )
            
            # Parse response as JSON if possible
            content = response.strip()
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # If not valid JSON, wrap it in a simple structure
                result = {
                    "analysis": content,
                    "message": "Response wasn't valid JSON, returning raw text"
                }
            
            # Add metadata to result
            result.update({
                "model": model_id,
                "success": True,
                "enabled": True,
                "provider": "huggingface",
                "tokens": {
                    "prompt": 0,  # HF API doesn't provide token counts directly
                    "completion": 0,
                    "total": 0
                }
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error calling HuggingFace API: {str(e)}")
            return {
                "error": str(e),
                "message": "Failed to analyze code with HuggingFace",
                "success": False,
                "enabled": True,
                "provider": "huggingface"
            }
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for the given texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (each vector is a list of floats)
        """
        if not self.config["enabled"]:
            logger.warning("AI features are disabled. Cannot create embeddings.")
            return [[] for _ in texts]  # Return empty embeddings
        
        provider = self.config["provider"].lower()
        
        # Check for empty input
        if not texts:
            return []
            
        # Check cache first
        if self.config["cache_enabled"]:
            cached_results = []
            uncached_texts = []
            uncached_indices = []
            
            for i, text in enumerate(texts):
                cache_key = self._create_cache_key(text, "embedding")
                cached = self._get_cached_result(cache_key)
                
                if cached and "embedding" in cached:
                    cached_results.append((i, cached["embedding"]))
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
            
            # If all embeddings were cached, return them
            if not uncached_texts:
                # Sort by original indices and extract embeddings
                sorted_results = sorted(cached_results, key=lambda x: x[0])
                return [result[1] for result in sorted_results]
                
            # Otherwise, we'll need to generate embeddings for uncached texts
            texts_to_embed = uncached_texts
        else:
            # If cache is disabled, embed all texts
            texts_to_embed = texts
            uncached_indices = list(range(len(texts)))
        
        try:
            if provider == "openai":
                embeddings = self._create_openai_embeddings(texts_to_embed)
            elif provider == "huggingface":
                embeddings = self._create_huggingface_embeddings(texts_to_embed)
            elif provider == "local":
                embeddings = self._create_local_embeddings(texts_to_embed)
            else:
                logger.warning(f"Embedding not supported for provider: {provider}")
                return [[] for _ in texts]  # Return empty embeddings
            
            # Cache the results
            if self.config["cache_enabled"]:
                for i, embedding in enumerate(embeddings):
                    text_index = uncached_indices[i]
                    text = texts[text_index]
                    cache_key = self._create_cache_key(text, "embedding")
                    self._cache_result(cache_key, {"embedding": embedding})
                
                # Combine cached and new embeddings
                all_embeddings = [None] * len(texts)
                
                # Add cached embeddings
                for i, embedding in cached_results:
                    all_embeddings[i] = embedding
                
                # Add new embeddings
                for i, embedding in zip(uncached_indices, embeddings):
                    all_embeddings[i] = embedding
                
                return all_embeddings
            else:
                return embeddings
                
        except Exception as e:
            logger.error(f"Error creating embeddings: {str(e)}")
            return [[] for _ in texts]  # Return empty embeddings on error
    
    def _create_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using OpenAI API."""
        try:
            response = self.client.embeddings.create(
                model=self.config["embedding_model"],
                input=texts
            )
            
            # Extract embeddings from response
            embeddings = [item.embedding for item in response.data]
            return embeddings
            
        except Exception as e:
            logger.error(f"Error creating OpenAI embeddings: {str(e)}")
            raise
    
    def _create_huggingface_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using HuggingFace API."""
        try:
            embeddings = []
            
            # HF API might not support batching, so process one at a time
            for text in texts:
                response = self.client.feature_extraction(
                    text=text,
                    model=self.config["embedding_model"]
                )
                
                # Response format may vary, handle different possible formats
                if isinstance(response, list) and len(response) > 0:
                    # If response is a list of vectors (for models that return per-token embeddings)
                    # Take the average or the [CLS] embedding (first token)
                    embedding = response[0]
                elif isinstance(response, dict) and "embedding" in response:
                    embedding = response["embedding"]
                else:
                    # Assume the response itself is the embedding vector
                    embedding = response
                
                embeddings.append(embedding)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error creating HuggingFace embeddings: {str(e)}")
            raise
    
    def _create_local_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using local models."""
        try:
            # Check if sentence-transformers is installed
            import sentence_transformers
            
            # Create model if not already initialized
            if not hasattr(self, "embedding_model"):
                model_name = self.config.get("local_embedding_model", "all-MiniLM-L6-v2")
                self.embedding_model = sentence_transformers.SentenceTransformer(model_name)
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False).tolist()
            return embeddings
            
        except ImportError:
            logger.error("sentence-transformers package not installed. Install with 'pip install sentence-transformers'")
            raise
        except Exception as e:
            logger.error(f"Error creating local embeddings: {str(e)}")
            raise
    
    def _create_cache_key(self, content: str, operation: str = "analysis", 
                         extras: Optional[str] = None) -> str:
        """
        Create a cache key for storing and retrieving results.
        
        Args:
            content: The content being analyzed or embedded
            operation: Type of operation (analysis, embedding, etc.)
            extras: Optional extra data to include in the key (e.g., prompt template)
            
        Returns:
            Cache key as a string
        """
        # Combine all inputs into a single string
        combined = f"{content}{operation}{extras or ''}{self.config['model']}"
        
        # Create a hash of the combined string
        hash_obj = hashlib.md5(combined.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a cached result if available.
        
        Args:
            cache_key: The cache key to look up
            
        Returns:
            Cached result as a dict, or None if not found
        """
        if not self.config["cache_enabled"]:
            return None
            
        cache_file = Path(self.config["cache_dir"]) / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading cache file: {str(e)}")
                return None
        
        return None
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """
        Cache a result for future use.
        
        Args:
            cache_key: The cache key to use
            result: The result to cache
        """
        if not self.config["cache_enabled"]:
            return
            
        cache_file = Path(self.config["cache_dir"]) / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f)
        except Exception as e:
            logger.warning(f"Error writing cache file: {str(e)}")
    
    def get_framework_detection_prompt(self) -> str:
        """Return the prompt template for framework detection."""
        return """
        Please analyze the following code file to identify frameworks, libraries, and technologies used.
        
        Filename: {filename}
        Language: {language}
        
        CODE:
        ```
        {code}
        ```
        
        Analyze the code and respond with a JSON object that includes:
        1. A list of frameworks and technologies detected
        2. Confidence scores (0-100) for each detection
        3. Evidence for each detection (specific code patterns, imports, etc.)
        
        Format your response as a JSON object with the following structure:
        ```json
        {
          "technologies": [
            {
              "name": "Framework/Technology Name",
              "category": "framework|library|language|database|etc",
              "confidence": 85,
              "evidence": ["Evidence 1", "Evidence 2", ...]
            }
          ],
          "suggestions": [
            {
              "text": "Suggestion text",
              "severity": "low|medium|high",
              "reason": "Reason for suggestion"
            }
          ]
        }
        ```
        
        Be precise in your detection, only include technologies with clear evidence.
        """
    
    def get_architecture_detection_prompt(self) -> str:
        """Return the prompt template for architecture pattern detection."""
        return """
        Please analyze the following code file to identify architectural patterns and code organization.
        
        Filename: {filename}
        Language: {language}
        
        CODE:
        ```
        {code}
        ```
        
        Analyze the code and respond with a JSON object that includes:
        1. Architectural patterns detected (MVC, MVVM, layered, microservices, etc.)
        2. Code organization patterns (modular, object-oriented, functional, etc.)
        3. Confidence scores (0-100) for each detection
        4. Evidence for each detection
        
        Format your response as a JSON object with the following structure:
        ```json
        {
          "patterns": [
            {
              "name": "Pattern Name",
              "type": "architecture|organization|design",
              "confidence": 85,
              "evidence": ["Evidence 1", "Evidence 2", ...]
            }
          ],
          "suggestions": [
            {
              "text": "Suggestion for architectural improvement",
              "severity": "low|medium|high",
              "reason": "Reason for suggestion"
            }
          ]
        }
        ```
        
        Be precise in your detection, only include patterns with clear evidence.
        """
    
    def get_code_quality_prompt(self) -> str:
        """Return the prompt template for code quality assessment."""
        return """
        Please analyze the following code file for code quality, best practices, and potential improvements.
        
        Filename: {filename}
        Language: {language}
        
        CODE:
        ```
        {code}
        ```
        
        Analyze the code and respond with a JSON object that includes:
        1. Code quality assessment (readability, maintainability, performance)
        2. Best practices adherence
        3. Potential issues or anti-patterns
        4. Suggestions for improvement
        
        Format your response as a JSON object with the following structure:
        ```json
        {
          "quality_assessment": {
            "readability": {
              "score": 85,
              "strengths": ["Strength 1", "Strength 2"],
              "weaknesses": ["Weakness 1", "Weakness 2"]
            },
            "maintainability": {
              "score": 75,
              "strengths": ["Strength 1", "Strength 2"],
              "weaknesses": ["Weakness 1", "Weakness 2"]
            },
            "performance": {
              "score": 90,
              "strengths": ["Strength 1", "Strength 2"],
              "weaknesses": ["Weakness 1", "Weakness 2"]
            }
          },
          "issues": [
            {
              "type": "anti-pattern|code-smell|performance|security",
              "severity": "low|medium|high",
              "description": "Description of the issue",
              "location": "Line number or method name"
            }
          ],
          "suggestions": [
            {
              "text": "Suggestion for improvement",
              "severity": "low|medium|high",
              "reason": "Reason for suggestion"
            }
          ]
        }
        ```
        
        Be thorough but fair in your assessment.
        """