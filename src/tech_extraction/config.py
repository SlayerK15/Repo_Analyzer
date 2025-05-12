"""
Configuration management for the Technology Extraction System.
Uses Pydantic Settings for type checking and validation.
"""
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import AnyHttpUrl, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    """Configuration settings for AI services."""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_model: str = "gpt-4-turbo-preview"
    backup_model: str = "gpt-3.5-turbo-16k"
    claude_model: str = "claude-3-haiku-20240307"
    max_tokens: int = 4096
    temperature: float = 0.2
    request_timeout: int = 120
    retry_attempts: int = 3
    retry_delay: int = 2
    batch_size: int = 5
    
    # Token budget allocation settings
    base_token_allocation: int = 1000
    token_per_importance_point: int = 200
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class DatabaseSettings(BaseSettings):
    """Database connection settings."""
    database_url: str = "sqlite:///./tech_extraction.db"
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800
    echo: bool = False
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class RedisSettings(BaseSettings):
    """Redis connection settings."""
    redis_url: str = "memory://"
    cache_ttl: int = 3600
    lock_timeout: int = 300
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class FileCollectionSettings(BaseSettings):
    """Settings for file collection and processing."""
    max_file_size_mb: float = 5.0
    max_depth: int = 10
    default_ignore_patterns: List[str] = [
        ".git", ".svn", ".hg", "node_modules", "venv", ".venv",
        ".idea", ".vscode", "__pycache__", "*.pyc", "*.so", "*.dll",
        "*.class", "*.o", "*.obj", "build", "dist", "*.egg-info",
        "*.egg", "*.min.js", "*.min.css", "vendor", "bower_components",
        "third_party", "test", "tests", "spec", "specs", "coverage"
    ]
    language_detection_confidence_threshold: float = 0.7
    min_sample_size: int = 10
    max_sample_size: int = 500
    stratified_sampling_ratio: Dict[str, float] = {
        "primary": 0.6,
        "config": 0.3,
        "other": 0.1
    }
    
    @validator("max_file_size_mb")
    def max_file_size_to_bytes(cls, v: float) -> int:
        """Convert max file size from MB to bytes."""
        return int(v * 1024 * 1024)
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class FrameworkDetectionSettings(BaseSettings):
    """Settings for framework and pattern detection."""
    min_pattern_confidence: float = 0.6
    definitive_pattern_weight: float = 1.0
    suggestive_pattern_weight: float = 0.5
    pattern_registry_path: str = "data/patterns"
    signature_match_threshold: float = 0.7
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class OutputSettings(BaseSettings):
    """Settings for output generation and reporting."""
    default_output_format: str = "json"
    available_formats: List[str] = ["json", "markdown", "html", "csv"]
    visualizations_enabled: bool = True
    confidence_threshold: float = 0.5
    detail_level: str = "medium"
    include_evidence: bool = True
    
    # Updated validator for Pydantic v2
    @validator("default_output_format")
    def validate_output_format(cls, v: str, values) -> str:
        """Validate that the output format is supported."""
        available_formats = values.get("available_formats", ["json", "markdown", "html", "csv"])
        if v not in available_formats:
            raise ValueError(f"Output format {v} not supported")
        return v
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class APISettings(BaseSettings):
    """Settings for the API service."""
    title: str = "Technology Extraction API"
    description: str = "API for extracting technologies from codebases"
    version: str = "0.1.0"
    openapi_url: str = "/openapi.json"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    root_path: str = ""
    cors_origins: List[Union[str, AnyHttpUrl]] = ["*"]
    api_prefix: str = "/api/v1"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class Settings(BaseSettings):
    """Main settings class that includes all subsettings."""
    project_name: str = "Technology Extraction System"
    debug: bool = Field(False, alias="DEBUG")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    environment: str = Field("development", alias="ENVIRONMENT")
    
    # Include all subsettings
    ai: AISettings = AISettings()
    db: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    file_collection: FileCollectionSettings = FileCollectionSettings()
    framework_detection: FrameworkDetectionSettings = FrameworkDetectionSettings()
    output: OutputSettings = OutputSettings()
    api: APISettings = APISettings()
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", 
                                     case_sensitive=True, extra="ignore")


# Create a global settings instance
settings = Settings()