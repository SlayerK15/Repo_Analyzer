"""
AI module for RepoAnalyzer.

This module provides AI-powered enhancements to the repository analysis
functionality, including improved technology detection, architecture analysis,
and code quality assessment.
"""

from repo_analyzer.ai.ai_integration import AIIntegration
from repo_analyzer.ai.ai_detector import AIDetector
from repo_analyzer.ai.prompt_templates import PROMPT_TEMPLATES

__all__ = ['AIIntegration', 'AIDetector', 'PROMPT_TEMPLATES']