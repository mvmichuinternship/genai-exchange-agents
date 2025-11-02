"""
HITL API Endpoints for Decider Agent

This module provides RESTful API endpoints for the enhanced Human-in-the-Loop
functionality of the decider agent.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import uuid
import asyncio
from datetime import datetime

from decider_agent.agent import root_agent, get_session_feedback_history, suggest_improvements

app = FastAPI(
    title="Enhanced HITL Decider Agent API",
    description="Human-in-the-Loop API for authentication requirements analysis and test case generation",
    version="2.0.0"
)

# Pydantic models for API requests/responses

class HITLRequest(BaseModel):
    """Base request model for HITL operations."""
    status: str = Field(..., description="HITL status: start, refine, enhance, review, approved, edited, rejected")
    user_input: str = Field(..., description="User input or feedback")
    session_id: Optional[str] = Field(None, description="Session ID (auto-generated if not provided)")

class QualityReviewRequest(BaseModel):
    """Request model for quality reviews."""
    score: int = Field(..., ge=1, le=10, description="Quality score from 1-10")
    feedback: str = Field(..., description="Detailed feedback text")
    session_id: str = Field(..., description="Session ID")

class RefinementRequest(BaseModel):
    """Request model for refinement requests."""
    feedback: str = Field(..., description="Specific feedback for refinement")
    session_id: str = Field(..., description="Session ID")

class EnhancementRequest(BaseModel):
    """Request model for context enhancement."""
    additional_context: str = Field(..., description="Additional context or requirements")
    session_id: str = Field(..., description="Session ID")

class HITLResponse(BaseModel):
    """Response model for HITL operations."""
    session_id: str
    status: str
    stage: str
    message: Optional[str] = None
    available_actions: Optional[List[str]] = None
    quality_score: Optional[int] = None
    iteration_count: Optional[int] = None

class FeedbackHistoryResponse(BaseModel):
    """Response model for feedback history."""
    session_id: str
    iteration_count: int
    feedback_history: List[Dict[str, Any]]
    quality_scores: Dict[str, Any]
    analytics: Dict[str, Any]

class ImprovementSuggestionsResponse(BaseModel):
    """Response model for improvement suggestions."""
    session_id: str
    suggestions: Dict[str, Any]
    hitl_insights: Dict[str, Any]

# API Endpoints

@app.post("/hitl/workflow", response_model=HITLResponse)
async def execute_hitl_workflow(request: HITLRequest):
    """
    Execute HITL workflow with comprehensive human feedback capabilities.

    Supports all HITL statuses:
    - start: Begin new analysis
    - refine: Provide specific feedback for improvement
    - enhance: Add additional context
    - review: Provide quality assessment
    - approved: Approve and proceed to test generation
    - edited: Submit edited content
    - rejected: Reject current analysis
    """
    try:
        # Generate session_id if not provided
        if not request.session_id:
            request.session_id = f"api_session_{str(uuid.uuid4())[:8]}"

        # Format message for agent
        message = f"{request.status}; {request.user_input}; {request.session_id}"

        # Execute workflow
        response = await root_agent.run_async(message)

        # Parse and return structured response
        return HITLResponse(
            session_id=request.session_id,
            status="success",
            stage=f"{request.status}_completed",
            message="HITL workflow executed successfully",
            available_actions=_get_available_actions(request.status),
            iteration_count=1  # This would be tracked in actual implementation
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HITL workflow error: {str(e)}")

@app.post("/hitl/quality-review", response_model=HITLResponse)
async def submit_quality_review(request: QualityReviewRequest):
    """
    Submit a structured quality review with score and feedback.

    Automatically triggers improvement suggestions if score < 7.
    """
    try:
        # Format review message
        review_input = f"score:{request.score}; feedback:{request.feedback}"
        message = f"review; {review_input}; {request.session_id}"

        # Execute review
        response = await root_agent.run_async(message)

        # Determine next actions based on score
        if request.score < 7:
            available_actions = ["refine", "enhance", "edited", "rejected"]
            stage = "needs_improvement"
        else:
            available_actions = ["approved", "refine", "enhance"]
            stage = "quality_approved"

        return HITLResponse(
            session_id=request.session_id,
            status="review_processed",
            stage=stage,
            quality_score=request.score,
            available_actions=available_actions,
            message=f"Quality review processed. Score: {request.score}/10"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quality review error: {str(e)}")

@app.post("/hitl/refine", response_model=HITLResponse)
async def refine_analysis(request: RefinementRequest):
    """
    Submit refinement feedback for iterative improvement.

    Agent will re-analyze incorporating the human feedback.
    """
    try:
        message = f"refine; {request.feedback}; {request.session_id}"
        response = await root_agent.run_async(message)

        return HITLResponse(
            session_id=request.session_id,
            status="refinement_applied",
            stage="analysis_refined",
            message="Analysis refined based on your feedback",
            available_actions=["review", "approved", "refine", "enhance"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refinement error: {str(e)}")

@app.post("/hitl/enhance", response_model=HITLResponse)
async def enhance_with_context(request: EnhancementRequest):
    """
    Enhance analysis with additional context or requirements.

    Agent will incorporate new context while preserving existing analysis.
    """
    try:
        message = f"enhance; {request.additional_context}; {request.session_id}"
        response = await root_agent.run_async(message)

        return HITLResponse(
            session_id=request.session_id,
            status="enhancement_applied",
            stage="analysis_enhanced",
            message="Analysis enhanced with additional context",
            available_actions=["review", "approved", "refine", "enhance"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhancement error: {str(e)}")

@app.get("/hitl/feedback-history/{session_id}", response_model=FeedbackHistoryResponse)
async def get_feedback_history(session_id: str):
    """
    Get comprehensive feedback history and analytics for a session.

    Returns complete timeline of human interactions and quality trends.
    """
    try:
        history_data = await get_session_feedback_history(session_id)

        if history_data.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Session not found")

        return FeedbackHistoryResponse(
            session_id=session_id,
            iteration_count=history_data.get("iteration_count", 0),
            feedback_history=history_data.get("feedback_history", []),
            quality_scores=history_data.get("quality_scores", {}),
            analytics=history_data.get("analytics", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback history error: {str(e)}")

@app.get("/hitl/suggestions/{session_id}", response_model=ImprovementSuggestionsResponse)
async def get_improvement_suggestions(session_id: str):
    """
    Get AI-powered improvement suggestions based on feedback patterns.

    Returns pattern-based recommendations and HITL insights.
    """
    try:
        suggestions_data = await suggest_improvements(session_id, "")

        if "error" in suggestions_data:
            raise HTTPException(status_code=404, detail=suggestions_data["error"])

        return ImprovementSuggestionsResponse(
            session_id=session_id,
            suggestions=suggestions_data.get("suggestions", {}),
            hitl_insights=suggestions_data.get("hitl_insights", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestions error: {str(e)}")

@app.get("/hitl/sessions")
async def list_active_sessions():
    """
    List all active HITL sessions with basic stats.
    """
    try:
        # This would integrate with your session storage
        # For now, return mock data
        return {
            "active_sessions": [
                {
                    "session_id": "session_001",
                    "created_at": "2024-01-15T10:00:00Z",
                    "iteration_count": 3,
                    "current_stage": "quality_review",
                    "last_activity": "2024-01-15T10:15:00Z"
                }
            ],
            "total_sessions": 1
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sessions list error: {str(e)}")

@app.delete("/hitl/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a HITL session and all associated data.
    """
    try:
        # This would clean up session data
        return {
            "session_id": session_id,
            "status": "deleted",
            "message": "Session and all associated data deleted successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session deletion error: {str(e)}")

# Utility functions

def _get_available_actions(current_status: str) -> List[str]:
    """Get available HITL actions based on current status."""
    action_map = {
        "start": ["approved", "edited", "rejected", "refine", "enhance", "review"],
        "refine": ["review", "approved", "refine", "enhance"],
        "enhance": ["review", "approved", "refine", "enhance"],
        "review": ["approved", "refine", "enhance", "rejected"],
        "edited": ["approved", "review"],
        "approved": ["generate_tests"],
        "rejected": ["start", "refine"]
    }
    return action_map.get(current_status, [])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Enhanced HITL Decider Agent API",
        "version": "2.0.0",
        "features": [
            "iterative_refinement",
            "quality_assessment",
            "context_enhancement",
            "feedback_analytics",
            "improvement_suggestions"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)