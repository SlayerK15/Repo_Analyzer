"""
Output Generation for the Technology Extraction System.

This module provides functionality for generating reports and visualizations
of the detected technologies in various formats.
"""
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from tech_extraction.models.technology import (
    Technology,
    TechnologyCategory,
    TechnologyStack,
    TechnologyGroup,
    TechnologyUsage,
)
from tech_extraction.results.technology_aggregation import TechnologyAggregation

logger = logging.getLogger(__name__)


class OutputGenerator:
    """
    Generator for creating output in various formats.
    
    The OutputGenerator performs the following operations:
    1. Generate structured reports in different formats (JSON, Markdown, HTML)
    2. Create visualizations of the technology stack
    3. Customize output based on audience and detail level
    """
    
    def __init__(self, tech_aggregation: TechnologyAggregation):
        """
        Initialize the output generator.
        
        Args:
            tech_aggregation: Technology aggregation instance
        """
        self.tech_aggregation = tech_aggregation
    
    def generate_json(
        self,
        confidence_threshold: float = 0.0,
        include_evidence: bool = True,
        detail_level: str = "medium"
    ) -> str:
        """
        Generate a JSON report of detected technologies.
        
        Args:
            confidence_threshold: Minimum confidence threshold for inclusion
            include_evidence: Whether to include evidence in the output
            detail_level: Detail level ("low", "medium", "high")
            
        Returns:
            JSON string representation of the report
        """
        # Get technologies above threshold
        technologies = [
            tech for tech in self.tech_aggregation.get_all_technologies()
            if tech.confidence >= confidence_threshold
        ]
        
        # Convert to dictionaries
        tech_dicts = []
        for tech in technologies:
            tech_dict = asdict(tech)
            
            # Adjust based on detail level
            if detail_level == "low":
                # Minimal details
                tech_dict.pop("evidence", None)
                tech_dict.pop("usage", None)
            elif detail_level == "medium":
                # Medium details
                if not include_evidence:
                    tech_dict.pop("evidence", None)
                
                # Limit evidence items
                if "evidence" in tech_dict and tech_dict["evidence"]:
                    tech_dict["evidence"] = tech_dict["evidence"][:3]
            
            tech_dicts.append(tech_dict)
        
        # Get technology stacks
        stacks = self.tech_aggregation.get_all_technology_stacks()
        stack_dicts = []
        
        for stack in stacks:
            # Only include stacks with primary technology above threshold
            if stack.primary_technology.confidence >= confidence_threshold:
                # Convert to dict with related technologies above threshold
                stack_dict = {
                    "name": stack.name,
                    "primary_technology": asdict(stack.primary_technology),
                    "related_technologies": [
                        asdict(tech) for tech in stack.related_technologies
                        if tech.confidence >= confidence_threshold
                    ]
                }
                
                # Adjust evidence based on detail level
                if detail_level != "high":
                    if "evidence" in stack_dict["primary_technology"]:
                        stack_dict["primary_technology"].pop("evidence", None)
                    
                    for tech in stack_dict["related_technologies"]:
                        tech.pop("evidence", None)
                
                stack_dicts.append(stack_dict)
        
        # Create final report structure
        report = {
            "technologies": tech_dicts,
            "technology_stacks": stack_dicts,
        }
        
        # Add technology groups if detail level is medium or high
        if detail_level in ["medium", "high"]:
            groups = self.tech_aggregation.get_technology_groups()
            group_dicts = []
            
            for group in groups:
                # Include only technologies above threshold
                filtered_techs = [
                    asdict(tech) for tech in group.technologies
                    if tech.confidence >= confidence_threshold
                ]
                
                # Remove evidence if needed
                if not include_evidence or detail_level == "medium":
                    for tech in filtered_techs:
                        tech.pop("evidence", None)
                
                if filtered_techs:  # Only include non-empty groups
                    group_dicts.append({
                        "name": group.name,
                        "technologies": filtered_techs
                    })
            
            report["technology_groups"] = group_dicts
        
        # Convert to JSON
        return json.dumps(report, indent=2)
    
    def generate_markdown(
        self,
        confidence_threshold: float = 0.0,
        include_evidence: bool = True,
        detail_level: str = "medium"
    ) -> str:
        """
        Generate a Markdown report of detected technologies.
        
        Args:
            confidence_threshold: Minimum confidence threshold for inclusion
            include_evidence: Whether to include evidence in the output
            detail_level: Detail level ("low", "medium", "high")
            
        Returns:
            Markdown string representation of the report
        """
        # Get technologies above threshold
        technologies = [
            tech for tech in self.tech_aggregation.get_all_technologies()
            if tech.confidence >= confidence_threshold
        ]
        
        # Sort by confidence
        technologies.sort(key=lambda t: t.confidence, reverse=True)
        
        # Get technology stacks
        stacks = self.tech_aggregation.get_all_technology_stacks()
        stacks = [
            stack for stack in stacks
            if stack.primary_technology.confidence >= confidence_threshold
        ]
        
        # Start building the report
        report = []
        
        # Add title and summary
        report.append("# Technology Detection Report\n")
        report.append(f"## Summary\n")
        report.append(f"Detected {len(technologies)} technologies ")
        report.append(f"and {len(stacks)} primary technology stacks.\n\n")
        
        # Add technology stacks section
        if stacks:
            report.append("## Technology Stacks\n")
            
            for stack in stacks:
                report.append(f"### {stack.name}\n")
                
                # Add primary technology
                primary = stack.primary_technology
                report.append(f"**Primary Technology:** {primary.name}")
                if primary.version:
                    report.append(f" (v{primary.version})")
                report.append(f" - {primary.category.name.title()}\n")
                
                report.append(f"Confidence: {primary.confidence:.1f}%\n")
                
                # Add related technologies
                related = [
                    tech for tech in stack.related_technologies
                    if tech.confidence >= confidence_threshold
                ]
                
                if related:
                    report.append("\n**Related Technologies:**\n")
                    
                    for tech in sorted(related, key=lambda t: t.confidence, reverse=True):
                        report.append(f"- {tech.name}")
                        if tech.version:
                            report.append(f" (v{tech.version})")
                        report.append(f" - {tech.category.name.title()}")
                        report.append(f" - Confidence: {tech.confidence:.1f}%\n")
                
                report.append("\n")
        
        # Add technologies by category if detail level is medium or high
        if detail_level in ["medium", "high"]:
            report.append("## Technologies by Category\n")
            
            # Get technology groups
            groups = self.tech_aggregation.get_technology_groups()
            
            for group in groups:
                # Filter by threshold
                filtered_techs = [
                    tech for tech in group.technologies
                    if tech.confidence >= confidence_threshold
                ]
                
                if not filtered_techs:  # Skip empty groups
                    continue
                
                report.append(f"### {group.name}\n")
                
                for tech in sorted(filtered_techs, key=lambda t: t.confidence, reverse=True):
                    report.append(f"- **{tech.name}**")
                    if tech.version:
                        report.append(f" (v{tech.version})")
                    report.append(f" - Confidence: {tech.confidence:.1f}%")
                    
                    # Add usage details for high detail level
                    if detail_level == "high" and tech.usage:
                        report.append(f"\n  - Used in {tech.usage.file_count} files")
                        report.append(f", {tech.usage.frequency} references")
                        report.append(f", Criticality: {tech.usage.criticality:.1f}%")
                    
                    report.append("\n")
                
                report.append("\n")
        
        # Add evidence section for high detail level
        if detail_level == "high" and include_evidence:
            report.append("## Evidence Details\n")
            
            # Take top technologies by confidence
            top_techs = sorted(technologies, key=lambda t: t.confidence, reverse=True)[:10]
            
            for tech in top_techs:
                report.append(f"### {tech.name}\n")
                
                if not tech.evidence:
                    report.append("No detailed evidence available.\n\n")
                    continue
                
                report.append("**Evidence:**\n")
                
                for i, evidence in enumerate(tech.evidence, 1):
                    report.append(f"{i}. **Type:** {evidence['type']}, ")
                    report.append(f"**Source:** {evidence['source']}\n")
                    
                    if evidence.get('file_path'):
                        report.append(f"   File: `{evidence['file_path']}`")
                        if evidence.get('line_number'):
                            report.append(f", Line: {evidence['line_number']}")
                        report.append("\n")
                    
                    if evidence.get('snippet'):
                        report.append(f"   ```\n   {evidence['snippet']}\n   ```\n")
                    
                    if evidence.get('details'):
                        report.append(f"   Details: {evidence['details']}\n")
                    
                    report.append("\n")
                
                report.append("\n")
        
        return "".join(report)
    
    def generate_html(
        self,
        confidence_threshold: float = 0.0,
        include_evidence: bool = True,
        detail_level: str = "medium"
    ) -> str:
        """
        Generate an HTML report of detected technologies.
        
        Args:
            confidence_threshold: Minimum confidence threshold for inclusion
            include_evidence: Whether to include evidence in the output
            detail_level: Detail level ("low", "medium", "high")
            
        Returns:
            HTML string representation of the report
        """
        # Get technologies above threshold
        technologies = [
            tech for tech in self.tech_aggregation.get_all_technologies()
            if tech.confidence >= confidence_threshold
        ]
        
        # Sort by confidence
        technologies.sort(key=lambda t: t.confidence, reverse=True)
        
        # Get technology stacks
        stacks = self.tech_aggregation.get_all_technology_stacks()
        stacks = [
            stack for stack in stacks
            if stack.primary_technology.confidence >= confidence_threshold
        ]
        
        # Start building the HTML report
        html = []
        
        # Add HTML header and styles
        html.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Technology Detection Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        .tech-card {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: #f9f9f9;
        }
        .tech-name {
            font-weight: bold;
            font-size: 1.2em;
            color: #2980b9;
        }
        .tech-version {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .tech-confidence {
            margin-top: 5px;
        }
        .progress-bar {
            background-color: #ecf0f1;
            border-radius: 13px;
            padding: 3px;
            margin-top: 5px;
        }
        .progress {
            background-color: #2980b9;
            height: 20px;
            border-radius: 10px;
            text-align: center;
            color: white;
            font-size: 0.8em;
            line-height: 20px;
        }
        .evidence-item {
            border-left: 3px solid #2980b9;
            padding-left: 10px;
            margin: 10px 0;
            font-size: 0.9em;
        }
        .code-snippet {
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            white-space: pre-wrap;
            margin: 5px 0;
        }
        .tech-group {
            margin-bottom: 30px;
        }
        .badge {
            display: inline-block;
            background-color: #3498db;
            color: white;
            border-radius: 12px;
            padding: 3px 8px;
            font-size: 0.8em;
            margin-right: 5px;
        }
        .related-tech {
            margin-left: 20px;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <h1>Technology Detection Report</h1>
""")
        
        # Add summary section
        html.append(f"<div class='summary-section'>")
        html.append(f"<h2>Summary</h2>")
        html.append(f"<p>Detected {len(technologies)} technologies and {len(stacks)} primary technology stacks.</p>")
        html.append(f"</div>")
        
        # Add technology stacks section
        if stacks:
            html.append("<h2>Technology Stacks</h2>")
            
            for stack in stacks:
                html.append(f"<div class='tech-stack'>")
                html.append(f"<h3>{stack.name}</h3>")
                
                # Add primary technology
                primary = stack.primary_technology
                html.append(f"<div class='tech-card'>")
                html.append(f"<div class='tech-name'>{primary.name}")
                if primary.version:
                    html.append(f" <span class='tech-version'>v{primary.version}</span>")
                html.append(f"</div>")
                
                html.append(f"<div class='badge'>{primary.category.name.title()}</div>")
                html.append(f"<div class='tech-confidence'>")
                html.append(f"<div class='progress-bar'>")
                html.append(f"<div class='progress' style='width: {primary.confidence}%;'>")
                html.append(f"{primary.confidence:.1f}%")
                html.append(f"</div></div></div>")
                
                # Add related technologies
                related = [
                    tech for tech in stack.related_technologies
                    if tech.confidence >= confidence_threshold
                ]
                
                if related:
                    html.append("<h4>Related Technologies</h4>")
                    
                    for tech in sorted(related, key=lambda t: t.confidence, reverse=True):
                        html.append(f"<div class='related-tech'>")
                        html.append(f"<div class='tech-name'>{tech.name}")
                        if tech.version:
                            html.append(f" <span class='tech-version'>v{tech.version}</span>")
                        html.append(f"</div>")
                        
                        html.append(f"<div class='badge'>{tech.category.name.title()}</div>")
                        html.append(f"<div class='tech-confidence'>")
                        html.append(f"<div class='progress-bar'>")
                        html.append(f"<div class='progress' style='width: {tech.confidence}%;'>")
                        html.append(f"{tech.confidence:.1f}%")
                        html.append(f"</div></div></div>")
                        html.append(f"</div>")
                
                html.append(f"</div>")
                html.append(f"</div>")
        
        # Add technologies by category if detail level is medium or high
        if detail_level in ["medium", "high"]:
            html.append("<h2>Technologies by Category</h2>")
            
            # Get technology groups
            groups = self.tech_aggregation.get_technology_groups()
            
            for group in groups:
                # Filter by threshold
                filtered_techs = [
                    tech for tech in group.technologies
                    if tech.confidence >= confidence_threshold
                ]
                
                if not filtered_techs:  # Skip empty groups
                    continue
                
                html.append(f"<div class='tech-group'>")
                html.append(f"<h3>{group.name}</h3>")
                
                for tech in sorted(filtered_techs, key=lambda t: t.confidence, reverse=True):
                    html.append(f"<div class='tech-card'>")
                    html.append(f"<div class='tech-name'>{tech.name}")
                    if tech.version:
                        html.append(f" <span class='tech-version'>v{tech.version}</span>")
                    html.append(f"</div>")
                    
                    html.append(f"<div class='tech-confidence'>")
                    html.append(f"<div class='progress-bar'>")
                    html.append(f"<div class='progress' style='width: {tech.confidence}%;'>")
                    html.append(f"{tech.confidence:.1f}%")
                    html.append(f"</div></div></div>")
                    
                    # Add usage details for high detail level
                    if detail_level == "high" and tech.usage:
                        html.append(f"<div class='tech-usage'>")
                        html.append(f"<p>Used in {tech.usage.file_count} files, ")
                        html.append(f"{tech.usage.frequency} references, ")
                        html.append(f"Criticality: {tech.usage.criticality:.1f}%</p>")
                        html.append(f"</div>")
                    
                    # Add evidence for high detail level
                    if detail_level == "high" and include_evidence and tech.evidence:
                        html.append(f"<div class='tech-evidence'>")
                        html.append(f"<h4>Evidence</h4>")
                        
                        for evidence in tech.evidence[:3]:  # Limit to top 3 evidence items
                            html.append(f"<div class='evidence-item'>")
                            html.append(f"<div><strong>Type:</strong> {evidence['type']}, ")
                            html.append(f"<strong>Source:</strong> {evidence['source']}</div>")
                            
                            if evidence.get('file_path'):
                                html.append(f"<div><strong>File:</strong> {evidence['file_path']}")
                                if evidence.get('line_number'):
                                    html.append(f", <strong>Line:</strong> {evidence['line_number']}")
                                html.append(f"</div>")
                            
                            if evidence.get('snippet'):
                                html.append(f"<div class='code-snippet'>{evidence['snippet']}</div>")
                            
                            if evidence.get('details'):
                                html.append(f"<div><strong>Details:</strong> {evidence['details']}</div>")
                            
                            html.append(f"</div>")
                        
                        html.append(f"</div>")
                    
                    html.append(f"</div>")
                
                html.append(f"</div>")
        
        # Close HTML document
        html.append("""
</body>
</html>
""")
        
        return "".join(html)
    
    def generate_csv(
        self,
        confidence_threshold: float = 0.0
    ) -> str:
        """
        Generate a CSV report of detected technologies.
        
        Args:
            confidence_threshold: Minimum confidence threshold for inclusion
            
        Returns:
            CSV string representation of the report
        """
        # Get technologies above threshold
        technologies = [
            tech for tech in self.tech_aggregation.get_all_technologies()
            if tech.confidence >= confidence_threshold
        ]
        
        # Sort by confidence
        technologies.sort(key=lambda t: t.confidence, reverse=True)
        
        # Create CSV content
        csv_lines = ["Name,Category,Version,Confidence,Files,References,Criticality"]
        
        for tech in technologies:
            name = tech.name.replace(",", " ")
            category = tech.category.name
            version = tech.version or "N/A"
            confidence = f"{tech.confidence:.1f}"
            
            # Usage stats
            files = str(tech.usage.file_count) if tech.usage else "N/A"
            references = str(tech.usage.frequency) if tech.usage else "N/A"
            criticality = f"{tech.usage.criticality:.1f}" if tech.usage else "N/A"
            
            csv_lines.append(f"{name},{category},{version},{confidence},{files},{references},{criticality}")
        
        return "\n".join(csv_lines)
    
    def save_report(
        self,
        output_path: str,
        format: str = "json",
        confidence_threshold: float = 0.0,
        include_evidence: bool = True,
        detail_level: str = "medium"
    ) -> bool:
        """
        Save a report to disk in the specified format.
        
        Args:
            output_path: Path to save the report
            format: Output format (json, markdown, html, csv)
            confidence_threshold: Minimum confidence threshold for inclusion
            include_evidence: Whether to include evidence in the output
            detail_level: Detail level ("low", "medium", "high")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate content based on format
            content = None
            
            if format.lower() == "json":
                content = self.generate_json(confidence_threshold, include_evidence, detail_level)
            elif format.lower() in ["markdown", "md"]:
                content = self.generate_markdown(confidence_threshold, include_evidence, detail_level)
            elif format.lower() == "html":
                content = self.generate_html(confidence_threshold, include_evidence, detail_level)
            elif format.lower() == "csv":
                content = self.generate_csv(confidence_threshold)
            else:
                logger.error(f"Unsupported output format: {format}")
                return False
            
            # Write content to file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"Saved {format} report to {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return False