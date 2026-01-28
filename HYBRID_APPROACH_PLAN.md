# Hybrid Approach: Minimal Loop + Enhanced Error Handling

## Design Overview

Combines **Approach 1's simplicity** (loop-based structure) with **Approach 2's robustness** (comprehensive error handling). Keeps the minimal code footprint while adding safety nets for production use.

## Changes to backend/ai_generator.py

### 1. Add Class Constants and Imports
```python
import logging
from typing import List, Optional, Dict, Any, Tuple

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
    # Configuration constants
    MAX_TOOL_ROUNDS = 2
    
    # Setup logger
    logger = logging.getLogger(__name__)
```

### 2. Update System Prompt
Add multi-round guidance to the SYSTEM_PROMPT:
```python
SYSTEM_PROMPT = """...[existing content]...

Tool Usage Guidelines:
- Use tools **only** for questions about specific course content or course structure
- **Multi-round capability**: You can make up to 2 sequential tool calls
  * First round: Get initial information or context
  * Second round (if needed): Make additional searches based on first results
- After receiving tool results, evaluate if additional searches are needed
- Synthesize tool results into accurate, fact-based responses
- If tool yields no results, state this clearly without offering alternatives
...[rest of existing content]...
"""
```

### 3. Refactor _handle_tool_execution() with Loop + Error Handling
```python
def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
    """
    Handle up to 2 rounds of sequential tool execution with comprehensive error handling.
    
    Args:
        initial_response: The response containing tool use requests
        base_params: Base API parameters including tools
        tool_manager: Manager to execute tools
        
    Returns:
        Tuple[str, Optional[str]]: (response_text, error_message)
        - If successful: (response_text, None)
        - If error: (fallback_text, error_message)
    """
    messages = base_params["messages"].copy()
    current_response = initial_response
    
    try:
        # Loop for up to MAX_TOOL_ROUNDS
        for round_num in range(1, self.MAX_TOOL_ROUNDS + 1):
            self.logger.debug(f"Starting tool execution round {round_num}/{self.MAX_TOOL_ROUNDS}")
            
            # Add assistant's response (with tool_use blocks) to messages
            messages.append({"role": "assistant", "content": current_response.content})
            
            # Execute all tool calls in this round
            tool_results = []
            for content_block in current_response.content:
                if content_block.type == "tool_use":
                    try:
                        # Execute tool with timeout protection
                        tool_result = tool_manager.execute_tool(
                            content_block.name, 
                            **content_block.input
                        )
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": tool_result
                        })
                        
                        self.logger.debug(f"Round {round_num}: Executed {content_block.name}")
                        
                    except Exception as tool_error:
                        # Handle individual tool failures gracefully
                        error_msg = f"Tool execution failed: {str(tool_error)}"
                        self.logger.error(f"Round {round_num}: {error_msg}")
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": error_msg,
                            "is_error": True
                        })
            
            # Check if any tools were executed
            if not tool_results:
                self.logger.warning(f"Round {round_num}: No tools executed despite tool_use stop_reason")
                break
            
            # Add tool results to messages
            messages.append({"role": "user", "content": tool_results})
            
            # Prepare next API call WITH tools still available (KEY FIX)
            next_params = {
                **self.base_params,
                "messages": messages,
                "system": base_params["system"],
                "tools": base_params.get("tools"),  # Keep tools available
                "tool_choice": {"type": "auto"}
            }
            
            try:
                # Make next API call
                current_response = self.client.messages.create(**next_params)
                self.logger.debug(f"Round {round_num}: API call successful, stop_reason={current_response.stop_reason}")
                
            except Exception as api_error:
                # Handle API call failures
                self.logger.error(f"Round {round_num}: API call failed: {str(api_error)}")
                return self._create_error_response(
                    f"API error in round {round_num}: {str(api_error)}"
                )
            
            # Check if Claude wants to make more tool calls
            if current_response.stop_reason != "tool_use":
                # No more tool calls needed - return final text response
                self.logger.debug(f"Round {round_num}: Conversation complete (stop_reason={current_response.stop_reason})")
                break
            
            # If we've reached max rounds and Claude still wants tools
            if round_num == self.MAX_TOOL_ROUNDS:
                self.logger.warning(f"Max rounds ({self.MAX_TOOL_ROUNDS}) reached, forcing final response")
                # Execute remaining tools and force text response
                return self._force_final_text_response(
                    current_response, 
                    messages, 
                    base_params, 
                    tool_manager
                )
        
        # Extract and return final text response
        return self._extract_text_response(current_response)
        
    except Exception as unexpected_error:
        # Catch-all for unexpected errors
        self.logger.exception(f"Unexpected error in multi-round tool execution: {unexpected_error}")
        return self._create_error_response(
            f"Unexpected error: {str(unexpected_error)}"
        )

def _force_final_text_response(self, 
                               last_response, 
                               messages: List[Dict],
                               base_params: Dict[str, Any],
                               tool_manager) -> str:
    """
    Force a final text response when max rounds reached but Claude still wants tools.
    Executes the final tool calls and makes one last API call WITHOUT tools.
    
    Args:
        last_response: Response with tool_use that exceeded max rounds
        messages: Current message history
        base_params: Base API parameters
        tool_manager: Tool execution manager
        
    Returns:
        Final text response
    """
    try:
        # Add last assistant response to messages
        messages.append({"role": "assistant", "content": last_response.content})
        
        # Execute final tool calls
        tool_results = []
        for content_block in last_response.content:
            if content_block.type == "tool_use":
                try:
                    tool_result = tool_manager.execute_tool(
                        content_block.name,
                        **content_block.input
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": tool_result
                    })
                except Exception as e:
                    self.logger.error(f"Final tool execution failed: {e}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": f"Error: {str(e)}",
                        "is_error": True
                    })
        
        # Add tool results
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        
        # Make final API call WITHOUT tools to force text response
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": base_params["system"]
            # Note: No tools or tool_choice - forces text response
        }
        
        final_response = self.client.messages.create(**final_params)
        self.logger.debug("Forced final response successful")
        
        return self._extract_text_response(final_response)
        
    except Exception as e:
        self.logger.error(f"Failed to force final response: {e}")
        return self._create_error_response(f"Failed to generate final response: {str(e)}")

def _extract_text_response(self, response) -> str:
    """
    Extract text content from API response.
    Handles different response formats safely.
    
    Args:
        response: Anthropic API response object
        
    Returns:
        Text content or error message
    """
    try:
        # Try to get text from first content block
        if response.content and len(response.content) > 0:
            for block in response.content:
                if hasattr(block, 'text') and block.text:
                    return block.text
        
        # Fallback
        self.logger.warning("No text content found in response")
        return "I apologize, but I couldn't generate a proper response."
        
    except Exception as e:
        self.logger.error(f"Error extracting text from response: {e}")
        return self._create_error_response(f"Response extraction error: {str(e)}")

def _create_error_response(self, error_message: str) -> str:
    """
    Create a user-friendly error response.
    
    Args:
        error_message: Technical error message for logging
        
    Returns:
        User-friendly error message
    """
    return (
        "I apologize, but I encountered an error while processing your request. "
        "Please try rephrasing your question or ask something else."
    )
```

### 4. Update generate_response() Return Type (Optional Enhancement)
No changes required - keeps existing signature for backward compatibility.

## Changes to backend/tests/test_ai_generator.py

### New Test Cases to Add

#### 1. Test Sequential Tool Calling (Happy Path)
```python
def test_sequential_tool_calling_two_rounds(self, ai_generator, mock_anthropic_client):
    """Test that Claude can make tool calls in 2 separate rounds"""
    
    # Round 1: Get course outline
    tool_use_1 = MockToolUse(
        tool_name="get_course_outline",
        tool_input={"course_name": "Python Basics"},
        tool_id="tool_round_1"
    )
    response_1 = MockAnthropicResponse(
        tool_use=[tool_use_1],
        stop_reason="tool_use"
    )
    
    # Round 2: Search based on outline results
    tool_use_2 = MockToolUse(
        tool_name="search_course_content",
        tool_input={"query": "lesson 4 topics", "course_name": "Python Basics"},
        tool_id="tool_round_2"
    )
    response_2 = MockAnthropicResponse(
        tool_use=[tool_use_2],
        stop_reason="tool_use"
    )
    
    # Final response after 2 rounds
    final_response = MockAnthropicResponse(
        text="Based on the course outline and detailed search, lesson 4 covers functions."
    )
    
    mock_anthropic_client.messages.create.side_effect = [
        response_1, response_2, final_response
    ]
    
    mock_tool_manager = Mock()
    mock_tool_manager.execute_tool.side_effect = [
        "Course outline: Lesson 1: Intro, Lesson 2: Variables...",
        "Lesson 4 details: Functions and parameters..."
    ]
    
    result = ai_generator.generate_response(
        query="What does lesson 4 cover?",
        tools=[{'name': 'get_course_outline'}, {'name': 'search_course_content'}],
        tool_manager=mock_tool_manager
    )
    
    # Verify 2 tool executions (one per round)
    assert mock_tool_manager.execute_tool.call_count == 2
    
    # Verify 3 API calls (initial + 2 rounds)
    assert mock_anthropic_client.messages.create.call_count == 3
    
    # Verify tools were available in all rounds
    for call in mock_anthropic_client.messages.create.call_args_list[1:]:
        assert 'tools' in call[1], "Tools should be available in follow-up calls"
    
    # Verify final response
    assert "lesson 4 covers functions" in result.lower()
```

#### 2. Test Max Rounds Limit
```python
def test_max_rounds_enforced(self, ai_generator, mock_anthropic_client):
    """Test that tool calling stops after MAX_TOOL_ROUNDS"""
    
    # Create 3 tool use responses (but should stop at 2)
    tool_responses = []
    for i in range(1, 4):
        tool_use = MockToolUse(
            tool_name="search_course_content",
            tool_input={"query": f"query_{i}"},
            tool_id=f"tool_{i}"
        )
        tool_responses.append(MockAnthropicResponse(
            tool_use=[tool_use],
            stop_reason="tool_use"
        ))
    
    # Final response after max rounds
    final_response = MockAnthropicResponse(
        text="Response after forcing completion"
    )
    
    mock_anthropic_client.messages.create.side_effect = tool_responses + [final_response]
    
    mock_tool_manager = Mock()
    mock_tool_manager.execute_tool.return_value = "Search result"
    
    result = ai_generator.generate_response(
        query="Complex multi-step query",
        tools=[{'name': 'search_course_content'}],
        tool_manager=mock_tool_manager
    )
    
    # Should execute tools only 3 times:
    # - 2 rounds of tool calls (enforced limit)
    # - 1 final tool execution when forcing completion
    assert mock_tool_manager.execute_tool.call_count == 3
    
    # Should make 4 API calls:
    # - Round 1: tool_use response
    # - Round 2: tool_use response (max reached)
    # - Force final: API call without tools
    assert mock_anthropic_client.messages.create.call_count <= 4
```

#### 3. Test Tool Execution Error Handling
```python
def test_tool_execution_error_graceful_handling(self, ai_generator, mock_anthropic_client):
    """Test that tool execution errors are handled gracefully"""
    
    tool_use = MockToolUse(
        tool_name="search_course_content",
        tool_input={"query": "test"},
        tool_id="tool_1"
    )
    initial_response = MockAnthropicResponse(
        tool_use=[tool_use],
        stop_reason="tool_use"
    )
    
    final_response = MockAnthropicResponse(
        text="I encountered an error but here's what I know..."
    )
    
    mock_anthropic_client.messages.create.side_effect = [initial_response, final_response]
    
    mock_tool_manager = Mock()
    mock_tool_manager.execute_tool.side_effect = Exception("Database connection failed")
    
    # Should not raise exception
    result = ai_generator.generate_response(
        query="Search for something",
        tools=[{'name': 'search_course_content'}],
        tool_manager=mock_tool_manager
    )
    
    # Should still return a response
    assert isinstance(result, str)
    assert len(result) > 0
    
    # Tool manager should have been called
    assert mock_tool_manager.execute_tool.called
```

#### 4. Test API Error During Round
```python
def test_api_error_during_tool_round(self, ai_generator, mock_anthropic_client):
    """Test handling of API errors during tool execution rounds"""
    
    tool_use = MockToolUse(
        tool_name="search_course_content",
        tool_input={"query": "test"}
    )
    initial_response = MockAnthropicResponse(
        tool_use=[tool_use],
        stop_reason="tool_use"
    )
    
    # First call succeeds, second call (after tool execution) fails
    mock_anthropic_client.messages.create.side_effect = [
        initial_response,
        Exception("API rate limit exceeded")
    ]
    
    mock_tool_manager = Mock()
    mock_tool_manager.execute_tool.return_value = "Tool result"
    
    result = ai_generator.generate_response(
        query="Search query",
        tools=[{'name': 'search_course_content'}],
        tool_manager=mock_tool_manager
    )
    
    # Should return error message, not raise exception
    assert isinstance(result, str)
    # Error message should be user-friendly
    assert "error" in result.lower() or "apologize" in result.lower()
```

#### 5. Test Early Termination (No Second Round Needed)
```python
def test_early_termination_one_round_sufficient(self, ai_generator, mock_anthropic_client):
    """Test that process terminates early if Claude doesn't need second round"""
    
    tool_use = MockToolUse(
        tool_name="search_course_content",
        tool_input={"query": "Python basics"}
    )
    initial_response = MockAnthropicResponse(
        tool_use=[tool_use],
        stop_reason="tool_use"
    )
    
    # After first tool execution, Claude has enough info
    final_response = MockAnthropicResponse(
        text="Complete answer based on first search",
        stop_reason="end_turn"
    )
    
    mock_anthropic_client.messages.create.side_effect = [initial_response, final_response]
    
    mock_tool_manager = Mock()
    mock_tool_manager.execute_tool.return_value = "Comprehensive search result"
    
    result = ai_generator.generate_response(
        query="What is Python?",
        tools=[{'name': 'search_course_content'}],
        tool_manager=mock_tool_manager
    )
    
    # Should only execute tool once
    assert mock_tool_manager.execute_tool.call_count == 1
    
    # Should only make 2 API calls (initial + follow-up, no second round)
    assert mock_anthropic_client.messages.create.call_count == 2
    
    assert "Complete answer" in result
```

#### 6. Test Logging (Optional, if logging is critical)
```python
def test_logging_tracks_rounds(self, ai_generator, mock_anthropic_client, caplog):
    """Test that logging properly tracks round execution"""
    
    import logging
    caplog.set_level(logging.DEBUG)
    
    # Setup 2-round scenario
    # ... (similar to test_sequential_tool_calling_two_rounds)
    
    # Verify logs contain round information
    assert "Starting tool execution round 1" in caplog.text
    assert "Starting tool execution round 2" in caplog.text
```

### Tests to Update

#### Update: test_generate_response_with_tool_use
- Update assertion to check that tools remain available in follow-up calls
- Verify message history structure

## Test Coverage Summary

### Current Coverage (Before Changes)
- ✅ Initialization
- ✅ Response without tools
- ✅ Response with conversation history
- ✅ Tools available but not used
- ✅ Single tool execution
- ✅ Multiple tools in one round
- ✅ Tool execution with "no results"
- ✅ System prompt structure
- ✅ API parameters

### New Coverage (After Changes)
- ✅ **Sequential 2-round tool calling** (primary feature)
- ✅ **Max rounds enforcement** (stops at 2)
- ✅ **Early termination** (1 round when sufficient)
- ✅ **Tool execution error handling** (graceful degradation)
- ✅ **API error handling** (during rounds)
- ✅ **Forced final response** (when max rounds reached with tool_use)
- ✅ **Response extraction** (text from different formats)
- ✅ **Logging and debugging** (round tracking)

### Coverage Gaps to Consider
- ⚠️ Performance/timeout tests
- ⚠️ Concurrent request handling
- ⚠️ Very large message histories
- ⚠️ Tool execution taking too long
- ⚠️ Malformed tool inputs

## Implementation Checklist

### Code Changes
- [ ] Add MAX_TOOL_ROUNDS constant
- [ ] Add logger setup
- [ ] Update SYSTEM_PROMPT with multi-round guidance
- [ ] Refactor _handle_tool_execution() with loop
- [ ] Add _force_final_text_response() method
- [ ] Add _extract_text_response() method
- [ ] Add _create_error_response() method
- [ ] Add try-except blocks for error handling

### Test Changes
- [ ] Add test_sequential_tool_calling_two_rounds
- [ ] Add test_max_rounds_enforced
- [ ] Add test_tool_execution_error_graceful_handling
- [ ] Add test_api_error_during_tool_round
- [ ] Add test_early_termination_one_round_sufficient
- [ ] Add test_logging_tracks_rounds (optional)
- [ ] Update test_generate_response_with_tool_use

### Documentation
- [ ] Update backend-tool-refactor.md with completion notes
- [ ] Add code comments explaining round logic
- [ ] Document error handling strategy

## Estimated Impact

### Lines of Code
- **Backend changes**: ~120 lines added/modified
- **Test changes**: ~150 lines added
- **Total**: ~270 lines

### Performance
- **Best case**: Same as before (1 API call for non-tool queries)
- **Average case**: 2-3 API calls (up from 1-2)
- **Worst case**: 4 API calls (2 tool rounds + forced final)

### Risk Level
- **Low**: Maintains backward compatibility
- **Low**: Comprehensive error handling
- **Low**: Well-tested with new test suite

## Next Steps

1. Review this plan
2. Approve approach
3. Implement code changes
4. Implement test changes
5. Run full test suite
6. Manual testing with real scenarios
7. Deploy to staging
8. Monitor logs for round usage patterns
