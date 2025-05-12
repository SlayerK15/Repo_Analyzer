"""
Command-line interface for the Technology Extraction System.
"""
import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from tech_extraction import __version__
from tech_extraction.config import settings
from tech_extraction.core.file_collection import FileCollectionEngine
from tech_extraction.core.language_detection import LanguageDetectionSubsystem
from tech_extraction.dependency.import_analyzer import ImportStatementAnalyzer
from tech_extraction.dependency.package_manifest import PackageManifestParser
from tech_extraction.evidence.confidence_scoring import ConfidenceScoringEngine
from tech_extraction.evidence.evidence_collection import EvidenceCollection
from tech_extraction.evidence.false_positive_mitigation import FalsePositiveMitigation
from tech_extraction.framework.architectural_pattern import ArchitecturalPatternRecognition
from tech_extraction.framework.signature_detection import SignatureDetectionEngine
from tech_extraction.optimization.cost_optimization import CostOptimization, CostMode
from tech_extraction.results.output_generation import OutputGenerator
from tech_extraction.results.technology_aggregation import TechnologyAggregation
from tech_extraction.results.visualization import VisualizationComponents


# Set up console for rich output
console = Console()


def configure_logging(verbose: bool = False):
    """
    Configure logging with appropriate levels and formats.
    
    Args:
        verbose: Whether to enable verbose logging
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )


def analyze_repository(
    repo_path: str,
    output_dir: Optional[str] = None,
    confidence_threshold: float = 50.0,
    include_evidence: bool = True,
    detail_level: str = "medium",
    output_format: str = "json",
    visualizations: bool = False,
    cost_mode: str = "balanced",
    verbose: bool = False
):
    """
    Analyze a repository and extract technology information.
    
    Args:
        repo_path: Path to the repository
        output_dir: Directory to save output files
        confidence_threshold: Confidence threshold (0-100)
        include_evidence: Whether to include evidence in output
        detail_level: Detail level (low, medium, high)
        output_format: Output format (json, markdown, html, csv)
        visualizations: Whether to create visualizations
        cost_mode: Cost optimization mode
        verbose: Enable verbose logging
    """
    # Configure logging
    configure_logging(verbose)
    
    # Log settings
    logging.info(f"Analyzing repository: {repo_path}")
    logging.info(f"Output format: {output_format}")
    logging.info(f"Confidence threshold: {confidence_threshold}")
    logging.info(f"Detail level: {detail_level}")
    
    # Create output directory if specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    else:
        # Default to a directory in the repo
        output_dir = os.path.join(repo_path, "tech_extraction_output")
        os.makedirs(output_dir, exist_ok=True)
    
    # Set cost optimization mode
    cost_optimizer = CostOptimization()
    cost_optimizer.set_mode(CostMode(cost_mode))
    
    # Start timer
    start_time = time.time()
    
    # Create progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
    ) as progress:
        # File collection task
        file_task = progress.add_task("[green]Collecting files...", total=100)
        
        # Initialize file collection engine
        file_collector = FileCollectionEngine(repo_path)
        
        # Collect files
        files = file_collector.scan_directory()
        progress.update(file_task, completed=50)
        
        # Sample files if there are too many
        if len(files) > 500:
            sample_files = file_collector.select_sample(files)
        else:
            sample_files = files
        
        progress.update(file_task, completed=100)
        
        # Language detection task
        lang_task = progress.add_task("[green]Detecting languages...", total=100)
        
        # Initialize language detection
        language_detector = LanguageDetectionSubsystem()
        
        # Detect languages
        language_info = language_detector.process_files(sample_files)
        
        # Generate language metadata
        language_metadata = language_detector.generate_metadata()
        
        progress.update(lang_task, completed=100)
        
        # Dependency analysis task
        dep_task = progress.add_task("[green]Analyzing dependencies...", total=100)
        
        # Initialize dependency analyzers
        manifest_parser = PackageManifestParser()
        import_analyzer = ImportStatementAnalyzer()
        
        # Parse manifest files
        manifests = []
        for file_info in sample_files:
            if any(file_info.path.endswith(ext) for ext in [
                "package.json", "requirements.txt", "pom.xml", "build.gradle",
                "Gemfile", "go.mod", "Cargo.toml", ".csproj"
            ]):
                manifest = manifest_parser.parse_manifest(Path(file_info.full_path))
                if manifest:
                    manifests.append(manifest)
        
        progress.update(dep_task, completed=50)
        
        # Analyze imports
        file_with_lang = [(Path(f.full_path), language_info[f.path]) 
                         for f in sample_files if f.path in language_info]
        imports = import_analyzer.analyze_files(file_with_lang)
        
        progress.update(dep_task, completed=100)
        
        # Framework detection task
        framework_task = progress.add_task("[green]Detecting frameworks...", total=100)
        
        # Initialize framework detectors
        signature_detector = SignatureDetectionEngine()
        
        # Detect framework patterns
        patterns = signature_detector.detect_patterns_in_files(sample_files)
        
        progress.update(framework_task, completed=100)
        
        # Architecture analysis task
        arch_task = progress.add_task("[green]Analyzing architecture...", total=100)
        
        # Initialize architecture analyzer
        arch_recognizer = ArchitecturalPatternRecognition(Path(repo_path))
        
        # Analyze architectural patterns
        architecture = arch_recognizer.analyze(sample_files)
        
        progress.update(arch_task, completed=100)
        
        # Evidence processing task
        evidence_task = progress.add_task("[green]Processing evidence...", total=100)
        
        # Initialize evidence and confidence components
        evidence_collection = EvidenceCollection()
        confidence_engine = ConfidenceScoringEngine()
        
        # Collect evidence
        for manifest in manifests:
            evidence_collection.collect_from_dependencies(manifest.dependencies)
        
        package_mapping = import_analyzer.PACKAGE_MAPPINGS.get("JavaScript", {})
        evidence_collection.collect_from_imports(imports, package_mapping)
        evidence_collection.collect_from_pattern_matches(patterns)
        
        progress.update(evidence_task, completed=50)
        
        # Add evidence to confidence engine
        for tech_name, evidence_list in evidence_collection.evidence_by_technology.items():
            confidence_engine.add_evidence_batch({tech_name: evidence_list})
        
        # Apply false positive mitigation
        mitigation = FalsePositiveMitigation(evidence_collection, confidence_engine)
        mitigation.mitigate_false_positives()
        
        progress.update(evidence_task, completed=100)
        
        # Technology aggregation task
        tech_task = progress.add_task("[green]Aggregating technologies...", total=100)
        
        # Aggregate technologies
        tech_aggregation = TechnologyAggregation(evidence_collection, confidence_engine)
        technologies = tech_aggregation.aggregate_technologies(confidence_threshold)
        tech_aggregation.group_technologies()
        tech_aggregation.create_technology_stacks()
        
        progress.update(tech_task, completed=100)
        
        # Results generation task
        results_task = progress.add_task("[green]Generating results...", total=100)
        
        # Generate output
        output_generator = OutputGenerator(tech_aggregation)
        
        # Save report in requested format
        report_filename = f"tech_report.{output_format}"
        report_path = os.path.join(output_dir, report_filename)
        
        output_generator.save_report(
            report_path,
            format=output_format,
            confidence_threshold=confidence_threshold,
            include_evidence=include_evidence,
            detail_level=detail_level
        )
        
        progress.update(results_task, completed=80)
        
        # Create visualizations if requested
        if visualizations:
            viz_dir = os.path.join(output_dir, "visualizations")
            os.makedirs(viz_dir, exist_ok=True)
            
            viz = VisualizationComponents(tech_aggregation)
            viz.export_figures(viz_dir, min_confidence=confidence_threshold)
            
            # Create dashboard
            dashboard_path = os.path.join(output_dir, "dashboard.html")
            viz.create_dashboard_html(dashboard_path, min_confidence=confidence_threshold)
        
        progress.update(results_task, completed=100)
    
    # End timer
    end_time = time.time()
    duration = end_time - start_time
    
    # Print summary
    console.print("\n[bold green]Analysis complete![/bold green]")
    console.print(f"Analyzed {len(sample_files)} files in {duration:.2f} seconds")
    console.print(f"Detected {len(technologies)} technologies")
    console.print(f"Results saved to {output_dir}")
    console.print(f"Report: {report_path}")
    
    if visualizations:
        console.print(f"Dashboard: {dashboard_path}")
    
    # Print cost usage if available
    cost_report = cost_optimizer.get_usage_report()
    if cost_report["cost_to_date"] > 0:
        console.print(f"\n[bold yellow]Cost Usage:[/bold yellow]")
        console.print(f"Total cost: ${cost_report['cost_to_date']:.4f}")
        console.print(f"Tokens used: {cost_report['tokens_used']}")
    
    return technologies


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description=f"Technology Extraction System v{__version__}",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "repo_path",
        help="Path to the repository to analyze"
    )
    
    parser.add_argument(
        "-o", "--output-dir",
        help="Directory to save output files",
        default=None
    )
    
    parser.add_argument(
        "-f", "--format",
        help="Output format",
        choices=["json", "markdown", "html", "csv"],
        default="json"
    )
    
    parser.add_argument(
        "-c", "--confidence-threshold",
        help="Confidence threshold (0-100)",
        type=float,
        default=50.0
    )
    
    parser.add_argument(
        "-d", "--detail-level",
        help="Detail level",
        choices=["low", "medium", "high"],
        default="medium"
    )
    
    parser.add_argument(
        "--no-evidence",
        help="Exclude evidence from output",
        action="store_true"
    )
    
    parser.add_argument(
        "-v", "--visualizations",
        help="Create visualizations",
        action="store_true"
    )
    
    parser.add_argument(
        "--cost-mode",
        help="Cost optimization mode",
        choices=["ai_only", "pattern_only", "hybrid", "balanced", "economy", "unlimited"],
        default="balanced"
    )
    
    parser.add_argument(
        "--verbose",
        help="Enable verbose logging",
        action="store_true"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"Technology Extraction System v{__version__}"
    )
    
    args = parser.parse_args()
    
    try:
        analyze_repository(
            repo_path=args.repo_path,
            output_dir=args.output_dir,
            confidence_threshold=args.confidence_threshold,
            include_evidence=not args.no_evidence,
            detail_level=args.detail_level,
            output_format=args.format,
            visualizations=args.visualizations,
            cost_mode=args.cost_mode,
            verbose=args.verbose
        )
        return 0
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if args.verbose:
            console.print_exception()
        return 1


if __name__ == "__main__":
    sys.exit(main())