"""Document loader for various file formats."""

import json
import logging
import mimetypes
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import re

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Handles loading and parsing of various document formats."""
    
    def __init__(self):
        """Initialize document loader."""
        self.supported_extensions = {
            '.md': 'markdown',
            '.markdown': 'markdown',
            '.txt': 'text',
            '.html': 'html',
            '.htm': 'html'
        }
        logger.info("DocumentLoader initialized")
    
    def load_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load a single file and return its content and metadata.
        
        Args:
            file_path: Path to the file to load
            
        Returns:
            Dictionary with content, metadata, and file info
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        # Check if file format is supported
        file_extension = file_path.suffix.lower()
        if file_extension not in self.supported_extensions:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                logger.warning(f"File is empty: {file_path}")
            
            # Extract metadata
            metadata = self._extract_metadata(file_path, content)
            
            logger.debug(f"Loaded file: {file_path} ({len(content)} chars)")
            
            return {
                "content": content,
                "metadata": metadata,
                "file_info": {
                    "path": str(file_path.absolute()),
                    "name": file_path.name,
                    "extension": file_extension,
                    "size": len(content)
                }
            }
            
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode file {file_path}: {e}")
            raise ValueError(f"Cannot decode file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to load file {file_path}: {e}")
            raise
    
    def load_directory(
        self, 
        directory_path: Union[str, Path],
        recursive: bool = True,
        file_patterns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Load all supported files from a directory.
        
        Args:
            directory_path: Path to directory
            recursive: Whether to search recursively
            file_patterns: Optional glob patterns to filter files
            
        Returns:
            List of loaded documents
            
        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        # Find all files
        files = self.find_files(directory_path, recursive, file_patterns)
        
        # Load each file
        documents = []
        for file_path in files:
            try:
                doc = self.load_file(file_path)
                documents.append(doc)
            except Exception as e:
                logger.warning(f"Failed to load file {file_path}: {e}")
                continue
        
        logger.info(f"Loaded {len(documents)} files from {directory_path}")
        return documents
    
    def find_files(
        self,
        directory_path: Union[str, Path],
        recursive: bool = True,
        file_patterns: Optional[List[str]] = None
    ) -> List[Path]:
        """Find all supported files in directory.
        
        Args:
            directory_path: Path to directory
            recursive: Whether to search recursively
            file_patterns: Optional glob patterns to filter files
            
        Returns:
            List of file paths
        """
        directory_path = Path(directory_path)
        files = []
        
        if recursive:
            # Use glob patterns if provided
            if file_patterns:
                for pattern in file_patterns:
                    files.extend(directory_path.rglob(pattern))
            else:
                # Find all files with supported extensions
                for ext in self.supported_extensions:
                    files.extend(directory_path.rglob(f"*{ext}"))
        else:
            # Non-recursive search
            if file_patterns:
                for pattern in file_patterns:
                    files.extend(directory_path.glob(pattern))
            else:
                for ext in self.supported_extensions:
                    files.extend(directory_path.glob(f"*{ext}"))
        
        # Filter out non-files and sort
        files = [f for f in files if f.is_file()]
        files.sort()
        
        logger.debug(f"Found {len(files)} files in {directory_path}")
        return files
    
    def _extract_metadata(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Extract metadata from file path and content.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            "file_path": str(file_path.absolute()),
            "file_name": file_path.name,
            "file_extension": file_path.suffix.lower(),
            "file_type": self.supported_extensions.get(file_path.suffix.lower(), "unknown")
        }
        
        # Extract file stats
        try:
            stat = file_path.stat()
            metadata.update({
                "file_size": stat.st_size,
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime
            })
        except Exception as e:
            logger.warning(f"Failed to get file stats for {file_path}: {e}")
        
        # Extract content-based metadata
        metadata.update(self._extract_content_metadata(content))
        
        return metadata
    
    def _extract_content_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from document content.
        
        Args:
            content: Document content
            
        Returns:
            Dictionary with content-based metadata
        """
        metadata = {
            "char_count": len(content),
            "word_count": len(content.split()),
            "line_count": len(content.splitlines())
        }
        
        # Extract title from markdown
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
        
        # Extract language hints (basic detection)
        if self._contains_japanese(content):
            metadata["language_hint"] = "ja"
        elif self._contains_chinese(content):
            metadata["language_hint"] = "zh"
        else:
            metadata["language_hint"] = "en"
        
        # Extract headings for markdown
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        if headings:
            # Convert headings to JSON string for ChromaDB compatibility
            headings_list = [
                {"level": len(level), "text": text.strip()}
                for level, text in headings
            ]
            metadata["headings"] = json.dumps(headings_list)
        
        return metadata
    
    def _contains_japanese(self, text: str) -> bool:
        """Check if text contains Japanese characters.
        
        Args:
            text: Text to check
            
        Returns:
            True if Japanese characters are found
        """
        # Check for Hiragana, Katakana, and Kanji
        japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
        return bool(japanese_pattern.search(text))
    
    def _contains_chinese(self, text: str) -> bool:
        """Check if text contains Chinese characters.
        
        Args:
            text: Text to check
            
        Returns:
            True if Chinese characters are found
        """
        # Check for CJK Unified Ideographs (includes Chinese)
        chinese_pattern = re.compile(r'[\u4E00-\u9FFF]')
        return bool(chinese_pattern.search(text))
    
    def chunk_document(
        self,
        content: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n\n"
    ) -> List[Dict[str, Any]]:
        """Split document content into chunks.
        
        Args:
            content: Document content to chunk
            chunk_size: Maximum size of each chunk
            chunk_overlap: Number of characters to overlap between chunks
            separator: Separator to split on
            
        Returns:
            List of chunks with metadata
        """
        if not content or not content.strip():
            return []
        
        # Simple chunking strategy
        chunks = []
        
        # First try to split by separator
        sections = content.split(separator)
        
        current_chunk = ""
        chunk_index = 0
        
        for section in sections:
            # If adding this section would exceed chunk_size, finalize current chunk
            if current_chunk and len(current_chunk) + len(section) > chunk_size:
                if current_chunk.strip():
                    chunk_metadata = {
                        "chunk_index": chunk_index,
                        "chunk_size": len(current_chunk),
                        "start_char": max(0, len("".join(chunks)) * chunk_size - chunk_overlap * chunk_index),
                        "end_char": len(current_chunk)
                    }
                    
                    chunks.append({
                        "text": current_chunk.strip(),
                        "metadata": chunk_metadata
                    })
                    
                    chunk_index += 1
                
                # Start new chunk with overlap if specified
                if chunk_overlap > 0 and current_chunk:
                    current_chunk = current_chunk[-chunk_overlap:] + section
                else:
                    current_chunk = section
            else:
                current_chunk += separator + section if current_chunk else section
        
        # Add final chunk if it has content
        if current_chunk.strip():
            chunk_metadata = {
                "chunk_index": chunk_index,
                "chunk_size": len(current_chunk),
                "start_char": max(0, len("".join([c["text"] for c in chunks])) - chunk_overlap * chunk_index),
                "end_char": len(current_chunk)
            }
            
            chunks.append({
                "text": current_chunk.strip(),
                "metadata": chunk_metadata
            })
        
        logger.debug(f"Split content into {len(chunks)} chunks")
        return chunks
    
    def get_supported_formats(self) -> Dict[str, str]:
        """Get supported file formats.
        
        Returns:
            Dictionary mapping extensions to format names
        """
        return self.supported_extensions.copy()
    
    def is_supported_file(self, file_path: Union[str, Path]) -> bool:
        """Check if file format is supported.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file format is supported
        """
        file_path = Path(file_path)
        return file_path.suffix.lower() in self.supported_extensions