"""
Worker implementation for the Technology Extraction System.

This module provides a background worker for processing analysis jobs.
"""
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Optional

import redis
from rich.console import Console
from rich.logging import RichHandler

from tech_extraction.config import settings
from tech_extraction.optimization.parallel_processing import (
    WorkloadDistributor,
    Task,
    TaskPriority,
)


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger(__name__)
console = Console()


class AnalysisWorker:
    """
    Worker for processing technology extraction jobs.
    
    Polls a Redis queue for jobs, processes them, and stores results.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize the analysis worker.
        
        Args:
            redis_url: Redis connection URL
        """
        # Default to configured URL
        self.redis_url = redis_url or settings.redis.redis_url
        
        # Initialize Redis connection
        self.redis = None
        if self.redis_url:
            try:
                self.redis = redis.from_url(self.redis_url)
                logger.info(f"Connected to Redis at {self.redis_url}")
            except Exception as e:
                logger.error(f"Error connecting to Redis: {e}")
                self.redis = None
        
        # Initialize workload distributor
        self.distributor = WorkloadDistributor()
        
        # Set queue names
        self.job_queue = "tech_extraction:jobs"
        self.result_queue = "tech_extraction:results"
        
        # Set running flag
        self.running = False
    
    def start(self):
        """Start the worker."""
        self.running = True
        logger.info("Starting worker")
        
        try:
            self._run_loop()
        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("Worker stopped")
    
    def stop(self):
        """Stop the worker."""
        self.running = False
    
    def _run_loop(self):
        """Run the main worker loop."""
        while self.running:
            # Check if Redis is available
            if not self.redis:
                logger.warning("Redis not available, trying to reconnect...")
                try:
                    self.redis = redis.from_url(self.redis_url)
                    logger.info("Reconnected to Redis")
                except Exception as e:
                    logger.error(f"Error reconnecting to Redis: {e}")
                    time.sleep(5)
                    continue
            
            # Try to get a job
            try:
                # Use blocking pop with timeout
                result = self.redis.blpop(self.job_queue, timeout=5)
                
                if result:
                    _, job_data = result
                    self._process_job(job_data)
                else:
                    # No job available, wait a bit
                    time.sleep(1)
            
            except redis.exceptions.ConnectionError:
                logger.error("Lost connection to Redis")
                self.redis = None
                time.sleep(5)
            
            except Exception as e:
                logger.error(f"Error processing job: {e}", exc_info=True)
                time.sleep(1)
    
    def _process_job(self, job_data: bytes):
        """
        Process a job from the queue.
        
        Args:
            job_data: Job data as bytes
        """
        try:
            # Parse job data
            job = json.loads(job_data)
            job_id = job.get("id")
            job_type = job.get("type")
            
            logger.info(f"Processing job {job_id} of type {job_type}")
            
            # Update job status
            self._update_job_status(job_id, "processing", "Job is being processed")
            
            # Dispatch based on job type
            if job_type == "repository_analysis":
                self._process_repository_analysis(job)
            else:
                logger.warning(f"Unknown job type: {job_type}")
                self._update_job_status(job_id, "failed", f"Unknown job type: {job_type}")
        
        except json.JSONDecodeError:
            logger.error(f"Invalid job data: {job_data}")
        
        except Exception as e:
            logger.error(f"Error processing job: {e}", exc_info=True)
            if "job_id" in locals():
                self._update_job_status(job_id, "failed", f"Error: {str(e)}")
    
    def _process_repository_analysis(self, job: Dict):
        """
        Process a repository analysis job.
        
        Args:
            job: Job data
        """
        job_id = job.get("id")
        repo_path = job.get("repo_path")
        
        if not repo_path or not os.path.exists(repo_path):
            self._update_job_status(job_id, "failed", f"Repository path not found: {repo_path}")
            return
        
        try:
            # Import here to avoid circular imports
            from tech_extraction.cli import analyze_repository
            
            # Get job parameters
            confidence_threshold = job.get("confidence_threshold", 50.0)
            include_evidence = job.get("include_evidence", True)
            detail_level = job.get("detail_level", "medium")
            output_format = job.get("output_format", "json")
            visualizations = job.get("visualizations", False)
            cost_mode = job.get("cost_mode", "balanced")
            
            # Create output directory
            output_dir = os.path.join(settings.api.root_path or ".", "output", job_id)
            os.makedirs(output_dir, exist_ok=True)
            
            # Update job status
            self._update_job_status(job_id, "processing", "Analyzing repository", progress=10)
            
            # Run analysis
            technologies = analyze_repository(
                repo_path=repo_path,
                output_dir=output_dir,
                confidence_threshold=confidence_threshold,
                include_evidence=include_evidence,
                detail_level=detail_level,
                output_format=output_format,
                visualizations=visualizations,
                cost_mode=cost_mode,
                verbose=True
            )
            
            # Create results
            report_filename = f"tech_report.{output_format}"
            report_path = os.path.join(output_dir, report_filename)
            
            # Create results URL
            base_url = settings.api.root_path or "http://localhost:8000"
            results_url = f"{base_url}/api/v1/analysis/{job_id}/results/{report_filename}"
            
            # Update job status
            self._update_job_status(
                job_id, 
                "completed", 
                "Analysis completed successfully",
                progress=100,
                results_url=results_url,
                output_dir=output_dir,
                technologies=[tech.__dict__ for tech in technologies]
            )
            
            logger.info(f"Completed job {job_id}")
        
        except Exception as e:
            logger.error(f"Error analyzing repository: {e}", exc_info=True)
            self._update_job_status(job_id, "failed", f"Analysis failed: {str(e)}")
    
    def _update_job_status(
        self,
        job_id: str,
        status: str,
        message: str,
        progress: float = 0.0,
        **kwargs
    ):
        """
        Update job status in Redis.
        
        Args:
            job_id: Job ID
            status: Job status
            message: Status message
            progress: Progress percentage (0-100)
            **kwargs: Additional data to store
        """
        if not self.redis:
            logger.warning("Cannot update job status: Redis not available")
            return
        
        try:
            # Create status data
            status_data = {
                "id": job_id,
                "status": status,
                "message": message,
                "progress": progress,
                "updated_at": time.time(),
                **kwargs
            }
            
            # Store in Redis
            self.redis.set(f"tech_extraction:job:{job_id}", json.dumps(status_data))
            
            # Add to results queue if completed or failed
            if status in ("completed", "failed"):
                self.redis.rpush(self.result_queue, json.dumps(status_data))
            
            logger.debug(f"Updated job {job_id} status: {status}")
        
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
    
    def submit_job(self, job_data: Dict) -> str:
        """
        Submit a job to the queue.
        
        Args:
            job_data: Job data
            
        Returns:
            Job ID
        """
        if not self.redis:
            raise RuntimeError("Redis not available")
        
        job_id = job_data.get("id")
        
        try:
            # Push to queue
            self.redis.rpush(self.job_queue, json.dumps(job_data))
            
            # Initialize job status
            self._update_job_status(job_id, "pending", "Job submitted", progress=0)
            
            logger.info(f"Submitted job {job_id}")
            return job_id
        
        except Exception as e:
            logger.error(f"Error submitting job: {e}")
            raise


def start():
    """Start the worker."""
    worker = AnalysisWorker()
    worker.start()


if __name__ == "__main__":
    start()