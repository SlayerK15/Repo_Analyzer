"""
Visualization Components for the Technology Extraction System.

This module provides functionality for creating visual representations
of the detected technologies including graphs, charts, and heatmaps.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from tech_extraction.models.technology import (
    Technology,
    TechnologyCategory,
    TechnologyStack,
    TechnologyGroup,
)
from tech_extraction.results.technology_aggregation import TechnologyAggregation

logger = logging.getLogger(__name__)


class VisualizationComponents:
    """
    Components for visualizing detected technologies.
    
    The VisualizationComponents performs the following operations:
    1. Create interactive visualizations of technology usage
    2. Generate dependency graphs and relationship maps
    3. Create technology distribution charts
    4. Visualize codebase technology coverage
    """
    
    def __init__(self, tech_aggregation: TechnologyAggregation):
        """
        Initialize the visualization components.
        
        Args:
            tech_aggregation: Technology aggregation instance
        """
        self.tech_aggregation = tech_aggregation
        
        # Color schemes for different visualizations
        self.category_colors = {
            "LANGUAGE": "#1f77b4",
            "FRAMEWORK": "#ff7f0e",
            "LIBRARY": "#2ca02c",
            "DATABASE": "#d62728",
            "ORM": "#9467bd",
            "BUILD_TOOL": "#8c564b",
            "TESTING": "#e377c2",
            "UI": "#7f7f7f",
            "STATE_MANAGEMENT": "#bcbd22",
            "INFRASTRUCTURE": "#17becf",
            "API": "#aec7e8",
            "PLUGIN": "#ffbb78",
            "TOOL": "#98df8a",
            "UNKNOWN": "#c5b0d5",
        }
    
    def create_technology_graph(
        self,
        min_confidence: float = 50.0,
        include_related: bool = True
    ) -> go.Figure:
        """
        Create an interactive graph visualization of technology relationships.
        
        Args:
            min_confidence: Minimum confidence threshold for inclusion
            include_related: Whether to include related technologies
            
        Returns:
            Plotly figure object
        """
        # Get technology stacks
        stacks = self.tech_aggregation.get_all_technology_stacks()
        
        # Prepare nodes and edges
        nodes = []
        edges = []
        node_colors = []
        node_sizes = []
        
        # Track added nodes to avoid duplicates
        added_nodes = set()
        
        # Add primary technologies as nodes
        for stack in stacks:
            primary = stack.primary_technology
            
            # Skip if below threshold
            if primary.confidence < min_confidence:
                continue
            
            # Add primary technology node
            if primary.name not in added_nodes:
                nodes.append(primary.name)
                added_nodes.add(primary.name)
                
                # Use category for color
                color = self.category_colors.get(primary.category.name, "#1f77b4")
                node_colors.append(color)
                
                # Use confidence for size
                size = 20 + (primary.confidence / 5)
                node_sizes.append(size)
            
            # Add related technologies as nodes and edges
            if include_related:
                for related in stack.related_technologies:
                    # Skip if below threshold
                    if related.confidence < min_confidence:
                        continue
                    
                    # Add related technology node
                    if related.name not in added_nodes:
                        nodes.append(related.name)
                        added_nodes.add(related.name)
                        
                        # Use category for color
                        color = self.category_colors.get(related.category.name, "#1f77b4")
                        node_colors.append(color)
                        
                        # Use confidence for size (smaller than primary)
                        size = 10 + (related.confidence / 10)
                        node_sizes.append(size)
                    
                    # Add edge from primary to related
                    edges.append((nodes.index(primary.name), nodes.index(related.name)))
        
        # Create graph layout
        pos = self._create_graph_layout(len(nodes))
        
        # Create figure
        fig = go.Figure()
        
        # Add edges
        for i, j in edges:
            fig.add_trace(
                go.Scatter(
                    x=[pos[i][0], pos[j][0]],
                    y=[pos[i][1], pos[j][1]],
                    mode="lines",
                    line=dict(width=1, color="#888"),
                    hoverinfo="none",
                    showlegend=False
                )
            )
        
        # Add nodes
        fig.add_trace(
            go.Scatter(
                x=[p[0] for p in pos],
                y=[p[1] for p in pos],
                mode="markers+text",
                marker=dict(
                    color=node_colors,
                    size=node_sizes,
                    line=dict(width=1, color="#333")
                ),
                text=nodes,
                textposition="bottom center",
                hovertemplate="%{text}<extra></extra>",
                showlegend=False
            )
        )
        
        # Set layout
        fig.update_layout(
            title="Technology Relationship Graph",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="white",
            margin=dict(t=50, l=0, r=0, b=0),
            height=800,
            width=1000
        )
        
        return fig
    
    def _create_graph_layout(self, num_nodes: int) -> List[Tuple[float, float]]:
        """
        Create a layout for the graph visualization.
        
        Args:
            num_nodes: Number of nodes in the graph
            
        Returns:
            List of (x, y) coordinates for each node
        """
        import math
        import random
        
        # Simple force-directed layout
        positions = []
        radius = 5
        
        if num_nodes <= 1:
            return [(0, 0)]
        
        # Place nodes in a circle with some randomness
        for i in range(num_nodes):
            angle = (2 * math.pi * i) / num_nodes
            x = radius * math.cos(angle) + random.uniform(-0.5, 0.5)
            y = radius * math.sin(angle) + random.uniform(-0.5, 0.5)
            positions.append((x, y))
        
        return positions
    
    def create_technology_distribution_chart(
        self,
        min_confidence: float = 50.0
    ) -> go.Figure:
        """
        Create a chart showing technology distribution by category.
        
        Args:
            min_confidence: Minimum confidence threshold for inclusion
            
        Returns:
            Plotly figure object
        """
        # Get technologies above threshold
        technologies = [
            tech for tech in self.tech_aggregation.get_all_technologies()
            if tech.confidence >= min_confidence
        ]
        
        # Group by category
        category_counts = {}
        for tech in technologies:
            category = tech.category.name
            if category in category_counts:
                category_counts[category] += 1
            else:
                category_counts[category] = 1
        
        # Sort categories by count
        sorted_categories = sorted(
            category_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Prepare data for chart
        categories = [c[0] for c in sorted_categories]
        counts = [c[1] for c in sorted_categories]
        colors = [self.category_colors.get(c, "#1f77b4") for c in categories]
        
        # Create figure
        fig = go.Figure(
            go.Bar(
                x=categories,
                y=counts,
                marker_color=colors,
                text=counts,
                textposition="auto"
            )
        )
        
        # Set layout
        fig.update_layout(
            title="Technology Distribution by Category",
            xaxis_title="Category",
            yaxis_title="Number of Technologies",
            plot_bgcolor="white",
            margin=dict(t=50, l=50, r=50, b=50),
            height=500,
            width=800
        )
        
        return fig
    
    def create_confidence_distribution_chart(self) -> go.Figure:
        """
        Create a chart showing the distribution of confidence scores.
        
        Returns:
            Plotly figure object
        """
        # Get all technologies
        technologies = self.tech_aggregation.get_all_technologies()
        
        # Extract confidence scores
        confidence_scores = [tech.confidence for tech in technologies]
        
        # Create histogram bins
        bins = list(range(0, 101, 10))  # 0-10, 10-20, ..., 90-100
        
        # Create histogram
        fig = go.Figure(
            go.Histogram(
                x=confidence_scores,
                xbins=dict(start=0, end=100, size=10),
                marker_color="#1f77b4",
                opacity=0.7,
                name="Confidence Distribution"
            )
        )
        
        # Add cumulative distribution
        fig.add_trace(
            go.Histogram(
                x=confidence_scores,
                xbins=dict(start=0, end=100, size=10),
                cumulative_enabled=True,
                marker_color="#ff7f0e",
                opacity=0.7,
                name="Cumulative"
            )
        )
        
        # Set layout
        fig.update_layout(
            title="Distribution of Confidence Scores",
            xaxis_title="Confidence Score",
            yaxis_title="Number of Technologies",
            barmode="overlay",
            plot_bgcolor="white",
            margin=dict(t=50, l=50, r=50, b=50),
            height=500,
            width=800,
            legend=dict(x=0.7, y=0.9)
        )
        
        return fig
    
    def create_top_technologies_chart(
        self, 
        top_n: int = 20,
        min_confidence: float = 50.0
    ) -> go.Figure:
        """
        Create a chart showing the top technologies by usage.
        
        Args:
            top_n: Number of top technologies to include
            min_confidence: Minimum confidence threshold for inclusion
            
        Returns:
            Plotly figure object
        """
        # Get technologies above threshold
        technologies = [
            tech for tech in self.tech_aggregation.get_all_technologies()
            if tech.confidence >= min_confidence
        ]
        
        # Sort by usage frequency
        technologies.sort(key=lambda t: t.usage.frequency if t.usage else 0, reverse=True)
        
        # Take top N
        top_techs = technologies[:top_n]
        
        # Prepare data for chart
        names = [tech.name for tech in top_techs]
        frequencies = [tech.usage.frequency if tech.usage else 0 for tech in top_techs]
        file_counts = [tech.usage.file_count if tech.usage else 0 for tech in top_techs]
        categories = [tech.category.name for tech in top_techs]
        colors = [self.category_colors.get(cat, "#1f77b4") for cat in categories]
        
        # Create figure with subplots
        fig = make_subplots(rows=1, cols=2, specs=[[{"type": "bar"}, {"type": "bar"}]],
                           subplot_titles=("References", "Files Used"))
        
        # Add frequency bar chart
        fig.add_trace(
            go.Bar(
                x=names,
                y=frequencies,
                marker_color=colors,
                text=frequencies,
                textposition="auto",
                name="References"
            ),
            row=1, col=1
        )
        
        # Add file count bar chart
        fig.add_trace(
            go.Bar(
                x=names,
                y=file_counts,
                marker_color=colors,
                text=file_counts,
                textposition="auto",
                name="Files"
            ),
            row=1, col=2
        )
        
        # Set layout
        fig.update_layout(
            title="Top Technologies by Usage",
            plot_bgcolor="white",
            margin=dict(t=80, l=50, r=50, b=150),
            height=600,
            width=1200,
            legend=dict(orientation="h", y=-0.2)
        )
        
        # Update x-axis to show labels vertically
        fig.update_xaxes(tickangle=90)
        
        return fig
    
    def create_heatmap(
        self,
        min_confidence: float = 50.0
    ) -> go.Figure:
        """
        Create a heatmap visualization of technology coverage.
        
        Args:
            min_confidence: Minimum confidence threshold for inclusion
            
        Returns:
            Plotly figure object
        """
        # Get technologies above threshold
        technologies = [
            tech for tech in self.tech_aggregation.get_all_technologies()
            if tech.confidence >= min_confidence
        ]
        
        # Group by category
        tech_by_category = {}
        for tech in technologies:
            category = tech.category.name
            if category not in tech_by_category:
                tech_by_category[category] = []
            tech_by_category[category].append(tech)
        
        # Prepare data for heatmap
        categories = list(tech_by_category.keys())
        
        # Create matrix of coverage values
        matrix = []
        tech_names = []
        
        for category in categories:
            category_techs = tech_by_category[category]
            
            # Sort by confidence
            category_techs.sort(key=lambda t: t.confidence, reverse=True)
            
            # Take top 10 for each category to prevent overcrowding
            for tech in category_techs[:10]:
                tech_names.append(tech.name)
                
                # Create row for this technology
                row = []
                for cat in categories:
                    # Higher value if it's the tech's category
                    if cat == category:
                        row.append(tech.confidence / 100)
                    else:
                        row.append(0)
                
                matrix.append(row)
        
        # Create heatmap
        fig = go.Figure(
            go.Heatmap(
                z=matrix,
                x=categories,
                y=tech_names,
                colorscale="Viridis",
                showscale=True,
                hoverongaps=False
            )
        )
        
        # Set layout
        fig.update_layout(
            title="Technology Coverage Heatmap",
            plot_bgcolor="white",
            margin=dict(t=50, l=150, r=50, b=50),
            height=800,
            width=1000
        )
        
        return fig
    
    def create_dashboard_html(
        self,
        output_path: str,
        min_confidence: float = 50.0
    ) -> bool:
        """
        Create an HTML dashboard with multiple visualizations.
        
        Args:
            output_path: Path to save the dashboard HTML
            min_confidence: Minimum confidence threshold for inclusion
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create visualizations
            graph_fig = self.create_technology_graph(min_confidence)
            dist_fig = self.create_technology_distribution_chart(min_confidence)
            conf_fig = self.create_confidence_distribution_chart()
            top_fig = self.create_top_technologies_chart(min_confidence=min_confidence)
            
            # Convert to HTML
            graph_html = graph_fig.to_html(full_html=False, include_plotlyjs=False)
            dist_html = dist_fig.to_html(full_html=False, include_plotlyjs=False)
            conf_html = conf_fig.to_html(full_html=False, include_plotlyjs=False)
            top_html = top_fig.to_html(full_html=False, include_plotlyjs=False)
            
            # Get all technologies above threshold
            technologies = [
                tech for tech in self.tech_aggregation.get_all_technologies()
                if tech.confidence >= min_confidence
            ]
            
            # Sort by confidence
            technologies.sort(key=lambda t: t.confidence, reverse=True)
            
            # Create technology table
            table_rows = []
            for tech in technologies:
                category = tech.category.name.title()
                version = tech.version or "N/A"
                confidence = f"{tech.confidence:.1f}%"
                
                file_count = tech.usage.file_count if tech.usage else "N/A"
                frequency = tech.usage.frequency if tech.usage else "N/A"
                
                row = f"""
                <tr>
                    <td>{tech.name}</td>
                    <td>{category}</td>
                    <td>{version}</td>
                    <td>{confidence}</td>
                    <td>{file_count}</td>
                    <td>{frequency}</td>
                </tr>
                """
                table_rows.append(row)
            
            table_html = "\n".join(table_rows)
            
            # Create dashboard HTML
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Technology Extraction Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
        }}
        .chart-container {{
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            padding: 20px;
        }}
        .row {{
            display: flex;
            flex-wrap: wrap;
            margin: 0 -10px;
        }}
        .col {{
            flex: 1;
            padding: 0 10px;
            min-width: 300px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Technology Extraction Dashboard</h1>
        <p>Analysis of detected technologies</p>
    </div>
    
    <div class="container">
        <div class="chart-container">
            <h2>Technology Relationship Graph</h2>
            {graph_html}
        </div>
        
        <div class="row">
            <div class="col">
                <div class="chart-container">
                    <h2>Technology Distribution</h2>
                    {dist_html}
                </div>
            </div>
            <div class="col">
                <div class="chart-container">
                    <h2>Confidence Distribution</h2>
                    {conf_html}
                </div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>Top Technologies</h2>
            {top_html}
        </div>
        
        <div class="chart-container">
            <h2>Technology Table</h2>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Category</th>
                        <th>Version</th>
                        <th>Confidence</th>
                        <th>Files</th>
                        <th>References</th>
                    </tr>
                </thead>
                <tbody>
                    {table_html}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>"""
            
            # Write to file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
            
            logger.info(f"Created dashboard HTML at {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating dashboard HTML: {e}")
            return False
    
    def export_figures(
        self,
        output_dir: str,
        min_confidence: float = 50.0,
        format: str = "png"
    ) -> Dict[str, str]:
        """
        Export figures to image files.
        
        Args:
            output_dir: Directory to save figures
            min_confidence: Minimum confidence threshold for inclusion
            format: Output format (png, svg, pdf, jpeg)
            
        Returns:
            Dictionary mapping figure names to file paths
        """
        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create visualizations
            graph_fig = self.create_technology_graph(min_confidence)
            dist_fig = self.create_technology_distribution_chart(min_confidence)
            conf_fig = self.create_confidence_distribution_chart()
            top_fig = self.create_top_technologies_chart(min_confidence=min_confidence)
            heatmap_fig = self.create_heatmap(min_confidence)
            
            # Export figures
            result = {}
            
            graph_path = str(output_path / f"technology_graph.{format}")
            graph_fig.write_image(graph_path)
            result["technology_graph"] = graph_path
            
            dist_path = str(output_path / f"technology_distribution.{format}")
            dist_fig.write_image(dist_path)
            result["technology_distribution"] = dist_path
            
            conf_path = str(output_path / f"confidence_distribution.{format}")
            conf_fig.write_image(conf_path)
            result["confidence_distribution"] = conf_path
            
            top_path = str(output_path / f"top_technologies.{format}")
            top_fig.write_image(top_path)
            result["top_technologies"] = top_path
            
            heatmap_path = str(output_path / f"technology_heatmap.{format}")
            heatmap_fig.write_image(heatmap_path)
            result["technology_heatmap"] = heatmap_path
            
            logger.info(f"Exported {len(result)} figures to {output_dir}")
            return result
        
        except Exception as e:
            logger.error(f"Error exporting figures: {e}")
            return {}