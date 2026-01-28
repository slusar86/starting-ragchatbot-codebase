"""
API Endpoint Tests for FastAPI Application

Tests the FastAPI endpoints (/api/query, /api/courses, /api/clear-session)
for proper request/response handling.

To avoid issues with static file mounting in the test environment,
we create a test app with only the API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Union, Dict
from unittest.mock import Mock, patch


# ============================================================================
# Pydantic Models (duplicated from app.py for test isolation)
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for course queries"""
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for course queries"""
    answer: str
    sources: List[Union[str, Dict[str, Optional[str]]]]
    session_id: str


class CourseStats(BaseModel):
    """Response model for course statistics"""
    total_courses: int
    course_titles: List[str]


class ClearSessionRequest(BaseModel):
    """Request model for clearing a session"""
    session_id: str


# ============================================================================
# Test Application Factory
# ============================================================================

def create_test_app(mock_rag_system):
    """
    Create a test FastAPI app with only API endpoints.
    This avoids the static file mounting issue in the test environment.
    """
    app = FastAPI(title="Test Course Materials RAG System")
    
    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        """Process a query and return response with sources"""
        try:
            session_id = request.session_id
            if not session_id:
                session_id = mock_rag_system.session_manager.create_session()
            
            answer, sources = mock_rag_system.query(request.query, session_id)
            
            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        """Get course analytics and statistics"""
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/clear-session")
    async def clear_session(request: ClearSessionRequest):
        """Clear a conversation session"""
        try:
            mock_rag_system.session_manager.clear_session(request.session_id)
            return {"success": True, "message": "Session cleared"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return app


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def test_client(mock_rag_system):
    """Create a test client with mocked RAG system"""
    app = create_test_app(mock_rag_system)
    return TestClient(app)


# ============================================================================
# Test /api/query Endpoint
# ============================================================================

@pytest.mark.api
class TestQueryEndpoint:
    """Tests for the /api/query endpoint"""
    
    def test_query_without_session_id(self, test_client, sample_query, mock_rag_system):
        """Test query endpoint creates a session when none provided"""
        response = test_client.post(
            "/api/query",
            json={"query": sample_query}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] == "test-session-123"
        
        # Verify RAG system was called
        mock_rag_system.query.assert_called_once()
    
    def test_query_with_session_id(self, test_client, sample_query, sample_session_id, mock_rag_system):
        """Test query endpoint uses provided session ID"""
        response = test_client.post(
            "/api/query",
            json={"query": sample_query, "session_id": sample_session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["session_id"] == sample_session_id
        mock_rag_system.query.assert_called_with(sample_query, sample_session_id)
    
    def test_query_with_empty_query(self, test_client):
        """Test query endpoint with empty query string"""
        response = test_client.post(
            "/api/query",
            json={"query": ""}
        )
        
        # Should still process (validation happens at RAG level)
        assert response.status_code in [200, 422]
    
    def test_query_missing_required_field(self, test_client):
        """Test query endpoint with missing required query field"""
        response = test_client.post(
            "/api/query",
            json={"session_id": "test-123"}
        )
        
        assert response.status_code == 422  # Validation error
        assert "query" in response.text.lower()
    
    def test_query_with_invalid_json(self, test_client):
        """Test query endpoint with malformed JSON"""
        response = test_client.post(
            "/api/query",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_query_response_structure(self, test_client, sample_query, mock_rag_system):
        """Test query response has correct structure"""
        response = test_client.post(
            "/api/query",
            json={"query": sample_query}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["session_id"], str)
        
        # Validate sources structure
        if data["sources"]:
            source = data["sources"][0]
            if isinstance(source, dict):
                assert "course" in source or "similarity" in source
    
    def test_query_error_handling(self, test_client, sample_query, mock_rag_system):
        """Test query endpoint handles RAG system errors"""
        # Make RAG system raise an exception
        mock_rag_system.query.side_effect = Exception("RAG system error")
        
        response = test_client.post(
            "/api/query",
            json={"query": sample_query}
        )
        
        assert response.status_code == 500
        assert "RAG system error" in response.text


# ============================================================================
# Test /api/courses Endpoint
# ============================================================================

@pytest.mark.api
class TestCoursesEndpoint:
    """Tests for the /api/courses endpoint"""
    
    def test_get_courses_success(self, test_client, mock_rag_system):
        """Test courses endpoint returns correct data"""
        response = test_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_courses" in data
        assert "course_titles" in data
        assert data["total_courses"] == 2
        assert len(data["course_titles"]) == 2
        
        # Verify RAG system was called
        mock_rag_system.get_course_analytics.assert_called_once()
    
    def test_get_courses_response_structure(self, test_client):
        """Test courses response has correct structure"""
        response = test_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)
        assert all(isinstance(title, str) for title in data["course_titles"])
    
    def test_get_courses_empty_result(self, test_client, mock_rag_system):
        """Test courses endpoint with no courses"""
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }
        
        response = test_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []
    
    def test_get_courses_error_handling(self, test_client, mock_rag_system):
        """Test courses endpoint handles errors"""
        mock_rag_system.get_course_analytics.side_effect = Exception("Database error")
        
        response = test_client.get("/api/courses")
        
        assert response.status_code == 500
        assert "Database error" in response.text
    
    def test_get_courses_wrong_method(self, test_client):
        """Test courses endpoint rejects POST requests"""
        response = test_client.post("/api/courses")
        
        assert response.status_code == 405  # Method not allowed


# ============================================================================
# Test /api/clear-session Endpoint
# ============================================================================

@pytest.mark.api
class TestClearSessionEndpoint:
    """Tests for the /api/clear-session endpoint"""
    
    def test_clear_session_success(self, test_client, sample_session_id, mock_rag_system):
        """Test clear session endpoint works correctly"""
        response = test_client.post(
            "/api/clear-session",
            json={"session_id": sample_session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "message" in data
        
        # Verify session manager was called
        mock_rag_system.session_manager.clear_session.assert_called_once_with(sample_session_id)
    
    def test_clear_session_missing_session_id(self, test_client):
        """Test clear session endpoint with missing session_id"""
        response = test_client.post(
            "/api/clear-session",
            json={}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_clear_session_invalid_session_id(self, test_client, mock_rag_system):
        """Test clear session with invalid session ID"""
        mock_rag_system.session_manager.clear_session.side_effect = KeyError("Session not found")
        
        response = test_client.post(
            "/api/clear-session",
            json={"session_id": "invalid-session"}
        )
        
        assert response.status_code == 500
    
    def test_clear_session_error_handling(self, test_client, mock_rag_system):
        """Test clear session endpoint handles errors"""
        mock_rag_system.session_manager.clear_session.side_effect = Exception("Clear failed")
        
        response = test_client.post(
            "/api/clear-session",
            json={"session_id": "test-session"}
        )
        
        assert response.status_code == 500
        assert "Clear failed" in response.text


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for API endpoints"""
    
    def test_full_conversation_flow(self, test_client, mock_rag_system):
        """Test a complete conversation flow"""
        # Step 1: Query without session
        response1 = test_client.post(
            "/api/query",
            json={"query": "What is Course 1 about?"}
        )
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]
        
        # Step 2: Follow-up query with session
        response2 = test_client.post(
            "/api/query",
            json={"query": "Tell me more", "session_id": session_id}
        )
        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id
        
        # Step 3: Get course stats
        response3 = test_client.get("/api/courses")
        assert response3.status_code == 200
        
        # Step 4: Clear session
        response4 = test_client.post(
            "/api/clear-session",
            json={"session_id": session_id}
        )
        assert response4.status_code == 200
    
    def test_concurrent_sessions(self, test_client, mock_rag_system):
        """Test handling multiple sessions"""
        # Create first session
        response1 = test_client.post(
            "/api/query",
            json={"query": "Query 1"}
        )
        session1 = response1.json()["session_id"]
        
        # Modify mock to return different session ID
        mock_rag_system.session_manager.create_session.return_value = "test-session-456"
        
        # Create second session
        response2 = test_client.post(
            "/api/query",
            json={"query": "Query 2"}
        )
        session2 = response2.json()["session_id"]
        
        # Sessions should be different
        assert session1 != session2
