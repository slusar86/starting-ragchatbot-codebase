"""
Shared pytest fixtures for the RAG system tests.
Provides mocking and test data setup for cleaner test execution.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any


# ============================================================================
# Mock Data Fixtures
# ============================================================================

@pytest.fixture
def sample_query():
    """Sample user query for testing"""
    return "What topics are covered in Course 1?"


@pytest.fixture
def sample_session_id():
    """Sample session ID for testing"""
    return "test-session-123"


@pytest.fixture
def sample_course_data():
    """Sample course data for testing"""
    return {
        "course_titles": ["Course 1: Introduction", "Course 2: Advanced Topics"],
        "total_courses": 2
    }


@pytest.fixture
def sample_query_response():
    """Sample query response data"""
    return {
        "answer": "Course 1 covers introduction to the topic and basic concepts.",
        "sources": [
            {
                "course": "Course 1",
                "instructor": "John Doe",
                "similarity": 0.85
            }
        ]
    }


@pytest.fixture
def sample_documents():
    """Sample document chunks for testing"""
    return [
        {
            "content": "Course 1 introduces basic concepts and fundamentals.",
            "metadata": {
                "course": "Course 1",
                "instructor": "John Doe",
                "chunk_id": 1
            }
        },
        {
            "content": "Course 2 covers advanced topics and applications.",
            "metadata": {
                "course": "Course 2",
                "instructor": "Jane Smith",
                "chunk_id": 2
            }
        }
    ]


# ============================================================================
# Mock Component Fixtures
# ============================================================================

@pytest.fixture
def mock_vector_store():
    """Mock VectorStore for testing"""
    mock = Mock()
    mock.add_documents.return_value = None
    mock.search.return_value = [
        ("Course 1 content here", {"course": "Course 1", "instructor": "John Doe"}, 0.85)
    ]
    mock.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Course 1", "Course 2"]
    }
    return mock


@pytest.fixture
def mock_ai_generator():
    """Mock AIGenerator for testing"""
    mock = Mock()
    mock.generate_answer.return_value = "This is a generated answer based on the context."
    return mock


@pytest.fixture
def mock_session_manager():
    """Mock SessionManager for testing"""
    mock = Mock()
    mock.create_session.return_value = "test-session-123"
    mock.add_to_history.return_value = None
    mock.get_history.return_value = []
    mock.clear_session.return_value = None
    return mock


@pytest.fixture
def mock_search_tools():
    """Mock SearchTools for testing"""
    mock = Mock()
    mock.search.return_value = [
        {
            "content": "Course 1 content",
            "metadata": {"course": "Course 1", "instructor": "John Doe"},
            "similarity": 0.85
        }
    ]
    return mock


@pytest.fixture
def mock_rag_system(mock_vector_store, mock_ai_generator, mock_session_manager):
    """Mock complete RAG system for testing"""
    mock = Mock()
    mock.vector_store = mock_vector_store
    mock.ai_generator = mock_ai_generator
    mock.session_manager = mock_session_manager
    
    # Mock query method - return sources as strings (not dicts with similarity)
    mock.query.return_value = (
        "This is a generated answer.",
        ["Course 1: Content from John Doe's course"]
    )
    
    # Mock course analytics
    mock.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Course 1", "Course 2"]
    }
    
    return mock


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    config = Mock()
    config.embedding_model = "test-model"
    config.chroma_path = "./test_chroma"
    config.anthropic_api_key = "test-api-key"
    return config


@pytest.fixture
def test_env_vars(monkeypatch):
    """Set test environment variables"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
    monkeypatch.setenv("EMBEDDING_MODEL", "test-model")
    monkeypatch.setenv("CHROMA_PATH", "./test_chroma")


# ============================================================================
# API Testing Fixtures
# ============================================================================

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic API client"""
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="This is a generated response.")]
    mock.messages.create.return_value = mock_response
    return mock


@pytest.fixture
def patch_anthropic(mock_anthropic_client):
    """Patch Anthropic client for testing"""
    with patch('anthropic.Anthropic', return_value=mock_anthropic_client):
        yield mock_anthropic_client


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client"""
    mock = MagicMock()
    mock_collection = MagicMock()
    mock_collection.count.return_value = 10
    mock_collection.query.return_value = {
        "documents": [["Sample document content"]],
        "metadatas": [[{"course": "Course 1", "instructor": "John Doe"}]],
        "distances": [[0.15]]
    }
    mock.get_or_create_collection.return_value = mock_collection
    return mock


@pytest.fixture
def patch_chroma(mock_chroma_client):
    """Patch ChromaDB for testing"""
    with patch('chromadb.Client', return_value=mock_chroma_client):
        yield mock_chroma_client


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def cleanup_test_files():
    """Cleanup test files after tests"""
    yield
    # Add cleanup logic here if needed
    pass


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks after each test"""
    yield
    # Mocks are automatically reset by pytest-mock
