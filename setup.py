"""
Setup configuration for the RepoAnalyzer library.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="repo-analyzer",
    version="0.2.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python library that analyzes code repositories to identify tech stacks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/repo-analyzer",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        'ai': [
            'openai>=1.0.0',
            'anthropic>=0.5.0',
            'tiktoken>=0.4.0',
            'huggingface_hub>=0.16.0',
        ],
        'local_ai': [
            'llama-cpp-python>=0.2.0',
            'sentence-transformers>=2.2.2',
        ]
    },
    entry_points={
        "console_scripts": [
            "repo-analyzer=repo_analyzer.cli:main",
            "repo-analyzer-ai=repo_analyzer.cli_enhanced:main",
        ],
    },
)