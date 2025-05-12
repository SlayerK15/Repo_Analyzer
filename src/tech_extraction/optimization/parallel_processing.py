"""
Parallel Processing for the Technology Extraction System.

This module provides functionality for distributing workloads across
multiple processes or threads to improve performance.
"""
import asyncio
import concurrent.futures
import logging
import multiprocessing
import os
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union

from tqdm import tqdm

from tech_extraction.config import settings

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Priority levels for scheduled tasks."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class ResourceType(Enum):
    """Types of resources that can be managed."""
    CPU = "cpu"
    MEMORY = "memory"
    IO = "io"
    NETWORK = "network"
    API = "api"


@dataclass
class TaskStats:
    """Statistics for a completed task."""
    start_time: float
    end_time: float
    success: bool
    error: Optional[Exception] = None
    
    @property
    def duration(self) -> float:
        """Get the task duration in seconds."""
        return self.end_time - self.start_time


T = TypeVar('T')  # Task result type
A = TypeVar('A')  # Task argument type


@dataclass
class Task(Generic[T, A]):
    """Task to be executed by a worker."""
    id: str
    func: Callable[..., T]
    args: Tuple = ()
    kwargs: Dict[str, Any] = None
    priority: TaskPriority = TaskPriority.NORMAL
    retry_count: int = 0
    max_retries: int = 3
    stats: Optional[TaskStats] = None
    result: Optional[T] = None
    callback: Optional[Callable[[T], None]] = None
    error_callback: Optional[Callable[[Exception], None]] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.kwargs is None:
            self.kwargs = {}


class ResourceManager:
    """
    Manager for tracking and limiting resource usage.
    
    Handles tracking CPU, memory, network, and API usage to
    prevent overloading system resources.
    """
    
    def __init__(self):
        """Initialize the resource manager."""
        # Available resources (adjustable at runtime)
        self.available_resources = {
            ResourceType.CPU: multiprocessing.cpu_count(),
            ResourceType.MEMORY: os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') * 0.8,  # 80% of total RAM
            ResourceType.IO: 100,  # Arbitrary units for I/O bandwidth
            ResourceType.NETWORK: 100,  # Arbitrary units for network bandwidth
            ResourceType.API: 10,  # Requests per second (adjustable)
        }
        
        # Current usage
        self.usage = {res_type: 0 for res_type in ResourceType}
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        # API rate limiting
        self.api_last_request_time = {}
        self.api_rate_limits = {
            "openai": 10,  # Requests per minute
            "anthropic": 10,  # Requests per minute
            "default": 20,  # Requests per minute
        }
    
    def acquire(self, res_type: ResourceType, amount: float = 1.0) -> bool:
        """
        Attempt to acquire resources.
        
        Args:
            res_type: Type of resource to acquire
            amount: Amount of resource to acquire
            
        Returns:
            True if resources were acquired, False otherwise
        """
        with self.lock:
            # Check if resources are available
            if self.usage[res_type] + amount <= self.available_resources[res_type]:
                self.usage[res_type] += amount
                return True
            return False
    
    def release(self, res_type: ResourceType, amount: float = 1.0):
        """
        Release previously acquired resources.
        
        Args:
            res_type: Type of resource to release
            amount: Amount of resource to release
        """
        with self.lock:
            self.usage[res_type] = max(0, self.usage[res_type] - amount)
    
    def set_available(self, res_type: ResourceType, amount: float):
        """
        Set the available amount of a resource.
        
        Args:
            res_type: Type of resource to set
            amount: Amount of resource available
        """
        with self.lock:
            self.available_resources[res_type] = amount
    
    def get_usage_percentage(self, res_type: ResourceType) -> float:
        """
        Get the current usage percentage of a resource.
        
        Args:
            res_type: Type of resource to check
            
        Returns:
            Percentage of resource in use (0-100)
        """
        with self.lock:
            if self.available_resources[res_type] > 0:
                return (self.usage[res_type] / self.available_resources[res_type]) * 100
            return 0
    
    def check_api_rate_limit(self, api_name: str) -> bool:
        """
        Check if API rate limit allows a new request.
        
        Args:
            api_name: Name of the API to check
            
        Returns:
            True if request is allowed, False otherwise
        """
        with self.lock:
            now = time.time()
            
            # Get the rate limit for this API
            rate_limit = self.api_rate_limits.get(api_name, self.api_rate_limits["default"])
            
            # Convert to seconds between requests
            min_interval = 60.0 / rate_limit
            
            # Check last request time
            last_time = self.api_last_request_time.get(api_name, 0)
            
            if now - last_time >= min_interval:
                # Update last request time
                self.api_last_request_time[api_name] = now
                return True
            
            return False
    
    def wait_for_api_rate_limit(self, api_name: str):
        """
        Wait until API rate limit allows a new request.
        
        Args:
            api_name: Name of the API to wait for
        """
        while not self.check_api_rate_limit(api_name):
            time.sleep(0.1)
    
    def set_api_rate_limit(self, api_name: str, requests_per_minute: int):
        """
        Set the API rate limit.
        
        Args:
            api_name: Name of the API to set
            requests_per_minute: Allowed requests per minute
        """
        with self.lock:
            self.api_rate_limits[api_name] = requests_per_minute


class WorkloadDistributor:
    """
    Distributor for task workloads across workers.
    
    Handles scheduling, prioritization, and resource allocation
    for parallel processing of tasks.
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize the workload distributor.
        
        Args:
            max_workers: Maximum number of worker threads/processes
        """
        # Default to number of CPUs
        self.max_workers = max_workers or multiprocessing.cpu_count()
        
        # Task queue (priority-based)
        self.tasks = []
        
        # Task results
        self.results = {}
        
        # Locks for thread safety
        self.task_lock = threading.RLock()
        self.result_lock = threading.RLock()
        
        # Resource manager
        self.resource_manager = ResourceManager()
        
        # Workers
        self.thread_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="tech_extraction_worker"
        )
        self.process_executor = concurrent.futures.ProcessPoolExecutor(
            max_workers=self.max_workers
        )
        
        # Status tracking
        self.active_tasks = set()
        self.completed_tasks = set()
        self.failed_tasks = set()
    
    def schedule_task(self, task: Task) -> str:
        """
        Schedule a task for execution.
        
        Args:
            task: Task to schedule
            
        Returns:
            Task ID
        """
        with self.task_lock:
            self.tasks.append(task)
            # Sort tasks by priority (higher priority first)
            self.tasks.sort(key=lambda t: t.priority.value, reverse=True)
        
        return task.id
    
    def _execute_task(self, task: Task) -> Any:
        """
        Execute a task and handle retries and callbacks.
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
        """
        start_time = time.time()
        
        try:
            with self.task_lock:
                self.active_tasks.add(task.id)
            
            # Execute the task
            result = task.func(*task.args, **(task.kwargs or {}))
            
            # Update task stats and result
            end_time = time.time()
            task.stats = TaskStats(start_time=start_time, end_time=end_time, success=True)
            task.result = result
            
            # Call callback if provided
            if task.callback:
                try:
                    task.callback(result)
                except Exception as e:
                    logger.warning(f"Error in task callback for task {task.id}: {e}")
            
            # Update status
            with self.task_lock:
                self.active_tasks.remove(task.id)
                self.completed_tasks.add(task.id)
            
            # Store result
            with self.result_lock:
                self.results[task.id] = result
            
            return result
            
        except Exception as e:
            end_time = time.time()
            task.stats = TaskStats(start_time=start_time, end_time=end_time, success=False, error=e)
            
            logger.warning(f"Error executing task {task.id}: {e}")
            
            # Handle retries
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                logger.info(f"Retrying task {task.id} (attempt {task.retry_count})")
                return self._execute_task(task)
            
            # Call error callback if provided
            if task.error_callback:
                try:
                    task.error_callback(e)
                except Exception as e2:
                    logger.warning(f"Error in task error callback for task {task.id}: {e2}")
            
            # Update status
            with self.task_lock:
                if task.id in self.active_tasks:
                    self.active_tasks.remove(task.id)
                self.failed_tasks.add(task.id)
            
            # Re-raise exception
            raise
    
    def process_tasks(self, use_threads: bool = True, show_progress: bool = False) -> Dict[str, Any]:
        """
        Process all scheduled tasks.
        
        Args:
            use_threads: Use threads instead of processes
            show_progress: Show progress bar
            
        Returns:
            Dictionary mapping task IDs to results
        """
        with self.task_lock:
            tasks_to_process = self.tasks.copy()
            self.tasks.clear()
        
        if not tasks_to_process:
            return {}
        
        # Use appropriate executor
        executor = self.thread_executor if use_threads else self.process_executor
        
        # Create futures
        futures = {}
        for task in tasks_to_process:
            future = executor.submit(self._execute_task, task)
            futures[future] = task.id
        
        # Wait for completion with optional progress bar
        if show_progress:
            with tqdm(total=len(futures), desc="Processing tasks") as pbar:
                for future in concurrent.futures.as_completed(futures):
                    pbar.update(1)
        else:
            # Wait for all tasks to complete
            concurrent.futures.wait(futures.keys())
        
        # Return results
        with self.result_lock:
            return self.results.copy()
    
    async def process_tasks_async(self, show_progress: bool = False) -> Dict[str, Any]:
        """
        Process all scheduled tasks asynchronously.
        
        Args:
            show_progress: Show progress bar
            
        Returns:
            Dictionary mapping task IDs to results
        """
        with self.task_lock:
            tasks_to_process = self.tasks.copy()
            self.tasks.clear()
        
        if not tasks_to_process:
            return {}
        
        # Create async tasks
        async_tasks = []
        for task in tasks_to_process:
            async_task = asyncio.create_task(self._execute_task_async(task))
            async_tasks.append(async_task)
        
        # Wait for completion with optional progress bar
        if show_progress:
            with tqdm(total=len(async_tasks), desc="Processing tasks") as pbar:
                for future in asyncio.as_completed(async_tasks):
                    await future
                    pbar.update(1)
        else:
            # Wait for all tasks to complete
            await asyncio.gather(*async_tasks)
        
        # Return results
        with self.result_lock:
            return self.results.copy()
    
    async def _execute_task_async(self, task: Task) -> Any:
        """
        Execute a task asynchronously.
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
        """
        # For CPU-bound tasks, run in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.thread_executor,
            self._execute_task,
            task
        )
    
    def get_result(self, task_id: str) -> Optional[Any]:
        """
        Get the result of a completed task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task result or None if not available
        """
        with self.result_lock:
            return self.results.get(task_id)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of tasks.
        
        Returns:
            Dictionary with task status information
        """
        with self.task_lock, self.result_lock:
            return {
                "pending_tasks": len(self.tasks),
                "active_tasks": len(self.active_tasks),
                "completed_tasks": len(self.completed_tasks),
                "failed_tasks": len(self.failed_tasks),
                "results_available": len(self.results),
                "resource_usage": {
                    str(res_type.name): self.resource_manager.get_usage_percentage(res_type)
                    for res_type in ResourceType
                }
            }
    
    def clear_results(self):
        """Clear all stored results."""
        with self.result_lock:
            self.results.clear()
    
    def shutdown(self, wait: bool = True):
        """
        Shutdown the workload distributor.
        
        Args:
            wait: Wait for pending tasks to complete
        """
        self.thread_executor.shutdown(wait=wait)
        self.process_executor.shutdown(wait=wait)


class BatchProcessor:
    """
    Processor for batch operations on files.
    
    Handles batched processing of files with progress tracking
    and resource management.
    """
    
    def __init__(self, workload_distributor: Optional[WorkloadDistributor] = None):
        """
        Initialize the batch processor.
        
        Args:
            workload_distributor: Workload distributor to use
        """
        self.workload_distributor = workload_distributor or WorkloadDistributor()
    
    def process_files_in_batches(
        self,
        files: List[Any],
        processor_func: Callable,
        batch_size: int = 10,
        show_progress: bool = True,
        use_threads: bool = True
    ) -> List[Any]:
        """
        Process files in batches.
        
        Args:
            files: List of files to process
            processor_func: Function to process each file
            batch_size: Number of files per batch
            show_progress: Show progress bar
            use_threads: Use threads instead of processes
            
        Returns:
            List of processing results
        """
        results = []
        total_files = len(files)
        
        # Process in batches
        with tqdm(total=total_files, desc="Processing files", disable=not show_progress) as pbar:
            for i in range(0, total_files, batch_size):
                batch = files[i:i+batch_size]
                
                # Create tasks for this batch
                for j, file_info in enumerate(batch):
                    task = Task(
                        id=f"file_{i+j}",
                        func=processor_func,
                        args=(file_info,)
                    )
                    self.workload_distributor.schedule_task(task)
                
                # Process tasks
                batch_results = self.workload_distributor.process_tasks(
                    use_threads=use_threads,
                    show_progress=False  # We already have our own progress bar
                )
                
                # Collect results
                results.extend(batch_results.values())
                
                # Update progress
                pbar.update(len(batch))
        
        return results
    
    async def process_files_in_batches_async(
        self,
        files: List[Any],
        processor_func: Callable,
        batch_size: int = 10,
        show_progress: bool = True
    ) -> List[Any]:
        """
        Process files in batches asynchronously.
        
        Args:
            files: List of files to process
            processor_func: Function to process each file
            batch_size: Number of files per batch
            show_progress: Show progress bar
            
        Returns:
            List of processing results
        """
        results = []
        total_files = len(files)
        
        # Process in batches
        with tqdm(total=total_files, desc="Processing files", disable=not show_progress) as pbar:
            for i in range(0, total_files, batch_size):
                batch = files[i:i+batch_size]
                
                # Create tasks for this batch
                for j, file_info in enumerate(batch):
                    task = Task(
                        id=f"file_{i+j}",
                        func=processor_func,
                        args=(file_info,)
                    )
                    self.workload_distributor.schedule_task(task)
                
                # Process tasks
                batch_results = await self.workload_distributor.process_tasks_async(
                    show_progress=False  # We already have our own progress bar
                )
                
                # Collect results
                results.extend(batch_results.values())
                
                # Update progress
                pbar.update(len(batch))
        
        return results
    
    def process_with_priority(
        self,
        items: List[Tuple[Any, TaskPriority]],
        processor_func: Callable,
        show_progress: bool = True,
        use_threads: bool = True
    ) -> Dict[str, Any]:
        """
        Process items with different priorities.
        
        Args:
            items: List of (item, priority) tuples
            processor_func: Function to process each item
            show_progress: Show progress bar
            use_threads: Use threads instead of processes
            
        Returns:
            Dictionary mapping task IDs to results
        """
        # Schedule all tasks with their priorities
        for i, (item, priority) in enumerate(items):
            task = Task(
                id=f"item_{i}",
                func=processor_func,
                args=(item,),
                priority=priority
            )
            self.workload_distributor.schedule_task(task)
        
        # Process tasks
        results = self.workload_distributor.process_tasks(
            use_threads=use_threads,
            show_progress=show_progress
        )
        
        return results