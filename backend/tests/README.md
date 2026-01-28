# Backend Tests

This directory contains comprehensive tests for the RAG chatbot backend components.

## Test Files

- **test_search_tools.py** - Tests for CourseSearchTool and ToolManager
- **test_ai_generator.py** - Tests for AI generator and tool calling functionality  
- **test_rag_system.py** - Integration tests for the complete RAG system

## Quick Start

### Install Dependencies
```bash
pip install pytest pytest-mock
```

### Run All Tests
```bash
# From the backend directory
cd backend
python -m pytest tests/ -v
```

### Run Specific Test File
```bash
python -m pytest tests/test_ai_generator.py -v
python -m pytest tests/test_search_tools.py -v
python -m pytest tests/test_rag_system.py -v
```

### Run with Coverage
```bash
pip install pytest-cov
python -m pytest tests/ --cov=. --cov-report=html
```

## Test Coverage

- **42 total tests** across 3 test files
- Tests use mocks for external dependencies (no API keys required)
- Focus on core functionality: search, AI generation, and RAG orchestration

## What Was Fixed

See [TEST_REPORT.md](TEST_REPORT.md) for detailed information about the bugs that were identified and fixed.

### Summary of Fixes
1. **ai_generator.py line 141** - Removed syntax error `}dane do fk`
2. **ai_generator.py line 144** - Fixed parameter unpacking from `*final` to `**final_params`
3. **search_tools.py line 253** - Fixed exception variable from `a` to `e`

These syntax errors were causing the "query failed" issue for all content-related questions.

## Notes

- Tests use unittest.mock to simulate external services
- No database or API connection required for unit tests
- All tests should pass after applying the fixes
