"""
Configuration module for RepoAnalyzer.

This module provides functionality for loading and managing configuration
settings for the RepoAnalyzer library. It supports loading configuration
from files, environment variables, and programmatic settings.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Set, List, Union

logger = logging.getLogger(__name__)

class RepoAnalyzerConfig:
    """
    Configuration manager for RepoAnalyzer.
    
    This class handles loading and managing configuration settings for
    the RepoAnalyzer library from various sources (files, environment, etc.).
    """
    
    # Default configuration settings
    DEFAULT_CONFIG = {
        # General settings
        "verbose": False,
        "max_file_size": 5 * 1024 * 1024,  # 5MB
        
        # Files and directories
        "exclude_dirs": [
            ".git", "node_modules", "venv", ".venv", "__pycache__", 
            "build", "dist", "target", "bin", "obj"
        ],
        "exclude_files": [
            "*.min.js", "*.min.css", "package-lock.json", "yarn.lock"
        ],
        
        # Analysis settings
        "min_confidence": 15,
        "max_evidence_items": 5,
        "include_categories": [
            "languages", "frameworks", "databases", "build_systems", 
            "package_managers", "frontend", "devops", "architecture", "testing"
        ],
        
        # Extensions for content analysis
        "content_extensions": [
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", 
            ".php", ".cs", ".json", ".yml", ".yaml", ".xml", ".gradle", 
            ".properties", ".conf", ".toml", ".html", ".vue", ".svelte"
        ],
        
        # Output settings
        "output_format": "json",
        "pretty_print": True,
        
        # Detection thresholds
        "detection_thresholds": {
            "languages": 5,
            "frameworks": 15,
            "databases": 15,
            "build_systems": 15,
            "package_managers": 15,
            "frontend": 15,
            "devops": 15,
            "architecture": 20,
            "testing": 15
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to a configuration file (optional)
        """
        # Start with default configuration
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Load configuration from file if provided
        if config_path:
            self.load_from_file(config_path)
        
        # Load configuration from environment variables
        self.load_from_env()
    
    def load_from_file(self, config_path: str) -> None:
        """
        Load configuration from a file.
        
        Args:
            config_path: Path to the configuration file
        """
        try:
            with open(config_path, 'r') as f:
                # Determine file format from extension
                if config_path.endswith('.json'):
                    file_config = json.load(f)
                elif config_path.endswith(('.yaml', '.yml')):
                    try:
                        import yaml
                        file_config = yaml.safe_load(f)
                    except ImportError:
                        logger.warning("PyYAML is not installed. Cannot load YAML configuration.")
                        return
                else:
                    logger.warning(f"Unsupported configuration file format: {config_path}")
                    return
                
                # Update configuration with file values
                self._update_config(file_config)
                logger.info(f"Loaded configuration from {config_path}")
                
        except Exception as e:
            logger.warning(f"Failed to load configuration from {config_path}: {str(e)}")
    
    def load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Map environment variables to configuration keys
        env_mapping = {
            "REPO_ANALYZER_VERBOSE": ("verbose", lambda x: x.lower() in ('true', '1', 'yes')),
            "REPO_ANALYZER_MAX_FILE_SIZE": ("max_file_size", int),
            "REPO_ANALYZER_EXCLUDE_DIRS": ("exclude_dirs", lambda x: x.split(',')),
            "REPO_ANALYZER_EXCLUDE_FILES": ("exclude_files", lambda x: x.split(',')),
            "REPO_ANALYZER_MIN_CONFIDENCE": ("min_confidence", int),
            "REPO_ANALYZER_MAX_EVIDENCE_ITEMS": ("max_evidence_items", int),
            "REPO_ANALYZER_INCLUDE_CATEGORIES": ("include_categories", lambda x: x.split(',')),
            "REPO_ANALYZER_OUTPUT_FORMAT": ("output_format", str),
            "REPO_ANALYZER_PRETTY_PRINT": ("pretty_print", lambda x: x.lower() in ('true', '1', 'yes')),
        }
        
        # Process environment variables
        for env_var, (config_key, converter) in env_mapping.items():
            if env_var in os.environ:
                try:
                    value = converter(os.environ[env_var])
                    self._set_config_value(config_key, value)
                    logger.debug(f"Loaded {config_key} from environment variable {env_var}")
                except Exception as e:
                    logger.warning(f"Failed to load {env_var}: {str(e)}")
    
    def _update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update configuration with new values.
        
        Args:
            new_config: Dictionary containing new configuration values
        """
        for key, value in new_config.items():
            self._set_config_value(key, value)
    
    def _set_config_value(self, key: str, value: Any) -> None:
        """
        Set a configuration value with validation.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        # Handle nested configuration
        if '.' in key:
            parent_key, child_key = key.split('.', 1)
            if parent_key in self.config and isinstance(self.config[parent_key], dict):
                self.config[parent_key][child_key] = value
            return
        
        # Validate and convert values for known keys
        if key == "exclude_dirs" and not isinstance(value, list):
            if isinstance(value, str):
                value = [value]
            else:
                logger.warning(f"Invalid value for {key}: {value} (expected list or string)")
                return
        
        elif key == "exclude_files" and not isinstance(value, list):
            if isinstance(value, str):
                value = [value]
            else:
                logger.warning(f"Invalid value for {key}: {value} (expected list or string)")
                return
        
        elif key == "max_file_size" and not isinstance(value, int):
            try:
                value = int(value)
            except ValueError:
                logger.warning(f"Invalid value for {key}: {value} (expected integer)")
                return
        
        elif key == "min_confidence" and (not isinstance(value, (int, float)) or value < 0 or value > 100):
            try:
                value = int(value)
                if value < 0 or value > 100:
                    raise ValueError("Confidence must be between 0 and 100")
            except ValueError:
                logger.warning(f"Invalid value for {key}: {value} (expected integer between 0 and 100)")
                return
        
        # Set the value
        self.config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value to return if key is not found
            
        Returns:
            Configuration value, or default if not found
        """
        # Handle nested configuration
        if '.' in key:
            parent_key, child_key = key.split('.', 1)
            parent = self.config.get(parent_key, {})
            if isinstance(parent, dict):
                return parent.get(child_key, default)
            return default
        
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._set_config_value(key, value)
    
    def get_exclude_dirs(self) -> Set[str]:
        """
        Get the set of directories to exclude from analysis.
        
        Returns:
            Set of directory names to exclude
        """
        exclude_dirs = self.get("exclude_dirs", [])
        return set(exclude_dirs)
    
    def get_exclude_files(self) -> List[str]:
        """
        Get the list of file patterns to exclude from analysis.
        
        Returns:
            List of file patterns to exclude
        """
        return self.get("exclude_files", [])
    
    def get_detection_threshold(self, category: str) -> int:
        """
        Get the detection threshold for a specific category.
        
        Args:
            category: Technology category
            
        Returns:
            Detection threshold for the category
        """
        thresholds = self.get("detection_thresholds", {})
        return thresholds.get(category, 15)
    
    def get_content_extensions(self) -> Set[str]:
        """
        Get the set of file extensions to include in content analysis.
        
        Returns:
            Set of file extensions
        """
        extensions = self.get("content_extensions", [])
        return set(extensions)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get the complete configuration as a dictionary.
        
        Returns:
            Dictionary containing all configuration settings
        """
        return self.config.copy()
    
    def save_to_file(self, config_path: str) -> None:
        """
        Save the current configuration to a file.
        
        Args:
            config_path: Path to save the configuration file
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
            
            # Determine file format from extension
            if config_path.endswith('.json'):
                with open(config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
            elif config_path.endswith(('.yaml', '.yml')):
                try:
                    import yaml
                    with open(config_path, 'w') as f:
                        yaml.dump(self.config, f, default_flow_style=False)
                except ImportError:
                    logger.warning("PyYAML is not installed. Cannot save YAML configuration.")
                    return
            else:
                logger.warning(f"Unsupported configuration file format: {config_path}")
                return
            
            logger.info(f"Saved configuration to {config_path}")
            
        except Exception as e:
            logger.warning(f"Failed to save configuration to {config_path}: {str(e)}")