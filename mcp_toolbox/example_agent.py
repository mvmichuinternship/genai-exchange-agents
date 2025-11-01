"""
Example agent demonstrating MCP toolbox integration.

This agent shows how to use the MCP tools for session management,
requirements storage, and test case persistence.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional

try:
    from google.adk.agents import Agent
    from google.adk.tools import FunctionTool
except ImportError:
    print("Warning: Google ADK not available. This is an example file.")
    Agent = None
    FunctionTool = None

from mcp_tools.tools import create_function_tools, mcp_tools


class MCPIntegratedAgent:
    """Example agent with MCP toolbox integration."""

    def __init__(self):
        """Initialize the agent with MCP tools."""
        self.mcp_tools = mcp_tools
        self.function_tools = create_function_tools()
        self.agent = None

    async def initialize(self):
        """Initialize the agent and MCP tools."""
        await self.mcp_tools.initialize()

        if Agent is not None:
            self.agent = Agent(
                model="gemini-2.0-flash-exp",
                name="mcp_integrated_agent",
                description="Agent with database and cache integration via MCP toolbox",
                instruction="""
                You are an intelligent agent that can manage sessions, requirements, and test cases
                using a database and caching system.

                When processing user requests:
                1. Always create or retrieve a session first using create_session or get_session
                2. Store requirements using create_requirement when analyzing user input
                3. Update requirements with create_requirement when they are edited
                4. Store test cases using create_test_cases_from_suite when generating test cases
                5. Track workflow steps using track_workflow_step for monitoring

                Use the available tools to persist all data and maintain session context.
                Always provide the session_id to users so they can reference their work later.
                """,
                tools=self.function_tools
            )

    async def process_workflow(
        self,
        user_input: str,
        user_id: str,
        session_id: Optional[str] = None,
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a complete workflow with MCP integration.

        Args:
            user_input: User's input text
            user_id: User identifier
            session_id: Optional existing session ID
            project_name: Optional project name

        Returns:
            Dictionary with workflow results
        """
        try:
            # Step 1: Create or get session
            if session_id is None:
                session_id = str(uuid.uuid4())
                session_result = await self.mcp_tools.create_session_tool(
                    session_id=session_id,
                    user_id=user_id,
                    project_name=project_name,
                    user_prompt=user_input,
                    agent_used="mcp_integrated_agent"
                )
                if not session_result["success"]:
                    return {"error": f"Failed to create session: {session_result['error']}"}
            else:
                session_result = await self.mcp_tools.get_session_tool(session_id)
                if not session_result["success"]:
                    return {"error": f"Session not found: {session_result['error']}"}

            # Step 2: Track workflow start
            await self.mcp_tools.track_workflow_step_tool(
                session_id=session_id,
                step_name="workflow_start",
                step_result={"user_input": user_input, "user_id": user_id}
            )

            # Step 3: Update session status to processing
            await self.mcp_tools.update_session_status_tool(session_id, "processing")

            # Step 4: Create requirements from user input
            # This is a simplified example - in real implementation,
            # you would use an analyzer agent here
            requirements = self._extract_requirements(user_input)

            for i, req_content in enumerate(requirements):
                await self.mcp_tools.create_requirement_tool(
                    session_id=session_id,
                    requirement_content=req_content,
                    requirement_type="functional",
                    priority="medium"
                )

            # Step 5: Generate test cases
            # This is a simplified example - in real implementation,
            # you would use a test case generator agent here
            test_suite = self._generate_test_suite(requirements, session_id)

            test_cases_result = await self.mcp_tools.create_test_cases_from_suite_tool(
                session_id=session_id,
                test_suite_json=test_suite
            )

            if not test_cases_result["success"]:
                return {"error": f"Failed to create test cases: {test_cases_result['error']}"}

            # Step 6: Update session status to completed
            await self.mcp_tools.update_session_status_tool(session_id, "completed")

            # Step 7: Track workflow completion
            await self.mcp_tools.track_workflow_step_tool(
                session_id=session_id,
                step_name="workflow_complete",
                step_result={
                    "requirements_created": len(requirements),
                    "test_cases_created": test_cases_result["test_cases_created"]
                }
            )

            # Step 8: Get full context for response
            context_result = await self.mcp_tools.get_session_with_full_context_tool(session_id)

            return {
                "success": True,
                "session_id": session_id,
                "requirements_created": len(requirements),
                "test_cases_created": test_cases_result["test_cases_created"],
                "context": context_result.get("context") if context_result["success"] else None
            }

        except Exception as e:
            # Track error
            if session_id:
                await self.mcp_tools.track_workflow_step_tool(
                    session_id=session_id,
                    step_name="workflow_error",
                    step_result={"error": str(e)}
                )
                await self.mcp_tools.update_session_status_tool(session_id, "failed")

            return {"error": str(e)}

    def _extract_requirements(self, user_input: str) -> list:
        """
        Extract requirements from user input.

        This is a simplified implementation. In reality, you would use
        an advanced NLP model or the requirement analyzer agent.
        """
        # Simple keyword-based extraction for demonstration
        requirements = []

        if "authentication" in user_input.lower():
            requirements.append("System must support user authentication")

        if "authorization" in user_input.lower():
            requirements.append("System must implement role-based authorization")

        if "oauth" in user_input.lower():
            requirements.append("System must support OAuth2 authentication flow")

        if "mfa" in user_input.lower() or "multi-factor" in user_input.lower():
            requirements.append("System must support multi-factor authentication")

        if not requirements:
            requirements.append(f"System requirement: {user_input}")

        return requirements

    def _generate_test_suite(self, requirements: list, session_id: str) -> str:
        """
        Generate a test suite JSON from requirements.

        This is a simplified implementation. In reality, you would use
        the test case generator agent.
        """
        import json
        from datetime import datetime

        test_cases = []

        for i, requirement in enumerate(requirements):
            test_case = {
                "test_id": f"TC_FUNC_{i+1:03d}",
                "priority": "HIGH",
                "type": "Functional",
                "summary": f"Test {requirement.lower()}",
                "preconditions": [
                    "System is running",
                    "Test environment is configured"
                ],
                "test_steps": [
                    "Navigate to the application",
                    f"Verify {requirement.lower()}",
                    "Confirm expected behavior"
                ],
                "test_data": {
                    "test_user": "testuser@example.com",
                    "test_password": "TestPassword123!"
                },
                "expected_result": f"System successfully implements: {requirement}",
                "requirement_traceability": f"REQ_{i+1:03d} - {requirement}"
            }
            test_cases.append(test_case)

        test_suite = {
            "test_suite": {
                "name": f"Test Suite for Session {session_id[:8]}",
                "description": "Generated test suite for authentication and authorization requirements",
                "total_tests": len(test_cases),
                "generated_date": datetime.now().date().isoformat(),
                "test_cases": test_cases
            }
        }

        return json.dumps(test_suite, indent=2)

    async def close(self):
        """Close MCP tools connections."""
        await self.mcp_tools.close()


# Example usage function
async def example_usage():
    """Demonstrate MCP toolbox usage."""
    agent = MCPIntegratedAgent()

    try:
        # Initialize
        await agent.initialize()

        # Process a sample workflow
        result = await agent.process_workflow(
            user_input="Create authentication system with OAuth2 and multi-factor authentication",
            user_id="user123",
            project_name="Security Enhancement Project"
        )

        print("Workflow Result:", result)

        # Retrieve session context
        if result.get("success") and result.get("session_id"):
            context = await agent.mcp_tools.get_session_with_full_context_tool(
                result["session_id"]
            )
            print("Session Context:", context)

    finally:
        await agent.close()


if __name__ == "__main__":
    """Run example usage."""
    asyncio.run(example_usage())