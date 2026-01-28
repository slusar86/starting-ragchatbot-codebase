"""
Tests for AIGenerator to validate tool calling functionality
"""

import os
import sys
from unittest.mock import MagicMock, Mock, call, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_generator import AIGenerator


class MockAnthropicResponse:
    """Mock for Anthropic API response"""

    def __init__(self, text=None, tool_use=None, stop_reason="end_turn"):
        self.stop_reason = stop_reason
        if tool_use:
            self.content = tool_use
        elif text:
            self.content = [Mock(text=text, type="text")]
        else:
            self.content = [Mock(text="Default response", type="text")]


class MockToolUse:
    """Mock for tool use content block"""

    def __init__(self, tool_name, tool_input, tool_id="test_id"):
        self.type = "tool_use"
        self.name = tool_name
        self.input = tool_input
        self.id = tool_id


class TestAIGenerator:
    """Test suite for AIGenerator tool calling functionality"""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Create a mock Anthropic client"""
        return Mock()

    @pytest.fixture
    def ai_generator(self, mock_anthropic_client):
        """Create an AIGenerator instance with mocked client"""
        with patch("ai_generator.anthropic.Anthropic", return_value=mock_anthropic_client):
            generator = AIGenerator(api_key="test_key", model="claude-3-sonnet-20240229")
            generator.client = mock_anthropic_client
            return generator

    def test_initialization(self):
        """Test AIGenerator initializes correctly"""
        with patch("ai_generator.anthropic.Anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client

            generator = AIGenerator(api_key="test_key", model="claude-3-sonnet-20240229")

            assert generator.model == "claude-3-sonnet-20240229"
            assert generator.client == mock_client
            mock_anthropic.assert_called_once_with(api_key="test_key")

    def test_generate_response_without_tools(self, ai_generator, mock_anthropic_client):
        """Test generating a response without using tools"""
        # Mock response
        mock_response = MockAnthropicResponse(text="This is a direct answer")
        mock_anthropic_client.messages.create.return_value = mock_response

        # Generate response
        result = ai_generator.generate_response(
            query="What is Python?", conversation_history=None, tools=None, tool_manager=None
        )

        # Verify
        assert result == "This is a direct answer"
        assert mock_anthropic_client.messages.create.called
        call_kwargs = mock_anthropic_client.messages.create.call_args[1]
        assert call_kwargs["messages"][0]["content"] == "What is Python?"
        assert "tools" not in call_kwargs

    def test_generate_response_with_conversation_history(self, ai_generator, mock_anthropic_client):
        """Test that conversation history is included in system prompt"""
        mock_response = MockAnthropicResponse(text="Response with history")
        mock_anthropic_client.messages.create.return_value = mock_response

        history = "User: Previous question\nAssistant: Previous answer"

        result = ai_generator.generate_response(
            query="Follow-up question", conversation_history=history, tools=None, tool_manager=None
        )

        # Verify history was included in system prompt
        call_kwargs = mock_anthropic_client.messages.create.call_args[1]
        assert "Previous question" in call_kwargs["system"]
        assert "Previous answer" in call_kwargs["system"]

    def test_generate_response_with_tools_no_tool_use(self, ai_generator, mock_anthropic_client):
        """Test response when tools are available but not used"""
        mock_response = MockAnthropicResponse(text="Direct answer without tools")
        mock_anthropic_client.messages.create.return_value = mock_response

        mock_tools = [{"name": "search_tool", "description": "Search content"}]
        mock_tool_manager = Mock()

        result = ai_generator.generate_response(
            query="General knowledge question", tools=mock_tools, tool_manager=mock_tool_manager
        )

        # Verify tools were provided but not executed
        assert result == "Direct answer without tools"
        call_kwargs = mock_anthropic_client.messages.create.call_args[1]
        assert "tools" in call_kwargs
        assert call_kwargs["tools"] == mock_tools
        mock_tool_manager.execute_tool.assert_not_called()

    def test_generate_response_with_tool_use(self, ai_generator, mock_anthropic_client):
        """Test response when AI decides to use a tool"""
        # Mock initial response with tool use
        tool_use_block = MockToolUse(
            tool_name="search_course_content",
            tool_input={"query": "Python basics", "course_name": "Programming"},
        )
        initial_response = MockAnthropicResponse(
            tool_use=[Mock(type="text", text="Let me search"), tool_use_block],
            stop_reason="tool_use",
        )

        # Mock final response after tool execution
        final_response = MockAnthropicResponse(
            text="Based on the course materials, Python is a high-level language."
        )

        mock_anthropic_client.messages.create.side_effect = [initial_response, final_response]

        # Mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Python is a programming language used for..."

        mock_tools = [{"name": "search_course_content", "description": "Search course materials"}]

        # Generate response
        result = ai_generator.generate_response(
            query="What is Python?", tools=mock_tools, tool_manager=mock_tool_manager
        )

        # Verify tool was executed
        mock_tool_manager.execute_tool.assert_called_once_with(
            "search_course_content", query="Python basics", course_name="Programming"
        )

        # Verify final response
        assert "Based on the course materials" in result

        # Verify API was called twice (initial + follow-up)
        assert mock_anthropic_client.messages.create.call_count == 2

    def test_handle_tool_execution_multiple_tools(self, ai_generator, mock_anthropic_client):
        """Test handling multiple tool calls in one response"""
        # Mock response with multiple tool uses
        tool_use_1 = MockToolUse(
            tool_name="search_course_content", tool_input={"query": "variables"}, tool_id="tool_1"
        )
        tool_use_2 = MockToolUse(
            tool_name="search_course_content", tool_input={"query": "functions"}, tool_id="tool_2"
        )

        initial_response = MockAnthropicResponse(
            tool_use=[tool_use_1, tool_use_2], stop_reason="tool_use"
        )
        final_response = MockAnthropicResponse(text="Combined answer from both searches")

        mock_anthropic_client.messages.create.side_effect = [initial_response, final_response]

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = [
            "Info about variables",
            "Info about functions",
        ]

        # Generate response
        result = ai_generator.generate_response(
            query="Explain variables and functions",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager,
        )

        # Verify both tools were executed
        assert mock_tool_manager.execute_tool.call_count == 2
        assert result == "Combined answer from both searches"

    def test_tool_execution_with_error(self, ai_generator, mock_anthropic_client):
        """Test that tool execution errors are handled gracefully"""
        tool_use_block = MockToolUse(
            tool_name="search_course_content", tool_input={"query": "test"}
        )
        initial_response = MockAnthropicResponse(tool_use=[tool_use_block], stop_reason="tool_use")
        final_response = MockAnthropicResponse(
            text="I couldn't find information in the course materials."
        )

        mock_anthropic_client.messages.create.side_effect = [initial_response, final_response]

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "No relevant content found."

        # This should not raise an exception
        result = ai_generator.generate_response(
            query="Find something that doesn't exist",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager,
        )

        assert "couldn't find" in result

    def test_system_prompt_structure(self, ai_generator):
        """Test that system prompt contains essential instructions"""
        system_prompt = ai_generator.SYSTEM_PROMPT

        # Check for key elements
        assert "search_course_content" in system_prompt
        assert "tool" in system_prompt.lower()
        assert "course" in system_prompt.lower()

    def test_api_parameters(self, ai_generator, mock_anthropic_client):
        """Test that API parameters are correctly set"""
        mock_response = MockAnthropicResponse(text="Test")
        mock_anthropic_client.messages.create.return_value = mock_response

        ai_generator.generate_response(query="Test query")

        call_kwargs = mock_anthropic_client.messages.create.call_args[1]

        # Check base parameters
        assert call_kwargs["model"] == "claude-3-sonnet-20240229"
        assert call_kwargs["temperature"] == 0
        assert call_kwargs["max_tokens"] == 800
        assert "messages" in call_kwargs
        assert "system" in call_kwargs


class TestAIGeneratorToolCallingSyntax:
    """Test suite specifically for syntax errors in tool calling code"""

    def test_handle_tool_execution_syntax(self):
        """Test that _handle_tool_execution has valid Python syntax"""
        # This test will fail if there are syntax errors in the module
        from ai_generator import AIGenerator

        # Verify the method exists and is callable
        assert hasattr(AIGenerator, "_handle_tool_execution")
        assert callable(getattr(AIGenerator, "_handle_tool_execution"))

    def test_final_params_construction(self):
        """Test that final_params dictionary is properly constructed"""
        # Import should succeed if syntax is correct
        try:
            from ai_generator import AIGenerator

            generator = AIGenerator(api_key="test", model="test-model")

            # Check that base_params exists
            assert hasattr(generator, "base_params")
            assert isinstance(generator.base_params, dict)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in AIGenerator: {e}")


class TestAIGeneratorMultiRound:
    """Test suite for multi-round sequential tool calling"""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Create a mock Anthropic client"""
        return Mock()

    @pytest.fixture
    def ai_generator(self, mock_anthropic_client):
        """Create an AIGenerator instance with mocked client"""
        with patch("ai_generator.anthropic.Anthropic", return_value=mock_anthropic_client):
            generator = AIGenerator(api_key="test_key", model="claude-3-sonnet-20240229")
            generator.client = mock_anthropic_client
            return generator

    def test_sequential_tool_calling_two_rounds(self, ai_generator, mock_anthropic_client):
        """Test that Claude can make tool calls in 2 separate rounds"""

        # Round 1: Get course outline
        tool_use_1 = MockToolUse(
            tool_name="get_course_outline",
            tool_input={"course_name": "Python Basics"},
            tool_id="tool_round_1",
        )
        response_1 = MockAnthropicResponse(tool_use=[tool_use_1], stop_reason="tool_use")

        # Round 2: Search based on outline results
        tool_use_2 = MockToolUse(
            tool_name="search_course_content",
            tool_input={"query": "lesson 4 topics", "course_name": "Python Basics"},
            tool_id="tool_round_2",
        )
        response_2 = MockAnthropicResponse(tool_use=[tool_use_2], stop_reason="tool_use")

        # Final response after 2 rounds
        final_response = MockAnthropicResponse(
            text="Based on the course outline and detailed search, lesson 4 covers functions."
        )

        mock_anthropic_client.messages.create.side_effect = [response_1, response_2, final_response]

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = [
            "Course outline: Lesson 1: Intro, Lesson 2: Variables...",
            "Lesson 4 details: Functions and parameters...",
        ]

        result = ai_generator.generate_response(
            query="What does lesson 4 cover?",
            tools=[{"name": "get_course_outline"}, {"name": "search_course_content"}],
            tool_manager=mock_tool_manager,
        )

        # Verify 2 tool executions (one per round)
        assert mock_tool_manager.execute_tool.call_count == 2

        # Verify 3 API calls (initial + 2 rounds)
        assert mock_anthropic_client.messages.create.call_count == 3

        # Verify tools were available in follow-up rounds (not just the first)
        for call_idx, call in enumerate(
            mock_anthropic_client.messages.create.call_args_list[1:], 1
        ):
            call_kwargs = call[1]
            assert "tools" in call_kwargs, f"Tools should be available in round {call_idx}"

        # Verify final response
        assert "lesson 4 covers functions" in result.lower()

    def test_max_rounds_enforced(self, ai_generator, mock_anthropic_client):
        """Test that tool calling stops after MAX_TOOL_ROUNDS"""

        # Create 3 tool use responses (but should stop at 2)
        tool_responses = []
        for i in range(1, 4):
            tool_use = MockToolUse(
                tool_name="search_course_content",
                tool_input={"query": f"query_{i}"},
                tool_id=f"tool_{i}",
            )
            tool_responses.append(
                MockAnthropicResponse(tool_use=[tool_use], stop_reason="tool_use")
            )

        # Final response after max rounds
        final_response = MockAnthropicResponse(text="Response after forcing completion")

        mock_anthropic_client.messages.create.side_effect = tool_responses + [final_response]

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Search result"

        result = ai_generator.generate_response(
            query="Complex multi-step query",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager,
        )

        # Should execute tools 3 times:
        # - Round 1: tool execution
        # - Round 2: tool execution (max reached)
        # - Forced final: tool execution
        assert mock_tool_manager.execute_tool.call_count == 3

        # Should make 4 API calls maximum
        assert mock_anthropic_client.messages.create.call_count <= 4

        # Should return a response
        assert isinstance(result, str)
        assert len(result) > 0

    def test_early_termination_one_round_sufficient(self, ai_generator, mock_anthropic_client):
        """Test that process terminates early if Claude doesn't need second round"""

        tool_use = MockToolUse(
            tool_name="search_course_content", tool_input={"query": "Python basics"}
        )
        initial_response = MockAnthropicResponse(tool_use=[tool_use], stop_reason="tool_use")

        # After first tool execution, Claude has enough info
        final_response = MockAnthropicResponse(
            text="Complete answer based on first search", stop_reason="end_turn"
        )

        mock_anthropic_client.messages.create.side_effect = [initial_response, final_response]

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Comprehensive search result"

        result = ai_generator.generate_response(
            query="What is Python?",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager,
        )

        # Should only execute tool once
        assert mock_tool_manager.execute_tool.call_count == 1

        # Should only make 2 API calls (initial + follow-up, no second round)
        assert mock_anthropic_client.messages.create.call_count == 2

        assert "Complete answer" in result

    def test_tool_execution_error_graceful_handling(self, ai_generator, mock_anthropic_client):
        """Test that tool execution errors are handled gracefully"""

        tool_use = MockToolUse(
            tool_name="search_course_content", tool_input={"query": "test"}, tool_id="tool_1"
        )
        initial_response = MockAnthropicResponse(tool_use=[tool_use], stop_reason="tool_use")

        final_response = MockAnthropicResponse(
            text="I encountered an error but here's what I know..."
        )

        mock_anthropic_client.messages.create.side_effect = [initial_response, final_response]

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = Exception("Database connection failed")

        # Should not raise exception
        result = ai_generator.generate_response(
            query="Search for something",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager,
        )

        # Should still return a response
        assert isinstance(result, str)
        assert len(result) > 0

        # Tool manager should have been called
        assert mock_tool_manager.execute_tool.called

    def test_api_error_during_tool_round(self, ai_generator, mock_anthropic_client):
        """Test handling of API errors during tool execution rounds"""

        tool_use = MockToolUse(tool_name="search_course_content", tool_input={"query": "test"})
        initial_response = MockAnthropicResponse(tool_use=[tool_use], stop_reason="tool_use")

        # First call succeeds, second call (after tool execution) fails
        mock_anthropic_client.messages.create.side_effect = [
            initial_response,
            Exception("API rate limit exceeded"),
        ]

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Tool result"

        result = ai_generator.generate_response(
            query="Search query",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager,
        )

        # Should return error message, not raise exception
        assert isinstance(result, str)
        # Error message should be user-friendly
        assert "error" in result.lower() or "apologize" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
