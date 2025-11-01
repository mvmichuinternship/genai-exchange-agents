"""
ADK Function Tools for Google's GenAI MCP Toolbox.

Provides Google ADK function tools that wrap the ToolboxClient for easy integration
with ADK agents.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

try:
    from google.adk.core import tool
except ImportError:
    # Mock decorator for development without ADK
    def tool(name: str = None, description: str = None):
        def decorator(func):
            func._tool_name = name
            func._tool_description = description
            return func
        return decorator

from .client import ToolboxClient, create_toolbox_client
from .models import Session, Requirement, TestCase, SessionContext


class ADKToolboxTools:
    """ADK function tools for Toolbox integration."""

    def __init__(self, server_url: str = "http://localhost:5000"):
        """Initialize with Toolbox server URL."""
        self.server_url = server_url
        self.logger = logging.getLogger(__name__)

    @tool(
        name="create_toolbox_session",
        description="Create a new agent session for workflow tracking and persistence"
    )
    async def create_session(self, user_id: str, user_prompt: str, project_name: str = None) -> Dict[str, Any]:
        """
        Create a new agent session.

        Args:
            user_id: User identifier for the session
            user_prompt: Initial user prompt that started the session
            project_name: Optional project name for organization

        Returns:
            Dictionary containing session details
        """
        try:
            async with create_toolbox_client(self.server_url) as client:
                session = await client.create_session(user_id, user_prompt, project_name)
                return {
                    "success": True,
                    "session_id": str(session.session_id),
                    "user_id": session.user_id,
                    "project_name": session.project_name,
                    "status": session.status,
                    "created_at": session.created_at.isoformat() if session.created_at else None
                }
        except Exception as e:
            self.logger.error(f"Error creating session: {e}")
            return {"success": False, "error": str(e)}

    @tool(
        name="get_toolbox_session",
        description="Retrieve session details by session ID"
    )
    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get session details.

        Args:
            session_id: Session UUID to retrieve

        Returns:
            Dictionary containing session details or error
        """
        try:
            async with create_toolbox_client(self.server_url) as client:
                session = await client.get_session(session_id)
                if session:
                    return {
                        "success": True,
                        "session": session.to_dict()
                    }
                else:
                    return {"success": False, "error": "Session not found"}
        except Exception as e:
            self.logger.error(f"Error getting session: {e}")
            return {"success": False, "error": str(e)}

    @tool(
        name="store_toolbox_requirement",
        description="Store a requirement analysis for a session"
    )
    async def store_requirement(self, session_id: str, content: str, requirement_type: str = "functional",
                              priority: str = "medium") -> Dict[str, Any]:
        """
        Store a requirement for a session.

        Args:
            session_id: Session UUID
            content: Requirement content text
            requirement_type: Type of requirement (functional, non-functional, security, etc.)
            priority: Priority level (low, medium, high, critical)

        Returns:
            Dictionary containing requirement details or error
        """
        try:
            async with create_toolbox_client(self.server_url) as client:
                requirement = await client.store_requirement(session_id, content, requirement_type, priority)
                return {
                    "success": True,
                    "requirement_id": str(requirement.requirement_id),
                    "content": requirement.content,
                    "requirement_type": requirement.requirement_type,
                    "priority": requirement.priority,
                    "created_at": requirement.created_at.isoformat() if requirement.created_at else None
                }
        except Exception as e:
            self.logger.error(f"Error storing requirement: {e}")
            return {"success": False, "error": str(e)}

    @tool(
        name="get_toolbox_requirements",
        description="Get all requirements for a specific session"
    )
    async def get_requirements(self, session_id: str, requirement_type: str = None) -> Dict[str, Any]:
        """
        Get requirements for a session.

        Args:
            session_id: Session UUID
            requirement_type: Optional filter by requirement type

        Returns:
            Dictionary containing list of requirements or error
        """
        try:
            async with create_toolbox_client(self.server_url) as client:
                if requirement_type:
                    requirements = await client.get_requirements_by_type(session_id, requirement_type)
                else:
                    requirements = await client.get_requirements(session_id)

                return {
                    "success": True,
                    "requirements": [req.to_dict() for req in requirements],
                    "count": len(requirements)
                }
        except Exception as e:
            self.logger.error(f"Error getting requirements: {e}")
            return {"success": False, "error": str(e)}

    @tool(
        name="store_toolbox_test_case",
        description="Store a structured test case with JSON content"
    )
    async def store_test_case(self, session_id: str, test_id: str, summary: str, priority: str = "MEDIUM",
                            test_type: str = "functional", preconditions: List[str] = None,
                            test_steps: List[str] = None, test_data: Dict[str, Any] = None,
                            expected_result: str = "", requirement_traceability: str = "") -> Dict[str, Any]:
        """
        Store a test case for a session.

        Args:
            session_id: Session UUID
            test_id: Human-readable test identifier (e.g., TC_AUTH_001)
            summary: Brief test case summary
            priority: Test priority (LOW, MEDIUM, HIGH, CRITICAL)
            test_type: Test type (functional, security, edge case, negative)
            preconditions: List of test preconditions
            test_steps: List of test execution steps
            test_data: Dictionary of test data
            expected_result: Expected test result
            requirement_traceability: Requirement traceability information

        Returns:
            Dictionary containing test case details or error
        """
        try:
            test_content = {
                "preconditions": preconditions or [],
                "test_steps": test_steps or [],
                "test_data": test_data or {},
                "expected_result": expected_result,
                "requirement_traceability": requirement_traceability
            }

            async with create_toolbox_client(self.server_url) as client:
                test_case = await client.store_test_case(session_id, test_id, summary, priority, test_type, test_content)
                return {
                    "success": True,
                    "test_case_id": str(test_case.test_case_id),
                    "test_id": test_case.test_id,
                    "summary": test_case.summary,
                    "priority": test_case.priority,
                    "test_type": test_case.test_type,
                    "created_at": test_case.created_at.isoformat() if test_case.created_at else None
                }
        except Exception as e:
            self.logger.error(f"Error storing test case: {e}")
            return {"success": False, "error": str(e)}

    @tool(
        name="store_toolbox_test_suite",
        description="Store multiple test cases from a structured test suite JSON"
    )
    async def store_test_suite(self, session_id: str, test_suite_json: str) -> Dict[str, Any]:
        """
        Store multiple test cases from a test suite.

        Args:
            session_id: Session UUID
            test_suite_json: JSON string containing test suite data

        Returns:
            Dictionary containing results or error
        """
        try:
            test_suite = json.loads(test_suite_json)

            async with create_toolbox_client(self.server_url) as client:
                test_cases = await client.store_test_suite(session_id, test_suite)
                return {
                    "success": True,
                    "test_cases_created": len(test_cases),
                    "test_case_ids": [str(tc.test_case_id) for tc in test_cases]
                }
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in test suite: {e}")
            return {"success": False, "error": f"Invalid JSON format: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error storing test suite: {e}")
            return {"success": False, "error": str(e)}

    @tool(
        name="get_toolbox_test_cases",
        description="Get all test cases for a specific session"
    )
    async def get_test_cases(self, session_id: str, priority: str = None, search_term: str = None) -> Dict[str, Any]:
        """
        Get test cases for a session.

        Args:
            session_id: Session UUID
            priority: Optional filter by priority (LOW, MEDIUM, HIGH, CRITICAL)
            search_term: Optional search term to filter test cases

        Returns:
            Dictionary containing list of test cases or error
        """
        try:
            async with create_toolbox_client(self.server_url) as client:
                if search_term:
                    test_cases = await client.search_test_cases(session_id, search_term)
                elif priority:
                    test_cases = await client.get_test_cases_by_priority(session_id, priority)
                else:
                    test_cases = await client.get_test_cases(session_id)

                return {
                    "success": True,
                    "test_cases": [tc.to_dict() for tc in test_cases],
                    "count": len(test_cases)
                }
        except Exception as e:
            self.logger.error(f"Error getting test cases: {e}")
            return {"success": False, "error": str(e)}

    @tool(
        name="get_toolbox_session_context",
        description="Get complete session context with all requirements and test cases"
    )
    async def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get complete session context.

        Args:
            session_id: Session UUID

        Returns:
            Dictionary containing complete session context or error
        """
        try:
            async with create_toolbox_client(self.server_url) as client:
                context = await client.get_session_context(session_id)
                if context:
                    return {
                        "success": True,
                        "context": context.to_dict(),
                        "summary": {
                            "requirements_count": len(context.requirements),
                            "test_cases_count": len(context.test_cases),
                            "critical_tests": len(context.get_critical_test_cases()),
                            "high_priority_requirements": len(context.get_high_priority_requirements())
                        }
                    }
                else:
                    return {"success": False, "error": "Session context not found"}
        except Exception as e:
            self.logger.error(f"Error getting session context: {e}")
            return {"success": False, "error": str(e)}

    @tool(
        name="get_toolbox_test_suite",
        description="Get test cases formatted as a structured test suite JSON"
    )
    async def get_test_suite(self, session_id: str) -> Dict[str, Any]:
        """
        Get test cases as a structured test suite.

        Args:
            session_id: Session UUID

        Returns:
            Dictionary containing structured test suite or error
        """
        try:
            async with create_toolbox_client(self.server_url) as client:
                context = await client.get_session_context(session_id)
                if context:
                    test_suite = context.to_test_suite_json()
                    return {
                        "success": True,
                        "test_suite": test_suite["test_suite"]
                    }
                else:
                    return {"success": False, "error": "Session not found"}
        except Exception as e:
            self.logger.error(f"Error getting test suite: {e}")
            return {"success": False, "error": str(e)}

    @tool(
        name="update_toolbox_session_status",
        description="Update session status (active, completed, archived)"
    )
    async def update_session_status(self, session_id: str, status: str) -> Dict[str, Any]:
        """
        Update session status.

        Args:
            session_id: Session UUID
            status: New status (active, completed, archived)

        Returns:
            Dictionary containing updated session details or error
        """
        try:
            async with create_toolbox_client(self.server_url) as client:
                session = await client.update_session_status(session_id, status)
                return {
                    "success": True,
                    "session_id": str(session.session_id),
                    "status": session.status,
                    "updated_at": session.updated_at.isoformat() if session.updated_at else None
                }
        except Exception as e:
            self.logger.error(f"Error updating session status: {e}")
            return {"success": False, "error": str(e)}

    @tool(
        name="get_user_toolbox_sessions",
        description="Get all sessions for a specific user"
    )
    async def get_user_sessions(self, user_id: str) -> Dict[str, Any]:
        """
        Get all sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary containing list of user sessions or error
        """
        try:
            async with create_toolbox_client(self.server_url) as client:
                sessions = await client.get_user_sessions(user_id)
                return {
                    "success": True,
                    "sessions": [session.to_dict() for session in sessions],
                    "count": len(sessions)
                }
        except Exception as e:
            self.logger.error(f"Error getting user sessions: {e}")
            return {"success": False, "error": str(e)}


def create_adk_toolbox_tools(server_url: str = "http://localhost:5000") -> List[Any]:
    """
    Create ADK function tools for Toolbox integration.

    Args:
        server_url: URL of the GenAI Toolbox server

    Returns:
        List of ADK function tools
    """
    tools_instance = ADKToolboxTools(server_url)

    # Extract all methods that have the _tool_name attribute (decorated with @tool)
    tools = []
    for attr_name in dir(tools_instance):
        attr = getattr(tools_instance, attr_name)
        if callable(attr) and hasattr(attr, '_tool_name'):
            tools.append(attr)

    return tools


# Global instance for easy access
toolbox_tools = ADKToolboxTools()

# Export individual tools for direct use
create_session = toolbox_tools.create_session
get_session = toolbox_tools.get_session
store_requirement = toolbox_tools.store_requirement
get_requirements = toolbox_tools.get_requirements
store_test_case = toolbox_tools.store_test_case
store_test_suite = toolbox_tools.store_test_suite
get_test_cases = toolbox_tools.get_test_cases
get_session_context = toolbox_tools.get_session_context
get_test_suite = toolbox_tools.get_test_suite
update_session_status = toolbox_tools.update_session_status
get_user_sessions = toolbox_tools.get_user_sessions