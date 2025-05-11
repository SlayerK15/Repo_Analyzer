"""
AI utilities for RepoAnalyzer.

This module provides helper functions and utilities for AI-enhanced analysis,
including formatting, validation, and post-processing of AI results.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

def format_repository_info(repo_path: str, file_count: int) -> str:
    """
    Format repository information for AI prompts.
    
    Args:
        repo_path: Path to the repository
        file_count: Number of files in the repository
        
    Returns:
        Formatted repository information string
    """
    return f"Repository path: {repo_path}\nFile count: {file_count}"

def format_technologies_for_prompt(technologies: List[Dict[str, Any]]) -> str:
    """
    Format technologies for AI prompts.
    
    Args:
        technologies: List of technology dictionaries
        
    Returns:
        Formatted technologies string
    """
    if not technologies:
        return "No technologies detected."
    
    # Sort technologies by confidence
    sorted_techs = sorted(technologies, key=lambda x: x.get("confidence", 0), reverse=True)
    
    # Format the technologies
    tech_lines = []
    for tech in sorted_techs:
        name = tech.get("name", "Unknown")
        category = tech.get("category", "Unknown")
        confidence = tech.get("confidence", 0)
        tech_lines.append(f"- {name} ({category}, {confidence:.1f}% confidence)")
    
    return "\n".join(tech_lines)

def format_architecture_for_prompt(patterns: List[Dict[str, Any]]) -> str:
    """
    Format architecture patterns for AI prompts.
    
    Args:
        patterns: List of architecture pattern dictionaries
        
    Returns:
        Formatted architecture patterns string
    """
    if not patterns:
        return "No architecture patterns detected."
    
    # Sort patterns by confidence
    sorted_patterns = sorted(patterns, key=lambda x: x.get("confidence", 0), reverse=True)
    
    # Format the patterns
    pattern_lines = []
    for pattern in sorted_patterns:
        name = pattern.get("name", "Unknown")
        pattern_type = pattern.get("type", "Unknown")
        confidence = pattern.get("confidence", 0)
        pattern_lines.append(f"- {name} ({pattern_type}, {confidence:.1f}% confidence)")
    
    return "\n".join(pattern_lines)

def format_code_quality_for_prompt(quality_assessment: Dict[str, Any]) -> str:
    """
    Format code quality assessment for AI prompts.
    
    Args:
        quality_assessment: Code quality assessment dictionary
        
    Returns:
        Formatted code quality string
    """
    if not quality_assessment:
        return "No code quality assessment performed."
    
    quality_lines = []
    
    # Add scores
    for aspect in ["readability", "maintainability", "performance"]:
        if aspect in quality_assessment:
            score = quality_assessment[aspect].get("score", 0)
            quality_lines.append(f"{aspect.capitalize()}: {score:.1f}/100")
    
    # Add strengths and weaknesses
    for aspect in ["readability", "maintainability", "performance"]:
        if aspect in quality_assessment:
            strengths = quality_assessment[aspect].get("strengths", [])
            weaknesses = quality_assessment[aspect].get("weaknesses", [])
            
            if strengths:
                quality_lines.append(f"\n{aspect.capitalize()} strengths:")
                for strength in strengths[:3]:  # Limit to top 3
                    quality_lines.append(f"- {strength}")
            
            if weaknesses:
                quality_lines.append(f"\n{aspect.capitalize()} weaknesses:")
                for weakness in weaknesses[:3]:  # Limit to top 3
                    quality_lines.append(f"- {weakness}")
    
    return "\n".join(quality_lines)

def parse_json_response(response: str) -> Dict[str, Any]:
    """
    Parse JSON response from AI.
    
    Args:
        response: JSON string from AI
        
    Returns:
        Parsed JSON as dictionary
    """
    try:
        # First, find the JSON block if it's surrounded by markdown code blocks
        if "```json" in response and "```" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_text = response[start:end].strip()
        elif "```" in response:
            # Try to find any code block
            start = response.find("```") + 3
            end = response.find("```", start)
            json_text = response[start:end].strip()
        else:
            # No code blocks, use the entire response
            json_text = response.strip()
        
        # Parse the JSON text
        return json.loads(json_text)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {str(e)}")
        logger.debug(f"Response: {response}")
        return {"error": f"Failed to parse AI response as JSON: {str(e)}"}
    except Exception as e:
        logger.error(f"Error parsing AI response: {str(e)}")
        return {"error": f"Error processing AI response: {str(e)}"}

def validate_ai_result(result: Dict[str, Any], result_type: str) -> Dict[str, Any]:
    """
    Validate and fix AI results to ensure proper structure.
    
    Args:
        result: AI result dictionary
        result_type: Type of result (technologies, architecture, code_quality)
        
    Returns:
        Validated and fixed result dictionary
    """
    # Check for error or non-success
    if "error" in result or not result.get("success", True):
        return result
    
    # Different validation logic based on result type
    if result_type == "technologies":
        # Ensure technologies is a list
        if "technologies" not in result:
            result["technologies"] = []
        elif not isinstance(result["technologies"], list):
            result["technologies"] = []
        
        # Validate each technology
        for tech in result.get("technologies", []):
            if not isinstance(tech, dict):
                continue
            
            # Ensure required fields
            if "name" not in tech:
                tech["name"] = "Unknown Technology"
            if "category" not in tech:
                tech["category"] = "unknown"
            if "confidence" not in tech:
                tech["confidence"] = 50.0
            if "evidence" not in tech:
                tech["evidence"] = []
    
    elif result_type == "architecture":
        # Ensure patterns is a list
        if "patterns" not in result:
            result["patterns"] = []
        elif not isinstance(result["patterns"], list):
            result["patterns"] = []
        
        # Validate each pattern
        for pattern in result.get("patterns", []):
            if not isinstance(pattern, dict):
                continue
            
            # Ensure required fields
            if "name" not in pattern:
                pattern["name"] = "Unknown Pattern"
            if "type" not in pattern:
                pattern["type"] = "unknown"
            if "confidence" not in pattern:
                pattern["confidence"] = 50.0
            if "evidence" not in pattern:
                pattern["evidence"] = []
    
    elif result_type == "code_quality":
        # Ensure quality_assessment exists
        if "quality_assessment" not in result:
            result["quality_assessment"] = {
                "readability": {"score": 0, "strengths": [], "weaknesses": []},
                "maintainability": {"score": 0, "strengths": [], "weaknesses": []},
                "performance": {"score": 0, "strengths": [], "weaknesses": []}
            }
        
        # Ensure issues is a list
        if "issues" not in result:
            result["issues"] = []
        elif not isinstance(result["issues"], list):
            result["issues"] = []
    
    # Ensure suggestions is a list for all result types
    if "suggestions" not in result:
        result["suggestions"] = []
    elif not isinstance(result["suggestions"], list):
        result["suggestions"] = []
    
    # Validate each suggestion
    for suggestion in result.get("suggestions", []):
        if not isinstance(suggestion, dict):
            continue
        
        # Ensure required fields
        if "text" not in suggestion:
            suggestion["text"] = "Unknown suggestion"
        if "severity" not in suggestion:
            suggestion["severity"] = "medium"
        if "reason" not in suggestion:
            suggestion["reason"] = "AI-detected suggestion"
    
    return result