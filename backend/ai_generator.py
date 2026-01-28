import logging
from typing import Any, Dict, List, Optional

import anthropic


class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""

    # Configuration constants
    MAX_TOOL_ROUNDS = 2

    # Setup logger
    logger = logging.getLogger(__name__)

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive search tools for course information.

Available Tools:
1. **search_course_content**: Search for specific content within course materials
   - Use for detailed questions about course topics, concepts, or specific lessons
   
2. **get_course_outline**: Retrieve complete course structure with all lessons
   - Use for questions about course structure, lesson lists, or what's covered in a course
   - Always returns: course title, course link, and complete list of lessons with numbers and titles

Tool Usage Guidelines:
- Use tools **only** for questions about specific course content or course structure
- **Multi-round capability**: You can make up to 2 sequential tool calls
  * First round: Get initial information or context
  * Second round (if needed): Make additional searches based on first results
- After receiving tool results, evaluate if additional searches are needed
- Synthesize tool results into accurate, fact-based responses
- If tool yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without searching
- **Course-specific questions**: Use appropriate tool first, then answer
- **Course outline queries**: Use get_course_outline tool to return course title, course link, and all lessons with numbers and titles
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, search explanations, or question-type analysis
 - Do not mention "based on the search results" or tool names


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {"model": self.model, "temperature": 0, "max_tokens": 800}

    def generate_response(
        self,
        query: str,
        conversation_history: Optional[str] = None,
        tools: Optional[List] = None,
        tool_manager=None,
    ) -> str:
        """
        Generate AI response with optional tool usage and conversation context.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """

        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content,
        }

        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}

        # Get response from Claude
        response = self.client.messages.create(**api_params)

        # Handle tool execution if needed
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_tool_execution(response, api_params, tool_manager)

        # Return direct response
        return response.content[0].text

    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        Handle up to 2 rounds of sequential tool execution with comprehensive error handling.

        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters including tools
            tool_manager: Manager to execute tools

        Returns:
            Final response text after tool execution
        """
        messages = base_params["messages"].copy()
        current_response = initial_response

        try:
            # Loop for up to MAX_TOOL_ROUNDS
            for round_num in range(1, self.MAX_TOOL_ROUNDS + 1):
                self.logger.debug(
                    f"Starting tool execution round {round_num}/{self.MAX_TOOL_ROUNDS}"
                )

                # Add assistant's response (with tool_use blocks) to messages
                messages.append({"role": "assistant", "content": current_response.content})

                # Execute all tool calls in this round
                tool_results = []
                for content_block in current_response.content:
                    if content_block.type == "tool_use":
                        try:
                            # Execute tool with error protection
                            tool_result = tool_manager.execute_tool(
                                content_block.name, **content_block.input
                            )

                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": content_block.id,
                                    "content": tool_result,
                                }
                            )

                            self.logger.debug(f"Round {round_num}: Executed {content_block.name}")

                        except Exception as tool_error:
                            # Handle individual tool failures gracefully
                            error_msg = f"Tool execution failed: {str(tool_error)}"
                            self.logger.error(f"Round {round_num}: {error_msg}")

                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": content_block.id,
                                    "content": error_msg,
                                    "is_error": True,
                                }
                            )

                # Check if any tools were executed
                if not tool_results:
                    self.logger.warning(
                        f"Round {round_num}: No tools executed despite tool_use stop_reason"
                    )
                    break

                # Add tool results to messages
                messages.append({"role": "user", "content": tool_results})

                # Prepare next API call WITH tools still available (KEY FIX)
                next_params = {
                    **self.base_params,
                    "messages": messages,
                    "system": base_params["system"],
                    "tools": base_params.get("tools"),  # Keep tools available
                    "tool_choice": {"type": "auto"},
                }

                try:
                    # Make next API call
                    current_response = self.client.messages.create(**next_params)
                    self.logger.debug(
                        f"Round {round_num}: API call successful, stop_reason={current_response.stop_reason}"
                    )

                except Exception as api_error:
                    # Handle API call failures
                    self.logger.error(f"Round {round_num}: API call failed: {str(api_error)}")
                    return self._create_error_response(
                        f"API error in round {round_num}: {str(api_error)}"
                    )

                # Check if Claude wants to make more tool calls
                if current_response.stop_reason != "tool_use":
                    # No more tool calls needed - return final text response
                    self.logger.debug(
                        f"Round {round_num}: Conversation complete (stop_reason={current_response.stop_reason})"
                    )
                    break

                # If we've reached max rounds and Claude still wants tools
                if round_num == self.MAX_TOOL_ROUNDS:
                    self.logger.warning(
                        f"Max rounds ({self.MAX_TOOL_ROUNDS}) reached, forcing final response"
                    )
                    # Execute remaining tools and force text response
                    return self._force_final_text_response(
                        current_response, messages, base_params, tool_manager
                    )

            # Extract and return final text response
            return self._extract_text_response(current_response)

        except Exception as unexpected_error:
            # Catch-all for unexpected errors
            self.logger.exception(
                f"Unexpected error in multi-round tool execution: {unexpected_error}"
            )
            return self._create_error_response(f"Unexpected error: {str(unexpected_error)}")

    def _force_final_text_response(
        self, last_response, messages: List[Dict], base_params: Dict[str, Any], tool_manager
    ) -> str:
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
                            content_block.name, **content_block.input
                        )
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": tool_result,
                            }
                        )
                    except Exception as e:
                        self.logger.error(f"Final tool execution failed: {e}")
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": f"Error: {str(e)}",
                                "is_error": True,
                            }
                        )

            # Add tool results
            if tool_results:
                messages.append({"role": "user", "content": tool_results})

            # Make final API call WITHOUT tools to force text response
            final_params = {
                **self.base_params,
                "messages": messages,
                "system": base_params["system"],
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
                    if hasattr(block, "text") and block.text:
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
