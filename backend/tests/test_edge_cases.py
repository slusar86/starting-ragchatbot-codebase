"""
Comprehensive edge case and regression tests for RAG system
Tests for limit values, boundary conditions, and known bugs
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import Config
from search_tools import CourseSearchTool
from vector_store import SearchResults, VectorStore


class TestVectorStoreEdgeCases:
    """Edge case and boundary tests for VectorStore"""

    def test_max_results_zero_raises_error(self):
        """REGRESSION: MAX_RESULTS=0 should raise ValueError to prevent empty results bug"""
        with patch("vector_store.chromadb"):
            with pytest.raises(ValueError, match="max_results must be positive"):
                VectorStore(chroma_path="./test", embedding_model="test", max_results=0)

    def test_max_results_negative_raises_error(self):
        """EDGE CASE: Negative MAX_RESULTS should be rejected"""
        with patch("vector_store.chromadb"):
            with pytest.raises(ValueError, match="max_results must be positive"):
                VectorStore(chroma_path="./test", embedding_model="test", max_results=-1)

    def test_max_results_one_works(self):
        """BOUNDARY: MAX_RESULTS=1 is valid minimum"""
        with patch("vector_store.chromadb") as mock_chromadb:
            mock_client = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client
            mock_chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction = Mock()
            mock_client.get_or_create_collection.return_value = Mock()

            store = VectorStore(chroma_path="./test", embedding_model="test", max_results=1)
            assert store.max_results == 1

    def test_max_results_large_value_works(self):
        """BOUNDARY: Large MAX_RESULTS values should work"""
        with patch("vector_store.chromadb") as mock_chromadb:
            mock_client = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client
            mock_chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction = Mock()
            mock_client.get_or_create_collection.return_value = Mock()

            store = VectorStore(chroma_path="./test", embedding_model="test", max_results=1000)
            assert store.max_results == 1000

    def test_search_with_explicit_limit_zero(self):
        """EDGE CASE: Explicit limit=0 in search should still use max_results"""
        with patch("vector_store.chromadb") as mock_chromadb:
            mock_client = Mock()
            mock_collection = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client
            mock_chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction = Mock()
            mock_client.get_or_create_collection.return_value = mock_collection

            mock_collection.query.return_value = {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }

            store = VectorStore(chroma_path="./test", embedding_model="test", max_results=5)

            # Explicit limit=0 should be used (even though it returns nothing)
            store.search(query="test", limit=0)

            call_kwargs = mock_collection.query.call_args[1]
            assert call_kwargs["n_results"] == 0, "Explicit limit=0 should be respected"

    def test_search_empty_query_string(self):
        """EDGE CASE: Empty query string"""
        with patch("vector_store.chromadb") as mock_chromadb:
            mock_client = Mock()
            mock_collection = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client
            mock_chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction = Mock()
            mock_client.get_or_create_collection.return_value = mock_collection

            mock_collection.query.return_value = {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }

            store = VectorStore(chroma_path="./test", embedding_model="test", max_results=5)
            result = store.search(query="")

            # Should not crash, just return empty results
            assert isinstance(result, SearchResults)

    def test_search_with_none_limit_uses_max_results(self):
        """BOUNDARY: limit=None should use configured max_results"""
        with patch("vector_store.chromadb") as mock_chromadb:
            mock_client = Mock()
            mock_collection = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client
            mock_chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction = Mock()
            mock_client.get_or_create_collection.return_value = mock_collection

            mock_collection.query.return_value = {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }

            store = VectorStore(chroma_path="./test", embedding_model="test", max_results=7)
            store.search(query="test", limit=None)

            call_kwargs = mock_collection.query.call_args[1]
            assert call_kwargs["n_results"] == 7, "None limit should use max_results"


class TestCourseSearchToolEdgeCases:
    """Edge cases for CourseSearchTool"""

    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store"""
        store = Mock()
        store.course_catalog = Mock()
        return store

    @pytest.fixture
    def search_tool(self, mock_vector_store):
        """Create search tool"""
        return CourseSearchTool(mock_vector_store)

    def test_execute_with_very_long_query(self, search_tool, mock_vector_store):
        """EDGE CASE: Very long query string"""
        long_query = "Python " * 1000  # 7000 characters

        mock_vector_store.search.return_value = SearchResults(
            documents=["Result"],
            metadata=[{"course_title": "Test", "lesson_number": 1}],
            distances=[0.5],
            error=None,
        )

        # Should not crash
        result = search_tool.execute(query=long_query)
        assert isinstance(result, str)
        mock_vector_store.search.assert_called_once()

    def test_execute_with_special_characters_in_query(self, search_tool, mock_vector_store):
        """EDGE CASE: Special characters in query"""
        special_query = "What is <script>alert('test')</script> & Python?"

        mock_vector_store.search.return_value = SearchResults.empty("No results")

        # Should handle without injection issues
        result = search_tool.execute(query=special_query)
        assert "No relevant content found" in result

    def test_execute_with_lesson_number_zero(self, search_tool, mock_vector_store):
        """EDGE CASE: lesson_number=0"""
        mock_vector_store.search.return_value = SearchResults(
            documents=["Intro content"],
            metadata=[{"course_title": "Course", "lesson_number": 0}],
            distances=[0.3],
            error=None,
        )

        # lesson_number=0 could be valid (intro/overview)
        result = search_tool.execute(query="test", lesson_number=0)
        assert "Lesson 0" in result

    def test_execute_with_negative_lesson_number(self, search_tool, mock_vector_store):
        """EDGE CASE: Negative lesson number"""
        mock_vector_store.search.return_value = SearchResults.empty("No results")

        # Should pass through to vector store (which may filter it out)
        result = search_tool.execute(query="test", lesson_number=-1)
        mock_vector_store.search.assert_called_once()

    def test_execute_with_unicode_course_name(self, search_tool, mock_vector_store):
        """EDGE CASE: Unicode characters in course name"""
        unicode_course = "Programmierung für Anfänger 初級プログラミング"

        mock_vector_store.search.return_value = SearchResults(
            documents=["Content"],
            metadata=[{"course_title": unicode_course, "lesson_number": 1}],
            distances=[0.4],
            error=None,
        )

        result = search_tool.execute(query="test", course_name=unicode_course)
        assert unicode_course in result

    def test_format_results_with_missing_metadata_fields(self, search_tool, mock_vector_store):
        """EDGE CASE: Metadata missing course_title or lesson_number"""
        mock_vector_store.search.return_value = SearchResults(
            documents=["Content without full metadata"],
            metadata=[{}],  # Empty metadata
            distances=[0.5],
            error=None,
        )

        # Should handle gracefully with defaults
        result = search_tool.execute(query="test")
        assert "unknown" in result  # Default course_title

    def test_format_results_with_null_lesson_number(self, search_tool, mock_vector_store):
        """EDGE CASE: lesson_number is None in metadata"""
        mock_vector_store.search.return_value = SearchResults(
            documents=["General course info"],
            metadata=[{"course_title": "Test Course", "lesson_number": None}],
            distances=[0.6],
            error=None,
        )

        result = search_tool.execute(query="test")
        # Should not show "Lesson None" or crash
        assert "Test Course" in result
        assert "Lesson None" not in result


class TestConfigValidation:
    """Tests for configuration validation"""

    def test_config_max_results_is_positive(self):
        """REGRESSION: Ensure config doesn't have MAX_RESULTS=0"""
        config = Config()
        assert (
            config.MAX_RESULTS > 0
        ), f"Config MAX_RESULTS must be positive, got {config.MAX_RESULTS}"

    def test_config_max_results_reasonable_range(self):
        """Config MAX_RESULTS should be in reasonable range"""
        config = Config()
        assert (
            1 <= config.MAX_RESULTS <= 100
        ), f"Config MAX_RESULTS should be 1-100, got {config.MAX_RESULTS}"

    def test_config_chunk_size_positive(self):
        """Chunk size must be positive"""
        config = Config()
        assert config.CHUNK_SIZE > 0

    def test_config_chunk_overlap_non_negative(self):
        """Chunk overlap should be non-negative"""
        config = Config()
        assert config.CHUNK_OVERLAP >= 0

    def test_config_chunk_overlap_less_than_size(self):
        """Chunk overlap should be less than chunk size"""
        config = Config()
        assert config.CHUNK_OVERLAP < config.CHUNK_SIZE, "Overlap should be less than chunk size"


class TestSearchResultsEdgeCases:
    """Edge cases for SearchResults"""

    def test_from_chroma_with_empty_results(self):
        """Empty ChromaDB results"""
        chroma_results = {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        result = SearchResults.from_chroma(chroma_results)
        assert result.is_empty()
        assert len(result.documents) == 0

    def test_from_chroma_with_missing_keys(self):
        """ChromaDB results missing expected keys"""
        chroma_results = {"documents": []}

        # Should handle gracefully
        result = SearchResults.from_chroma(chroma_results)
        # Will use empty lists as defaults

    def test_empty_with_none_error_message(self):
        """Empty results with None error message"""
        result = SearchResults.empty(None)
        assert result.is_empty()
        assert result.error is None

    def test_empty_with_empty_string_error(self):
        """Empty results with empty string error"""
        result = SearchResults.empty("")
        assert result.is_empty()
        assert result.error == ""


class TestRegressionBugs:
    """Tests for specific bugs that were fixed"""

    def test_max_results_zero_bug(self):
        """
        REGRESSION TEST: MAX_RESULTS=0 caused all searches to fail

        Bug: Config had MAX_RESULTS=0, causing VectorStore to request
        0 results from ChromaDB, always returning empty results.

        Fix: Changed config to MAX_RESULTS=5 and added validation.
        """
        with patch("vector_store.chromadb"):
            # This should now raise an error instead of silently failing
            with pytest.raises(ValueError):
                VectorStore(chroma_path="./test", embedding_model="test", max_results=0)

    def test_syntax_error_in_ai_generator(self):
        """
        REGRESSION TEST: Syntax errors in ai_generator.py

        Bug: Line 141 had '}dane do fk' and line 144 had '*final'
        Fix: Removed invalid text and fixed parameter unpacking
        """
        # If this imports successfully, the syntax errors are fixed
        from ai_generator import AIGenerator

        # Verify the class is properly defined
        assert hasattr(AIGenerator, "generate_response")
        assert hasattr(AIGenerator, "_handle_tool_execution")

    def test_exception_variable_mismatch(self):
        """
        REGRESSION TEST: Exception variable mismatch in search_tools.py

        Bug: Caught as 'a' but used as 'e'
        Fix: Changed to 'except Exception as e:'
        """
        from search_tools import CourseOutlineTool

        # Verify the class is properly defined
        assert hasattr(CourseOutlineTool, "execute")


class TestExploratoryScenarios:
    """Exploratory tests for real-world scenarios"""

    def test_concurrent_searches_dont_interfere(self):
        """EXPLORATORY: Multiple searches should be independent"""
        with patch("vector_store.chromadb") as mock_chromadb:
            mock_client = Mock()
            mock_collection = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client
            mock_chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction = Mock()
            mock_client.get_or_create_collection.return_value = mock_collection

            mock_collection.query.side_effect = [
                {"documents": [["Result 1"]], "metadatas": [[{}]], "distances": [[0.5]]},
                {"documents": [["Result 2"]], "metadatas": [[{}]], "distances": [[0.3]]},
            ]

            store = VectorStore(chroma_path="./test", embedding_model="test", max_results=5)

            result1 = store.search(query="query1")
            result2 = store.search(query="query2")

            assert result1.documents[0] == "Result 1"
            assert result2.documents[0] == "Result 2"

    def test_search_with_all_filters(self):
        """EXPLORATORY: Search with all possible filters"""
        with patch("vector_store.chromadb") as mock_chromadb:
            mock_client = Mock()
            mock_collection = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client
            mock_chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction = Mock()
            mock_client.get_or_create_collection.return_value = mock_collection

            mock_collection.query.return_value = {
                "documents": [["Filtered content"]],
                "metadatas": [[{"course_title": "Test", "lesson_number": 5}]],
                "distances": [[0.2]],
            }

            # Mock course resolution
            mock_catalog = Mock()
            mock_catalog.query.return_value = {
                "documents": [["Test Course"]],
                "metadatas": [[{"title": "Test Course"}]],
            }
            mock_client.get_or_create_collection.side_effect = [mock_catalog, mock_collection]

            store = VectorStore(chroma_path="./test", embedding_model="test", max_results=5)

            result = store.search(
                query="complex query", course_name="Test", lesson_number=5, limit=3
            )

            # Verify the filter was built correctly
            call_kwargs = mock_collection.query.call_args[1]
            assert "where" in call_kwargs
            assert call_kwargs["n_results"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
