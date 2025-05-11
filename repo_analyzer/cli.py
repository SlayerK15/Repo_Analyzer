#!/usr/bin/env python3
"""
Command Line Interface for RepoAnalyzer.

This module provides a user-friendly command-line interface for the 
RepoAnalyzer library, allowing users to analyze repositories and 
generate reports from the terminal.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

# Import main RepoAnalyzer class
from repo_analyzer import RepoAnalyzer

def setup_logger(verbose: bool) -> logging.Logger:
    """
    Set up a logger for the application.
    
    Args:
        verbose: Whether to enable verbose logging
        
    Returns:
        Configured logger instance
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    logger = logging.getLogger("repo-analyzer")
    logger.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="RepoAnalyzer - Analyze code repositories to identify tech stacks",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments
    parser.add_argument(
        "repo_path", 
        help="Path to the repository to analyze"
    )
    
    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--output", "-o", 
        help="Path to save the analysis results (JSON format)"
    )
    output_group.add_argument(
        "--format", "-f", 
        choices=["json", "yaml", "markdown", "text"], 
        default="text",
        help="Output format for the analysis results"
    )
    output_group.add_argument(
        "--pretty", "-p", 
        action="store_true",
        help="Pretty-print JSON output"
    )
    
    # Filtering options
    filter_group = parser.add_argument_group("Filtering Options")
    filter_group.add_argument(
        "--min-confidence", 
        type=int, 
        default=15,
        help="Minimum confidence score for including technologies (0-100)"
    )
    filter_group.add_argument(
        "--categories",
        nargs="+",
        choices=["languages", "frameworks", "databases", "build_systems", 
                "package_managers", "frontend", "devops", "architecture", "testing"],
        help="Only include specific technology categories"
    )
    
    # Analysis options
    analysis_group = parser.add_argument_group("Analysis Options")
    analysis_group.add_argument(
        "--exclude-dirs",
        nargs="+",
        default=[],
        help="Additional directories to exclude from analysis"
    )
    analysis_group.add_argument(
        "--max-file-size",
        type=int,
        default=5 * 1024 * 1024,  # 5MB
        help="Maximum file size in bytes to analyze"
    )
    
    # Visualization options
    viz_group = parser.add_argument_group("Visualization Options")
    viz_group.add_argument(
        "--generate-graph",
        action="store_true",
        help="Generate a graph visualization of the tech stack (requires matplotlib)"
    )
    viz_group.add_argument(
        "--graph-output",
        help="Path to save the graph visualization"
    )
    
    # Add Docker generator integration
    docker_group = parser.add_argument_group("Docker Generator Options")
    docker_group.add_argument(
        "--generate-dockerfile",
        action="store_true",
        help="Generate a Dockerfile based on the detected tech stack"
    )
    docker_group.add_argument(
        "--dockerfile-output",
        help="Path to save the generated Dockerfile"
    )
    
    # Miscellaneous options
    misc_group = parser.add_argument_group("Miscellaneous Options")
    misc_group.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Enable verbose output"
    )
    misc_group.add_argument(
        "--quiet", "-q", 
        action="store_true",
        help="Suppress all output except errors"
    )
    misc_group.add_argument(
        "--version", 
        action="store_true",
        help="Show version information and exit"
    )
    
    return parser.parse_args()

def filter_results(tech_stack: Dict[str, Any], min_confidence: int, 
                  categories: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Filter the tech stack results based on confidence score and categories.
    
    Args:
        tech_stack: The tech stack analysis results
        min_confidence: Minimum confidence score for inclusion
        categories: List of categories to include (if None, include all)
        
    Returns:
        Filtered tech stack results
    """
    filtered_stack = {}
    
    # Copy metadata and primary technologies
    for key in ["metadata", "primary_technologies"]:
        if key in tech_stack:
            filtered_stack[key] = tech_stack[key]
    
    # Filter categories
    for category, technologies in tech_stack.items():
        # Skip metadata and primary technologies
        if category in ["metadata", "primary_technologies"]:
            continue
        
        # Check if this category should be included
        if categories and category not in categories:
            continue
        
        # Filter technologies by confidence score
        filtered_techs = {}
        for tech, details in technologies.items():
            if isinstance(details, dict) and "confidence" in details:
                if details["confidence"] >= min_confidence:
                    filtered_techs[tech] = details
        
        # Add filtered technologies to results
        if filtered_techs:
            filtered_stack[category] = filtered_techs
    
    return filtered_stack

def generate_markdown_report(tech_stack: Dict[str, Any]) -> str:
    """
    Generate a Markdown report from the tech stack analysis.
    
    Args:
        tech_stack: The tech stack analysis results
        
    Returns:
        Markdown-formatted report
    """
    # Get metadata
    metadata = tech_stack.get("metadata", {})
    repo_path = metadata.get("repo_path", "Unknown")
    file_count = metadata.get("file_count", 0)
    analysis_time = metadata.get("analysis_time_seconds", 0)
    analyzed_at = metadata.get("analyzed_at", "Unknown")
    
    # Get primary technologies
    primary_tech = tech_stack.get("primary_technologies", {})
    
    # Start building the markdown report
    markdown = f"# Repository Analysis Report\n\n"
    
    # Add metadata section
    markdown += f"## Metadata\n\n"
    markdown += f"- **Repository:** {repo_path}\n"
    markdown += f"- **Files analyzed:** {file_count}\n"
    markdown += f"- **Analysis time:** {analysis_time:.2f} seconds\n"
    markdown += f"- **Analyzed at:** {analyzed_at}\n\n"
    
    # Add primary technologies section
    if primary_tech:
        markdown += f"## Primary Technologies\n\n"
        for category, tech in primary_tech.items():
            markdown += f"- **{category.replace('_', ' ').title()}:** {tech}\n"
        markdown += "\n"
    
    # Add detailed sections for each category
    for category in ["languages", "frameworks", "databases", "build_systems", 
                    "package_managers", "frontend", "devops", "architecture", "testing"]:
        techs = tech_stack.get(category, {})
        if techs:
            # Add category header
            markdown += f"## {category.replace('_', ' ').title()}\n\n"
            
            # Sort technologies by confidence
            sorted_techs = sorted(
                [(tech, details.get("confidence", 0)) for tech, details in techs.items()],
                key=lambda x: x[1],
                reverse=True
            )
            
            # Add technologies as table
            markdown += "| Technology | Confidence | Evidence |\n"
            markdown += "|------------|------------|----------|\n"
            
            for tech, confidence in sorted_techs:
                details = techs[tech]
                evidence = details.get("evidence", [])
                evidence_list = "<br>".join(evidence[:3])  # Show up to 3 pieces of evidence
                markdown += f"| {tech} | {confidence:.1f}% | {evidence_list} |\n"
            
            markdown += "\n"
    
    return markdown

def generate_text_report(tech_stack: Dict[str, Any]) -> str:
    """
    Generate a plain text report from the tech stack analysis.
    
    Args:
        tech_stack: The tech stack analysis results
        
    Returns:
        Plain text formatted report
    """
    # Get metadata
    metadata = tech_stack.get("metadata", {})
    repo_path = metadata.get("repo_path", "Unknown")
    file_count = metadata.get("file_count", 0)
    analysis_time = metadata.get("analysis_time_seconds", 0)
    analyzed_at = metadata.get("analyzed_at", "Unknown")
    
    # Get primary technologies
    primary_tech = tech_stack.get("primary_technologies", {})
    
    # Start building the text report
    text = "===== REPOSITORY ANALYSIS REPORT =====\n\n"
    
    # Add metadata
    text += f"Repository: {repo_path}\n"
    text += f"Files analyzed: {file_count}\n"
    text += f"Analysis time: {analysis_time:.2f} seconds\n"
    text += f"Analyzed at: {analyzed_at}\n\n"
    
    # Add primary technologies
    if primary_tech:
        text += "Primary Technologies:\n"
        for category, tech in primary_tech.items():
            text += f"  - {category.replace('_', ' ').title()}: {tech}\n"
        text += "\n"
    
    # Add detailed sections for each category
    for category in ["languages", "frameworks", "databases", "build_systems", 
                    "package_managers", "frontend", "devops", "architecture", "testing"]:
        techs = tech_stack.get(category, {})
        if techs:
            # Add category header
            text += f"{category.replace('_', ' ').title()}:\n"
            
            # Sort technologies by confidence
            sorted_techs = sorted(
                [(tech, details.get("confidence", 0)) for tech, details in techs.items()],
                key=lambda x: x[1],
                reverse=True
            )
            
            # Add technologies
            for tech, confidence in sorted_techs:
                text += f"  - {tech} ({confidence:.1f}%)\n"
            
            text += "\n"
    
    text += "==========================================\n"
    
    return text

def save_output(tech_stack: Dict[str, Any], output_path: str, 
               output_format: str, pretty_print: bool) -> str:
    """
    Save the tech stack analysis results to a file.
    
    Args:
        tech_stack: The tech stack analysis results
        output_path: Path to save the results
        output_format: Format to save the results (json, yaml, markdown, text)
        pretty_print: Whether to pretty-print JSON output
        
    Returns:
        Path to the saved file
    """
    # Make sure output directory exists
    output_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(output_dir, exist_ok=True)
    
    # Save in the appropriate format
    if output_format == "json":
        with open(output_path, "w") as f:
            if pretty_print:
                json.dump(tech_stack, f, indent=2)
            else:
                json.dump(tech_stack, f)
    
    elif output_format == "yaml":
        try:
            import yaml
            with open(output_path, "w") as f:
                yaml.dump(tech_stack, f, sort_keys=False, default_flow_style=False)
        except ImportError:
            print("Error: PyYAML is not installed. Install it with 'pip install pyyaml'.")
            sys.exit(1)
    
    elif output_format == "markdown":
        with open(output_path, "w") as f:
            f.write(generate_markdown_report(tech_stack))
    
    elif output_format == "text":
        with open(output_path, "w") as f:
            f.write(generate_text_report(tech_stack))
    
    return output_path

def generate_graph(tech_stack: Dict[str, Any], output_path: Optional[str] = None) -> Optional[str]:
    """
    Generate a graph visualization of the tech stack.
    
    Args:
        tech_stack: The tech stack analysis results
        output_path: Path to save the graph visualization
        
    Returns:
        Path to the saved graph visualization, or None if generation failed
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm
        import numpy as np
        from matplotlib.patches import Wedge
        
        # Create figure
        plt.figure(figsize=(12, 8))
        
        # Get primary technologies to highlight
        primary_tech = tech_stack.get("primary_technologies", {})
        
        # Categories to visualize
        categories = ["languages", "frameworks", "databases", "build_systems", 
                     "package_managers", "frontend", "devops", "architecture", "testing"]
        
        # Filter out empty categories
        categories = [cat for cat in categories if tech_stack.get(cat, {})]
        
        # Number of categories
        n_categories = len(categories)
        
        # Colors for categories
        colors = cm.tab10(np.linspace(0, 1, n_categories))
        
        # Plot each category
        for i, (category, color) in enumerate(zip(categories, colors)):
            techs = tech_stack.get(category, {})
            
            # Sort technologies by confidence
            sorted_techs = sorted(
                [(tech, details.get("confidence", 0)) for tech, details in techs.items()],
                key=lambda x: x[1],
                reverse=True
            )
            
            # Number of technologies
            n_techs = len(sorted_techs)
            
            # Skip empty categories
            if n_techs == 0:
                continue
            
            # Plot technologies
            y_positions = np.arange(n_techs) * 0.8 + i * 5
            confidences = [confidence for _, confidence in sorted_techs]
            tech_names = [tech for tech, _ in sorted_techs]
            
            # Create horizontal bars
            bars = plt.barh(y_positions, confidences, height=0.6, color=color, alpha=0.7)
            
            # Add category label
            plt.text(-10, y_positions[0] + 1, category.replace('_', ' ').title(), 
                    fontsize=12, fontweight='bold', ha='right')
            
            # Add labels for each technology
            for j, (tech, confidence) in enumerate(sorted_techs):
                is_primary = primary_tech.get(category) == tech
                weight = 'bold' if is_primary else 'normal'
                
                # Add technology name
                plt.text(0, y_positions[j], f" {tech} ", fontsize=10, 
                        fontweight=weight, va='center')
                
                # Add confidence value
                plt.text(confidence + 1, y_positions[j], f"{confidence:.1f}%", 
                        fontsize=8, va='center')
        
        # Set plot properties
        plt.xlim(0, 105)  # Confidence scale from 0-100
        plt.xlabel('Confidence Score (%)')
        plt.title('Repository Tech Stack Analysis', fontsize=14, fontweight='bold')
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Save or display the plot
        if output_path:
            # Make sure output directory exists
            output_dir = os.path.dirname(os.path.abspath(output_path))
            os.makedirs(output_dir, exist_ok=True)
            
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            return output_path
        else:
            plt.show()
            return None
            
    except ImportError:
        print("Error: Matplotlib is not installed. Install it with 'pip install matplotlib'.")
        return None

def generate_dockerfile(tech_stack: Dict[str, Any], output_path: Optional[str] = None) -> Optional[str]:
    """
    Generate a Dockerfile based on the detected tech stack.
    
    Args:
        tech_stack: The tech stack analysis results
        output_path: Path to save the Dockerfile
        
    Returns:
        Path to the saved Dockerfile, or None if generation failed
    """
    try:
        # Import the Dockerfile Generator
        from dockerfile_generator import DockerfileGenerator
        
        # Get repository path from metadata
        repo_path = tech_stack.get("metadata", {}).get("repo_path", ".")
        
        # Create Dockerfile generator
        generator = DockerfileGenerator(repo_path, output_path)
        
        # Use pre-analyzed tech stack instead of re-analyzing
        generator.tech_stack = tech_stack
        
        # Generate Dockerfile
        dockerfile_content = generator._generate_dockerfile_content(
            generator._determine_base_image()
        )
        
        # Save the Dockerfile
        if output_path:
            with open(output_path, "w") as f:
                f.write(dockerfile_content)
            return output_path
        
        # Return the content if no output path is provided
        return dockerfile_content
        
    except ImportError:
        print("Error: Dockerfile Generator is not available. Make sure it's installed correctly.")
        return None

def main():
    """Main entry point for the command-line interface."""
    # Parse arguments
    args = parse_arguments()
    
    # Show version and exit if requested
    if args.version:
        from repo_analyzer import __version__
        print(f"RepoAnalyzer version {__version__}")
        return 0
    
    # Configure logging
    logger = setup_logger(args.verbose and not args.quiet)
    
    try:
        # Validate repository path
        if not os.path.isdir(args.repo_path):
            logger.error(f"Error: '{args.repo_path}' is not a valid directory")
            return 1
        
        # Combine default and user-specified excluded directories
        exclude_dirs = set([
            '.git', 'node_modules', 'venv', '.venv', '__pycache__', 
            'build', 'dist', 'target', 'bin', 'obj'
        ])
        exclude_dirs.update(args.exclude_dirs)
        
        if not args.quiet:
            logger.info(f"Analyzing repository: {args.repo_path}")
        
        # Create and configure analyzer
        analyzer = RepoAnalyzer(
            repo_path=args.repo_path,
            exclude_dirs=exclude_dirs,
            max_file_size=args.max_file_size,
            verbose=args.verbose and not args.quiet
        )
        
        # Run analysis
        tech_stack = analyzer.analyze()
        
        # Filter results
        filtered_stack = filter_results(
            tech_stack, 
            args.min_confidence, 
            args.categories
        )
        
        # Display results if not quiet
        if not args.quiet:
            # Print summary to console
            if args.format == "text":
                print(generate_text_report(filtered_stack))
            elif args.format == "markdown":
                print(generate_markdown_report(filtered_stack))
            elif args.format == "json":
                if args.pretty:
                    print(json.dumps(filtered_stack, indent=2))
                else:
                    print(json.dumps(filtered_stack))
            elif args.format == "yaml":
                try:
                    import yaml
                    print(yaml.dump(filtered_stack, sort_keys=False, default_flow_style=False))
                except ImportError:
                    logger.error("Error: PyYAML is not installed. Install it with 'pip install pyyaml'.")
                    return 1
        
        # Save results to file if requested
        if args.output:
            output_path = save_output(
                filtered_stack, 
                args.output, 
                args.format, 
                args.pretty
            )
            if not args.quiet:
                logger.info(f"Analysis results saved to: {output_path}")
        
        # Generate graph if requested
        if args.generate_graph:
            graph_path = generate_graph(filtered_stack, args.graph_output)
            if graph_path and not args.quiet:
                logger.info(f"Graph visualization saved to: {graph_path}")
        
        # Generate Dockerfile if requested
        if args.generate_dockerfile:
            dockerfile_path = args.dockerfile_output or os.path.join(args.repo_path, "Dockerfile")
            generated_path = generate_dockerfile(filtered_stack, dockerfile_path)
            if generated_path and not args.quiet:
                logger.info(f"Dockerfile generated at: {dockerfile_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error analyzing repository: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())