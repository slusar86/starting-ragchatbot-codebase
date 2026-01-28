"""
Tests for CourseSearchTool to validate search functionality
"""

import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from search_tools import CourseSearchTool, ToolManager
from vector_store import SearchResults


class TestCourseSearchTool:
    """Test suite for CourseSearchTool.execute() method"""

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store"""
        store = Mock()
        store.course_catalog = Mock()
        return store

    @pytest.fixture
    def search_tool(self, mock_vector_store):
        """Create a CourseSearchTool instance with mocked dependencies"""
        return CourseSearchTool(mock_vector_store)

    def test_get_tool_definition(self, search_tool):
        """Test that tool definition is properly formatted"""
        definition = search_tool.get_tool_definition()

        assert definition["name"] == "search_course_content"
        assert "description" in definition
        assert "input_schema" in definition
        assert definition["input_schema"]["type"] == "object"
        assert "query" in definition["input_schema"]["properties"]
        assert "query" in definition["input_schema"]["required"]

    def test_execute_with_results(self, search_tool, mock_vector_store):
        """Test execute method returns formatted results when content is found"""
        # Mock successful search results
        mock_results = SearchResults(
            documents=["This is content about Python programming."],
            metadata=[{"course_title": "Introduction to Programming", "lesson_number": 1}],
            distances=[0.5],
            error=None,
        )
        mock_vector_store.search.return_value = mock_results

        # Execute search
        result = search_tool.execute(
            query="Python basics", course_name="Programming", lesson_number=1
        )

        # Verify results
        assert result is not None
        assert isinstance(result, str)
        assert "Introduction to Programming" in result
        assert "Lesson 1" in result
        assert "Python programming" in result

        # Verify search was called with correct parameters
        mock_vector_store.search.assert_called_once_with(
            query="Python basics", course_name="Programming", lesson_number=1
        )

    def test_execute_with_error(self, search_tool, mock_vector_store):
        """Test execute method handles search errors properly"""
        # Mock error scenario
        mock_results = SearchResults(
            documents=[], metadata=[], distances=[], error="Database connection failed"
        )
        mock_vector_store.search.return_value = mock_results

        # Execute search
        result = search_tool.execute(query="test query")

        # Verify error is returned
        assert result == "Database connection failed"

    def test_execute_with_empty_results(self, search_tool, mock_vector_store):
        """Test execute method handles empty results properly"""
        # Mock empty results
        mock_results = SearchResults(documents=[], metadata=[], distances=[], error=None)
        mock_vector_store.search.return_value = mock_results

        # Execute search with filters
        result = search_tool.execute(
            query="nonexistent topic", course_name="Test Course", lesson_number=5
        )

        # Verify appropriate message
        assert "No relevant content found" in result
        assert "Test Course" in result
        assert "lesson 5" in result

    def test_execute_without_filters(self, search_tool, mock_vector_store):
        """Test execute method works without course/lesson filters"""
        # Mock results
        mock_results = SearchResults(
            documents=["General content about machine learning."],
            metadata=[{"course_title": "AI Fundamentals", "lesson_number": 3}],
            distances=[0.3],
            error=None,
        )
        mock_vector_store.search.return_value = mock_results

        # Execute search without filters
        result = search_tool.execute(query="machine learning")

        # Verify search was called correctly
        mock_vector_store.search.assert_called_once_with(
            query="machine learning", course_name=None, lesson_number=None
        )

        assert "AI Fundamentals" in result
        assert "machine learning" in result

    def test_format_results_sorting(self, search_tool, mock_vector_store):
        """Test that results are sorted by lesson number"""
        # Mock results with multiple lessons in wrong order
        mock_results = SearchResults(
            documents=["Lesson 3 content", "Lesson 1 content", "Lesson 2 content"],
            metadata=[
                {"course_title": "Test Course", "lesson_number": 3},
                {"course_title": "Test Course", "lesson_number": 1},
                {"course_title": "Test Course", "lesson_number": 2},
            ],
            distances=[0.1, 0.2, 0.3],
            error=None,
        )
        mock_vector_store.search.return_value = mock_results

        result = search_tool.execute(query="test")

        # Check that lessons appear in correct order
        lesson_1_pos = result.find("Lesson 1")
        lesson_2_pos = result.find("Lesson 2")
        lesson_3_pos = result.find("Lesson 3")

        assert (
            lesson_1_pos < lesson_2_pos < lesson_3_pos
        ), "Results should be sorted by lesson number"

    def test_sources_tracking(self, search_tool, mock_vector_store):
        """Test that sources are properly tracked"""
        # Mock results
        mock_results = SearchResults(
            documents=["Content about databases"],
            metadata=[{"course_title": "Database Systems", "lesson_number": 2}],
            distances=[0.4],
            error=None,
        )
        mock_vector_store.search.return_value = mock_results

        # Mock course catalog for lesson link lookup
        mock_vector_store.course_catalog.get.return_value = {
            "metadatas": [
                {
                    "lessons_json": '[{"lesson_number": 2, "lesson_title": "SQL Basics", "lesson_link": "https://example.com/lesson2"}]'
                }
            ]
        }

        # Execute search
        search_tool.execute(query="databases")

        # Check sources are tracked
        assert len(search_tool.last_sources) > 0
        source = search_tool.last_sources[0]
        assert "text" in source
        assert "Database Systems" in source["text"]


class TestToolManager:
    """Test suite for ToolManager"""

    @pytest.fixture
    def tool_manager(self):
        """Create a ToolManager instance"""
        return ToolManager()

    @pytest.fixture
    def mock_search_tool(self):
        """Create a mock search tool"""
        tool = Mock()
        tool.get_tool_definition.return_value = {
            "name": "test_search",
            "description": "Test tool",
            "input_schema": {"type": "object", "properties": {}},
        }
        tool.execute.return_value = "Test result"
        tool.last_sources = []
        return tool

    def test_register_tool(self, tool_manager, mock_search_tool):
        """Test that tools can be registered"""
        tool_manager.register_tool(mock_search_tool)
        assert "test_search" in tool_manager.tools

    def test_get_tool_definitions(self, tool_manager, mock_search_tool):
        """Test getting all tool definitions"""
        tool_manager.register_tool(mock_search_tool)
        definitions = tool_manager.get_tool_definitions()

        assert len(definitions) == 1
        assert definitions[0]["name"] == "test_search"

    def test_execute_tool(self, tool_manager, mock_search_tool):
        """Test executing a registered tool"""
        tool_manager.register_tool(mock_search_tool)
        result = tool_manager.execute_tool("test_search", query="test")

        assert result == "Test result"
        mock_search_tool.execute.assert_called_once_with(query="test")

    def test_execute_nonexistent_tool(self, tool_manager):
        """Test executing a tool that doesn't exist"""
        result = tool_manager.execute_tool("nonexistent_tool")
        assert "not found" in result.lower()

    def test_get_last_sources(self, tool_manager, mock_search_tool):
        """Test retrieving sources from tools"""
        mock_search_tool.last_sources = [{"text": "Test Source", "link": "http://test.com"}]
        tool_manager.register_tool(mock_search_tool)

        sources = tool_manager.get_last_sources()
        assert len(sources) == 1
        assert sources[0]["text"] == "Test Source"

    def test_reset_sources(self, tool_manager, mock_search_tool):
        """Test resetting sources"""
        mock_search_tool.last_sources = [{"text": "Test", "link": "http://test.com"}]
        tool_manager.register_tool(mock_search_tool)

        tool_manager.reset_sources()
        assert len(mock_search_tool.last_sources) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
