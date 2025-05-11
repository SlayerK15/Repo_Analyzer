#!/usr/bin/env python3
"""
Basic example showing how to use the RepoAnalyzer library.

This example demonstrates analyzing a local repository to identify
its complete technology stack.
"""

import os
import sys
import json
from pathlib import Path

# Ensure the repo_analyzer package is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import RepoAnalyzer
from repo_analyzer import RepoAnalyzer

def main():
    """Run the basic example."""
    # Get repository path from command line or use current directory
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
    else:
        # Use the repository's own code for self-analysis
        repo_path = str(Path(__file__).parent.parent)

    print(f"Analyzing repository: {repo_path}")
    
    # Configure the analyzer
    # You can customize these parameters
    exclude_dirs = {"node_modules", "venv", "__pycache__", ".git"}
    max_file_size = 2 * 1024 * 1024  # 2MB
    verbose = True
    
    # Create an analyzer instance
    analyzer = RepoAnalyzer(
        repo_path=repo_path,
        exclude_dirs=exclude_dirs,
        max_file_size=max_file_size,
        verbose=verbose
    )
    
    # Run the analysis
    print("Running analysis...")
    tech_stack = analyzer.analyze()
    
    # Print a summary to the console
    print("\n=== Analysis Summary ===")
    analyzer.print_summary()
    
    # Save results to a file
    output_file = "analysis_results.json"
    analyzer.save_results(output_file)
    print(f"\nDetailed results saved to: {output_file}")
    
    # Access specific components from the tech stack
    primary_language = tech_stack["primary_technologies"].get("languages")
    primary_framework = tech_stack["primary_technologies"].get("frameworks")
    
    print(f"\nPrimary language: {primary_language}")
    print(f"Primary framework: {primary_framework}")
    
    # Show languages with confidence scores
    print("\nLanguages detected:")
    for language, details in tech_stack.get("languages", {}).items():
        confidence = details.get("confidence", 0)
        if confidence > 30:  # Only show languages with reasonable confidence
            print(f"- {language}: {confidence:.1f}% confidence")

if __name__ == "__main__":
    main()
