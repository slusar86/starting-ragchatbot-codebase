"""
Integration tests for RAG system to validate end-to-end content query handling
"""

import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models import Course, CourseChunk, Lesson
from rag_system import RAGSystem
from vector_store import SearchResults


class MockConfig:
    """Mock configuration for testing"""

    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    CHROMA_PATH = "./test_chroma_db"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    MAX_RESULTS = 0
    ANTHROPIC_API_KEY = "test_api_key"
    ANTHROPIC_MODEL = "claude-3-sonnet-20240229"
    MAX_HISTORY = 10


class TestRAGSystemIntegration:
    """Integration tests for the RAG system query flow"""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        return MockConfig()

    @pytest.fixture
    def rag_system(self, mock_config):
        """Create RAG system with mocked dependencies"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore"),
            patch("rag_system.AIGenerator"),
            patch("rag_system.SessionManager"),
            patch("rag_system.CourseSearchTool"),
            patch("rag_system.CourseOutlineTool"),
        ):

            system = RAGSystem(mock_config)
            return system

    def test_rag_system_initialization(self, rag_system):
        """Test that RAG system initializes all components"""
        assert rag_system.document_processor is not None
        assert rag_system.vector_store is not None
        assert rag_system.ai_generator is not None
        assert rag_system.session_manager is not None
        assert rag_system.tool_manager is not None
        assert rag_system.search_tool is not None

    def test_query_without_session(self, rag_system):
        """Test querying without a session ID"""
        # Mock AI generator response
        rag_system.ai_generator.generate_response = Mock(
            return_value="Python is a programming language"
        )
        rag_system.tool_manager.get_last_sources = Mock(return_value=[])
        rag_system.tool_manager.reset_sources = Mock()

        # Execute query
        response, sources = rag_system.query("What is Python?")

        # Verify response
        assert response == "Python is a programming language"
        assert isinstance(sources, list)

        # Verify AI generator was called
        rag_system.ai_generator.generate_response.assert_called_once()
        call_kwargs = rag_system.ai_generator.generate_response.call_args[1]
        assert "query" in call_kwargs
        assert "tools" in call_kwargs
        assert "tool_manager" in call_kwargs

    def test_query_with_session(self, rag_system):
        """Test querying with a session ID maintains context"""
        # Mock session manager
        rag_system.session_manager.get_conversation_history = Mock(
            return_value="Previous: User asked about variables"
        )
        rag_system.session_manager.add_exchange = Mock()

        # Mock AI generator
        rag_system.ai_generator.generate_response = Mock(return_value="Variables store data values")
        rag_system.tool_manager.get_last_sources = Mock(return_value=[])
        rag_system.tool_manager.reset_sources = Mock()

        # Execute query with session
        response, sources = rag_system.query(
            "Tell me more about them", session_id="test_session_123"
        )

        # Verify history was retrieved
        rag_system.session_manager.get_conversation_history.assert_called_with("test_session_123")

        # Verify conversation was updated
        rag_system.session_manager.add_exchange.assert_called_once()

        # Verify AI generator received history
        call_kwargs = rag_system.ai_generator.generate_response.call_args[1]
        assert call_kwargs["conversation_history"] == "Previous: User asked about variables"

    def test_query_with_tool_use(self, rag_system):
        """Test query flow when AI uses search tool"""
        # Mock AI generator to simulate tool use
        rag_system.ai_generator.generate_response = Mock(
            return_value="Based on the course, Python is versatile"
        )

        # Mock tool manager with sources
        mock_sources = [
            {"text": "Introduction to Python - Lesson 1", "link": "https://example.com/lesson1"}
        ]
        rag_system.tool_manager.get_last_sources = Mock(return_value=mock_sources)
        rag_system.tool_manager.reset_sources = Mock()

        # Execute query
        response, sources = rag_system.query("What is Python?")

        # Verify sources were retrieved and reset
        assert sources == mock_sources
        rag_system.tool_manager.get_last_sources.assert_called_once()
        rag_system.tool_manager.reset_sources.assert_called_once()

    def test_query_passes_tools_to_ai(self, rag_system):
        """Test that query passes tool definitions to AI generator"""
        # Mock tool manager
        mock_tool_defs = [
            {"name": "search_course_content", "description": "Search courses"},
            {"name": "get_course_outline", "description": "Get course outline"},
        ]
        rag_system.tool_manager.get_tool_definitions = Mock(return_value=mock_tool_defs)

        # Mock AI generator
        rag_system.ai_generator.generate_response = Mock(return_value="Response")
        rag_system.tool_manager.get_last_sources = Mock(return_value=[])
        rag_system.tool_manager.reset_sources = Mock()

        # Execute query
        rag_system.query("Test query")

        # Verify tools were passed
        call_kwargs = rag_system.ai_generator.generate_response.call_args[1]
        assert call_kwargs["tools"] == mock_tool_defs
        assert call_kwargs["tool_manager"] == rag_system.tool_manager

    def test_query_formats_prompt(self, rag_system):
        """Test that query formats the prompt correctly"""
        rag_system.ai_generator.generate_response = Mock(return_value="Answer")
        rag_system.tool_manager.get_last_sources = Mock(return_value=[])
        rag_system.tool_manager.reset_sources = Mock()

        user_query = "Explain loops in Python"
        rag_system.query(user_query)

        # Check that prompt includes the user query
        call_kwargs = rag_system.ai_generator.generate_response.call_args[1]
        prompt = call_kwargs["query"]
        assert user_query in prompt
        assert "course materials" in prompt.lower()

    def test_query_error_handling(self, rag_system):
        """Test that query handles errors gracefully"""
        # Mock AI generator to raise an exception
        rag_system.ai_generator.generate_response = Mock(
            side_effect=Exception("API connection failed")
        )

        # Query should raise the exception (app.py handles it)
        with pytest.raises(Exception) as exc_info:
            rag_system.query("Test query")

        assert "API connection failed" in str(exc_info.value)


class TestRAGSystemContentRetrieval:
    """Tests specifically for content-related query handling"""

    @pytest.fixture
    def rag_system_with_mocks(self, mock_config):
        """Create RAG system with specific mocks for content testing"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore") as mock_vs,
            patch("rag_system.AIGenerator") as mock_ai,
            patch("rag_system.SessionManager"),
            patch("rag_system.CourseSearchTool") as mock_search,
            patch("rag_system.CourseOutlineTool"),
        ):

            system = RAGSystem(mock_config)

            # Set up specific mocks
            system.vector_store = mock_vs.return_value
            system.ai_generator = mock_ai.return_value
            system.search_tool = mock_search.return_value

            return system

    def test_content_query_uses_search_tool(self, rag_system_with_mocks):
        """Test that content queries trigger search tool"""

        # Mock AI generator to simulate tool execution
        def mock_generate(query, conversation_history=None, tools=None, tool_manager=None):
            # Simulate AI deciding to use the tool
            if tool_manager:
                tool_manager.execute_tool(
                    "search_course_content",
                    query="Python basics",
                    course_name="Introduction to Programming",
                )
            return "Python is a high-level programming language"

        rag_system_with_mocks.ai_generator.generate_response = mock_generate
        rag_system_with_mocks.tool_manager.get_last_sources = Mock(return_value=[])
        rag_system_with_mocks.tool_manager.reset_sources = Mock()

        # Execute content query
        response, sources = rag_system_with_mocks.query(
            "What is Python in the Introduction to Programming course?"
        )

        # Verify tool was executed
        rag_system_with_mocks.tool_manager.execute_tool.assert_called()

    def test_query_failed_scenario(self, rag_system_with_mocks):
        """Test scenario that leads to 'query failed' response"""
        # This simulates what might cause "query failed"

        # Mock search tool to return error
        rag_system_with_mocks.search_tool.execute = Mock(return_value="Database connection failed")

        # Mock AI to use the tool
        def mock_generate_with_error(
            query, conversation_history=None, tools=None, tool_manager=None
        ):
            if tool_manager:
                result = tool_manager.execute_tool("search_course_content", query="test")
                # AI might say query failed if tool returns error
                if "failed" in result.lower() or "error" in result.lower():
                    return "query failed"
            return "Success"

        rag_system_with_mocks.ai_generator.generate_response = mock_generate_with_error
        rag_system_with_mocks.tool_manager.get_last_sources = Mock(return_value=[])
        rag_system_with_mocks.tool_manager.reset_sources = Mock()

        response, sources = rag_system_with_mocks.query("What is Python?")

        # This might result in "query failed"
        assert "failed" in response.lower() or "error" in response.lower()

    def test_empty_results_handling(self, rag_system_with_mocks):
        """Test how system handles empty search results"""
        # Mock search returning no results
        rag_system_with_mocks.search_tool.execute = Mock(return_value="No relevant content found.")

        def mock_generate(query, conversation_history=None, tools=None, tool_manager=None):
            if tool_manager:
                result = tool_manager.execute_tool("search_course_content", query="nonexistent")
                return f"I searched but found: {result}"
            return "Default response"

        rag_system_with_mocks.ai_generator.generate_response = mock_generate
        rag_system_with_mocks.tool_manager.get_last_sources = Mock(return_value=[])
        rag_system_with_mocks.tool_manager.reset_sources = Mock()

        response, sources = rag_system_with_mocks.query("Tell me about nonexistent topic")

        assert "No relevant content found" in response


class TestRAGSystemSourceTracking:
    """Tests for proper source tracking through the query flow"""

    def test_sources_flow_from_tool_to_response(self, mock_config):
        """Test that sources from tool execution reach the final response"""
        with (
            patch("rag_system.DocumentProcessor"),
            patch("rag_system.VectorStore"),
            patch("rag_system.AIGenerator"),
            patch("rag_system.SessionManager"),
            patch("rag_system.CourseSearchTool"),
            patch("rag_system.CourseOutlineTool"),
        ):

            system = RAGSystem(mock_config)

            # Mock sources from tool
            mock_sources = [
                {"text": "Python Course - Lesson 1", "link": "https://course.com/lesson1"},
                {"text": "Python Course - Lesson 2", "link": "https://course.com/lesson2"},
            ]

            system.tool_manager.get_last_sources = Mock(return_value=mock_sources)
            system.tool_manager.reset_sources = Mock()
            system.ai_generator.generate_response = Mock(return_value="Answer about Python")

            # Execute query
            response, sources = system.query("What is Python?")

            # Verify sources are returned
            assert sources == mock_sources
            assert len(sources) == 2
            assert sources[0]["link"] == "https://course.com/lesson1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
