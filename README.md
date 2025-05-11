# RepoAnalyzer

**RepoAnalyzer** is a Python library that analyzes code repositories to identify their complete technology stack. It provides detailed information about programming languages, frameworks, databases, build systems, frontend technologies, DevOps tools, architecture patterns, and testing frameworks used in a project.

## Features

- **Programming Language Detection**: Identifies languages used in the repository with confidence scores
- **Framework Detection**: Recognizes web frameworks, backend frameworks, and libraries
- **Database Technology Detection**: Identifies SQL and NoSQL database technologies
- **Build System & Package Manager Identification**: Detects build tools and dependency management systems
- **Frontend Technology Recognition**: Identifies frontend frameworks, CSS frameworks, state management libraries, etc.
- **DevOps Tool Analysis**: Detects containerization, CI/CD, infrastructure as code, monitoring tools
- **Architecture Pattern Recognition**: Identifies architectural patterns like MVC, MVVM, microservices, etc.
- **Testing Framework Detection**: Recognizes testing libraries, frameworks, and test patterns

## Installation

You can install the package using pip:

```bash
pip install repo-analyzer
```

Or install directly from the source code:

```bash
git clone https://github.com/yourusername/repo-analyzer.git
cd repo-analyzer
pip install -e .
```

## Usage

### Command Line

The simplest way to use RepoAnalyzer is through the command line:

```bash
repo-analyzer /path/to/your/repository
```

This will analyze the repository and print a summary of the detected technology stack to the console. You can also save the results to a JSON file:

```bash
repo-analyzer /path/to/your/repository --output results.json
```

### Python API

You can also use RepoAnalyzer in your Python code:

```python
from repo_analyzer import RepoAnalyzer

# Create an analyzer instance
analyzer = RepoAnalyzer('/path/to/your/repository', verbose=True)

# Run the analysis
tech_stack = analyzer.analyze()

# Print a summary
analyzer.print_summary()

# Save results to a file
analyzer.save_results('results.json')

# Access specific components
languages = tech_stack.get('languages', {})
frameworks = tech_stack.get('frameworks', {})
databases = tech_stack.get('databases', {})
primary_tech = tech_stack.get('primary_technologies', {})

# Get the primary language
primary_language = primary_tech.get('languages')
print(f"Primary language: {primary_language}")
```

## Example Output

Here's an example of the summary output:

```
===== REPOSITORY ANALYSIS SUMMARY =====

Repository: /path/to/example-repo
Files analyzed: 342
Analysis time: 1.56 seconds
Analyzed at: 2025-05-09 15:30:45.120000

Primary Technologies:
  - Languages: JavaScript
  - Frameworks: React
  - Databases: PostgreSQL
  - Build Systems: Webpack
  - Package Managers: npm
  - Frontend: Tailwind CSS
  - Devops: Docker
  - Architecture: Feature-based architecture
  - Testing: Jest

Languages:
  - JavaScript (100.0%)
  - TypeScript (85.3%)
  - CSS (32.7%)
  - HTML (15.2%)

Frameworks:
  - React (100.0%)
  - Express (58.7%)
  - Next.js (45.2%)

Databases:
  - PostgreSQL (100.0%)
  - Redis (45.8%)

Build Systems:
  - Webpack (100.0%)
  - Babel (76.5%)

Package Managers:
  - npm (100.0%)
  - yarn (35.2%)

Frontend:
  - Tailwind CSS (100.0%)
  - Redux (72.3%)
  - React Query (45.8%)

Devops:
  - Docker (100.0%)
  - GitHub Actions (85.6%)
  - Kubernetes (32.1%)

Architecture:
  - Feature-based architecture (100.0%)
  - REST API (78.5%)

Testing:
  - Jest (100.0%)
  - React Testing Library (85.2%)
  - Cypress (42.3%)

=======================================
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.