# Course Materials RAG System

A Retrieval-Augmented Generation (RAG) system designed to answer questions about course materials using semantic search and AI-powered responses.

## Overview

This application is a full-stack web application that enables users to query course materials and receive intelligent, context-aware responses. It uses ChromaDB for vector storage, Anthropic's Claude for AI generation, and provides a web interface for interaction.


## Prerequisites

- Python 3.13 or higher
- uv (Python package manager)
- An Anthropic API key (for Claude AI)
- **For Windows**: Use Git Bash to run the application commands - [Download Git for Windows](https://git-scm.com/downloads/win)

## Installation

1. **Install uv** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install Python dependencies**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```bash
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

## Running the Application

### Quick Start

Use the provided shell script:
```bash
chmod +x run.sh
./run.sh
```

### Manual Start

```bash
cd backend
uv run uvicorn app:app --reload --port 8000
```

The application will be available at:
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## Testing

The project includes comprehensive test coverage for both backend and frontend.

### Run All Tests
```powershell
# Backend tests (pytest)
python -m pytest backend/tests/ -v

# Frontend E2E tests (Playwright)
python frontend/tests/run_all_tests.py

# Individual frontend test suites
python frontend/tests/test_theme_toggle.py
python frontend/tests/test_chat_functionality.py
python frontend/tests/test_ui_components.py
```

### Pre-Push Hook
All tests run automatically before git push to ensure code quality:
- 86 backend tests
- 25+ frontend E2E tests
- Audio feedback on success/failure

See [TESTING.md](TESTING.md) for detailed testing documentation.

## Features

- **Semantic Search**: Vector-based search using ChromaDB
- **AI Responses**: Powered by Claude 3.5 Sonnet
- **Course Analytics**: Track and display course statistics
- **Session Management**: Maintain conversation history
- **Theme Support**: Light and dark mode with persistence
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Accessibility**: ARIA labels, keyboard navigation
- **Comprehensive Testing**: Backend and frontend E2E tests
