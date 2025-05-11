# Create a file named analyze_repo.py:
from repo_analyzer import RepoAnalyzer

# Create an analyzer instance
analyzer = RepoAnalyzer('/home/kanav/Desktop/infrawave-version3')

# Run the analysis
tech_stack = analyzer.analyze()

# Print a summary
analyzer.print_summary()

# Save results to a file
analyzer.save_results('results.json')