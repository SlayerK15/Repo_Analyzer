# Technology Extraction System

A comprehensive system for analyzing codebases and detecting technologies, frameworks, libraries, and architectural patterns used in software projects.

## Overview

The Technology Extraction System analyzes source code repositories to identify:

- Programming languages
- Frameworks and libraries
- Database technologies
- API patterns
- Architectural patterns
- Build tools and dependencies

It uses a combination of static analysis techniques and AI-powered detection to provide accurate and comprehensive results with confidence scores.

## Features

- **Intelligent File Collection**: Efficiently scans and samples large repositories
- **Language Detection**: Identifies programming languages with confidence scores
- **Dependency Analysis**: Parses package manifest files and analyzes import statements
- **Framework Pattern Recognition**: Detects framework-specific patterns and signatures
- **Architectural Pattern Recognition**: Identifies design patterns and system architectures
- **Evidence-Based Confidence Scoring**: Calculates confidence scores based on multiple evidence types
- **False Positive Mitigation**: Applies validation rules to reduce false positives
- **Multiple Output Formats**: Generates reports in JSON, Markdown, HTML, and CSV
- **Interactive Visualizations**: Creates charts and graphs of technology relationships
- **Parallel Processing**: Efficiently processes files in parallel
- **Caching**: Multi-level caching system for improved performance
- **Cost Optimization**: Manages AI API usage for optimal cost-performance balance
- **REST API**: Full-featured API for integration with other systems

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/tech-extraction-system.git
cd tech-extraction-system

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install dependencies
pip install poetry
poetry install
```

## Usage

### Command Line Interface

```bash
# Analyze a repository
tech-extract /path/to/repo --output-dir ./results --format html

# Options
tech-extract /path/to/repo \
  --output-dir ./results \
  --format html \
  --confidence-threshold 60 \
  --detail-level high \
  --visualizations \
  --cost-mode balanced
```

### Python API

```python
from tech_extraction.cli import analyze_repository

# Analyze a repository
technologies = analyze_repository(
    repo_path="/path/to/repo",
    output_dir="./results",
    confidence_threshold=60.0,
    include_evidence=True,
    detail_level="medium",
    output_format="json",
    visualizations=True,
    cost_mode="balanced"
)

# Process results
for tech in technologies:
    print(f"{tech.name}: {tech.confidence}% confidence")
```

### REST API

```bash
# Start the API server
uvicorn tech_extraction.api.main:app --host 0.0.0.0 --port 8000

# Or use Docker
docker-compose up api
```

Then access the API at `http://localhost:8000/docs` for interactive Swagger documentation.

## Configuration

Create a `.env` file in the project root with the following variables:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tech_extraction

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Providers
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Logging
LOG_LEVEL=INFO

# API
ROOT_PATH=http://localhost:8000
```

## Architecture

The system is organized into several major components:

1. **Core System Components**: File collection and language detection
2. **Dependency Analysis Pipeline**: Package manifest parsing and import analysis
3. **Framework Pattern Recognition**: Detection of framework signatures and patterns
4. **AI Integration Layer**: Dynamic prompt generation and AI integration
5. **Evidence Processing System**: Evidence collection and confidence scoring
6. **Results Processing Pipeline**: Technology aggregation and output generation
7. **Performance Optimization**: Caching, parallel processing, and cost management
8. **API and User Interfaces**: REST API, CLI, and visualizations

## Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# Or just the API
docker-compose up api

# Or just the worker
docker-compose up worker
```

## Development

```bash
# Install development dependencies
poetry install --with dev

# Run tests
pytest

# Run linters
black src tests
isort src tests
mypy src

# Run with hot reloading
uvicorn tech_extraction.api.main:app --reload
```

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.