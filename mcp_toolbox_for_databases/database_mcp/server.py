"""
MCP Server implementation for database operations.

This module implements a Model Context Protocol (MCP) server that provides
standardized database operations for Google ADK agents.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime
import uuid

try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource, Tool, TextContent, ImageContent, EmbeddedResource,
        CallToolRequest, CallToolResult, ListResourcesRequest, ListResourcesResult,
        ListToolsRequest, ListToolsResult, ReadResourceRequest, ReadResourceResult
    )
    import asyncpg
    from pydantic import BaseModel
except ImportError as e:
    print(f"Warning: MCP dependencies not available: {e}")
    print("Install with: pip install mcp mcp-server-postgres asyncpg")
    Server = None
    asyncpg = None


class DatabaseMCPServer:
    """MCP Server for database operations."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize the MCP server."""
        self.database_url = database_url or os.getenv('DATABASE_URL')
        self.server = None
        self.db_pool = None
        self.logger = logging.getLogger(__name__)

        if Server is None:
            raise ImportError("MCP dependencies not available. Install with: pip install mcp mcp-server-postgres")

    async def initialize(self):
        """Initialize the MCP server and database connection."""
        # Create MCP server
        self.server = Server("database-mcp-server")

        # Initialize database pool
        if self.database_url and asyncpg:
            try:
                self.db_pool = await asyncpg.create_pool(self.database_url)
                self.logger.info("Database connection pool created")
            except Exception as e:
                self.logger.error(f"Failed to create database pool: {e}")
                raise

        # Register MCP handlers
        self._register_handlers()

        self.logger.info("MCP Server initialized")

    def _register_handlers(self):
        """Register MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available database tools."""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="create_session",
                        description="Create a new session in the database",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string"},
                                "user_id": {"type": "string"},
                                "project_name": {"type": "string"},
                                "user_prompt": {"type": "string"},
                                "agent_used": {"type": "string"},
                                "workflow_type": {"type": "string"}
                            },
                            "required": ["session_id", "user_id"]
                        }
                    ),
                    Tool(
                        name="get_session",
                        description="Get session by ID",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string"}
                            },
                            "required": ["session_id"]
                        }
                    ),
                    Tool(
                        name="update_session_status",
                        description="Update session status",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string"},
                                "status": {"type": "string"}
                            },
                            "required": ["session_id", "status"]
                        }
                    ),
                    Tool(
                        name="create_requirement",
                        description="Create a new requirement",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string"},
                                "content": {"type": "string"},
                                "requirement_type": {"type": "string"},
                                "priority": {"type": "string"},
                                "source": {"type": "string"}
                            },
                            "required": ["session_id", "content"]
                        }
                    ),
                    Tool(
                        name="get_session_requirements",
                        description="Get all requirements for a session",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string"}
                            },
                            "required": ["session_id"]
                        }
                    ),
                    Tool(
                        name="create_test_cases_from_suite",
                        description="Create test cases from structured test suite JSON",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string"},
                                "test_suite_json": {"type": "string"}
                            },
                            "required": ["session_id", "test_suite_json"]
                        }
                    ),
                    Tool(
                        name="get_session_test_cases",
                        description="Get test cases for a session",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string"},
                                "as_suite": {"type": "boolean"}
                            },
                            "required": ["session_id"]
                        }
                    ),
                    Tool(
                        name="get_session_with_context",
                        description="Get session with all requirements and test cases",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string"}
                            },
                            "required": ["session_id"]
                        }
                    )
                ]
            )

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                if name == "create_session":
                    result = await self._create_session(**arguments)
                elif name == "get_session":
                    result = await self._get_session(**arguments)
                elif name == "update_session_status":
                    result = await self._update_session_status(**arguments)
                elif name == "create_requirement":
                    result = await self._create_requirement(**arguments)
                elif name == "get_session_requirements":
                    result = await self._get_session_requirements(**arguments)
                elif name == "create_test_cases_from_suite":
                    result = await self._create_test_cases_from_suite(**arguments)
                elif name == "get_session_test_cases":
                    result = await self._get_session_test_cases(**arguments)
                elif name == "get_session_with_context":
                    result = await self._get_session_with_context(**arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Unknown tool: {name}")]
                    )

                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(result, default=str))]
                )

            except Exception as e:
                self.logger.error(f"Tool call error for {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps({"error": str(e)}))]
                )

    async def _create_session(self, session_id: str, user_id: str, project_name: str = None,
                            user_prompt: str = None, agent_used: str = "mcp_agent",
                            workflow_type: str = "full") -> Dict[str, Any]:
        """Create a new session."""
        if not self.db_pool:
            return {"error": "Database not available"}

        async with self.db_pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO sessions (session_id, user_id, project_name, user_prompt,
                                        agent_used, workflow_type, mcp_session_data)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, session_id, user_id, project_name, user_prompt, agent_used,
                    workflow_type, json.dumps({"created_via": "mcp", "version": "1.0.0"}))

                # Create MCP session record
                mcp_session_id = f"mcp_{session_id}"
                await conn.execute("""
                    INSERT INTO mcp_sessions (mcp_session_id, session_id, protocol_version)
                    VALUES ($1, $2, $3)
                """, mcp_session_id, session_id, "1.0.0")

                return {
                    "success": True,
                    "session_id": session_id,
                    "mcp_session_id": mcp_session_id,
                    "created_at": datetime.utcnow().isoformat()
                }
            except Exception as e:
                return {"error": str(e)}

    async def _get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session by ID."""
        if not self.db_pool:
            return {"error": "Database not available"}

        async with self.db_pool.acquire() as conn:
            try:
                row = await conn.fetchrow("""
                    SELECT s.*, m.mcp_session_id, m.protocol_version, m.connection_status
                    FROM sessions s
                    LEFT JOIN mcp_sessions m ON s.session_id = m.session_id
                    WHERE s.session_id = $1
                """, session_id)

                if not row:
                    return {"error": "Session not found"}

                return {
                    "success": True,
                    "session": dict(row)
                }
            except Exception as e:
                return {"error": str(e)}

    async def _update_session_status(self, session_id: str, status: str) -> Dict[str, Any]:
        """Update session status."""
        if not self.db_pool:
            return {"error": "Database not available"}

        async with self.db_pool.acquire() as conn:
            try:
                await conn.execute("""
                    UPDATE sessions SET status = $1, updated_at = NOW()
                    WHERE session_id = $2
                """, status, session_id)

                # Update MCP session activity
                await conn.execute("""
                    UPDATE mcp_sessions SET last_activity = NOW()
                    WHERE session_id = $1
                """, session_id)

                return {
                    "success": True,
                    "session_id": session_id,
                    "status": status,
                    "updated_at": datetime.utcnow().isoformat()
                }
            except Exception as e:
                return {"error": str(e)}

    async def _create_requirement(self, session_id: str, content: str,
                                requirement_type: str = "functional", priority: str = "medium",
                                source: str = "mcp_generated") -> Dict[str, Any]:
        """Create a new requirement."""
        if not self.db_pool:
            return {"error": "Database not available"}

        async with self.db_pool.acquire() as conn:
            try:
                requirement_id = f"{session_id}_req_{uuid.uuid4().hex[:8]}"

                await conn.execute("""
                    INSERT INTO requirements (id, session_id, original_content, requirement_type,
                                            priority, source, mcp_metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, requirement_id, session_id, content, requirement_type, priority, source,
                    json.dumps({"created_via": "mcp", "mcp_version": "1.0.0"}))

                # Log MCP operation
                await self._log_mcp_operation(session_id, "insert", "requirements", {
                    "requirement_id": requirement_id,
                    "content_length": len(content)
                })

                return {
                    "success": True,
                    "requirement_id": requirement_id,
                    "session_id": session_id,
                    "created_at": datetime.utcnow().isoformat()
                }
            except Exception as e:
                return {"error": str(e)}

    async def _get_session_requirements(self, session_id: str) -> Dict[str, Any]:
        """Get all requirements for a session."""
        if not self.db_pool:
            return {"error": "Database not available"}

        async with self.db_pool.acquire() as conn:
            try:
                rows = await conn.fetch("""
                    SELECT * FROM requirements WHERE session_id = $1 ORDER BY created_at
                """, session_id)

                requirements = [dict(row) for row in rows]

                return {
                    "success": True,
                    "requirements": requirements,
                    "count": len(requirements)
                }
            except Exception as e:
                return {"error": str(e)}

    async def _create_test_cases_from_suite(self, session_id: str, test_suite_json: str) -> Dict[str, Any]:
        """Create test cases from structured test suite JSON."""
        if not self.db_pool:
            return {"error": "Database not available"}

        try:
            test_suite_data = json.loads(test_suite_json)

            # Extract test_suite if wrapped
            if "test_suite" in test_suite_data:
                test_suite_data = test_suite_data["test_suite"]

            async with self.db_pool.acquire() as conn:
                created_test_cases = []

                for i, test_case_data in enumerate(test_suite_data.get("test_cases", [])):
                    test_case_id = f"{session_id}_tc_{i+1}"

                    await conn.execute("""
                        INSERT INTO test_cases (
                            id, session_id, test_name, test_description, test_steps,
                            expected_results, test_type, priority, test_data, preconditions,
                            test_suite_name, test_suite_description, test_id, summary,
                            requirement_traceability, mcp_generated, mcp_metadata
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                    """,
                        test_case_id, session_id,
                        test_case_data.get("summary", f"Test Case {i+1}"),
                        test_case_data.get("summary", ""),
                        json.dumps(test_case_data.get("test_steps", [])),
                        test_case_data.get("expected_result", ""),
                        test_case_data.get("type", "functional").lower(),
                        test_case_data.get("priority", "medium").lower(),
                        json.dumps(test_case_data.get("test_data", {})),
                        "; ".join(test_case_data.get("preconditions", [])),
                        test_suite_data.get("name", f"Test Suite {session_id}"),
                        test_suite_data.get("description", ""),
                        test_case_data.get("test_id", f"TC_MCP_{i+1:03d}"),
                        test_case_data.get("summary", ""),
                        test_case_data.get("requirement_traceability", ""),
                        True,  # mcp_generated
                        json.dumps({
                            "created_via": "mcp",
                            "suite_total_tests": test_suite_data.get("total_tests", 0),
                            "generated_date": test_suite_data.get("generated_date", "")
                        })
                    )

                    created_test_cases.append(test_case_id)

                # Log MCP operation
                await self._log_mcp_operation(session_id, "insert", "test_cases", {
                    "test_cases_created": len(created_test_cases),
                    "suite_name": test_suite_data.get("name", "")
                })

                return {
                    "success": True,
                    "session_id": session_id,
                    "test_cases_created": len(created_test_cases),
                    "test_case_ids": created_test_cases
                }

        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}

    async def _get_session_test_cases(self, session_id: str, as_suite: bool = False) -> Dict[str, Any]:
        """Get test cases for a session."""
        if not self.db_pool:
            return {"error": "Database not available"}

        async with self.db_pool.acquire() as conn:
            try:
                rows = await conn.fetch("""
                    SELECT * FROM test_cases WHERE session_id = $1 ORDER BY created_at
                """, session_id)

                test_cases = [dict(row) for row in rows]

                if as_suite and test_cases:
                    # Format as test suite
                    suite_name = test_cases[0].get("test_suite_name", f"Test Suite {session_id}")
                    suite_description = test_cases[0].get("test_suite_description", "")

                    formatted_test_cases = []
                    for tc in test_cases:
                        formatted_tc = {
                            "test_id": tc.get("test_id", tc["id"]),
                            "priority": (tc.get("priority") or "medium").upper(),
                            "type": (tc.get("test_type") or "functional").title(),
                            "summary": tc.get("summary") or tc.get("test_name", ""),
                            "preconditions": tc.get("preconditions", "").split("; ") if tc.get("preconditions") else [],
                            "test_steps": tc.get("test_steps") or [],
                            "test_data": tc.get("test_data") or {},
                            "expected_result": tc.get("expected_results") or "",
                            "requirement_traceability": tc.get("requirement_traceability") or ""
                        }
                        formatted_test_cases.append(formatted_tc)

                    test_suite = {
                        "name": suite_name,
                        "description": suite_description,
                        "total_tests": len(formatted_test_cases),
                        "generated_date": datetime.utcnow().date().isoformat(),
                        "test_cases": formatted_test_cases
                    }

                    return {
                        "success": True,
                        "session_id": session_id,
                        "test_suite": test_suite
                    }
                else:
                    return {
                        "success": True,
                        "test_cases": test_cases,
                        "count": len(test_cases)
                    }

            except Exception as e:
                return {"error": str(e)}

    async def _get_session_with_context(self, session_id: str) -> Dict[str, Any]:
        """Get session with all requirements and test cases."""
        if not self.db_pool:
            return {"error": "Database not available"}

        async with self.db_pool.acquire() as conn:
            try:
                # Get session
                session_row = await conn.fetchrow("""
                    SELECT s.*, m.mcp_session_id, m.protocol_version
                    FROM sessions s
                    LEFT JOIN mcp_sessions m ON s.session_id = m.session_id
                    WHERE s.session_id = $1
                """, session_id)

                if not session_row:
                    return {"error": "Session not found"}

                # Get requirements
                req_rows = await conn.fetch("""
                    SELECT * FROM requirements WHERE session_id = $1 ORDER BY created_at
                """, session_id)

                # Get test cases
                tc_rows = await conn.fetch("""
                    SELECT * FROM test_cases WHERE session_id = $1 ORDER BY created_at
                """, session_id)

                return {
                    "success": True,
                    "context": {
                        "session": dict(session_row),
                        "requirements": [dict(row) for row in req_rows],
                        "test_cases": [dict(row) for row in tc_rows]
                    }
                }

            except Exception as e:
                return {"error": str(e)}

    async def _log_mcp_operation(self, session_id: str, operation_type: str,
                               table_name: str, operation_data: Dict[str, Any]):
        """Log MCP operation for audit trail."""
        if not self.db_pool:
            return

        try:
            async with self.db_pool.acquire() as conn:
                mcp_session_id = f"mcp_{session_id}"
                await conn.execute("""
                    INSERT INTO mcp_operations (mcp_session_id, operation_type, table_name, operation_data)
                    VALUES ($1, $2, $3, $4)
                """, mcp_session_id, operation_type, table_name, json.dumps(operation_data))
        except Exception as e:
            self.logger.error(f"Failed to log MCP operation: {e}")

    async def run(self):
        """Run the MCP server."""
        await self.initialize()

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, InitializationOptions(
                    server_name="database-mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                )
            )

    async def close(self):
        """Close the MCP server and database connections."""
        if self.db_pool:
            await self.db_pool.close()


async def main():
    """Main function to run the MCP server."""
    logging.basicConfig(level=logging.INFO)

    server = DatabaseMCPServer()
    try:
        await server.run()
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    finally:
        await server.close()


if __name__ == "__main__":
    asyncio.run(main())