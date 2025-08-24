"""Setup configuration for RAG Second Brain system."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="rag-second-brain",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Second Brain for Development - Local RAG system with MCP server and CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rag-second-brain",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Documentation",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "chromadb>=0.4.22",
        "langchain>=0.1.0",
        "sentence-transformers>=2.2.2",
        "numpy>=1.24.0",
        "click>=8.1.7",
        "rich>=13.7.0",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "black>=23.12.0",
            "mypy>=1.7.0",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
        ],
        "mcp": [
            # MCP dependencies will be added here
        ],
    },
    entry_points={
        "console_scripts": [
            "rag=rag.cli.main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "rag": ["config/*.yaml", "config/*.json"],
    },
)