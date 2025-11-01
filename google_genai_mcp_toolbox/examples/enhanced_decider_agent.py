"""
Enhanced Decider Agent with Google GenAI MCP Toolbox integration.

This example shows how to integrate the existing decider agent with
Google's GenAI Toolbox for persistent database operations.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

# Import the existing decider agent
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../decider/decider_agent'))

try:
    from agent import DeciderAgent
except ImportError:
    print("⚠️  Decider agent not found. Creating mock implementation.")

    class DeciderAgent:
        """Mock DeciderAgent for demonstration."""

        def __init__(self, **kwargs):
            self.name = kwargs.get('name', 'mock_decider')

        async def process_request(self, user_prompt: str, **kwargs) -> Dict[str, Any]:
            """Mock request processing."""
            return {
                "decision": f"Mock decision for: {user_prompt[:50]}...",
                "reasoning": "This is a mock implementation",
                "recommendations": ["Install the actual DeciderAgent", "Configure proper integration"]
            }

# Import Toolbox integration
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from adk_toolbox import ToolboxClient, create_adk_toolbox_tools, SessionContext
except ImportError:
    print("⚠️  ADK Toolbox not available. Please install dependencies.")
    ToolboxClient = None


class EnhancedDeciderAgent:
    """
    Enhanced Decider Agent with Google GenAI MCP Toolbox persistence.

    This agent extends the original DeciderAgent with:
    - Session management and persistence
    - Requirements storage and tracking
    - Test case generation and storage
    - Complete workflow context retrieval
    """

    def __init__(self,
                 toolbox_server_url: str = "http://localhost:5000",
                 agent_config: Dict[str, Any] = None):
        """
        Initialize the enhanced decider agent.

        Args:
            toolbox_server_url: URL of the GenAI Toolbox server
            agent_config: Configuration for the underlying DeciderAgent
        """
        self.toolbox_server_url = toolbox_server_url

        # Initialize the base DeciderAgent
        self.base_agent = DeciderAgent(**(agent_config or {}))

        # Add Toolbox tools if available
        if ToolboxClient:
            self.toolbox_tools = create_adk_toolbox_tools(toolbox_server_url)
        else:
            self.toolbox_tools = []

        self.current_session_id = None

    async def process_request_with_persistence(self,
                                             user_prompt: str,
                                             user_id: str,
                                             project_name: Optional[str] = None,
                                             store_requirements: bool = True,
                                             generate_test_cases: bool = True) -> Dict[str, Any]:
        """
        Process a request with full persistence workflow.

        Args:
            user_prompt: User's request/prompt
            user_id: User identifier
            project_name: Optional project name
            store_requirements: Whether to store requirements analysis
            generate_test_cases: Whether to generate and store test cases

        Returns:
            Dictionary containing the complete workflow result
        """
        if not ToolboxClient:
            # Fallback to base agent without persistence
            result = await self.base_agent.process_request(user_prompt)
            result["warning"] = "Persistence not available - ToolboxClient not installed"
            return result

        try:
            async with ToolboxClient(self.toolbox_server_url) as client:
                # Step 1: Create session
                session = await client.create_session(user_id, user_prompt, project_name)
                self.current_session_id = str(session.session_id)

                print(f"✅ Created session: {self.current_session_id}")

                # Step 2: Process with base agent
                base_result = await self.base_agent.process_request(user_prompt)

                # Step 3: Store requirements if requested
                stored_requirements = []
                if store_requirements and "requirements" in base_result:
                    for req in base_result["requirements"]:
                        requirement = await client.store_requirement(
                            session_id=self.current_session_id,
                            content=req.get("content", ""),
                            requirement_type=req.get("type", "functional"),
                            priority=req.get("priority", "medium")
                        )
                        stored_requirements.append(requirement.to_dict())

                # Step 4: Generate and store test cases if requested
                stored_test_cases = []
                if generate_test_cases:
                    test_cases = await self._generate_test_cases_from_decision(base_result)
                    for tc_data in test_cases:
                        test_case = await client.store_test_case_from_json(
                            session_id=self.current_session_id,
                            test_case_json=tc_data
                        )
                        stored_test_cases.append(test_case.to_dict())

                # Step 5: Get complete session context
                context = await client.get_session_context(self.current_session_id)

                # Prepare enhanced result
                enhanced_result = {
                    **base_result,
                    "session_id": self.current_session_id,
                    "persistence": {
                        "session": session.to_dict(),
                        "requirements_stored": len(stored_requirements),
                        "test_cases_stored": len(stored_test_cases),
                        "context": context.to_dict() if context else None
                    },
                    "toolbox_integration": True
                }

                return enhanced_result

        except Exception as e:
            print(f"❌ Error in persistent workflow: {e}")
            # Fallback to base agent
            result = await self.base_agent.process_request(user_prompt)
            result["persistence_error"] = str(e)
            return result

    async def continue_session(self, session_id: str, additional_prompt: str) -> Dict[str, Any]:
        """
        Continue an existing session with additional input.

        Args:
            session_id: Existing session ID
            additional_prompt: Additional user input

        Returns:
            Dictionary containing the updated workflow result
        """
        if not ToolboxClient:
            return {"error": "Persistence not available"}

        try:
            async with ToolboxClient(self.toolbox_server_url) as client:
                # Get existing session context
                context = await client.get_session_context(session_id)
                if not context:
                    return {"error": "Session not found"}

                # Combine previous context with new prompt
                full_prompt = f"""
                Previous session context:
                - Original prompt: {context.session.user_prompt}
                - Requirements: {len(context.requirements)} stored
                - Test cases: {len(context.test_cases)} stored

                Additional request: {additional_prompt}
                """

                # Process with base agent
                result = await self.base_agent.process_request(full_prompt)

                # Store additional requirements if any
                if "requirements" in result:
                    for req in result["requirements"]:
                        await client.store_requirement(
                            session_id=session_id,
                            content=req.get("content", ""),
                            requirement_type=req.get("type", "functional"),
                            priority=req.get("priority", "medium")
                        )

                # Update session status
                await client.update_session_status(session_id, "active")

                # Get updated context
                updated_context = await client.get_session_context(session_id)

                return {
                    **result,
                    "session_id": session_id,
                    "session_continued": True,
                    "updated_context": updated_context.to_dict() if updated_context else None
                }

        except Exception as e:
            return {"error": f"Error continuing session: {str(e)}"}

    async def get_session_history(self, user_id: str) -> Dict[str, Any]:
        """
        Get all sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary containing user's session history
        """
        if not ToolboxClient:
            return {"error": "Persistence not available"}

        try:
            async with ToolboxClient(self.toolbox_server_url) as client:
                sessions = await client.get_user_sessions(user_id)
                return {
                    "user_id": user_id,
                    "sessions": [session.to_dict() for session in sessions],
                    "total_sessions": len(sessions)
                }
        except Exception as e:
            return {"error": f"Error getting session history: {str(e)}"}

    async def export_session_as_test_suite(self, session_id: str) -> Dict[str, Any]:
        """
        Export session test cases as a structured test suite.

        Args:
            session_id: Session ID to export

        Returns:
            Dictionary containing the test suite
        """
        if not ToolboxClient:
            return {"error": "Persistence not available"}

        try:
            async with ToolboxClient(self.toolbox_server_url) as client:
                context = await client.get_session_context(session_id)
                if not context:
                    return {"error": "Session not found"}

                test_suite = context.to_test_suite_json()
                return {
                    "success": True,
                    "session_id": session_id,
                    "test_suite": test_suite
                }
        except Exception as e:
            return {"error": f"Error exporting test suite: {str(e)}"}

    async def _generate_test_cases_from_decision(self, decision_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate test cases from the decider agent's output.

        Args:
            decision_result: Result from the base DeciderAgent

        Returns:
            List of test case dictionaries
        """
        test_cases = []

        # Extract key elements from decision
        decision = decision_result.get("decision", "")
        recommendations = decision_result.get("recommendations", [])
        reasoning = decision_result.get("reasoning", "")

        # Generate test cases based on recommendations
        for i, recommendation in enumerate(recommendations[:3], 1):  # Limit to 3 test cases
            test_case = {
                "test_id": f"TC_DEC_{i:03d}",
                "priority": "HIGH" if i == 1 else "MEDIUM",
                "type": "Functional",
                "summary": f"Test implementation of: {recommendation[:80]}...",
                "preconditions": [
                    "System is properly configured",
                    "Required dependencies are installed",
                    "Test environment is available"
                ],
                "test_steps": [
                    f"Implement recommendation: {recommendation}",
                    "Verify implementation meets requirements",
                    "Test functionality and edge cases",
                    "Validate against acceptance criteria"
                ],
                "test_data": {
                    "recommendation": recommendation,
                    "decision_context": decision[:100] + "..." if len(decision) > 100 else decision
                },
                "expected_result": f"Recommendation '{recommendation}' is successfully implemented and working as expected",
                "requirement_traceability": f"REQ_DEC_{i:03d} - {recommendation[:50]}..."
            }
            test_cases.append(test_case)

        # Add a general decision validation test case
        if test_cases:
            validation_test = {
                "test_id": "TC_DEC_VAL",
                "priority": "CRITICAL",
                "type": "Validation",
                "summary": "Validate overall decision implementation",
                "preconditions": [
                    "All recommendation test cases have passed",
                    "System integration is complete"
                ],
                "test_steps": [
                    "Review all implemented recommendations",
                    "Test end-to-end workflow",
                    "Validate decision reasoning is sound",
                    "Confirm objectives are met"
                ],
                "test_data": {
                    "full_decision": decision,
                    "reasoning": reasoning,
                    "total_recommendations": len(recommendations)
                },
                "expected_result": "All recommendations are successfully implemented and the overall decision objective is achieved",
                "requirement_traceability": "REQ_DEC_OVERALL - Complete decision implementation"
            }
            test_cases.append(validation_test)

        return test_cases


async def example_usage():
    """Example of using the Enhanced Decider Agent."""
    print("🚀 Enhanced Decider Agent with Google GenAI MCP Toolbox")
    print("=" * 60)

    # Initialize the enhanced agent
    agent = EnhancedDeciderAgent(
        toolbox_server_url="http://localhost:5000",
        agent_config={
            "name": "enhanced_decider",
            "model": "gpt-4"  # or whatever model you prefer
        }
    )

    try:
        # Example 1: Process a request with persistence
        print("\n📝 Example 1: Processing request with persistence")
        result = await agent.process_request_with_persistence(
            user_prompt="I need to design a user authentication system with OAuth2 and multi-factor authentication",
            user_id="example_user_123",
            project_name="Authentication System Design"
        )

        if "session_id" in result:
            session_id = result["session_id"]
            print(f"✅ Session created: {session_id}")
            print(f"📊 Requirements stored: {result['persistence']['requirements_stored']}")
            print(f"🧪 Test cases stored: {result['persistence']['test_cases_stored']}")

            # Example 2: Continue the session
            print(f"\n🔄 Example 2: Continuing session {session_id}")
            continue_result = await agent.continue_session(
                session_id=session_id,
                additional_prompt="Also add support for social login (Google, Facebook, GitHub)"
            )

            if continue_result.get("session_continued"):
                print("✅ Session continued successfully")

            # Example 3: Export as test suite
            print(f"\n📋 Example 3: Exporting session as test suite")
            export_result = await agent.export_session_as_test_suite(session_id)

            if export_result.get("success"):
                test_suite = export_result["test_suite"]
                print(f"✅ Test suite exported with {test_suite['test_suite']['total_tests']} test cases")

                # Save to file
                with open(f"test_suite_{session_id[:8]}.json", "w") as f:
                    json.dump(test_suite, f, indent=2)
                print(f"💾 Test suite saved to: test_suite_{session_id[:8]}.json")

        # Example 4: Get user session history
        print(f"\n📚 Example 4: Getting user session history")
        history_result = await agent.get_session_history("example_user_123")

        if "sessions" in history_result:
            print(f"✅ Found {history_result['total_sessions']} sessions for user")

    except Exception as e:
        print(f"❌ Error in example: {e}")

    print("\n🎉 Enhanced Decider Agent example completed!")


if __name__ == "__main__":
    asyncio.run(example_usage())