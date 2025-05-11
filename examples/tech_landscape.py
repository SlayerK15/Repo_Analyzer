#!/usr/bin/env python3
"""
Technology landscape analyzer.

This example demonstrates how to analyze multiple repositories to create
a technology landscape view across projects. It's useful for understanding
technology patterns in an organization's codebase.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt

# Ensure the repo_analyzer package is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import RepoAnalyzer
from repo_analyzer import RepoAnalyzer

def analyze_repositories(repo_paths, verbose=False):
    """
    Analyze multiple repositories and return aggregated results.
    
    Args:
        repo_paths: List of paths to repositories to analyze
        verbose: Whether to print verbose output
        
    Returns:
        Dict with aggregated technology data
    """
    # Configure common analyzer settings
    exclude_dirs = {"node_modules", "venv", "__pycache__", ".git"}
    max_file_size = 2 * 1024 * 1024  # 2MB
    
    all_results = []
    
    # Analyze each repository
    for repo_path in repo_paths:
        if verbose:
            print(f"Analyzing repository: {repo_path}")
        
        repo_name = os.path.basename(os.path.normpath(repo_path))
        
        try:
            # Create analyzer for this repository
            analyzer = RepoAnalyzer(
                repo_path=repo_path,
                exclude_dirs=exclude_dirs,
                max_file_size=max_file_size,
                verbose=verbose
            )
            
            # Run analysis
            tech_stack = analyzer.analyze()
            
            # Add repository name
            tech_stack["repo_name"] = repo_name
            
            # Add to results
            all_results.append(tech_stack)
            
            if verbose:
                print(f"Completed analysis of {repo_name}")
        
        except Exception as e:
            print(f"Error analyzing {repo_name}: {str(e)}")
    
    return all_results

def aggregate_results(all_results):
    """
    Aggregate technology data across repositories.
    
    Args:
        all_results: List of analysis results from multiple repositories
        
    Returns:
        Dict with aggregated technology data
    """
    tech_landscape = {
        "repositories": [],
        "languages": defaultdict(int),
        "frameworks": defaultdict(int),
        "databases": defaultdict(int),
        "frontend": defaultdict(int),
        "build_systems": defaultdict(int),
        "package_managers": defaultdict(int),
        "devops": defaultdict(int),
        "testing": defaultdict(int),
        "primary_languages": defaultdict(int),
        "primary_frameworks": defaultdict(int)
    }
    
    # Aggregate data from all repositories
    for result in all_results:
        repo_name = result.get("repo_name", "Unknown")
        tech_landscape["repositories"].append(repo_name)
        
        # Count primary technologies
        if "primary_technologies" in result:
            primary_tech = result["primary_technologies"]
            if "languages" in primary_tech and primary_tech["languages"]:
                tech_landscape["primary_languages"][primary_tech["languages"]] += 1
            
            if "frameworks" in primary_tech and primary_tech["frameworks"]:
                tech_landscape["primary_frameworks"][primary_tech["frameworks"]] += 1
        
        # Count all technologies with high confidence
        for category in ["languages", "frameworks", "databases", "frontend", 
                        "build_systems", "package_managers", "devops", "testing"]:
            if category in result:
                for tech, details in result[category].items():
                    if details.get("confidence", 0) > 50:  # Only count high confidence detections
                        tech_landscape[category][tech] += 1
    
    # Convert defaultdicts to regular dicts
    for key in tech_landscape:
        if isinstance(tech_landscape[key], defaultdict):
            tech_landscape[key] = dict(tech_landscape[key])
    
    return tech_landscape

def generate_visualizations(tech_landscape, output_dir):
    """
    Generate visualizations of the technology landscape.
    
    Args:
        tech_landscape: Aggregated technology data
        output_dir: Directory to save visualizations
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create visualizations for categories
    categories = [
        "primary_languages", 
        "primary_frameworks", 
        "languages", 
        "frameworks", 
        "databases", 
        "frontend"
    ]
    
    for category in categories:
        data = tech_landscape.get(category, {})
        if not data:
            continue
            
        # Sort by frequency
        items = sorted(data.items(), key=lambda x: x[1], reverse=True)
        labels = [item[0] for item in items[:10]]  # Top 10 items
        values = [item[1] for item in items[:10]]
        
        # Create figure
        plt.figure(figsize=(10, 6))
        plt.bar(labels, values)
        plt.xlabel('Technology')
        plt.ylabel('Number of Repositories')
        plt.title(f'Top {category.replace("_", " ").title()}')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save figure
        output_file = os.path.join(output_dir, f"{category}_chart.png")
        plt.savefig(output_file)
        plt.close()
        
        print(f"Generated visualization: {output_file}")

def main():
    """Run the tech landscape analyzer."""
    parser = argparse.ArgumentParser(
        description="Analyze multiple repositories to create a technology landscape"
    )
    parser.add_argument(
        "repo_dirs", nargs="+",
        help="Directories containing repositories to analyze"
    )
    parser.add_argument(
        "--output", "-o", default="tech_landscape",
        help="Output directory for results and visualizations"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Find all repositories in the specified directories
    all_repos = []
    for repo_dir in args.repo_dirs:
        if os.path.isdir(repo_dir):
            # Check if this is a git repository
            if os.path.isdir(os.path.join(repo_dir, ".git")):
                all_repos.append(repo_dir)
            else:
                # Check subdirectories for git repositories
                for subdir in os.listdir(repo_dir):
                    full_path = os.path.join(repo_dir, subdir)
                    if os.path.isdir(full_path) and os.path.isdir(os.path.join(full_path, ".git")):
                        all_repos.append(full_path)
    
    if not all_repos:
        print("No repositories found in the specified directories.")
        return
    
    print(f"Found {len(all_repos)} repositories to analyze:")
    for repo in all_repos:
        print(f"- {repo}")
    
    # Analyze repositories
    print(f"\nAnalyzing {len(all_repos)} repositories...")
    results = analyze_repositories(all_repos, args.verbose)
    
    # Aggregate results
    print("\nAggregating results...")
    tech_landscape = aggregate_results(results)
    
    # Save results
    os.makedirs(args.output, exist_ok=True)
    output_file = os.path.join(args.output, "tech_landscape.json")
    with open(output_file, 'w') as f:
        json.dump(tech_landscape, f, indent=2)
    
    print(f"\nSaved technology landscape data to {output_file}")
    
    # Generate visualizations
    try:
        import matplotlib
        print("\nGenerating visualizations...")
        generate_visualizations(tech_landscape, args.output)
    except ImportError:
        print("\nMatplotlib not installed. Skipping visualization generation.")
        print("Install with: pip install matplotlib")
    
    # Print summary
    print("\n=== Technology Landscape Summary ===")
    print(f"Analyzed {len(tech_landscape['repositories'])} repositories")
    
    print("\nTop Primary Languages:")
    for lang, count in sorted(tech_landscape["primary_languages"].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"- {lang}: {count} repositories")
    
    print("\nTop Frameworks:")
    for framework, count in sorted(tech_landscape["frameworks"].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"- {framework}: {count} repositories")
    
    print("\nTop Databases:")
    for db, count in sorted(tech_landscape["databases"].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"- {db}: {count} repositories")

if __name__ == "__main__":
    main()
