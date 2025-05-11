"""
Utility functions for working with files in a repository.

This module provides helper functions for scanning repositories, 
finding files, loading file content, and other file-related operations
that support the repository analysis process.
"""

import os
import logging
from typing import Dict, List, Set, Optional

logger = logging.getLogger(__name__)

def get_all_files(repo_path: str, exclude_dirs: Optional[Set[str]] = None) -> List[str]:
    """
    Get all files in the repository, excluding specified directories.
    
    This function walks through the repository directory recursively,
    collecting all file paths while skipping directories specified in
    the exclude_dirs set.
    
    Args:
        repo_path: Path to the repository
        exclude_dirs: Set of directory names to exclude (default: None)
        
    Returns:
        List of relative file paths in the repository
    """
    all_files = []
    exclude_dirs = exclude_dirs or set()
    
    for root, dirs, files in os.walk(repo_path):
        # Skip excluded directories by modifying dirs in-place
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            file_path = os.path.join(root, file)
            
            # Get path relative to repo_path
            relative_path = os.path.relpath(file_path, repo_path)
            all_files.append(relative_path)
    
    return all_files

def load_files_content(repo_path: str, files: List[str], max_file_size: int = 5 * 1024 * 1024) -> Dict[str, str]:
    """
    Load content of relevant files for deeper analysis.
    
    This function loads the content of files that might contain useful information
    for the technology stack analysis, focusing on certain file extensions and
    respecting a maximum file size to avoid memory issues.
    
    Args:
        repo_path: Path to the repository
        files: List of file paths (relative to repo_path)
        max_file_size: Maximum file size in bytes to load (default: 5MB)
        
    Returns:
        Dict mapping file paths to their content
    """
    content = {}
    
    # Define relevant extensions for content analysis
    relevant_extensions = {
        # Code files
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rb', '.php', '.cs',
        '.rs', '.c', '.cpp', '.swift', '.kt', '.scala', '.sh', '.bash', '.ps1',
        
        # Web files
        '.html', '.css', '.scss', '.less', '.vue', '.svelte', 
        
        # Config files
        '.json', '.yml', '.yaml', '.xml', '.toml', '.ini', '.conf', '.properties',
        '.gradle', '.lock', '.mod', '.sum', '.csproj', '.sln',
        
        # Package files
        'Gemfile', 'Rakefile', 'Dockerfile', 'Makefile', 'requirements.txt',
        'package.json', 'composer.json', 'pom.xml', 'build.gradle',
        
        # Special cases
        '.gitignore', '.dockerignore'
    }
    
    # Total files to process
    total_files = len(files)
    processed = 0
    skipped_size = 0
    skipped_ext = 0
    skipped_error = 0
    
    for file_path in files:
        processed += 1
        if processed % 100 == 0:
            logger.debug(f"Processing file {processed}/{total_files}")
        
        # Check file extension
        _, ext = os.path.splitext(file_path)
        filename = os.path.basename(file_path)
        
        # Check if file should be analyzed (by extension or full filename)
        if ext.lower() in relevant_extensions or filename in relevant_extensions:
            full_path = os.path.join(repo_path, file_path)
            
            try:
                # Check file size
                file_size = os.path.getsize(full_path)
                if file_size > max_file_size:
                    logger.debug(f"Skipping large file: {file_path} ({file_size} bytes)")
                    skipped_size += 1
                    continue
                
                # Check if it's likely a binary file (simple heuristic)
                if _is_likely_binary(full_path):
                    logger.debug(f"Skipping likely binary file: {file_path}")
                    skipped_ext += 1
                    continue
                
                # Load file content
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_content = f.read()
                    
                    # Only store non-empty content
                    if file_content.strip():
                        content[file_path] = file_content
                    
            except Exception as e:
                logger.debug(f"Error reading file {file_path}: {str(e)}")
                skipped_error += 1
        else:
            skipped_ext += 1
    
    logger.debug(f"Files processed: {processed}, content loaded: {len(content)}")
    logger.debug(f"Files skipped - size: {skipped_size}, extension: {skipped_ext}, error: {skipped_error}")
    
    return content

def _is_likely_binary(file_path: str) -> bool:
    """
    Check if a file is likely binary using a simple heuristic.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if the file is likely binary, False otherwise
    """
    # Common binary file extensions
    binary_extensions = {
        '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.gz', '.tar',
        '.jar', '.class', '.pyc', '.pyd', '.so', '.dll', '.exe', '.bin', '.dat',
        '.db', '.sqlite', '.o', '.obj', '.a', '.lib', '.dylib', '.iso', '.mp3',
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.wav', '.ogg', '.woff', '.woff2',
        '.ttf', '.eot', '.svg'
    }
    
    # Check extension
    _, ext = os.path.splitext(file_path)
    if ext.lower() in binary_extensions:
        return True
    
    # Read a small chunk to check for binary data
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            chunk = f.read(1024)
            # Count control characters (except common ones like newline, tab)
            control_chars = sum(1 for c in chunk if ord(c) < 32 and c not in '\n\r\t')
            # If more than 10% are control characters, likely binary
            if len(chunk) > 0 and control_chars / len(chunk) > 0.1:
                return True
    except Exception:
        # If we can't read it as text, it's likely binary
        return True
    
    return False

def get_directory_structure(repo_path: str, exclude_dirs: Optional[Set[str]] = None) -> Dict:
    """
    Get the directory structure of the repository.
    
    This function creates a nested dictionary representing the directory structure,
    which can be useful for identifying architecture patterns.
    
    Args:
        repo_path: Path to the repository
        exclude_dirs: Set of directory names to exclude (default: None)
        
    Returns:
        Nested dictionary representing the directory structure
    """
    exclude_dirs = exclude_dirs or set()
    structure = {}
    
    for root, dirs, files in os.walk(repo_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        # Get path relative to repo_path
        path = os.path.relpath(root, repo_path)
        if path == '.':
            # Skip root directory
            continue
        
        # Create nested dictionary
        parts = path.split(os.sep)
        current = structure
        for part in parts:
            if part not in current:
                current[part] = {}
            current = current[part]
    
    return structure

def count_files_by_type(files: List[str]) -> Dict[str, int]:
    """
    Count files by extension.
    
    Args:
        files: List of file paths
        
    Returns:
        Dict mapping file extensions to counts
    """
    counts = {}
    
    for file_path in files:
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext:
            counts[ext] = counts.get(ext, 0) + 1
    
    return counts

def find_files_matching_patterns(files: List[str], patterns: List[str]) -> List[str]:
    """
    Find files whose paths match any of the given patterns.
    
    Args:
        files: List of file paths
        patterns: List of patterns to match (substring matches)
        
    Returns:
        List of file paths that match any pattern
    """
    matching_files = []
    
    for file_path in files:
        if any(pattern in file_path for pattern in patterns):
            matching_files.append(file_path)
    
    return matching_files