"""
MCP tools for Cloud SQL and Redis integration with Google ADK agents.

This module provides function tools that can be used by agents to interact
with the database and cache.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

try:
    from google.adk.tools import FunctionTool
except ImportError:
    print("Warning: Google ADK tools not available. Install with: pip install google-adk")
    FunctionTool = None

from .database import db_manager
from .redis_client import redis_manager
from .models import (
    SessionCreate, SessionUpdate, RequirementCreate, RequirementUpdate,
    TestCaseCreate, TestCaseUpdate, TestSuite
)


class MCPTools:
    """MCP tools for database and cache operations."""

    def __init__(self):
        """Initialize MCP tools."""
        self.db_manager = db_manager
        self.redis_manager = redis_manager
        self._initialized = False

    async def initialize(self):
        """Initialize database and Redis connections."""
        if not self._initialized:
            await self.db_manager.initialize()
            try:
                await self.redis_manager.initialize()
            except Exception as e:
                print(f"Warning: Could not initialize Redis: {e}")
            self._initialized = True

    async def close(self):
        """Close connections."""
        await self.db_manager.close()
        await self.redis_manager.close()
        self._initialized = False

    # Session management tools
    async def create_session_tool(
        self,
        session_id: str,
        user_id: str,
        project_name: Optional[str] = None,
        user_prompt: Optional[str] = None,
        agent_used: str = "sequential_workflow",
        workflow_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Create a new session in the database.

        Args:
            session_id: Unique session identifier
            user_id: User identifier
            project_name: Optional project name
            user_prompt: Initial user prompt
            agent_used: Agent type used
            workflow_type: Type of workflow

        Returns:
            Dictionary with session creation result
        """
        try:
            await self.initialize()

            session_data = SessionCreate(
                session_id=session_id,
                user_id=user_id,
                project_name=project_name,
                user_prompt=user_prompt,
                agent_used=agent_used,
                workflow_type=workflow_type
            )

            session = await self.db_manager.create_session(session_data)

            # Cache the session
            session_dict = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "project_name": session.project_name,
                "user_prompt": session.user_prompt,
                "status": session.status,
                "agent_used": session.agent_used,
                "workflow_type": session.workflow_type,
                "created_at": session.created_at.isoformat()
            }

            await self.redis_manager.cache_session(session_id, session_dict)

            return {
                "success": True,
                "session_id": session.session_id,
                "status": session.status,
                "created_at": session.created_at.isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_session_tool(self, session_id: str) -> Dict[str, Any]:
        """
        Get session by ID, checking cache first.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with session data or error
        """
        try:
            await self.initialize()

            # Try cache first
            cached_session = await self.redis_manager.get_cached_session(session_id)
            if cached_session:
                return {
                    "success": True,
                    "source": "cache",
                    "session": cached_session
                }

            # Get from database
            session = await self.db_manager.get_session_by_id(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }

            session_dict = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "project_name": session.project_name,
                "user_prompt": session.user_prompt,
                "status": session.status,
                "rag_context_loaded": session.rag_context_loaded,
                "rag_enabled": session.rag_enabled,
                "agent_used": session.agent_used,
                "workflow_type": session.workflow_type,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat()
            }

            # Cache for future use
            await self.redis_manager.cache_session(session_id, session_dict)

            return {
                "success": True,
                "source": "database",
                "session": session_dict
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def update_session_status_tool(self, session_id: str, status: str) -> Dict[str, Any]:
        """
        Update session status.

        Args:
            session_id: Session identifier
            status: New status

        Returns:
            Dictionary with update result
        """
        try:
            await self.initialize()

            session_update = SessionUpdate(status=status)
            updated_session = await self.db_manager.update_session(session_id, session_update)

            if not updated_session:
                return {
                    "success": False,
                    "error": "Session not found"
                }

            # Invalidate cache
            await self.redis_manager.invalidate_session(session_id)

            return {
                "success": True,
                "session_id": session_id,
                "status": updated_session.status,
                "updated_at": updated_session.updated_at.isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # Requirements management tools
    async def create_requirement_tool(
        self,
        session_id: str,
        requirement_content: str,
        requirement_type: str = "functional",
        priority: str = "medium",
        source: str = "agent_generated"
    ) -> Dict[str, Any]:
        """
        Create a new requirement.

        Args:
            session_id: Session identifier
            requirement_content: Requirement text content
            requirement_type: Type of requirement
            priority: Priority level
            source: Source of requirement

        Returns:
            Dictionary with requirement creation result
        """
        try:
            await self.initialize()

            requirement_id = f"{session_id}_req_{uuid.uuid4().hex[:8]}"

            requirement_data = RequirementCreate(
                id=requirement_id,
                session_id=session_id,
                original_content=requirement_content,
                requirement_type=requirement_type,
                priority=priority,
                source=source
            )

            requirement = await self.db_manager.create_requirement(requirement_data)

            # Invalidate requirements cache for this session
            await self.redis_manager.delete(f"requirements:{session_id}")

            return {
                "success": True,
                "requirement_id": requirement.id,
                "session_id": requirement.session_id,
                "requirement_type": requirement.requirement_type,
                "priority": requirement.priority,
                "created_at": requirement.created_at.isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def update_requirement_tool(
        self,
        requirement_id: str,
        edited_content: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a requirement.

        Args:
            requirement_id: Requirement identifier
            edited_content: Updated requirement content
            priority: Updated priority
            status: Updated status

        Returns:
            Dictionary with update result
        """
        try:
            await self.initialize()

            update_data = RequirementUpdate(
                edited_content=edited_content,
                priority=priority,
                status=status
            )

            updated_requirement = await self.db_manager.update_requirement(requirement_id, update_data)

            if not updated_requirement:
                return {
                    "success": False,
                    "error": "Requirement not found"
                }

            # Invalidate cache
            await self.redis_manager.delete(f"requirements:{updated_requirement.session_id}")

            return {
                "success": True,
                "requirement_id": updated_requirement.id,
                "session_id": updated_requirement.session_id,
                "updated_at": updated_requirement.updated_at.isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_session_requirements_tool(self, session_id: str) -> Dict[str, Any]:
        """
        Get all requirements for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with requirements list
        """
        try:
            await self.initialize()

            # Try cache first
            cached_requirements = await self.redis_manager.get_cached_requirements(session_id)
            if cached_requirements:
                return {
                    "success": True,
                    "source": "cache",
                    "requirements": cached_requirements,
                    "count": len(cached_requirements)
                }

            # Get from database
            requirements = await self.db_manager.get_requirements_by_session(session_id)

            requirements_list = [
                {
                    "id": req.id,
                    "original_content": req.original_content,
                    "edited_content": req.edited_content,
                    "requirement_type": req.requirement_type,
                    "priority": req.priority,
                    "status": req.status,
                    "version": req.version,
                    "source": req.source,
                    "tags": req.tags,
                    "created_at": req.created_at.isoformat(),
                    "updated_at": req.updated_at.isoformat()
                }
                for req in requirements
            ]

            # Cache for future use
            await self.redis_manager.cache_requirements(session_id, requirements_list)

            return {
                "success": True,
                "source": "database",
                "requirements": requirements_list,
                "count": len(requirements_list)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # Test case management tools
    async def create_test_cases_from_suite_tool(
        self,
        session_id: str,
        test_suite_json: str
    ) -> Dict[str, Any]:
        """
        Create test cases from a structured test suite JSON.

        Args:
            session_id: Session identifier
            test_suite_json: JSON string containing the test suite

        Returns:
            Dictionary with test case creation results
        """
        try:
            await self.initialize()

            # Parse the test suite JSON
            test_suite_data = json.loads(test_suite_json)

            # Extract test_suite from the JSON if it's wrapped
            if "test_suite" in test_suite_data:
                test_suite_data = test_suite_data["test_suite"]

            test_suite = TestSuite(**test_suite_data)

            # Create test cases
            test_cases = await self.db_manager.create_test_cases_from_suite(session_id, test_suite)

            # Invalidate test cases cache
            await self.redis_manager.delete(f"test_cases:{session_id}")

            return {
                "success": True,
                "session_id": session_id,
                "test_suite_name": test_suite.name,
                "test_cases_created": len(test_cases),
                "test_case_ids": [tc.id for tc in test_cases]
            }

        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON format: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_session_test_cases_tool(self, session_id: str, as_suite: bool = False) -> Dict[str, Any]:
        """
        Get test cases for a session.

        Args:
            session_id: Session identifier
            as_suite: Whether to return in test suite format

        Returns:
            Dictionary with test cases
        """
        try:
            await self.initialize()

            if as_suite:
                # Return as structured test suite
                test_suite = await self.db_manager.get_test_cases_as_suite(session_id)

                if not test_suite:
                    return {
                        "success": False,
                        "error": "No test cases found for session"
                    }

                return {
                    "success": True,
                    "session_id": session_id,
                    "test_suite": test_suite.dict()
                }
            else:
                # Try cache first
                cached_test_cases = await self.redis_manager.get_cached_test_cases(session_id)
                if cached_test_cases:
                    return {
                        "success": True,
                        "source": "cache",
                        "test_cases": cached_test_cases,
                        "count": len(cached_test_cases)
                    }

                # Get from database
                test_cases = await self.db_manager.get_test_cases_by_session(session_id)

                test_cases_list = [
                    {
                        "id": tc.id,
                        "test_name": tc.test_name,
                        "test_description": tc.test_description,
                        "test_steps": tc.test_steps,
                        "expected_results": tc.expected_results,
                        "test_type": tc.test_type,
                        "priority": tc.priority,
                        "status": tc.status,
                        "test_data": tc.test_data,
                        "preconditions": tc.preconditions,
                        "test_id": tc.test_id,
                        "summary": tc.summary,
                        "requirement_traceability": tc.requirement_traceability,
                        "created_at": tc.created_at.isoformat(),
                        "updated_at": tc.updated_at.isoformat()
                    }
                    for tc in test_cases
                ]

                # Cache for future use
                await self.redis_manager.cache_test_cases(session_id, test_cases_list)

                return {
                    "success": True,
                    "source": "database",
                    "test_cases": test_cases_list,
                    "count": len(test_cases_list)
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # Workflow tracking tools
    async def track_workflow_step_tool(
        self,
        session_id: str,
        step_name: str,
        step_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track a workflow step execution.

        Args:
            session_id: Session identifier
            step_name: Name of the workflow step
            step_result: Result data from the step

        Returns:
            Dictionary with tracking result
        """
        try:
            await self.initialize()

            success = await self.redis_manager.track_workflow_step(session_id, step_name, step_result)

            return {
                "success": success,
                "session_id": session_id,
                "step": step_name,
                "tracked_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_session_with_full_context_tool(self, session_id: str) -> Dict[str, Any]:
        """
        Get session with all related requirements and test cases.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with complete session context
        """
        try:
            await self.initialize()

            context = await self.db_manager.get_session_with_context(session_id)

            if not context:
                return {
                    "success": False,
                    "error": "Session not found"
                }

            return {
                "success": True,
                "context": context
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Create MCP tools instance
mcp_tools = MCPTools()


def create_function_tools() -> List[Any]:
    """Create Google ADK function tools for MCP operations."""
    if FunctionTool is None:
        print("Warning: Google ADK not available, returning empty tools list")
        return []

    tools = [
        FunctionTool(
            func=mcp_tools.create_session_tool,
            name="create_session",
            description="Create a new session in the database for tracking agent workflow"
        ),
        FunctionTool(
            func=mcp_tools.get_session_tool,
            name="get_session",
            description="Get session data by ID, checking cache first"
        ),
        FunctionTool(
            func=mcp_tools.update_session_status_tool,
            name="update_session_status",
            description="Update the status of an existing session"
        ),
        FunctionTool(
            func=mcp_tools.create_requirement_tool,
            name="create_requirement",
            description="Create a new requirement for a session"
        ),
        FunctionTool(
            func=mcp_tools.update_requirement_tool,
            name="update_requirement",
            description="Update an existing requirement with edited content"
        ),
        FunctionTool(
            func=mcp_tools.get_session_requirements_tool,
            name="get_session_requirements",
            description="Get all requirements for a session"
        ),
        FunctionTool(
            func=mcp_tools.create_test_cases_from_suite_tool,
            name="create_test_cases_from_suite",
            description="Create test cases from a structured test suite JSON"
        ),
        FunctionTool(
            func=mcp_tools.get_session_test_cases_tool,
            name="get_session_test_cases",
            description="Get test cases for a session, optionally as structured test suite"
        ),
        FunctionTool(
            func=mcp_tools.track_workflow_step_tool,
            name="track_workflow_step",
            description="Track execution of a workflow step"
        ),
        FunctionTool(
            func=mcp_tools.get_session_with_full_context_tool,
            name="get_session_with_full_context",
            description="Get session with all related requirements and test cases"
        )
    ]

    return tools