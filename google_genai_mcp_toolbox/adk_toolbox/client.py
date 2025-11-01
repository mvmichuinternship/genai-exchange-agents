"""
Toolbox Client for Google's GenAI MCP Toolbox.

Provides a Python client wrapper for interacting with Google's GenAI Toolbox server
using the toolbox-core SDK.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

try:
    from toolbox_core import ToolboxClient as CoreToolboxClient
except ImportError:
    CoreToolboxClient = None
    logging.warning("toolbox-core not available. Install with: pip install toolbox-core")

from .models import Session, Requirement, TestCase, SessionContext, SessionSummary


class ToolboxClient:
    """
    Client for interacting with Google's GenAI MCP Toolbox server.

    This client wraps the toolbox-core SDK to provide a more convenient interface
    for ADK agents to interact with database tools.
    """

    def __init__(self, server_url: str = "http://localhost:5000"):
        """
        Initialize the Toolbox client.

        Args:
            server_url: URL of the GenAI Toolbox server
        """
        self.server_url = server_url
        self._client = None
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self):
        """Connect to the Toolbox server."""
        if CoreToolboxClient is None:
            raise ImportError("toolbox-core not available. Install with: pip install toolbox-core")

        try:
            self._client = CoreToolboxClient(self.server_url)
            await self._client.__aenter__()
            self.logger.info(f"Connected to Toolbox server at {self.server_url}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Toolbox server: {e}")
            raise

    async def disconnect(self):
        """Disconnect from the Toolbox server."""
        if self._client:
            try:
                await self._client.__aexit__(None, None, None)
                self.logger.info("Disconnected from Toolbox server")
            except Exception as e:
                self.logger.error(f"Error during disconnect: {e}")
            finally:
                self._client = None

    async def invoke_tool(self, tool_name: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Invoke a tool on the Toolbox server.

        Args:
            tool_name: Name of the tool to invoke
            parameters: Parameters to pass to the tool

        Returns:
            List of result rows from the tool execution
        """
        if not self._client:
            await self.connect()

        try:
            result = await self._client.invoke_tool(tool_name, parameters)
            self.logger.debug(f"Tool {tool_name} executed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Error invoking tool {tool_name}: {e}")
            raise

    async def load_toolset(self, toolset_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load tools from a toolset.

        Args:
            toolset_name: Name of the toolset to load (None for all tools)

        Returns:
            List of available tools
        """
        if not self._client:
            await self.connect()

        try:
            if toolset_name:
                tools = await self._client.load_toolset(toolset_name)
            else:
                tools = await self._client.load_toolset()

            self.logger.info(f"Loaded {len(tools)} tools from toolset: {toolset_name or 'all'}")
            return tools
        except Exception as e:
            self.logger.error(f"Error loading toolset {toolset_name}: {e}")
            raise

    # Session Management Methods
    async def create_session(self, user_id: str, user_prompt: str, project_name: Optional[str] = None) -> Session:
        """Create a new agent session."""
        result = await self.invoke_tool("create-session", {
            "user_id": user_id,
            "user_prompt": user_prompt,
            "project_name": project_name
        })

        if result and len(result) > 0:
            return Session.from_dict(result[0])
        else:
            raise ValueError("Failed to create session")

    async def get_session(self, session_id: Union[str, UUID]) -> Optional[Session]:
        """Get session by ID."""
        result = await self.invoke_tool("get-session", {
            "session_id": str(session_id)
        })

        if result and len(result) > 0:
            return Session.from_dict(result[0])
        return None

    async def update_session_status(self, session_id: Union[str, UUID], status: str) -> Session:
        """Update session status."""
        result = await self.invoke_tool("update-session-status", {
            "session_id": str(session_id),
            "status": status
        })

        if result and len(result) > 0:
            return Session.from_dict(result[0])
        else:
            raise ValueError("Failed to update session status")

    async def get_user_sessions(self, user_id: str) -> List[SessionSummary]:
        """Get all sessions for a user."""
        result = await self.invoke_tool("get-user-sessions", {
            "user_id": user_id
        })

        return [SessionSummary.from_dict(row) for row in result]

    # Requirements Management Methods
    async def store_requirement(self, session_id: Union[str, UUID], content: str,
                              requirement_type: str = "functional", priority: str = "medium") -> Requirement:
        """Store a requirement for a session."""
        result = await self.invoke_tool("store-requirement", {
            "session_id": str(session_id),
            "content": content,
            "requirement_type": requirement_type,
            "priority": priority
        })

        if result and len(result) > 0:
            return Requirement.from_dict(result[0])
        else:
            raise ValueError("Failed to store requirement")

    async def get_requirements(self, session_id: Union[str, UUID]) -> List[Requirement]:
        """Get all requirements for a session."""
        result = await self.invoke_tool("get-requirements", {
            "session_id": str(session_id)
        })

        return [Requirement.from_dict(row) for row in result]

    async def get_requirements_by_type(self, session_id: Union[str, UUID], requirement_type: str) -> List[Requirement]:
        """Get requirements filtered by type."""
        result = await self.invoke_tool("get-requirements-by-type", {
            "session_id": str(session_id),
            "requirement_type": requirement_type
        })

        return [Requirement.from_dict(row) for row in result]

    # Test Case Management Methods
    async def store_test_case(self, session_id: Union[str, UUID], test_id: str, summary: str,
                            priority: str = "MEDIUM", test_type: str = "functional",
                            test_content: Dict[str, Any] = None) -> TestCase:
        """Store a test case for a session."""
        if test_content is None:
            test_content = {}

        result = await self.invoke_tool("store-test-case", {
            "session_id": str(session_id),
            "test_id": test_id,
            "summary": summary,
            "priority": priority,
            "test_type": test_type,
            "test_content": json.dumps(test_content)
        })

        if result and len(result) > 0:
            # Add the test_content back to the result for proper model creation
            result[0]["test_content"] = test_content
            return TestCase.from_dict(result[0])
        else:
            raise ValueError("Failed to store test case")

    async def store_test_case_from_json(self, session_id: Union[str, UUID], test_case_json: Dict[str, Any]) -> TestCase:
        """Store a test case from a complete JSON structure."""
        return await self.store_test_case(
            session_id=session_id,
            test_id=test_case_json.get("test_id", ""),
            summary=test_case_json.get("summary", ""),
            priority=test_case_json.get("priority", "MEDIUM"),
            test_type=test_case_json.get("type", "functional"),
            test_content={
                "preconditions": test_case_json.get("preconditions", []),
                "test_steps": test_case_json.get("test_steps", []),
                "test_data": test_case_json.get("test_data", {}),
                "expected_result": test_case_json.get("expected_result", ""),
                "requirement_traceability": test_case_json.get("requirement_traceability", "")
            }
        )

    async def store_test_suite(self, session_id: Union[str, UUID], test_suite: Dict[str, Any]) -> List[TestCase]:
        """Store multiple test cases from a test suite JSON."""
        test_cases = []

        suite_data = test_suite.get("test_suite", {})
        for test_case_data in suite_data.get("test_cases", []):
            test_case = await self.store_test_case_from_json(session_id, test_case_data)
            test_cases.append(test_case)

        return test_cases

    async def get_test_cases(self, session_id: Union[str, UUID]) -> List[TestCase]:
        """Get all test cases for a session."""
        result = await self.invoke_tool("get-test-cases", {
            "session_id": str(session_id)
        })

        return [TestCase.from_dict(row) for row in result]

    async def get_test_cases_by_priority(self, session_id: Union[str, UUID], priority: str) -> List[TestCase]:
        """Get test cases filtered by priority."""
        result = await self.invoke_tool("get-test-cases-by-priority", {
            "session_id": str(session_id),
            "priority": priority
        })

        return [TestCase.from_dict(row) for row in result]

    async def search_test_cases(self, session_id: Union[str, UUID], search_term: str) -> List[TestCase]:
        """Search test cases by content."""
        result = await self.invoke_tool("search-test-cases", {
            "session_id": str(session_id),
            "search_term": search_term
        })

        return [TestCase.from_dict(row) for row in result]

    # Complex Queries
    async def get_session_context(self, session_id: Union[str, UUID]) -> Optional[SessionContext]:
        """Get complete session context with requirements and test cases."""
        result = await self.invoke_tool("get-session-context", {
            "session_id": str(session_id)
        })

        if result and len(result) > 0:
            return SessionContext.from_dict(result[0])
        return None

    async def get_session_summary(self, session_id: Union[str, UUID]) -> Optional[SessionSummary]:
        """Get session summary with counts."""
        result = await self.invoke_tool("get-session-summary", {
            "session_id": str(session_id)
        })

        if result and len(result) > 0:
            return SessionSummary.from_dict(result[0])
        return None

    # Utility Methods
    async def get_active_sessions(self) -> List[SessionSummary]:
        """Get all active sessions."""
        result = await self.invoke_tool("get-active-sessions", {})
        return [SessionSummary.from_dict(row) for row in result]

    async def health_check(self) -> bool:
        """Check if the Toolbox server is healthy."""
        try:
            # Try to get active sessions as a health check
            await self.get_active_sessions()
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False


class ToolboxClientContext:
    """Context manager for ToolboxClient."""

    def __init__(self, server_url: str = "http://localhost:5000"):
        self.server_url = server_url
        self.client = None

    async def __aenter__(self) -> ToolboxClient:
        """Enter async context."""
        self.client = ToolboxClient(self.server_url)
        await self.client.connect()
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self.client:
            await self.client.disconnect()


# Convenience function for creating client context
def create_toolbox_client(server_url: str = "http://localhost:5000") -> ToolboxClientContext:
    """Create a ToolboxClient context manager."""
    return ToolboxClientContext(server_url)