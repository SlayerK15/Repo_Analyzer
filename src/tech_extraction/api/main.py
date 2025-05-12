"""
FastAPI implementation for the Technology Extraction System.

This module provides RESTful API endpoints for using the technology
extraction functionality.
"""
import logging
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, BackgroundTasks, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

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
from tech_extraction.optimization.cost_optimization import CostOptimization
from tech_extraction.results.output_generation import OutputGenerator
from tech_extraction.results.technology_aggregation import TechnologyAggregation
from tech_extraction.results.visualization import VisualizationComponents

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.api.title,
    description=settings.api.description,
    version=settings.api.version,
    openapi_url=settings.api.openapi_url,
    docs_url=settings.api.docs_url,
    redoc_url=settings.api.redoc_url,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a global job storage
job_storage = {}


class AnalysisRequest(BaseModel):
    """Request model for repository analysis."""
    repo_path: Optional[str] = Field(None, description="Path to local repository")
    repo_url: Optional[str] = Field(None, description="URL to Git repository")
    confidence_threshold: float = Field(50.0, description="Confidence threshold for inclusion")
    include_evidence: bool = Field(True, description="Whether to include evidence in results")
    detail_level: str = Field("medium", description="Detail level (low, medium, high)")
    output_format: str = Field("json", description="Output format (json, markdown, html, csv)")
    create_visualizations: bool = Field(False, description="Whether to create visualizations")


class AnalysisResponse(BaseModel):
    """Response model for repository analysis."""
    job_id: str = Field(..., description="Job ID for tracking analysis")
    status: str = Field("pending", description="Job status")
    message: str = Field("Analysis job submitted", description="Status message")


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str = Field(..., description="Job ID")
    status: str = Field(..., description="Job status")
    progress: float = Field(0.0, description="Analysis progress (0-100)")
    message: Optional[str] = Field(None, description="Status message")
    results_url: Optional[str] = Field(None, description="URL to results if completed")


class AnalysisStats(BaseModel):
    """Statistics for analysis results."""
    execution_time: float = Field(..., description="Execution time in seconds")
    files_analyzed: int = Field(..., description="Number of files analyzed")
    technologies_detected: int = Field(..., description="Number of technologies detected")
    confidence_average: float = Field(..., description="Average confidence score")


class AnalysisResults(BaseModel):
    """Results of repository analysis."""
    technologies: List[Dict] = Field(..., description="Detected technologies")
    technology_stacks: List[Dict] = Field(..., description="Technology stacks")
    stats: AnalysisStats = Field(..., description="Analysis statistics")


async def analyze_repository(
    job_id: str,
    repo_path: str,
    confidence_threshold: float,
    include_evidence: bool,
    detail_level: str,
    output_format: str,
    create_visualizations: bool
):
    """
    Analyze a repository in the background.
    
    Args:
        job_id: Job ID
        repo_path: Path to repository
        confidence_threshold: Confidence threshold
        include_evidence: Include evidence in results
        detail_level: Detail level
        output_format: Output format
        create_visualizations: Create visualizations
    """
    try:
        # Update job status
        job_storage[job_id].update({
            "status": "processing",
            "progress": 10.0,
            "message": "Collecting files"
        })
        
        # Create temporary output directory
        output_dir = Path(f"./output/{job_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        file_collector = FileCollectionEngine(repo_path)
        language_detector = LanguageDetectionSubsystem()
        
        # Collect files
        files = file_collector.scan_directory()
        
        # Sample files if there are too many
        if len(files) > 500:
            sample_files = file_collector.select_sample(files)
        else:
            sample_files = files
        
        # Update job status
        job_storage[job_id].update({
            "progress": 20.0,
            "message": f"Collected {len(sample_files)} files for analysis"
        })
        
        # Detect languages
        language_info = language_detector.process_files(sample_files)
        
        # Initialize dependency analyzers
        manifest_parser = PackageManifestParser()
        import_analyzer = ImportStatementAnalyzer()
        
        # Update job status
        job_storage[job_id].update({
            "progress": 30.0,
            "message": "Analyzing dependencies"
        })
        
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
        
        # Analyze imports
        file_with_lang = [(Path(f.full_path), language_info[f.path]) 
                         for f in sample_files if f.path in language_info]
        imports = import_analyzer.analyze_files(file_with_lang)
        
        # Update job status
        job_storage[job_id].update({
            "progress": 50.0,
            "message": "Detecting frameworks and patterns"
        })
        
        # Initialize framework detectors
        signature_detector = SignatureDetectionEngine()
        arch_recognizer = ArchitecturalPatternRecognition(Path(repo_path))
        
        # Detect framework patterns
        patterns = signature_detector.detect_patterns_in_files(sample_files)
        
        # Analyze architectural patterns
        architecture = arch_recognizer.analyze(sample_files)
        
        # Update job status
        job_storage[job_id].update({
            "progress": 70.0,
            "message": "Processing evidence and calculating confidence"
        })
        
        # Initialize evidence and confidence components
        evidence_collection = EvidenceCollection()
        confidence_engine = ConfidenceScoringEngine()
        
        # Collect evidence
        for manifest in manifests:
            evidence_collection.collect_from_dependencies(manifest.dependencies)
        
        package_mapping = import_analyzer.PACKAGE_MAPPINGS.get("JavaScript", {})
        evidence_collection.collect_from_imports(imports, package_mapping)
        evidence_collection.collect_from_pattern_matches(patterns)
        
        # Add evidence to confidence engine
        for tech_name, evidence_list in evidence_collection.evidence_by_technology.items():
            confidence_engine.add_evidence_batch({tech_name: evidence_list})
        
        # Apply false positive mitigation
        mitigation = FalsePositiveMitigation(evidence_collection, confidence_engine)
        mitigation.mitigate_false_positives()
        
        # Update job status
        job_storage[job_id].update({
            "progress": 80.0,
            "message": "Aggregating technologies"
        })
        
        # Aggregate technologies
        tech_aggregation = TechnologyAggregation(evidence_collection, confidence_engine)
        technologies = tech_aggregation.aggregate_technologies(confidence_threshold)
        tech_aggregation.group_technologies()
        tech_aggregation.create_technology_stacks()
        
        # Generate output
        output_generator = OutputGenerator(tech_aggregation)
        
        # Save report in requested format
        report_filename = f"report.{output_format}"
        report_path = output_dir / report_filename
        
        output_generator.save_report(
            str(report_path),
            format=output_format,
            confidence_threshold=confidence_threshold,
            include_evidence=include_evidence,
            detail_level=detail_level
        )
        
        # Create visualizations if requested
        if create_visualizations:
            viz_dir = output_dir / "visualizations"
            viz_dir.mkdir(exist_ok=True)
            
            viz = VisualizationComponents(tech_aggregation)
            viz.export_figures(str(viz_dir), min_confidence=confidence_threshold)
            
            # Create dashboard
            dashboard_path = output_dir / "dashboard.html"
            viz.create_dashboard_html(str(dashboard_path), min_confidence=confidence_threshold)
        
        # Create results data
        # Calculate stats
        import time
        stats = AnalysisStats(
            execution_time=time.time() - job_storage[job_id]["start_time"],
            files_analyzed=len(sample_files),
            technologies_detected=len(technologies),
            confidence_average=sum(t.confidence for t in technologies) / len(technologies) if technologies else 0
        )
        
        # Create results URL
        base_url = settings.api.root_path or "http://localhost:8000"
        results_url = f"{base_url}/api/v1/analysis/{job_id}/results/{report_filename}"
        
        # Update job status
        job_storage[job_id].update({
            "status": "completed",
            "progress": 100.0,
            "message": "Analysis completed successfully",
            "results_url": results_url,
            "output_dir": str(output_dir),
            "results": {
                "technologies": [tech.__dict__ for tech in technologies],
                "technology_stacks": [stack.__dict__ for stack in tech_aggregation.get_all_technology_stacks()],
                "stats": stats.__dict__
            }
        })
        
    except Exception as e:
        logger.error(f"Error analyzing repository: {e}", exc_info=True)
        job_storage[job_id].update({
            "status": "failed",
            "message": f"Analysis failed: {str(e)}"
        })


@app.post("/api/v1/analysis", response_model=AnalysisResponse)
async def start_analysis(
    background_tasks: BackgroundTasks,
    analysis_request: AnalysisRequest
):
    """Start repository analysis."""
    # Validate request
    if not analysis_request.repo_path and not analysis_request.repo_url:
        raise HTTPException(status_code=400, detail="Either repo_path or repo_url must be provided")
    
    # Use local path if provided, otherwise clone repository
    repo_path = analysis_request.repo_path
    if not repo_path and analysis_request.repo_url:
        # Clone repository to temporary directory
        import subprocess
        
        temp_dir = tempfile.mkdtemp()
        try:
            subprocess.run(
                ["git", "clone", analysis_request.repo_url, temp_dir],
                check=True,
                capture_output=True
            )
            repo_path = temp_dir
        except subprocess.CalledProcessError as e:
            logger.error(f"Error cloning repository: {e.stderr.decode()}")
            raise HTTPException(status_code=400, detail=f"Error cloning repository: {e.stderr.decode()}")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create job entry
    job_storage[job_id] = {
        "id": job_id,
        "status": "pending",
        "progress": 0.0,
        "message": "Analysis job submitted",
        "repo_path": repo_path,
        "start_time": time.time()
    }
    
    # Start analysis in background
    background_tasks.add_task(
        analyze_repository,
        job_id=job_id,
        repo_path=repo_path,
        confidence_threshold=analysis_request.confidence_threshold,
        include_evidence=analysis_request.include_evidence,
        detail_level=analysis_request.detail_level,
        output_format=analysis_request.output_format,
        create_visualizations=analysis_request.create_visualizations
    )
    
    return AnalysisResponse(
        job_id=job_id,
        status="pending",
        message="Analysis job submitted"
    )


@app.get("/api/v1/analysis/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get job status."""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_storage[job_id]
    
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        results_url=job.get("results_url")
    )


@app.get("/api/v1/analysis/{job_id}/results", response_model=AnalysisResults)
async def get_analysis_results(job_id: str):
    """Get analysis results."""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_storage[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job is not completed: {job['status']}")
    
    if "results" not in job:
        raise HTTPException(status_code=500, detail="Results not available")
    
    return job["results"]


@app.get("/api/v1/analysis/{job_id}/results/{filename}")
async def get_analysis_file(job_id: str, filename: str):
    """Get analysis result file."""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_storage[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job is not completed: {job['status']}")
    
    if "output_dir" not in job:
        raise HTTPException(status_code=500, detail="Output directory not available")
    
    output_dir = Path(job["output_dir"])
    file_path = output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    return FileResponse(str(file_path))


@app.delete("/api/v1/analysis/{job_id}")
async def delete_analysis_job(job_id: str):
    """Delete analysis job and associated files."""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_storage[job_id]
    
    # Delete output directory if available
    if "output_dir" in job:
        output_dir = Path(job["output_dir"])
        if output_dir.exists():
            shutil.rmtree(str(output_dir))
    
    # Delete temporary directory if this was a cloned repository
    if "repo_path" in job and job["repo_path"].startswith(tempfile.gettempdir()):
        repo_path = Path(job["repo_path"])
        if repo_path.exists():
            shutil.rmtree(str(repo_path))
    
    # Remove from job storage
    del job_storage[job_id]
    
    return {"status": "success", "message": "Job deleted"}


@app.post("/api/v1/upload")
async def upload_repository(file: UploadFile = File(...)):
    """Upload a repository archive for analysis."""
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    archive_path = temp_dir / file.filename
    
    try:
        # Save uploaded file
        with open(archive_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Extract archive
        extract_dir = temp_dir / "repo"
        extract_dir.mkdir()
        
        if archive_path.suffix.lower() in [".zip"]:
            import zipfile
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        elif archive_path.suffix.lower() in [".tar", ".gz", ".tgz"]:
            import tarfile
            with tarfile.open(archive_path) as tar:
                tar.extractall(path=extract_dir)
        else:
            raise HTTPException(status_code=400, detail="Unsupported archive format")
        
        return {"status": "success", "repo_path": str(extract_dir)}
    
    except Exception as e:
        logger.error(f"Error processing upload: {e}", exc_info=True)
        if temp_dir.exists():
            shutil.rmtree(str(temp_dir))
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")


@app.get("/api/v1/health")
async def health_check():
    """API health check endpoint."""
    return {"status": "ok", "version": settings.api.version}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the Technology Extraction API", 
            "docs": "/docs",
            "redoc": "/redoc"}


def start():
    """Start the API server."""
    uvicorn.run(
        "tech_extraction.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    start()