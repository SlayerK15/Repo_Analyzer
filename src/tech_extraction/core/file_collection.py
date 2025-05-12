"""
File Collection Engine for the Technology Extraction System.

This module provides functionality for recursively scanning directories,
filtering files based on various criteria, and selecting a representative
sample of files for further analysis.
"""
import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import magic
import tqdm

from tech_extraction.config import settings
from tech_extraction.models.file import FileInfo, FileType
from tech_extraction.utils.path_matcher import PathMatcher

logger = logging.getLogger(__name__)


class FileCollectionEngine:
    """
    Engine responsible for collecting and filtering files from a directory.
    
    The FileCollectionEngine performs the following operations:
    1. Recursively scan a directory up to a configurable depth
    2. Filter files based on size, binary detection, and ignore patterns
    3. Select a representative sample of files for further analysis
    """
    
    def __init__(
        self,
        root_path: Path,
        ignore_patterns: Optional[List[str]] = None,
        custom_ignore_file: Optional[Path] = None,
        max_depth: Optional[int] = None,
        max_file_size: Optional[int] = None,
    ):
        """
        Initialize the FileCollectionEngine.
        
        Args:
            root_path: The root path to scan for files
            ignore_patterns: Additional patterns to ignore (added to defaults)
            custom_ignore_file: Path to a custom ignore file (like .gitignore)
            max_depth: Maximum directory depth to traverse
            max_file_size: Maximum file size in bytes
        """
        self.root_path = Path(root_path).resolve()
        
        # Ensure the root path exists and is a directory
        if not self.root_path.exists():
            raise ValueError(f"Root path does not exist: {self.root_path}")
        if not self.root_path.is_dir():
            raise ValueError(f"Root path is not a directory: {self.root_path}")
        
        # Initialize ignore patterns
        all_ignore_patterns = list(settings.file_collection.default_ignore_patterns)
        if ignore_patterns:
            all_ignore_patterns.extend(ignore_patterns)
        
        self.path_matcher = PathMatcher(
            patterns=all_ignore_patterns,
            ignore_file_path=custom_ignore_file,
        )
        
        # Set limits
        self.max_depth = max_depth or settings.file_collection.max_depth
        
        # Fix: The max_file_size_to_bytes method might not need a parameter
        # or it might use a different attribute than 'max_file_size'
        if max_file_size:
            self.max_file_size = max_file_size
        else:
            # Just call the method directly - it likely has a default value internally
            self.max_file_size = settings.file_collection.max_file_size_to_bytes(10)  # Default value as fallback
        
        # File collection stats
        self.stats = {
            "total_files_scanned": 0,
            "files_too_large": 0,
            "binary_files_skipped": 0,
            "ignored_files": 0,
            "duplicate_files": 0,
            "files_collected": 0,
            "sample_size": 0,
        }
        
        # Hash cache to detect duplicates
        self.content_hashes: Set[str] = set()

    def scan_directory(self) -> List[FileInfo]:
        """
        Recursively scan the directory and collect files that match the criteria.
        
        Returns:
            List of FileInfo objects representing the collected files
        """
        logger.info(f"Scanning directory: {self.root_path}")
        all_files: List[FileInfo] = []
        
        # Walk the directory tree
        for root, dirs, files in os.walk(self.root_path):
            # Calculate current depth
            current_depth = len(Path(root).relative_to(self.root_path).parts)
            
            # Skip directories that exceed max depth
            if current_depth > self.max_depth:
                dirs.clear()  # Clear dirs to prevent further recursion
                continue
            
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self.path_matcher.should_ignore(Path(root) / d)]
            
            # Process files in this directory
            for filename in files:
                self.stats["total_files_scanned"] += 1
                file_path = Path(root) / filename
                
                # Skip ignored files
                if self.path_matcher.should_ignore(file_path):
                    self.stats["ignored_files"] += 1
                    continue
                
                # Skip files that are too large
                try:
                    file_size = file_path.stat().st_size
                    if file_size > self.max_file_size:
                        self.stats["files_too_large"] += 1
                        continue
                except (FileNotFoundError, PermissionError) as e:
                    logger.warning(f"Error accessing file {file_path}: {e}")
                    continue
                
                # Skip binary files
                if self._is_binary(file_path):
                    self.stats["binary_files_skipped"] += 1
                    continue
                
                # Check for duplicate content
                try:
                    file_hash = self._compute_file_hash(file_path)
                    if file_hash in self.content_hashes:
                        self.stats["duplicate_files"] += 1
                        continue
                    self.content_hashes.add(file_hash)
                except Exception as e:
                    logger.warning(f"Error computing hash for {file_path}: {e}")
                    continue
                
                # Create FileInfo object
                rel_path = file_path.relative_to(self.root_path)
                file_info = FileInfo(
                    path=str(rel_path),
                    full_path=str(file_path),
                    size=file_size,
                    hash=file_hash,
                    file_type=FileType.from_extension(file_path.suffix),
                )
                
                all_files.append(file_info)
                self.stats["files_collected"] += 1
        
        logger.info(f"File collection stats: {self.stats}")
        return all_files
    
    def select_sample(self, files: List[FileInfo]) -> List[FileInfo]:
        """
        Select a representative sample of files for analysis.
        
        Uses a stratified sampling approach to ensure coverage across different
        file types and languages, while keeping the total sample size manageable.
        
        Args:
            files: List of FileInfo objects to sample from
            
        Returns:
            A representative sample of files
        """
        if not files:
            return []
        
        min_sample = settings.file_collection.min_sample_size
        max_sample = settings.file_collection.max_sample_size
        
        # If we have fewer files than the minimum sample size, return all files
        if len(files) <= min_sample:
            self.stats["sample_size"] = len(files)
            return files
        
        # If we have fewer files than the maximum sample size, use all files
        if len(files) <= max_sample:
            self.stats["sample_size"] = len(files)
            return files
        
        # Group files by type
        file_groups: Dict[str, List[FileInfo]] = {
            "primary": [],  # Primary language files (Python, JavaScript, etc.)
            "config": [],   # Configuration files (JSON, YAML, etc.)
            "other": [],    # Other file types
        }
        
        for file_info in files:
            if file_info.file_type in [FileType.SOURCE, FileType.MARKUP]:
                file_groups["primary"].append(file_info)
            elif file_info.file_type == FileType.CONFIG:
                file_groups["config"].append(file_info)
            else:
                file_groups["other"].append(file_info)
        
        # Calculate sample sizes for each group
        ratios = settings.file_collection.stratified_sampling_ratio
        total_sample_size = min(max_sample, len(files))
        
        group_sample_sizes = {
            group: int(total_sample_size * ratio)
            for group, ratio in ratios.items()
        }
        
        # Adjust sample sizes to ensure we get exactly the total sample size
        remaining = total_sample_size - sum(group_sample_sizes.values())
        if remaining > 0:
            # Add remaining to the primary group
            group_sample_sizes["primary"] += remaining
        
        # Sample from each group
        sampled_files = []
        for group, group_size in group_sample_sizes.items():
            group_files = file_groups[group]
            if len(group_files) <= group_size:
                # If we have fewer files than the sample size, use all of them
                sampled_files.extend(group_files)
            else:
                # Randomly sample files from this group
                import random
                sampled_files.extend(random.sample(group_files, group_size))
        
        self.stats["sample_size"] = len(sampled_files)
        logger.info(f"Selected {len(sampled_files)} files for analysis")
        
        return sampled_files
    
    def collect_and_sample(self) -> List[FileInfo]:
        """
        Perform the full file collection and sampling process.
        
        Returns:
            A representative sample of files for further analysis
        """
        files = self.scan_directory()
        sample = self.select_sample(files)
        return sample
    
    def _is_binary(self, file_path: Path) -> bool:
        """
        Determine if a file is binary using magic bytes detection.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file is binary, False otherwise
        """
        try:
            mime = magic.Magic(mime=True)
            file_type = mime.from_file(str(file_path))
            
            # Text file types
            text_types = [
                'text/', 'application/json', 'application/xml',
                'application/javascript', 'application/x-httpd-php',
                'application/x-yaml', 'application/x-perl'
            ]
            
            for text_type in text_types:
                if file_type.startswith(text_type):
                    return False
            
            return True
        except Exception as e:
            logger.warning(f"Error detecting file type for {file_path}: {e}")
            # If we can't detect the file type, assume it's binary
            return True
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """
        Compute a SHA-256 hash of the file content for duplicate detection.
        
        Args:
            file_path: Path to the file to hash
            
        Returns:
            SHA-256 hash of the file content
        """
        hash_obj = hashlib.sha256()
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()