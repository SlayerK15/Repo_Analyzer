from analyzer_enhanced import RepoAnalyzer

# Configure AI settings
ai_config = {
    "enabled": True,
    "provider": "openai",  # or "anthropic", "local", "huggingface"
    "model": "gpt-4",      # or "claude-3-opus", etc.
    "temperature": 0.1,
    "cache_enabled": True,
}

# Create an enhanced analyzer instance
analyzer = RepoAnalyzer(
    repo_path='D:\Projects\ecommerce_project',
    ai_config=ai_config
)

# Run the analysis
tech_stack = analyzer.analyze()

# Print the AI-enhanced summary
analyzer.print_ai_summary()

# Save results
analyzer.save_results('ai_analysis_results.json')