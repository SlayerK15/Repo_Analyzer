"""
Prompt Engineering Subsystem for the Technology Extraction System.

This module provides functionality for generating optimized prompts for
AI models to extract technology information from code snippets.
"""
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from tech_extraction.config import settings
from tech_extraction.models.file import FileInfo, LanguageInfo

logger = logging.getLogger(__name__)


class PromptEngineeringSubsystem:
    """
    Subsystem for generating optimized prompts for AI models.
    
    The PromptEngineeringSubsystem performs the following operations:
    1. Generate language-specific prompts for technology detection
    2. Include appropriate context from files
    3. Optimize prompts for token usage
    """
    
    # Maximum tokens to include from a single file
    MAX_FILE_TOKENS = 2000
    
    # Estimated tokens per character for different languages
    TOKENS_PER_CHAR = {
        "default": 0.25,  # General ratio for most languages
        "Chinese": 0.5,   # Higher ratio for languages with non-ASCII characters
        "Japanese": 0.5,
        "Korean": 0.5,
        "Thai": 0.5,
        "Arabic": 0.4,
        "Russian": 0.35,
    }
    
    # Framework detection prompt template
    FRAMEWORK_DETECTION_TEMPLATE = """
You are an expert code analyzer tasked with identifying technologies, libraries, and frameworks used in code snippets.

Based on the following code file, identify all frameworks, libraries, and technologies being used.
Focus on concrete evidence in the code, not speculation. Provide confidence levels (0-100) for each detection.

File Path: {file_path}
Language: {language}
Size: {size} bytes

Code:
```{language_syntax}
{code_content}
```

Respond with a JSON object in this format:
{{
  "technologies": [
    {{
      "name": "technology name",
      "category": "framework|library|language|tool",
      "confidence": 90,
      "evidence": ["specific evidence from code"]
    }},
    // additional technologies...
  ]
}}
"""
    
    # Architecture analysis prompt template
    ARCHITECTURE_ANALYSIS_TEMPLATE = """
You are an expert software architect tasked with analyzing code to identify architectural patterns and design principles.

Based on the following code files, identify the architectural patterns, design principles, and code organization being used.
Focus on concrete evidence in the code, not speculation. Provide confidence levels (0-100) for each detection.

{file_summaries}

Respond with a JSON object in this format:
{{
  "architecture": [
    {{
      "pattern": "pattern name",
      "type": "architectural_pattern|design_pattern|code_organization",
      "confidence": 90,
      "evidence": ["specific evidence from code"]
    }},
    // additional patterns...
  ],
  "database_integration": [
    {{
      "type": "ORM|query_builder|raw_sql",
      "technology": "technology name", 
      "confidence": 85,
      "evidence": ["specific evidence from code"]
    }}
  ],
  "api_patterns": [
    {{
      "type": "REST|GraphQL|RPC|SOAP",
      "confidence": 80,
      "evidence": ["specific evidence from code"]
    }}
  ]
}}
"""
    
    # Technology recommendation prompt template
    TECHNOLOGY_RECOMMENDATION_TEMPLATE = """
You are an expert technology consultant tasked with analyzing a codebase and suggesting improvements, updates, or alternatives.

Based on the following technologies detected in the codebase, provide recommendations for:
1. Version updates if technologies appear outdated
2. Alternative technologies that might improve the codebase
3. Additional technologies that would complement the existing stack

Existing technologies:
{detected_technologies}

Respond with a JSON object in this format:
{{
  "recommendations": [
    {{
      "type": "update|alternative|addition",
      "current_technology": "current technology name",
      "recommended_technology": "recommended technology name",
      "reasoning": "brief explanation of the recommendation",
      "priority": "high|medium|low"
    }},
    // additional recommendations...
  ]
}}
"""
    
    def __init__(self):
        """Initialize the prompt engineering subsystem."""
        pass
    
    def estimate_tokens(self, text: str, language: str = "default") -> int:
        """
        Estimate the number of tokens in a piece of text.
        
        Args:
            text: The text to estimate tokens for
            language: The human language of the text
            
        Returns:
            Estimated token count
        """
        tokens_per_char = self.TOKENS_PER_CHAR.get(language, self.TOKENS_PER_CHAR["default"])
        return int(len(text) * tokens_per_char)
    
    def truncate_content(self, content: str, max_tokens: int, language: str = "default") -> str:
        """
        Truncate content to fit within token limit.
        
        Args:
            content: The content to truncate
            max_tokens: Maximum tokens to allow
            language: The human language of the content
            
        Returns:
            Truncated content
        """
        estimated_tokens = self.estimate_tokens(content, language)
        
        if estimated_tokens <= max_tokens:
            return content
        
        # Calculate approximate character limit
        tokens_per_char = self.TOKENS_PER_CHAR.get(language, self.TOKENS_PER_CHAR["default"])
        char_limit = int(max_tokens / tokens_per_char)
        
        # Try to truncate at a newline to keep context cleaner
        truncated = content[:char_limit]
        last_newline = truncated.rfind('\n')
        
        if last_newline > char_limit * 0.8:  # Only use newline if it's not too far back
            truncated = truncated[:last_newline]
        
        return truncated + "\n\n[... truncated due to length ...]"
    
    def select_important_snippets(self, content: str, max_tokens: int, language: str = "default") -> str:
        """
        Select important parts of the content to include in the prompt.
        
        This is a more sophisticated version of truncation that attempts to preserve
        the most important parts of the file for technology detection.
        
        Args:
            content: The file content
            max_tokens: Maximum tokens to include
            language: The programming language
            
        Returns:
            Selected content snippets
        """
        # For now, we'll prioritize:
        # 1. Imports/includes at the top
        # 2. Class/function definitions
        # 3. Start and end of the file
        
        # If the content is small enough, just return it all
        if self.estimate_tokens(content, language) <= max_tokens:
            return content
        
        lines = content.split('\n')
        
        # Get the first ~20% of the file (likely to contain imports)
        first_part_size = int(len(lines) * 0.2)
        first_part = lines[:first_part_size]
        
        # Get important lines with class/function definitions
        important_patterns = [
            r"^\s*(?:class|def|function|import|include|from|package|use|require)",
            r"^\s*@(?:Component|Controller|Service|Repository|Entity|RestController|Module)",
            r"^\s*<(?:template|component|script|style)",
        ]
        
        important_lines = []
        for i, line in enumerate(lines[first_part_size:], first_part_size):
            for pattern in important_patterns:
                if re.match(pattern, line):
                    # Include the line and a few lines after it for context
                    context_lines = min(3, len(lines) - i)
                    important_lines.extend(lines[i:i+context_lines])
                    important_lines.append('')  # Empty line as separator
                    break
        
        # Combine first part with important lines
        result = '\n'.join(first_part)
        result += '\n\n[...]\n\n'
        result += '\n'.join(important_lines)
        
        # If we still have token budget, include the end of the file
        combined_tokens = self.estimate_tokens(result, language)
        if combined_tokens < max_tokens:
            remaining_tokens = max_tokens - combined_tokens
            chars_per_token = 1 / self.TOKENS_PER_CHAR.get(language, self.TOKENS_PER_CHAR["default"])
            chars_to_include = int(remaining_tokens * chars_per_token * 0.8)  # 80% to be safe
            
            # Add the end of the file
            end_part = '\n'.join(lines[-20:])  # Last 20 lines as a simple heuristic
            if len(end_part) > chars_to_include:
                end_part = end_part[-chars_to_include:]
                # Try to start at a newline for cleaner context
                first_newline = end_part.find('\n')
                if first_newline > 0:
                    end_part = end_part[first_newline+1:]
            
            result += '\n\n[...]\n\n' + end_part
        
        # Final check to ensure we're within token budget
        if self.estimate_tokens(result, language) > max_tokens:
            result = self.truncate_content(result, max_tokens, language)
        
        return result
    
    def generate_framework_detection_prompt(
        self, file_info: FileInfo, language_info: LanguageInfo
    ) -> str:
        """
        Generate a prompt for framework detection.
        
        Args:
            file_info: Information about the file
            language_info: Language information
            
        Returns:
            Generated prompt for framework detection
        """
        try:
            # Read file content
            with open(file_info.full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Select important content based on token budget
            max_tokens = self.MAX_FILE_TOKENS
            selected_content = self.select_important_snippets(content, max_tokens, language_info.name)
            
            # Map language to syntax highlighting format
            language_syntax = language_info.name.lower()
            if language_syntax == "javascript (react)":
                language_syntax = "jsx"
            elif language_syntax == "typescript (react)":
                language_syntax = "tsx"
            
            # Generate prompt
            prompt = self.FRAMEWORK_DETECTION_TEMPLATE.format(
                file_path=file_info.path,
                language=language_info.name,
                size=file_info.size,
                language_syntax=language_syntax,
                code_content=selected_content
            )
            
            return prompt
        
        except Exception as e:
            logger.error(f"Error generating framework detection prompt for {file_info.path}: {e}")
            return ""
    
    def generate_architecture_analysis_prompt(
        self, file_summaries: List[Dict[str, Union[str, FileInfo, LanguageInfo]]]
    ) -> str:
        """
        Generate a prompt for architecture analysis.
        
        Args:
            file_summaries: List of file summaries
            
        Returns:
            Generated prompt for architecture analysis
        """
        try:
            # Create file summary text
            summaries_text = ""
            
            for i, summary in enumerate(file_summaries, 1):
                file_info = summary["file_info"]
                language_info = summary["language_info"]
                content = summary.get("content", "")
                
                if not content:
                    try:
                        with open(file_info.full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Limit content size
                        content = self.select_important_snippets(content, 800, language_info.name)
                    except Exception as e:
                        logger.warning(f"Error reading file {file_info.path}: {e}")
                        content = "[Error reading file]"
                
                # Map language to syntax highlighting format
                language_syntax = language_info.name.lower()
                if language_syntax == "javascript (react)":
                    language_syntax = "jsx"
                elif language_syntax == "typescript (react)":
                    language_syntax = "tsx"
                
                summary_text = f"File {i}: {file_info.path}\n"
                summary_text += f"Language: {language_info.name}\n"
                summary_text += f"Code:\n```{language_syntax}\n{content}\n```\n\n"
                
                summaries_text += summary_text
            
            # Generate prompt
            prompt = self.ARCHITECTURE_ANALYSIS_TEMPLATE.format(
                file_summaries=summaries_text
            )
            
            return prompt
        
        except Exception as e:
            logger.error(f"Error generating architecture analysis prompt: {e}")
            return ""
    
    def generate_technology_recommendation_prompt(
        self, detected_technologies: List[Dict]
    ) -> str:
        """
        Generate a prompt for technology recommendations.
        
        Args:
            detected_technologies: List of detected technologies
            
        Returns:
            Generated prompt for technology recommendations
        """
        try:
            # Format detected technologies
            tech_text = ""
            
            for tech in detected_technologies:
                tech_text += f"- {tech['name']} (Category: {tech['category']}, Confidence: {tech['confidence']})\n"
                if "version" in tech and tech["version"]:
                    tech_text += f"  Version: {tech['version']}\n"
            
            # Generate prompt
            prompt = self.TECHNOLOGY_RECOMMENDATION_TEMPLATE.format(
                detected_technologies=tech_text
            )
            
            return prompt
        
        except Exception as e:
            logger.error(f"Error generating technology recommendation prompt: {e}")
            return ""
    
    def optimize_context_window(
        self, files: List[Tuple[FileInfo, LanguageInfo]], token_budget: int
    ) -> List[Dict]:
        """
        Optimize the use of the context window by selecting representative file snippets.
        
        Args:
            files: List of (file_info, language_info) tuples
            token_budget: Total token budget available
            
        Returns:
            List of file dictionaries with selected content
        """
        # Calculate base allocation per file
        base_allocation = token_budget // len(files)
        
        result = []
        remaining_budget = token_budget
        
        # First pass: allocate base tokens to each file
        for file_info, language_info in files:
            # Skip files we can't read
            try:
                with open(file_info.full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Calculate importance score (can be extended with more criteria)
                importance = 1.0
                # Config files and main files get higher importance
                if any(pattern in file_info.path.lower() for pattern in 
                       ['config', 'settings', 'main', 'index', 'app']):
                    importance = 1.5
                
                # Allocate tokens based on importance
                allocated_tokens = min(int(base_allocation * importance), remaining_budget)
                remaining_budget -= allocated_tokens
                
                # Select content based on allocation
                selected_content = self.select_important_snippets(
                    content, allocated_tokens, language_info.name
                )
                
                result.append({
                    "file_info": file_info,
                    "language_info": language_info,
                    "content": selected_content,
                    "allocated_tokens": allocated_tokens,
                })
            
            except Exception as e:
                logger.warning(f"Error processing file {file_info.path}: {e}")
        
        # If we have remaining budget, distribute it to files with high importance first
        if remaining_budget > 0 and result:
            # Sort by importance (for now, just by allocation which reflects importance)
            result.sort(key=lambda x: x["allocated_tokens"], reverse=True)
            
            for file_dict in result:
                if remaining_budget <= 0:
                    break
                
                # Try to allocate more tokens
                additional_tokens = min(500, remaining_budget)  # Cap at 500 additional tokens
                if additional_tokens > 0:
                    file_info = file_dict["file_info"]
                    language_info = file_dict["language_info"]
                    
                    try:
                        with open(file_info.full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        new_allocation = file_dict["allocated_tokens"] + additional_tokens
                        selected_content = self.select_important_snippets(
                            content, new_allocation, language_info.name
                        )
                        
                        file_dict["content"] = selected_content
                        file_dict["allocated_tokens"] = new_allocation
                        remaining_budget -= additional_tokens
                    
                    except Exception as e:
                        logger.warning(f"Error reallocating tokens for {file_info.path}: {e}")
        
        return result