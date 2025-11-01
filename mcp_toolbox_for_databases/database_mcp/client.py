"""
MCP Client for database operations.

This module provides a client to interact with the MCP database server,
allowing Google ADK agents to perform database operations through the
Model Context Protocol.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    from mcp.client import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    import httpx
except ImportError as e:
    print(f"Warning: MCP client dependencies not available: {e}")
    print("Install with: pip install mcp httpx")
    ClientSession = None
    stdio_client = None


class DatabaseMCPClient:
    """Client for interacting with the database MCP server."""

    def __init__(self, server_command: Optional[List[str]] = None):
        """
        Initialize the MCP client.

        Args:
            server_command: Command to start the MCP server. If None, uses default.
        """
        self.server_command = server_command or [
            "python", "-m", "database_mcp.server"
        ]
        self.session: Optional[ClientSession] = None
        self.logger = logging.getLogger(__name__)

        if ClientSession is None:
            raise ImportError("MCP client dependencies not available")

    async def connect(self):
        """Connect to the MCP server."""
        try:
            server_params = StdioServerParameters(
                command=self.server_command[0],
                args=self.server_command[1:] if len(self.server_command) > 1 else []
            )

            self.session = await stdio_client(server_params)
            await self.session.initialize()

            self.logger.info("Connected to MCP database server")

        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server: {e}")
            raise

    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session:
            await self.session.close()
            self.session = None
            self.logger.info("Disconnected from MCP server")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        try:
            result = await self.session.call_tool(tool_name, arguments)

            if result.content and len(result.content) > 0:
                # Parse the result content
                content = result.content[0]
                if hasattr(content, 'text'):
                    return json.loads(content.text)
                else:
                    return {"error": "Invalid response format"}
            else:
                return {"error": "No response content"}

        except Exception as e:
            self.logger.error(f"Tool call failed for {tool_name}: {e}")
            return {"error": str(e)}

    # Session management methods
    async def create_session(self, session_id: str, user_id: str,
                           project_name: Optional[str] = None,
                           user_prompt: Optional[str] = None,
                           agent_used: str = "mcp_agent",
                           workflow_type: str = "full") -> Dict[str, Any]:
        """Create a new session."""
        return await self.call_tool("create_session", {
            "session_id": session_id,
            "user_id": user_id,
            "project_name": project_name,
            "user_prompt": user_prompt,
            "agent_used": agent_used,
            "workflow_type": workflow_type
        })

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session by ID."""
        return await self.call_tool("get_session", {
            "session_id": session_id
        })

    async def update_session_status(self, session_id: str, status: str) -> Dict[str, Any]:
        """Update session status."""
        return await self.call_tool("update_session_status", {
            "session_id": session_id,
            "status": status
        })

    # Requirements management methods
    async def create_requirement(self, session_id: str, content: str,
                               requirement_type: str = "functional",
                               priority: str = "medium",
                               source: str = "mcp_generated") -> Dict[str, Any]:
        """Create a new requirement."""
        return await self.call_tool("create_requirement", {
            "session_id": session_id,
            "content": content,
            "requirement_type": requirement_type,
            "priority": priority,
            "source": source
        })

    async def get_session_requirements(self, session_id: str) -> Dict[str, Any]:
        """Get all requirements for a session."""
        return await self.call_tool("get_session_requirements", {
            "session_id": session_id
        })

    # Test case management methods
    async def create_test_cases_from_suite(self, session_id: str,
                                         test_suite_json: str) -> Dict[str, Any]:
        """Create test cases from structured test suite JSON."""
        return await self.call_tool("create_test_cases_from_suite", {
            "session_id": session_id,
            "test_suite_json": test_suite_json
        })

    async def get_session_test_cases(self, session_id: str,
                                   as_suite: bool = False) -> Dict[str, Any]:
        """Get test cases for a session."""
        return await self.call_tool("get_session_test_cases", {
            "session_id": session_id,
            "as_suite": as_suite
        })

    # Context management methods
    async def get_session_with_context(self, session_id: str) -> Dict[str, Any]:
        """Get session with all requirements and test cases."""
        return await self.call_tool("get_session_with_context", {
            "session_id": session_id
        })

    # Convenience methods for common workflows
    async def create_session_workflow(self, user_id: str, user_prompt: str,
                                    project_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a complete session workflow."""
        session_id = f"mcp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_id[:8]}"

        # Create session
        session_result = await self.create_session(
            session_id=session_id,
            user_id=user_id,
            project_name=project_name,
            user_prompt=user_prompt
        )

        if not session_result.get("success"):
            return session_result

        # Create initial requirement from user prompt
        if user_prompt:
            req_result = await self.create_requirement(
                session_id=session_id,
                content=user_prompt,
                requirement_type="initial_prompt",
                source="user_input"
            )

            if not req_result.get("success"):
                return {"error": f"Failed to create initial requirement: {req_result.get('error')}"}

        return {
            "success": True,
            "session_id": session_id,
            "workflow_created": True
        }

    async def store_agent_analysis(self, session_id: str, analysis_content: str,
                                 requirement_type: str = "functional") -> Dict[str, Any]:
        """Store agent analysis as requirements."""
        return await self.create_requirement(
            session_id=session_id,
            content=analysis_content,
            requirement_type=requirement_type,
            source="agent_analysis"
        )

    async def store_generated_test_cases(self, session_id: str,
                                       test_cases_content: str) -> Dict[str, Any]:
        """Store generated test cases."""
        # Try to parse as JSON first
        try:
            # Check if it's already valid JSON
            json.loads(test_cases_content)
            return await self.create_test_cases_from_suite(session_id, test_cases_content)
        except json.JSONDecodeError:
            # Create a simple test suite structure
            simple_suite = {
                "test_suite": {
                    "name": f"Generated Test Suite for {session_id}",
                    "description": "Test cases generated by agent",
                    "total_tests": 1,
                    "generated_date": datetime.utcnow().date().isoformat(),
                    "test_cases": [
                        {
                            "test_id": "TC_GEN_001",
                            "priority": "MEDIUM",
                            "type": "Functional",
                            "summary": "Generated test case",
                            "preconditions": ["System is ready"],
                            "test_steps": test_cases_content.split('\n')[:10],  # First 10 lines
                            "test_data": {},
                            "expected_result": "Test completes successfully",
                            "requirement_traceability": "Generated from agent analysis"
                        }
                    ]
                }
            }

            return await self.create_test_cases_from_suite(
                session_id,
                json.dumps(simple_suite)
            )


# Global client instance
_global_client: Optional[DatabaseMCPClient] = None


async def get_client() -> DatabaseMCPClient:
    """Get the global MCP client instance."""
    global _global_client

    if _global_client is None:
        _global_client = DatabaseMCPClient()
        await _global_client.connect()

    return _global_client


async def close_client():
    """Close the global MCP client."""
    global _global_client

    if _global_client:
        await _global_client.disconnect()
        _global_client = None


# Context manager for client lifecycle
class MCPClientContext:
    """Context manager for MCP client lifecycle."""

    def __init__(self, server_command: Optional[List[str]] = None):
        self.client = DatabaseMCPClient(server_command)

    async def __aenter__(self) -> DatabaseMCPClient:
        await self.client.connect()
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()


# Example usage
async def example_usage():
    """Example of using the MCP client."""
    async with MCPClientContext() as client:
        # Create a session
        session_result = await client.create_session_workflow(
            user_id="user123",
            user_prompt="Create authentication system with OAuth2",
            project_name="Security Project"
        )

        if session_result.get("success"):
            session_id = session_result["session_id"]
            print(f"Created session: {session_id}")

            # Store analysis
            analysis_result = await client.store_agent_analysis(
                session_id=session_id,
                analysis_content="System requires OAuth2 implementation with PKCE flow"
            )
            print(f"Stored analysis: {analysis_result}")

            # Store test cases
            test_cases = '''
            {
              "test_suite": {
                "name": "OAuth2 Test Suite",
                "description": "Test cases for OAuth2 authentication",
                "total_tests": 2,
                "generated_date": "2025-10-31",
                "test_cases": [
                  {
                    "test_id": "TC_AUTH_001",
                    "priority": "HIGH",
                    "type": "Functional",
                    "summary": "Test OAuth2 authorization flow",
                    "preconditions": ["OAuth2 server is running", "Client is registered"],
                    "test_steps": ["Navigate to login", "Click OAuth2 login", "Verify redirect"],
                    "test_data": {"client_id": "test_client", "scope": "read"},
                    "expected_result": "User is authenticated and redirected",
                    "requirement_traceability": "REQ_AUTH_001 - OAuth2 Implementation"
                  }
                ]
              }
            }
            '''

            test_result = await client.store_generated_test_cases(session_id, test_cases)
            print(f"Stored test cases: {test_result}")

            # Get full context
            context = await client.get_session_with_context(session_id)
            print(f"Session context: {context}")


if __name__ == "__main__":
    asyncio.run(example_usage())