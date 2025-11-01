"""
Enhanced decider agent with MCP toolbox integration.

This agent integrates with the MCP toolbox for persistent session management,
requirements storage, and test case persistence.
"""

from google.adk.agents import Agent
from a2a.client import ClientFactory, ClientConfig
from a2a.types import TransportProtocol
from google.adk.tools import FunctionTool
import httpx
from google.auth import default
from google.auth.transport.requests import Request
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from typing import Optional, Dict, Any
import uuid
import json
import sys
import os

# Add MCP toolbox to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'mcp_toolbox'))

try:
    from mcp_tools.tools import create_function_tools, mcp_tools
    MCP_AVAILABLE = True
except ImportError:
    print("Warning: MCP toolbox not available. Running without persistence.")
    MCP_AVAILABLE = False
    mcp_tools = None


PROJECT_ID = "195472357560"
LOCATION = "us-central1"
ANALYZER_RESOURCE_ID = "5155975060502085632"
GENERATOR_RESOURCE_ID = "7810284090883571712"

ANALYZER_CARD_URL = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ANALYZER_RESOURCE_ID}/a2a/v1/card"
GENERATOR_CARD_URL = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{GENERATOR_RESOURCE_ID}/a2a/v1/card"

# In-memory state for sessions without MCP
agent_state: Dict[str, Any] = {}


def create_client_factory():
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    httpx_client = httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        },
        timeout=60.0,
    )
    return ClientFactory(
        ClientConfig(
            supported_transports=[TransportProtocol.http_json],
            use_client_preference=True,
            httpx_client=httpx_client,
        ),
    )


def create_remote_agents():
    """Create and return remote A2A agents"""
    requirement_analyzer = RemoteA2aAgent(
        name="requirement_analyzer",
        description="Auth requirements analyzer that analyzes authentication and authorization requirements",
        agent_card=ANALYZER_CARD_URL,
        a2a_client_factory=create_client_factory(),
    )

    test_case_generator = RemoteA2aAgent(
        name="test_case_generator",
        description="Test case generator that generates test cases based on analysis",
        agent_card=GENERATOR_CARD_URL,
        a2a_client_factory=create_client_factory(),
    )

    return requirement_analyzer, test_case_generator


async def execute_workflow_with_mcp(status: str, user_input: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute workflow with MCP toolbox integration for persistence.

    Args:
        status: Workflow status - 'start', 'approved', 'edited', or 'rejected'
        user_input: User input text for the workflow
        session_id: Optional session ID for tracking workflow state

    Returns:
        Workflow result with status, stage, and relevant data
    """
    if not MCP_AVAILABLE:
        return await execute_workflow_fallback(status, user_input, session_id)

    try:
        # Initialize MCP tools
        await mcp_tools.initialize()

        status = status.strip().lower()
        user_input = user_input.strip()

        if session_id is None:
            session_id = str(uuid.uuid4())

        if status == "start":
            # Create session in database
            session_result = await mcp_tools.create_session_tool(
                session_id=session_id,
                user_id="default_user",  # In production, get from context
                project_name="Authentication Project",
                user_prompt=user_input,
                agent_used="decider_agent",
                workflow_type="analysis_generation"
            )

            if not session_result["success"]:
                return {
                    "status": "failed",
                    "error": f"Failed to create session: {session_result['error']}",
                    "session_id": session_id
                }

            # Track workflow start
            await mcp_tools.track_workflow_step_tool(
                session_id=session_id,
                step_name="workflow_start",
                step_result={"user_input": user_input, "status": status}
            )

            # Update session status
            await mcp_tools.update_session_status_tool(session_id, "analyzing")

            # Delegate to requirement analyzer
            analyzer, _ = create_remote_agents()

            try:
                analysis_response = await analyzer.run_async(
                    user_input=user_input,
                    session_id=session_id
                )

                # Extract analysis text
                analysis_text = ""
                if hasattr(analysis_response, 'output') and analysis_response.output:
                    analysis_text = str(analysis_response.output)
                elif hasattr(analysis_response, 'message') and analysis_response.message:
                    if hasattr(analysis_response.message, 'parts') and analysis_response.message.parts:
                        analysis_text = analysis_response.message.parts[0].text
                else:
                    analysis_text = str(analysis_response)

                # Store requirements in database
                await mcp_tools.create_requirement_tool(
                    session_id=session_id,
                    requirement_content=analysis_text,
                    requirement_type="functional",
                    priority="medium",
                    source="agent_generated"
                )

                # Track analysis completion
                await mcp_tools.track_workflow_step_tool(
                    session_id=session_id,
                    step_name="analysis_complete",
                    step_result={"analysis": analysis_text}
                )

                # Update session status
                await mcp_tools.update_session_status_tool(session_id, "pending_review")

                return {
                    "status": "pending",
                    "stage": "awaiting_human_review",
                    "analysis": analysis_text,
                    "session_id": session_id,
                    "persistence": "enabled"
                }

            except Exception as e:
                await mcp_tools.track_workflow_step_tool(
                    session_id=session_id,
                    step_name="analysis_error",
                    step_result={"error": str(e)}
                )
                return {
                    "status": "failed",
                    "error": f"Analysis failed: {str(e)}",
                    "session_id": session_id
                }

        elif status in {"approved", "edited"}:
            # Get session to verify it exists
            session_result = await mcp_tools.get_session_tool(session_id)
            if not session_result["success"]:
                return {
                    "status": "failed",
                    "error": "Session not found",
                    "session_id": session_id
                }

            # Update session status
            await mcp_tools.update_session_status_tool(session_id, "generating")

            # Get input for generation
            if status == "edited":
                # Update requirement with edited content
                requirements = await mcp_tools.get_session_requirements_tool(session_id)
                if requirements["success"] and requirements["requirements"]:
                    req_id = requirements["requirements"][0]["id"]
                    await mcp_tools.update_requirement_tool(
                        requirement_id=req_id,
                        edited_content=user_input
                    )
                input_text = user_input
            else:
                # Get original analysis from requirements
                requirements = await mcp_tools.get_session_requirements_tool(session_id)
                if requirements["success"] and requirements["requirements"]:
                    input_text = requirements["requirements"][0]["original_content"]
                else:
                    input_text = user_input

            # Delegate to test case generator
            _, generator = create_remote_agents()

            try:
                generated_response = await generator.run_async(
                    user_input=input_text,
                    session_id=session_id
                )

                # Extract test cases
                test_cases_text = ""
                if hasattr(generated_response, 'output') and generated_response.output:
                    test_cases_text = str(generated_response.output)
                elif hasattr(generated_response, 'message') and generated_response.message:
                    if hasattr(generated_response.message, 'parts') and generated_response.message.parts:
                        test_cases_text = generated_response.message.parts[0].text
                else:
                    test_cases_text = str(generated_response)

                # Try to parse and store test cases in structured format
                try:
                    # Attempt to parse as JSON
                    if test_cases_text.strip().startswith('{'):
                        await mcp_tools.create_test_cases_from_suite_tool(
                            session_id=session_id,
                            test_suite_json=test_cases_text
                        )
                    else:
                        # Create a simple test suite structure
                        simple_suite = {
                            "test_suite": {
                                "name": f"Test Suite for Session {session_id[:8]}",
                                "description": "Generated test cases",
                                "total_tests": 1,
                                "generated_date": "2025-10-31",
                                "test_cases": [
                                    {
                                        "test_id": "TC_GEN_001",
                                        "priority": "MEDIUM",
                                        "type": "Functional",
                                        "summary": "Generated test case",
                                        "preconditions": ["System is ready"],
                                        "test_steps": test_cases_text.split('\n')[:5],
                                        "test_data": {},
                                        "expected_result": "Test passes as expected",
                                        "requirement_traceability": "Generated from analysis"
                                    }
                                ]
                            }
                        }
                        await mcp_tools.create_test_cases_from_suite_tool(
                            session_id=session_id,
                            test_suite_json=json.dumps(simple_suite)
                        )

                except Exception as e:
                    print(f"Warning: Could not parse test cases as structured format: {e}")

                # Track generation completion
                await mcp_tools.track_workflow_step_tool(
                    session_id=session_id,
                    step_name="generation_complete",
                    step_result={"test_cases": test_cases_text}
                )

                # Update session status
                await mcp_tools.update_session_status_tool(session_id, "completed")

                return {
                    "status": "done",
                    "stage": "test_cases_generated",
                    "test_cases": test_cases_text,
                    "session_id": session_id,
                    "persistence": "enabled"
                }

            except Exception as e:
                await mcp_tools.track_workflow_step_tool(
                    session_id=session_id,
                    step_name="generation_error",
                    step_result={"error": str(e)}
                )
                return {
                    "status": "failed",
                    "error": f"Generation failed: {str(e)}",
                    "session_id": session_id
                }

        elif status == "rejected":
            if session_id:
                await mcp_tools.update_session_status_tool(session_id, "rejected")
                await mcp_tools.track_workflow_step_tool(
                    session_id=session_id,
                    step_name="workflow_rejected",
                    step_result={"reason": "User rejected analysis"}
                )

            return {
                "status": "failed",
                "stage": "rejected",
                "session_id": session_id,
                "persistence": "enabled"
            }

        else:
            return {
                "status": "failed",
                "reason": "invalid_status",
                "session_id": session_id
            }

    except Exception as e:
        return {
            "status": "failed",
            "error": f"MCP integration error: {str(e)}",
            "session_id": session_id
        }


async def execute_workflow_fallback(status: str, user_input: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Fallback workflow execution without MCP (original implementation).
    """
    global agent_state

    status = status.strip().lower()
    user_input = user_input.strip()

    if session_id is None:
        session_id = str(uuid.uuid4())

    if session_id not in agent_state:
        agent_state[session_id] = {}

    session_data = agent_state[session_id]

    if status == "start":
        # The root agent will delegate to requirement_analyzer sub-agent
        session_data["analyzer_input"] = user_input
        return {
            "status": "delegating",
            "stage": "analyzing",
            "delegate_to": "requirement_analyzer",
            "input": user_input,
            "session_id": session_id,
            "persistence": "disabled"
        }

    elif status in {"approved", "edited"}:
        input_text = user_input if status == "edited" else session_data.get("last_analysis", "")

        # The root agent will delegate to test_case_generator sub-agent
        return {
            "status": "delegating",
            "stage": "generating",
            "delegate_to": "test_case_generator",
            "input": input_text,
            "session_id": session_id,
            "persistence": "disabled"
        }

    elif status == "rejected":
        return {
            "status": "failed",
            "stage": "rejected",
            "session_id": session_id,
            "persistence": "disabled"
        }

    else:
        return {
            "status": "failed",
            "reason": "invalid_status",
            "session_id": session_id
        }


# Create the workflow function (with or without MCP)
if MCP_AVAILABLE:
    execute_workflow = execute_workflow_with_mcp
else:
    execute_workflow = execute_workflow_fallback


# Create FunctionTool from the execute_workflow function
workflow_tool = FunctionTool(
    func=execute_workflow,
)

# Create tools list - include MCP tools if available
tools = [workflow_tool]
if MCP_AVAILABLE:
    mcp_function_tools = create_function_tools()
    tools.extend(mcp_function_tools)

# Create remote agents as sub-agents
requirement_analyzer, test_case_generator = create_remote_agents()

# Create root agent with sub-agents and tools
root_agent = Agent(
    model="gemini-2.0-flash-exp",
    name="decider_agent_with_mcp",
    description="Enhanced workflow decider agent with persistent session management via MCP toolbox",
    instruction=f"""
    You are an enhanced workflow orchestrator agent that manages authentication requirements analysis and test case generation with persistent data storage.

    {'🔗 MCP TOOLBOX ENABLED: You have access to persistent storage via Cloud SQL and Redis caching.' if MCP_AVAILABLE else '⚠️ MCP TOOLBOX DISABLED: Running in fallback mode with in-memory storage.'}

    For every user message, follow this workflow:

    1. **Parse Input**: Extract status, user_input, and optional session_id from the message format:
       - "status; user_input" or "status; user_input; session_id"
       - Status can be: 'start', 'approved', 'edited', or 'rejected'

    2. **Execute Workflow**: Call the 'execute_workflow' tool with parsed parameters.

    3. **Delegate to Sub-agents**: Based on the workflow result:
       - If status is 'start': Delegate to 'requirement_analyzer' sub-agent
       - If status is 'approved'/'edited': Delegate to 'test_case_generator' sub-agent
       - If status is 'rejected': Acknowledge and offer to restart

    4. **Session Management** {'(MCP Enabled)' if MCP_AVAILABLE else '(Fallback Mode)'}:
       {'- Sessions are persisted in Cloud SQL database' if MCP_AVAILABLE else '- Sessions are stored in memory only'}
       {'- Requirements and test cases are stored permanently' if MCP_AVAILABLE else '- Data is lost when process restarts'}
       {'- Redis caching for performance optimization' if MCP_AVAILABLE else '- No caching available'}
       {'- Full workflow tracking and audit trail' if MCP_AVAILABLE else '- Limited state tracking'}

    {'5. **Additional Tools Available**:' if MCP_AVAILABLE else ''}
    {'   - get_session: Retrieve session data' if MCP_AVAILABLE else ''}
    {'   - get_session_requirements: Get stored requirements' if MCP_AVAILABLE else ''}
    {'   - get_session_test_cases: Get stored test cases' if MCP_AVAILABLE else ''}
    {'   - get_session_with_full_context: Get complete session data' if MCP_AVAILABLE else ''}

    Always maintain session_id throughout the workflow and provide clear status updates to users.
    When responding, clearly indicate whether persistence is enabled or disabled.
    """,
    sub_agents=[requirement_analyzer, test_case_generator],
    tools=tools,
)