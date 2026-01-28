from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Protocol

from vector_store import SearchResults, VectorStore


class Tool(ABC):
    """Abstract base class for all tools"""

    @abstractmethod
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return Anthropic tool definition for this tool"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool with given parameters"""
        pass


class CourseSearchTool(Tool):
    """Tool for searching course content with semantic course name matching"""

    def __init__(self, vector_store: VectorStore):
        self.store = vector_store
        self.last_sources = []  # Track sources from last search

    def get_tool_definition(self) -> Dict[str, Any]:
        """Return Anthropic tool definition for this tool"""
        return {
            "name": "search_course_content",
            "description": "Search course materials with smart course name matching and lesson filtering",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for in the course content",
                    },
                    "course_name": {
                        "type": "string",
                        "description": "Course title (partial matches work, e.g. 'MCP', 'Introduction')",
                    },
                    "lesson_number": {
                        "type": "integer",
                        "description": "Specific lesson number to search within (e.g. 1, 2, 3)",
                    },
                },
                "required": ["query"],
            },
        }

    def execute(
        self, query: str, course_name: Optional[str] = None, lesson_number: Optional[int] = None
    ) -> str:
        """
        Execute the search tool with given parameters.

        Args:
            query: What to search for
            course_name: Optional course filter
            lesson_number: Optional lesson filter

        Returns:
            Formatted search results or error message
        """

        # Use the vector store's unified search interface
        results = self.store.search(
            query=query, course_name=course_name, lesson_number=lesson_number
        )

        # Handle errors
        if results.error:
            return results.error

        # Handle empty results
        if results.is_empty():
            filter_info = ""
            if course_name:
                filter_info += f" in course '{course_name}'"
            if lesson_number:
                filter_info += f" in lesson {lesson_number}"
            return f"No relevant content found{filter_info}."

        # Format and return results
        return self._format_results(results)

    def _format_results(self, results: SearchResults) -> str:
        """Format search results with course and lesson context"""
        formatted = []
        sources = []  # Track sources for the UI with links

        # Combine documents and metadata for sorting
        combined = list(zip(results.documents, results.metadata))

        # Sort by lesson number (treat None as -1 to put them first)
        combined.sort(
            key=lambda x: x[1].get("lesson_number") if x[1].get("lesson_number") is not None else -1
        )

        for doc, meta in combined:
            course_title = meta.get("course_title", "unknown")
            lesson_num = meta.get("lesson_number")

            # Build context header
            header = f"[{course_title}"
            if lesson_num is not None:
                header += f" - Lesson {lesson_num}"
            header += "]"

            # Build source with text and link
            source_text = course_title
            if lesson_num is not None:
                source_text += f" - Lesson {lesson_num}"

            # Get lesson link from course catalog
            lesson_link = self._get_lesson_link(course_title, lesson_num)

            # Add structured source
            sources.append({"text": source_text, "link": lesson_link})

            formatted.append(f"{header}\n{doc}")

        # Store sources for retrieval
        self.last_sources = sources

        return "\n\n".join(formatted)

    def _get_lesson_link(self, course_title: str, lesson_number: Optional[int]) -> Optional[str]:
        """Retrieve lesson link from course catalog"""
        if lesson_number is None:
            return None

        try:
            import json

            # Query course catalog for this course
            result = self.store.course_catalog.get(ids=[course_title], include=["metadatas"])

            if not result or not result.get("metadatas"):
                return None

            metadata = result["metadatas"][0]
            lessons_json = metadata.get("lessons_json")

            if not lessons_json:
                return None

            # Parse lessons and find matching lesson number
            lessons = json.loads(lessons_json)
            for lesson in lessons:
                if lesson.get("lesson_number") == lesson_number:
                    return lesson.get("lesson_link")

            return None
        except Exception as e:
            # If lookup fails, return None (source will still work without link)
            print(f"Warning: Could not fetch lesson link: {e}")
            return None


class CourseOutlineTool(Tool):
    """Tool for retrieving complete course outlines with lesson details"""

    def __init__(self, vector_store: VectorStore):
        self.store = vector_store

    def get_tool_definition(self) -> Dict[str, Any]:
        """Return Anthropic tool definition for this tool"""
        return {
            "name": "get_course_outline",
            "description": "Get the complete course outline including course title, course link, and all lessons with their numbers and titles. Use this when users ask about course structure, lesson list, or what lessons are available in a course.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "course_name": {
                        "type": "string",
                        "description": "Course title or partial course name to get the outline for",
                    }
                },
                "required": ["course_name"],
            },
        }

    def execute(self, course_name: str) -> str:
        """
        Execute the course outline retrieval.

        Args:
            course_name: Course title or partial name

        Returns:
            Formatted course outline with lessons or error message
        """
        # First, resolve the course name using semantic search
        course_title = self.store._resolve_course_name(course_name)

        if not course_title:
            return f"No course found matching '{course_name}'"

        # Get the complete course metadata
        try:
            import json

            result = self.store.course_catalog.get(ids=[course_title], include=["metadatas"])

            if not result or not result.get("metadatas") or not result["metadatas"]:
                return f"Course metadata not found for '{course_title}'"

            metadata = result["metadatas"][0]

            # Extract course information
            title = metadata.get("title", course_title)
            course_link = metadata.get("course_link", "No link available")
            lessons_json = metadata.get("lessons_json", "[]")

            # Parse lessons
            lessons = json.loads(lessons_json)

            # Format the output
            output = f"**Course:** {title}\n"
            output += f"**Course Link:** {course_link}\n\n"
            output += f"**Course Outline:**\n"

            for lesson in lessons:
                lesson_num = lesson.get("lesson_number", "?")
                lesson_title = lesson.get("lesson_title", "Untitled")
                output += f"- Lesson {lesson_num}: {lesson_title}\n"

            return output

        except Exception as e:
            return f"Error retrieving course outline: {str(e)}"


class ToolManager:
    """Manages available tools for the AI"""

    def __init__(self):
        self.tools = {}

    def register_tool(self, tool: Tool):
        """Register any tool that implements the Tool interface"""
        tool_def = tool.get_tool_definition()
        tool_name = tool_def.get("name")
        if not tool_name:
            raise ValueError("Tool must have a 'name' in its definition")
        self.tools[tool_name] = tool

    def get_tool_definitions(self) -> list:
        """Get all tool definitions for Anthropic tool calling"""
        return [tool.get_tool_definition() for tool in self.tools.values()]

    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool by name with given parameters"""
        if tool_name not in self.tools:
            return f"Tool '{tool_name}' not found"

        return self.tools[tool_name].execute(**kwargs)

    def get_last_sources(self) -> list:
        """Get sources from the last search operation"""
        # Check all tools for last_sources attribute
        for tool in self.tools.values():
            if hasattr(tool, "last_sources") and tool.last_sources:
                return tool.last_sources
        return []

    def reset_sources(self):
        """Reset sources from all tools that track sources"""
        for tool in self.tools.values():
            if hasattr(tool, "last_sources"):
                tool.last_sources = []
