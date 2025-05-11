#!/usr/bin/env python3
"""
AI-enhanced repository analysis example.

This example demonstrates how to use the AI-enhanced RepoAnalyzer to analyze
a repository with AI assistance for more accurate detection and intelligent
recommendations.
"""

import os
import sys
import json
from pathlib import Path

# Ensure the repo_analyzer package is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import enhanced RepoAnalyzer
from analyzer_enhanced import RepoAnalyzer

def main():
    """Run the AI-enhanced analyzer example."""
    # Get repository path from command line or use current directory
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
    else:
        # Use the repository's own code for self-analysis
        repo_path = str(Path(__file__).parent.parent)

    print(f"Analyzing repository with AI assistance: {repo_path}")
    
    # Configure the analyzer
    exclude_dirs = {"node_modules", "venv", "__pycache__", ".git"}
    max_file_size = 2 * 1024 * 1024  # 2MB
    verbose = True
    
    # Configure AI settings
    # Note: You'll need to set the appropriate API key in your environment
    # For OpenAI: export OPENAI_API_KEY="your-api-key"
    # For Anthropic: export ANTHROPIC_API_KEY="your-api-key"
    ai_config = {
        "enabled": True,
        "provider": "openai",  # or "anthropic", "local", "huggingface"
        "model": "gpt-4",  # or "claude-3-opus", etc.
        "temperature": 0.1,
        "cache_enabled": True,  # Cache results to avoid redundant API calls
    }
    
    # Create an enhanced analyzer instance with AI capabilities
    analyzer = RepoAnalyzer(
        repo_path=repo_path,
        exclude_dirs=exclude_dirs,
        max_file_size=max_file_size,
        verbose=verbose,
        ai_config=ai_config
    )
    
    print("Running AI-enhanced analysis...")
    tech_stack = analyzer.analyze()
    
    # Print a summary to the console
    print("\n=== AI-Enhanced Analysis Summary ===")
    analyzer.print_summary()
    
    # Print AI-specific summary
    print("\n=== AI Analysis Details ===")
    analyzer.print_ai_summary()
    
    # Save results to a file
    output_file = "ai_analysis_results.json"
    analyzer.save_results(output_file)
    print(f"\nDetailed results saved to: {output_file}")
    
    # Access AI-specific insights
    if "ai_analysis" in tech_stack and tech_stack["ai_analysis"].get("enabled", False):
        # Get AI recommendations
        print("\n=== AI Recommendations ===")
        recommendations = tech_stack["ai_analysis"].get("recommendations", [])
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec.get('text', 'No recommendation text')}")
            print(f"   Severity: {rec.get('severity', 'N/A')}")
            print(f"   Reason: {rec.get('reason', 'N/A')}")
            print()
        
        # Get code quality assessment if available
        if "code_quality" in tech_stack["ai_analysis"]:
            quality = tech_stack["ai_analysis"]["code_quality"].get("quality_assessment", {})
            
            print("\n=== Code Quality Assessment ===")
            for aspect, details in quality.items():
                score = details.get("score", "N/A")
                print(f"{aspect.capitalize()}: {score}/100")
                
                print("  Strengths:")
                for strength in details.get("strengths", []):
                    print(f"  - {strength}")
                
                print("  Weaknesses:")
                for weakness in details.get("weaknesses", []):
                    print(f"  - {weakness}")
                print()
    else:
        print("\nAI analysis was not enabled or failed to run.")
        print("Check that you have set the appropriate API key.")

if __name__ == "__main__":
    main()
