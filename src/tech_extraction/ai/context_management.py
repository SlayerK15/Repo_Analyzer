"""
Context Management for the Technology Extraction System.

This module provides functionality for managing the context window
used by AI models, optimizing token usage, and prioritizing important files.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from tech_extraction.ai.provider_management import AIProviderManager
from tech_extraction.config import settings
from tech_extraction.models.file import FileInfo, LanguageInfo

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manager for optimizing AI context window usage.
    
    The ContextManager performs the following operations:
    1. Prioritize files based on importance
    2. Allocate token budget efficiently
    3. Apply content summarization and chunking strategies
    """
    
    # Importance weights for different file types
    FILE_IMPORTANCE_WEIGHTS = {
        # Configuration files
        "package.json": 10,
        "requirements.txt": 10,
        "build.gradle": 9,
        "pom.xml": 9,
        "Gemfile": 9,
        "go.mod": 9,
        "Cargo.toml": 9,
        "Pipfile": 9,
        ".csproj": 9,
        
        # Main application files
        "app.py": 8,
        "main.py": 8,
        "index.js": 8,
        "server.js": 8,
        "application.java": 8,
        "Program.cs": 8,
        
        # Framework configuration
        "settings.py": 7,
        "urls.py": 7,
        "routes.js": 7,
        "webpack.config.js": 7,
        "tsconfig.json": 7,
        "babel.config.js": 7,
        "angular.json": 7,
        "next.config.js": 7,
        
        # Database models
        "models.py": 6,
        "schema.js": 6,
        "migrations": 5,
        "entities": 5,
        
        # Controllers and views
        "controllers": 4,
        "views": 4,
        "components": 4,
        
        # Test files
        "test": 2,
        "spec": 2,
        
        # Documentation
        "README.md": 3,
        "docs": 2,
    }
    
    def __init__(self, provider_manager: AIProviderManager):
        """
        Initialize the context manager.
        
        Args:
            provider_manager: AI provider manager for token counting
        """
        self.provider_manager = provider_manager
        
        # Token tracking
        self.total_tokens_used = 0
        self.token_budget = 0
        self.token_allocation = {}
    
    def calculate_file_importance(self, file_info: FileInfo) -> float:
        """
        Calculate the importance score of a file for prioritization.
        
        Args:
            file_info: Information about the file
            
        Returns:
            Importance score (higher is more important)
        """
        path = file_info.path.lower()
        filename = Path(path).name
        
        # Start with base importance
        importance = 1.0
        
        # Check for exact filename matches
        if filename in self.FILE_IMPORTANCE_WEIGHTS:
            importance = self.FILE_IMPORTANCE_WEIGHTS[filename]
            return importance
        
        # Check for partial matches in path
        for key, weight in self.FILE_IMPORTANCE_WEIGHTS.items():
            if key.lower() in path:
                importance = max(importance, weight * 0.8)  # Slight discount for partial match
        
        # Boost importance based on other factors
        
        # Size-based importance (smaller files often more critical)
        if file_info.size < 1024:  # < 1KB
            importance *= 1.2
        elif file_info.size > 1024 * 100:  # > 100KB
            importance *= 0.8
        
        # Location-based importance (files at root often more critical)
        if path.count('/') <= 1:
            importance *= 1.2
        
        return importance
    
    def prioritize_files(self, files: List[Tuple[FileInfo, LanguageInfo]]) -> List[Tuple[FileInfo, LanguageInfo, float]]:
        """
        Prioritize files based on importance for analysis.
        
        Args:
            files: List of (file_info, language_info) tuples
            
        Returns:
            List of (file_info, language_info, importance) tuples sorted by importance
        """
        prioritized = []
        
        for file_info, language_info in files:
            importance = self.calculate_file_importance(file_info)
            prioritized.append((file_info, language_info, importance))
        
        # Sort by importance (descending)
        prioritized.sort(key=lambda x: x[2], reverse=True)
        
        return prioritized
    
    def allocate_token_budget(
        self, files: List[Tuple[FileInfo, LanguageInfo, float]], total_budget: int
    ) -> Dict[str, int]:
        """
        Allocate token budget across files based on importance.
        
        Args:
            files: List of (file_info, language_info, importance) tuples
            total_budget: Total token budget available
            
        Returns:
            Dictionary mapping file paths to token allocations
        """
        self.token_budget = total_budget
        allocation = {}
        
        # Calculate total importance for weighted distribution
        total_importance = sum(importance for _, _, importance in files)
        
        # Base allocation: 20% of budget distributed equally, 80% by importance
        base_budget = total_budget * 0.2
        importance_budget = total_budget * 0.8
        
        base_per_file = base_budget / len(files) if files else 0
        
        # Allocate tokens
        for file_info, _, importance in files:
            # Calculate importance-weighted allocation
            importance_allocation = (importance / total_importance) * importance_budget if total_importance > 0 else 0
            
            # Total allocation for this file
            file_allocation = int(base_per_file + importance_allocation)
            
            # Ensure minimum allocation
            file_allocation = max(file_allocation, 100)
            
            allocation[file_info.path] = file_allocation
            self.token_allocation[file_info.path] = file_allocation
        
        logger.info(f"Allocated {sum(allocation.values())} tokens across {len(files)} files")
        return allocation
    
    def chunk_file_content(
        self, content: str, chunk_size: int, overlap: int = 200
    ) -> List[Tuple[str, int, int]]:
        """
        Split file content into chunks for processing.
        
        Args:
            content: File content to chunk
            chunk_size: Maximum chunk size in tokens
            overlap: Overlap between chunks in tokens
            
        Returns:
            List of (chunk_content, start_pos, end_pos) tuples
        """
        chunks = []
        content_length = len(content)
        
        # Estimate chars per token (rough approximation)
        chars_per_token = 4
        chunk_chars = chunk_size * chars_per_token
        overlap_chars = overlap * chars_per_token
        
        # Create chunks
        pos = 0
        while pos < content_length:
            # Calculate end position
            end_pos = min(pos + chunk_chars, content_length)
            
            # If not the last chunk, try to break at a newline
            if end_pos < content_length:
                # Look for a newline to break at
                nl_pos = content.rfind('\n', pos + chunk_chars - overlap_chars, end_pos)
                if nl_pos > pos:
                    end_pos = nl_pos + 1  # Include the newline
            
            # Extract the chunk
            chunk = content[pos:end_pos]
            chunks.append((chunk, pos, end_pos))
            
            # Move to next position with overlap
            if end_pos == content_length:
                break
            
            pos = end_pos - overlap_chars
            # Make sure we advance at least a little
            if pos <= chunks[-1][1]:
                pos = chunks[-1][1] + min(100, chunk_chars // 10)
        
        return chunks
    
    def extract_important_sections(self, content: str, language: str) -> str:
        """
        Extract important sections from file content for summarization.
        
        Args:
            content: File content
            language: Programming language
            
        Returns:
            Extracted important sections
        """
        # Split into lines
        lines = content.split('\n')
        
        # Initialize important sections
        important_lines = []
        
        # Always include the first 10 lines (imports, package declarations, etc.)
        important_lines.extend(lines[:min(10, len(lines))])
        
        # Language-specific important patterns
        patterns_by_language = {
            "Python": [
                r"^import\s+", r"^from\s+.+\s+import", r"^class\s+", r"^def\s+",
                r"@app\.", r"@blueprint\.", r"@route", r"@api", r"asyncio",
                "models", "serializers", "views", "controllers", "app.",
            ],
            "JavaScript": [
                r"^import\s+", r"^const\s+.+\s+=\s+require", r"^class\s+", r"^function\s+",
                r"^const\s+.+\s+=\s+\(.*\)\s+=>\s+{", "express", "app.", "router.",
                "mongoose", "sequelize", "axios",
            ],
            "TypeScript": [
                r"^import\s+", r"^export\s+", r"^interface\s+", r"^type\s+", r"^class\s+",
                r"@Component", r"@Injectable", r"@Module", "@Input", "@Output",
            ],
            "Java": [
                r"^import\s+", r"^package\s+", r"^public\s+class", r"^private\s+class",
                r"@Controller", r"@Service", r"@Repository", r"@Entity", r"@RestController",
            ],
            "Ruby": [
                r"^require", r"^module\s+", r"^class\s+", r"^def\s+",
                "belongs_to", "has_many", "ActiveRecord", "ApplicationController",
            ],
        }
        
        # Get patterns for this language, or use generic patterns
        patterns = patterns_by_language.get(
            language, 
            [r"^import", r"^class", r"^function", r"^def", r"^const", r"^public", r"^private"]
        )
        
        # Scan for important lines
        for i, line in enumerate(lines):
            # Skip if already included in first 10 lines
            if i < 10:
                continue
                
            # Check for important patterns
            if any(pattern in line for pattern in patterns):
                # Include this line and the next 2 lines for context
                important_lines.append(line)
                for j in range(1, 3):
                    if i + j < len(lines):
                        important_lines.append(lines[i + j])
        
        # Add some lines from the end of the file
        if len(lines) > 20:
            important_lines.append("\n# End of file\n")
            important_lines.extend(lines[-5:])
        
        return '\n'.join(important_lines)
    
    def summarize_file_content(self, content: str, language: str, max_tokens: int) -> str:
        """
        Summarize file content to fit within token limit.
        
        Args:
            content: File content
            language: Programming language
            max_tokens: Maximum tokens allowed
            
        Returns:
            Summarized content
        """
        # Count tokens in the original content
        estimated_tokens = self.provider_manager.count_tokens(content)
        
        if estimated_tokens <= max_tokens:
            # No summarization needed
            return content
        
        # Extract important sections first
        important_sections = self.extract_important_sections(content, language)
        
        # Check if important sections fit within token limit
        important_tokens = self.provider_manager.count_tokens(important_sections)
        
        if important_tokens <= max_tokens:
            return important_sections
        
        # Still too large, truncate with indication
        # Estimate chars per token (rough approximation)
        chars_per_token = len(important_sections) / important_tokens
        max_chars = int(max_tokens * chars_per_token * 0.9)  # 10% safety margin
        
        truncated = important_sections[:max_chars]
        
        # Try to truncate at a newline
        last_newline = truncated.rfind('\n')
        if last_newline > max_chars * 0.8:  # Only if not too far back
            truncated = truncated[:last_newline]
        
        truncated += "\n\n... [content truncated to fit token limit] ..."
        
        return truncated
    
    def prepare_file_for_analysis(
        self, file_info: FileInfo, language_info: LanguageInfo, token_allocation: int
    ) -> Tuple[str, int]:
        """
        Prepare a file for analysis by reading content and optimizing for tokens.
        
        Args:
            file_info: Information about the file
            language_info: Language information
            token_allocation: Tokens allocated to this file
            
        Returns:
            Tuple of (optimized_content, tokens_used)
        """
        try:
            # Read file content
            with open(file_info.full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Summarize content to fit within token allocation
            summarized = self.summarize_file_content(
                content, language_info.name, token_allocation
            )
            
            # Count actual tokens used
            tokens_used = self.provider_manager.count_tokens(summarized)
            self.total_tokens_used += tokens_used
            
            return summarized, tokens_used
        
        except Exception as e:
            logger.error(f"Error preparing file {file_info.path} for analysis: {e}")
            return f"[Error reading file: {str(e)}]", 0
    
    def prepare_files_batch(
        self, files: List[Tuple[FileInfo, LanguageInfo]], batch_token_limit: int
    ) -> List[Dict]:
        """
        Prepare a batch of files for analysis, optimizing token usage.
        
        Args:
            files: List of (file_info, language_info) tuples
            batch_token_limit: Maximum tokens for this batch
            
        Returns:
            List of dictionaries with prepared file information
        """
        # Reset token tracking
        self.total_tokens_used = 0
        self.token_allocation = {}
        
        # Prioritize files
        prioritized = self.prioritize_files(files)
        
        # Allocate token budget
        allocation = self.allocate_token_budget(prioritized, batch_token_limit)
        
        # Prepare files
        prepared = []
        remaining_tokens = batch_token_limit
        
        for file_info, language_info, importance in prioritized:
            # Check if we have tokens left
            if remaining_tokens <= 0:
                break
            
            # Adjust allocation if needed
            allocation[file_info.path] = min(allocation[file_info.path], remaining_tokens)
            
            # Prepare file
            content, tokens_used = self.prepare_file_for_analysis(
                file_info, language_info, allocation[file_info.path]
            )
            
            prepared.append({
                "file_info": file_info,
                "language_info": language_info,
                "content": content,
                "tokens_used": tokens_used,
                "importance": importance
            })
            
            remaining_tokens -= tokens_used
        
        logger.info(f"Prepared {len(prepared)} files using {self.total_tokens_used} tokens")
        return prepared
    
    def get_token_usage_stats(self) -> Dict:
        """
        Get token usage statistics.
        
        Returns:
            Dictionary with token usage statistics
        """
        return {
            "total_tokens_used": self.total_tokens_used,
            "token_budget": self.token_budget,
            "token_allocation": self.token_allocation,
            "utilization_percentage": (self.total_tokens_used / self.token_budget * 100) if self.token_budget else 0
        }