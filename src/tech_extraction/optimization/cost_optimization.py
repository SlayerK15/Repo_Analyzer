"""
Cost Optimization for the Technology Extraction System.

This module provides functionality for monitoring and optimizing costs,
particularly focused on AI API usage.
"""
import json
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union

from tech_extraction.config import settings

logger = logging.getLogger(__name__)


class CostMode(Enum):
    """Modes for cost optimization."""
    AI_ONLY = "ai_only"  # Use AI for all analysis
    PATTERN_ONLY = "pattern_only"  # Use pattern matching only
    HYBRID = "hybrid"  # Use both methods with configurable ratios
    BALANCED = "balanced"  # Balanced approach (default)
    ECONOMY = "economy"  # Economy mode - minimize AI usage
    UNLIMITED = "unlimited"  # No cost constraints


@dataclass
class CostSettings:
    """Settings for cost optimization."""
    mode: CostMode = CostMode.BALANCED
    max_budget: float = 0.0  # 0 means no explicit limit
    token_budget: int = 0  # 0 means no explicit limit
    ai_analysis_ratio: float = 0.5  # For hybrid mode, ratio of files to analyze with AI
    important_file_threshold: float = 0.7  # Importance threshold for AI analysis


class CostOptimization:
    """
    System for optimizing and managing API costs.
    
    The CostOptimization performs the following operations:
    1. Track token and cost usage
    2. Manage budgets and enforce limits
    3. Optimize analysis strategies based on cost constraints
    4. Provide usage reports and forecasts
    """
    
    # Cost per 1000 tokens for different models (prompt, completion)
    MODEL_COSTS = {
        "gpt-4-turbo-preview": (0.01, 0.03),
        "gpt-4-vision-preview": (0.01, 0.03),
        "gpt-4": (0.03, 0.06),
        "gpt-3.5-turbo-16k": (0.0015, 0.002),
        "gpt-3.5-turbo": (0.0015, 0.002),
        "claude-3-opus-20240229": (0.015, 0.075),
        "claude-3-sonnet-20240229": (0.003, 0.015),
        "claude-3-haiku-20240307": (0.00025, 0.00125),
    }
    
    def __init__(self, settings_path: Optional[str] = None):
        """
        Initialize the cost optimization system.
        
        Args:
            settings_path: Path to cost settings file
        """
        # Initialize settings
        self.settings = CostSettings()
        self.usage_data = {
            "tokens": {
                "prompt": 0,
                "completion": 0,
                "total": 0,
            },
            "costs": {
                "prompt": 0.0,
                "completion": 0.0,
                "total": 0.0,
            },
            "requests": {
                "total": 0,
                "by_model": {},
            },
            "start_time": time.time(),
            "last_update": time.time(),
        }
        
        # Initialize tracking files
        self.settings_path = settings_path or os.path.join(
            os.path.expanduser("~"), ".tech_extraction", "cost_settings.json"
        )
        self.usage_path = os.path.join(
            os.path.expanduser("~"), ".tech_extraction", "usage_data.json"
        )
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
        
        # Load settings if available
        self.load_settings()
        
        # Load usage data if available
        self.load_usage_data()
    
    def load_settings(self):
        """Load cost settings from file."""
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, 'r') as f:
                    data = json.load(f)
                
                # Convert mode string to enum
                if "mode" in data:
                    data["mode"] = CostMode(data["mode"])
                
                # Update settings
                for key, value in data.items():
                    if hasattr(self.settings, key):
                        setattr(self.settings, key, value)
                
                logger.info(f"Loaded cost settings from {self.settings_path}")
            
            except Exception as e:
                logger.warning(f"Error loading cost settings: {e}")
    
    def save_settings(self):
        """Save cost settings to file."""
        try:
            # Convert enum to string
            data = {
                "mode": self.settings.mode.value,
                "max_budget": self.settings.max_budget,
                "token_budget": self.settings.token_budget,
                "ai_analysis_ratio": self.settings.ai_analysis_ratio,
                "important_file_threshold": self.settings.important_file_threshold,
            }
            
            with open(self.settings_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved cost settings to {self.settings_path}")
        
        except Exception as e:
            logger.warning(f"Error saving cost settings: {e}")
    
    def load_usage_data(self):
        """Load usage data from file."""
        if os.path.exists(self.usage_path):
            try:
                with open(self.usage_path, 'r') as f:
                    data = json.load(f)
                
                # Update usage data
                self.usage_data.update(data)
                
                logger.info(f"Loaded usage data from {self.usage_path}")
            
            except Exception as e:
                logger.warning(f"Error loading usage data: {e}")
    
    def save_usage_data(self):
        """Save usage data to file."""
        try:
            # Update last update time
            self.usage_data["last_update"] = time.time()
            
            with open(self.usage_path, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
            
            logger.debug(f"Saved usage data to {self.usage_path}")
        
        except Exception as e:
            logger.warning(f"Error saving usage data: {e}")
    
    def update_usage(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ):
        """
        Update usage data with new API call information.
        
        Args:
            model: Model name
            prompt_tokens: Number of prompt tokens used
            completion_tokens: Number of completion tokens used
        """
        # Update token counts
        self.usage_data["tokens"]["prompt"] += prompt_tokens
        self.usage_data["tokens"]["completion"] += completion_tokens
        self.usage_data["tokens"]["total"] += prompt_tokens + completion_tokens
        
        # Update request counts
        self.usage_data["requests"]["total"] += 1
        
        if model in self.usage_data["requests"]["by_model"]:
            self.usage_data["requests"]["by_model"][model] += 1
        else:
            self.usage_data["requests"]["by_model"][model] = 1
        
        # Calculate costs
        prompt_cost, completion_cost = self._calculate_cost(model, prompt_tokens, completion_tokens)
        
        # Update cost data
        self.usage_data["costs"]["prompt"] += prompt_cost
        self.usage_data["costs"]["completion"] += completion_cost
        self.usage_data["costs"]["total"] += prompt_cost + completion_cost
        
        # Save updated data
        self.save_usage_data()
    
    def _calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> Tuple[float, float]:
        """
        Calculate the cost of an API call.
        
        Args:
            model: Model name
            prompt_tokens: Number of prompt tokens used
            completion_tokens: Number of completion tokens used
            
        Returns:
            Tuple of (prompt_cost, completion_cost)
        """
        # Get cost rates for the model
        if model in self.MODEL_COSTS:
            prompt_rate, completion_rate = self.MODEL_COSTS[model]
        else:
            # Use a default rate for unknown models
            logger.warning(f"Unknown model {model}, using default cost rates")
            prompt_rate, completion_rate = 0.01, 0.03
        
        # Calculate costs (per 1000 tokens)
        prompt_cost = (prompt_tokens / 1000) * prompt_rate
        completion_cost = (completion_tokens / 1000) * completion_rate
        
        return prompt_cost, completion_cost
    
    def check_budget(self) -> bool:
        """
        Check if current usage is within budget.
        
        Returns:
            True if within budget, False otherwise
        """
        # Check cost budget
        if self.settings.max_budget > 0:
            if self.usage_data["costs"]["total"] >= self.settings.max_budget:
                logger.warning(f"Cost budget exceeded: ${self.usage_data['costs']['total']:.2f} / ${self.settings.max_budget:.2f}")
                return False
        
        # Check token budget
        if self.settings.token_budget > 0:
            if self.usage_data["tokens"]["total"] >= self.settings.token_budget:
                logger.warning(f"Token budget exceeded: {self.usage_data['tokens']['total']} / {self.settings.token_budget}")
                return False
        
        return True
    
    def get_usage_report(self) -> Dict:
        """
        Get a report of current usage.
        
        Returns:
            Dictionary with usage information
        """
        # Calculate duration
        duration = time.time() - self.usage_data["start_time"]
        hours = duration / 3600
        
        # Calculate hourly and projected costs
        hourly_cost = self.usage_data["costs"]["total"] / hours if hours > 0 else 0
        projected_cost_24h = hourly_cost * 24 if hours > 0 else 0
        
        return {
            "tokens_used": self.usage_data["tokens"]["total"],
            "cost_to_date": self.usage_data["costs"]["total"],
            "requests_made": self.usage_data["requests"]["total"],
            "duration_hours": hours,
            "hourly_cost": hourly_cost,
            "projected_cost_24h": projected_cost_24h,
            "budget_status": {
                "max_budget": self.settings.max_budget,
                "token_budget": self.settings.token_budget,
                "within_budget": self.check_budget(),
                "cost_percentage": (self.usage_data["costs"]["total"] / self.settings.max_budget * 100) 
                                  if self.settings.max_budget > 0 else 0,
                "token_percentage": (self.usage_data["tokens"]["total"] / self.settings.token_budget * 100) 
                                   if self.settings.token_budget > 0 else 0,
            },
            "model_usage": self.usage_data["requests"]["by_model"],
        }
    
    def reset_usage(self):
        """Reset usage data."""
        self.usage_data = {
            "tokens": {
                "prompt": 0,
                "completion": 0,
                "total": 0,
            },
            "costs": {
                "prompt": 0.0,
                "completion": 0.0,
                "total": 0.0,
            },
            "requests": {
                "total": 0,
                "by_model": {},
            },
            "start_time": time.time(),
            "last_update": time.time(),
        }
        
        self.save_usage_data()
        logger.info("Reset usage data")
    
    def set_mode(self, mode: CostMode):
        """
        Set the cost optimization mode.
        
        Args:
            mode: New cost mode
        """
        self.settings.mode = mode
        self.save_settings()
        logger.info(f"Set cost mode to {mode.value}")
    
    def set_budget(self, max_budget: float, token_budget: int = 0):
        """
        Set budget limits.
        
        Args:
            max_budget: Maximum cost budget (0 for no limit)
            token_budget: Maximum token budget (0 for no limit)
        """
        self.settings.max_budget = max_budget
        self.settings.token_budget = token_budget
        self.save_settings()
        logger.info(f"Set budget limits: ${max_budget:.2f}, {token_budget} tokens")
    
    def should_use_ai_for_file(self, importance_score: float) -> bool:
        """
        Determine if AI should be used for a file based on settings and importance.
        
        Args:
            importance_score: Importance score of the file (0-1)
            
        Returns:
            True if AI should be used, False otherwise
        """
        # Check if within budget
        if not self.check_budget():
            # If we're over budget, only use AI for very important files
            return importance_score > 0.9
        
        # Check mode
        if self.settings.mode == CostMode.AI_ONLY:
            return True
        elif self.settings.mode == CostMode.PATTERN_ONLY:
            return False
        elif self.settings.mode == CostMode.HYBRID:
            # Use importance score and ratio
            return importance_score >= (1.0 - self.settings.ai_analysis_ratio)
        elif self.settings.mode == CostMode.BALANCED:
            # Use importance threshold
            return importance_score >= self.settings.important_file_threshold
        elif self.settings.mode == CostMode.ECONOMY:
            # Very selective AI usage
            return importance_score > 0.85
        elif self.settings.mode == CostMode.UNLIMITED:
            return True
        
        # Default to balanced approach
        return importance_score >= self.settings.important_file_threshold
    
    def get_token_allocation(self, files_count: int) -> int:
        """
        Calculate token allocation per file based on current settings.
        
        Args:
            files_count: Number of files to allocate tokens for
            
        Returns:
            Token allocation per file
        """
        # Base allocation
        if self.settings.mode == CostMode.ECONOMY:
            base_allocation = 1000  # Low allocation for economy mode
        elif self.settings.mode == CostMode.UNLIMITED:
            base_allocation = 4000  # High allocation for unlimited mode
        else:
            base_allocation = 2000  # Default allocation
        
        # If we have a token budget, distribute it
        if self.settings.token_budget > 0:
            # Calculate remaining budget
            remaining = max(0, self.settings.token_budget - self.usage_data["tokens"]["total"])
            
            # Estimated number of files that will use AI
            ai_ratio = {
                CostMode.AI_ONLY: 1.0,
                CostMode.PATTERN_ONLY: 0.0,
                CostMode.HYBRID: self.settings.ai_analysis_ratio,
                CostMode.BALANCED: 0.5,
                CostMode.ECONOMY: 0.2,
                CostMode.UNLIMITED: 1.0
            }[self.settings.mode]
            
            ai_files = int(files_count * ai_ratio)
            
            if ai_files > 0:
                # Distribute remaining budget
                per_file = remaining // ai_files
                
                # Use the smaller of base_allocation or calculated per_file
                return min(base_allocation, per_file) if per_file > 0 else base_allocation
        
        return base_allocation
    
    def estimate_cost(
        self,
        files_count: int,
        model: str = "gpt-3.5-turbo-16k",
        average_tokens_per_file: int = 2000
    ) -> Dict:
        """
        Estimate the cost of processing a set of files.
        
        Args:
            files_count: Number of files to process
            model: Model to use
            average_tokens_per_file: Average number of tokens per file
            
        Returns:
            Dictionary with cost estimation
        """
        # Estimate number of files that will use AI
        ai_ratio = {
            CostMode.AI_ONLY: 1.0,
            CostMode.PATTERN_ONLY: 0.0,
            CostMode.HYBRID: self.settings.ai_analysis_ratio,
            CostMode.BALANCED: 0.5,
            CostMode.ECONOMY: 0.2,
            CostMode.UNLIMITED: 1.0
        }[self.settings.mode]
        
        ai_files = int(files_count * ai_ratio)
        
        # Estimate token usage
        prompt_tokens = ai_files * average_tokens_per_file
        completion_tokens = ai_files * (average_tokens_per_file * 0.3)  # Estimate 30% of input size
        
        # Calculate costs
        prompt_cost, completion_cost = self._calculate_cost(model, prompt_tokens, completion_tokens)
        total_cost = prompt_cost + completion_cost
        
        return {
            "files_count": files_count,
            "ai_files": ai_files,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "prompt_cost": prompt_cost,
            "completion_cost": completion_cost,
            "total_cost": total_cost,
        }


# Create a global instance
cost_optimizer = CostOptimization()