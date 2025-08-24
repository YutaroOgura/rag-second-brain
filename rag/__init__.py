"""RAG Second Brain - A Second Brain for Development."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Package metadata
__title__ = "rag-second-brain"
__description__ = "A Second Brain for Development - Local RAG system with MCP server and CLI"
__url__ = "https://github.com/yourusername/rag-second-brain"
__license__ = "MIT"

# Version components
VERSION_MAJOR = 0
VERSION_MINOR = 1
VERSION_PATCH = 0

# Import main components for easier access
from .core.database import DatabaseManager
from .core.vectorizer import Vectorizer
from .core.search import SearchEngine

__all__ = [
    "DatabaseManager",
    "Vectorizer", 
    "SearchEngine",
    "__version__",
]