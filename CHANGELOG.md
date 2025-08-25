# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-08-25

### 🎉 Initial Release

#### Added
- **Core Features**
  - MCP (Model Context Protocol) server implementation for Claude Code integration
  - Japanese morphological analysis engine (MeCab alternative)
  - Hybrid search system (Vector + Keyword + Grep)
  - 3-stage fallback search mechanism
  - Token optimization for MCP response limits (25,000 tokens)

- **Japanese Language Support**
  - Custom morphological analyzer without external dependencies
  - Specialized dictionary with 50+ Ultra Pay related terms
  - Compound word recognition and extraction
  - Mixed Japanese-English document support

- **Search Improvements**
  - 4.2x improvement in search accuracy for Japanese queries
  - Multiple search types: vector, keyword, hybrid, fallback
  - Query preprocessing with synonym expansion
  - Result truncation to 80 characters for token efficiency

- **Documentation**
  - Comprehensive documentation structure in `/docs`
  - Architecture design documents
  - Implementation guides
  - Operations manual
  - MCP setup guide

- **Testing**
  - Integration tests for Phase 2 features
  - Japanese analyzer unit tests
  - Performance benchmarks

#### Technical Specifications
- **Languages**: Python 3.10+, Node.js 18+
- **Database**: ChromaDB for vector storage
- **Embedding Model**: intfloat/multilingual-e5-base
- **Performance**: 
  - Search response < 500ms
  - Memory usage < 100MB
  - Token usage: 5,000-8,000 per MCP response

#### Known Issues
- None at this release

---

## Development History

### Phase 2 (2025-08-24 to 2025-08-25)
- Implemented Japanese morphological analysis
- Added specialized dictionary generation
- Integrated compound word extraction

### Phase 1 (2025-08-23 to 2025-08-24)
- Implemented fallback search mechanism
- Added query preprocessing
- Achieved 4.2x search accuracy improvement

### MVP (2025-08-22 to 2025-08-23)
- Initial MCP server implementation
- Basic RAG search functionality
- ChromaDB integration