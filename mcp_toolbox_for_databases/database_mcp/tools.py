"""
Google ADK Function Tools for MCP Database integration.

This module provides function tools that can be used by Google ADK agents
to interact with the MCP database server for persistent storage operations.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from google.adk.tools import FunctionTool
except ImportError:
    print("Warning: Google ADK tools not available. Install with: pip install google-adk")
    FunctionTool = None

from .client import DatabaseMCPClient, MCPClientContext


class MCPDatabaseTools:
    """Tools for MCP database operations."""

    def __init__(self):
        """Initialize MCP database tools."""
        self.client = None
        self._initialized = False

    async def _get_client(self) -> DatabaseMCPClient:
        """Get or create MCP client."""
        if not self.client:
            self.client = DatabaseMCPClient()
            await self.client.connect()
            self._initialized = True
        return self.client

    async def close(self):
        """Close MCP client connection."""
        if self.client:
            await self.client.disconnect()
            self.client = None
            self._initialized = False

    # Tool functions for Google ADK agents
    async def create_mcp_session(
        self,
        user_id: str,
        user_prompt: str,
        project_name: Optional[str] = None,
        agent_used: str = "adk_agent",
        workflow_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Create a new session using MCP database server.

        Args:
            user_id: User identifier
            user_prompt: Initial user prompt
            project_name: Optional project name
            agent_used: Agent type used
            workflow_type: Type of workflow

        Returns:
            Dictionary with session creation result
        """
        try:
            client = await self._get_client()

            # Generate unique session ID
            session_id = f"mcp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            result = await client.create_session(
                session_id=session_id,
                user_id=user_id,
                project_name=project_name,
                user_prompt=user_prompt,
                agent_used=agent_used,
                workflow_type=workflow_type
            )

            return {
                "success": result.get("success", False),
                "session_id": session_id,
                "mcp_session_id": result.get("mcp_session_id"),
                "created_at": result.get("created_at"),
                "error": result.get("error")
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"MCP session creation failed: {str(e)}"
            }

    async def get_mcp_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get session data from MCP database server.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with session data
        """
        try:
            client = await self._get_client()
            result = await client.get_session(session_id)

            return {
                "success": result.get("success", False),
                "session": result.get("session"),
                "error": result.get("error")
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"MCP session retrieval failed: {str(e)}"
            }

    async def update_mcp_session_status(self, session_id: str, status: str) -> Dict[str, Any]:
        """
        Update session status in MCP database.

        Args:
            session_id: Session identifier
            status: New status

        Returns:
            Dictionary with update result
        """
        try:
            client = await self._get_client()
            result = await client.update_session_status(session_id, status)

            return {
                "success": result.get("success", False),
                "session_id": session_id,
                "status": status,
                "updated_at": result.get("updated_at"),
                "error": result.get("error")
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"MCP session status update failed: {str(e)}"
            }

    async def store_mcp_requirement(
        self,
        session_id: str,
        requirement_content: str,
        requirement_type: str = "functional",
        priority: str = "medium",
        source: str = "agent_generated"
    ) -> Dict[str, Any]:
        """
        Store requirement in MCP database.

        Args:
            session_id: Session identifier
            requirement_content: Requirement text content
            requirement_type: Type of requirement
            priority: Priority level
            source: Source of requirement

        Returns:
            Dictionary with storage result
        """
        try:
            client = await self._get_client()
            result = await client.create_requirement(
                session_id=session_id,
                content=requirement_content,
                requirement_type=requirement_type,
                priority=priority,
                source=source
            )

            return {
                "success": result.get("success", False),
                "requirement_id": result.get("requirement_id"),
                "session_id": session_id,
                "created_at": result.get("created_at"),
                "error": result.get("error")
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"MCP requirement storage failed: {str(e)}"
            }

    async def get_mcp_session_requirements(self, session_id: str) -> Dict[str, Any]:
        """
        Get all requirements for a session from MCP database.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with requirements list
        """
        try:
            client = await self._get_client()
            result = await client.get_session_requirements(session_id)

            return {
                "success": result.get("success", False),
                "requirements": result.get("requirements", []),
                "count": result.get("count", 0),
                "error": result.get("error")
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"MCP requirements retrieval failed: {str(e)}"
            }

    async def store_mcp_test_cases(
        self,
        session_id: str,
        test_suite_json: str
    ) -> Dict[str, Any]:
        """
        Store test cases from structured test suite JSON in MCP database.

        Args:
            session_id: Session identifier
            test_suite_json: JSON string containing the test suite

        Returns:
            Dictionary with storage result
        """
        try:
            client = await self._get_client()
            result = await client.create_test_cases_from_suite(session_id, test_suite_json)

            return {
                "success": result.get("success", False),
                "session_id": session_id,
                "test_cases_created": result.get("test_cases_created", 0),
                "test_case_ids": result.get("test_case_ids", []),
                "error": result.get("error")
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"MCP test cases storage failed: {str(e)}"
            }

    async def get_mcp_session_test_cases(
        self,
        session_id: str,
        as_suite: bool = False
    ) -> Dict[str, Any]:
        """
        Get test cases for a session from MCP database.

        Args:
            session_id: Session identifier
            as_suite: Whether to return in test suite format

        Returns:
            Dictionary with test cases
        """
        try:
            client = await self._get_client()
            result = await client.get_session_test_cases(session_id, as_suite)

            return {
                "success": result.get("success", False),
                "session_id": session_id,
                "test_cases": result.get("test_cases"),
                "test_suite": result.get("test_suite"),
                "count": result.get("count", 0),
                "error": result.get("error")
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"MCP test cases retrieval failed: {str(e)}"
            }

    async def get_mcp_session_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get complete session context from MCP database.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with complete session context
        """
        try:
            client = await self._get_client()
            result = await client.get_session_with_context(session_id)

            return {
                "success": result.get("success", False),
                "context": result.get("context"),
                "error": result.get("error")
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"MCP session context retrieval failed: {str(e)}"
            }

    # Convenience methods for common workflows
    async def store_agent_analysis_mcp(
        self,
        session_id: str,
        analysis_content: str,
        analysis_type: str = "requirements_analysis"
    ) -> Dict[str, Any]:
        """
        Store agent analysis results in MCP database.

        Args:
            session_id: Session identifier
            analysis_content: Analysis content from agent
            analysis_type: Type of analysis performed

        Returns:
            Dictionary with storage result
        """
        return await self.store_mcp_requirement(
            session_id=session_id,
            requirement_content=analysis_content,
            requirement_type=analysis_type,
            source="agent_analysis"
        )

    async def store_generated_test_cases_mcp(
        self,
        session_id: str,
        test_cases_content: str
    ) -> Dict[str, Any]:
        """
        Store generated test cases, converting to structured format if needed.

        Args:
            session_id: Session identifier
            test_cases_content: Test cases content (JSON or text)

        Returns:
            Dictionary with storage result
        """
        try:
            client = await self._get_client()
            return await client.store_generated_test_cases(session_id, test_cases_content)

        except Exception as e:
            return {
                "success": False,
                "error": f"MCP test cases generation storage failed: {str(e)}"
            }


# Global tools instance
mcp_db_tools = MCPDatabaseTools()


def create_database_tools() -> List[Any]:
    """Create Google ADK function tools for MCP database operations."""
    if FunctionTool is None:
        print("Warning: Google ADK not available, returning empty tools list")
        return []

    tools = [
        FunctionTool(
            func=mcp_db_tools.create_mcp_session,
            name="create_mcp_session",
            description="Create a new session in MCP database for tracking agent workflow"
        ),
        FunctionTool(
            func=mcp_db_tools.get_mcp_session,
            name="get_mcp_session",
            description="Get session data from MCP database by ID"
        ),
        FunctionTool(
            func=mcp_db_tools.update_mcp_session_status,
            name="update_mcp_session_status",
            description="Update the status of an existing session in MCP database"
        ),
        FunctionTool(
            func=mcp_db_tools.store_mcp_requirement,
            name="store_mcp_requirement",
            description="Store a requirement in MCP database"
        ),
        FunctionTool(
            func=mcp_db_tools.get_mcp_session_requirements,
            name="get_mcp_session_requirements",
            description="Get all requirements for a session from MCP database"
        ),
        FunctionTool(
            func=mcp_db_tools.store_mcp_test_cases,
            name="store_mcp_test_cases",
            description="Store test cases from structured test suite JSON in MCP database"
        ),
        FunctionTool(
            func=mcp_db_tools.get_mcp_session_test_cases,
            name="get_mcp_session_test_cases",
            description="Get test cases for a session from MCP database"
        ),
        FunctionTool(
            func=mcp_db_tools.get_mcp_session_context,
            name="get_mcp_session_context",
            description="Get complete session context from MCP database"
        ),
        FunctionTool(
            func=mcp_db_tools.store_agent_analysis_mcp,
            name="store_agent_analysis_mcp",
            description="Store agent analysis results in MCP database"
        ),
        FunctionTool(
            func=mcp_db_tools.store_generated_test_cases_mcp,
            name="store_generated_test_cases_mcp",
            description="Store generated test cases in MCP database with format conversion"
        )
    ]

    return tools


# Cleanup function
async def cleanup_mcp_tools():
    """Cleanup MCP tools connections."""
    await mcp_db_tools.close()