"""
Enhanced decider agent using Google's MCP Toolbox for databases.

This agent demonstrates integration with the MCP database server for persistent
session management, requirements storage, and test case persistence.
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
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from database_mcp.tools import create_database_tools, mcp_db_tools
    MCP_AVAILABLE = True
except ImportError:
    print("Warning: MCP Toolbox for databases not available. Running without persistence.")
    MCP_AVAILABLE = False
    mcp_db_tools = None


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
    Execute workflow with MCP Toolbox for databases integration.

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
        status = status.strip().lower()
        user_input = user_input.strip()

        if session_id is None:
            session_id = str(uuid.uuid4())

        if status == "start":
            # Create session in MCP database
            session_result = await mcp_db_tools.create_mcp_session(
                user_id="default_user",  # In production, get from context
                user_prompt=user_input,
                project_name="Authentication Analysis Project",
                agent_used="mcp_decider_agent",
                workflow_type="analysis_generation"
            )

            if not session_result["success"]:
                return {
                    "status": "failed",
                    "error": f"Failed to create MCP session: {session_result['error']}",
                    "session_id": session_id
                }

            # Use the MCP session ID
            mcp_session_id = session_result["session_id"]

            # Update session status to analyzing
            await mcp_db_tools.update_mcp_session_status(mcp_session_id, "analyzing")

            # Delegate to requirement analyzer
            analyzer, _ = create_remote_agents()

            try:
                analysis_response = await analyzer.run_async(
                    user_input=user_input,
                    session_id=mcp_session_id
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

                # Store analysis as requirement in MCP database
                req_result = await mcp_db_tools.store_agent_analysis_mcp(
                    session_id=mcp_session_id,
                    analysis_content=analysis_text,
                    analysis_type="requirements_analysis"
                )

                if not req_result["success"]:
                    print(f"Warning: Failed to store analysis in MCP database: {req_result['error']}")

                # Update session status
                await mcp_db_tools.update_mcp_session_status(mcp_session_id, "pending_review")

                return {
                    "status": "pending",
                    "stage": "awaiting_human_review",
                    "analysis": analysis_text,
                    "session_id": mcp_session_id,
                    "mcp_session_id": session_result.get("mcp_session_id"),
                    "persistence": "mcp_enabled",
                    "requirement_stored": req_result["success"]
                }

            except Exception as e:
                await mcp_db_tools.update_mcp_session_status(mcp_session_id, "analysis_failed")
                return {
                    "status": "failed",
                    "error": f"Analysis failed: {str(e)}",
                    "session_id": mcp_session_id
                }

        elif status in {"approved", "edited"}:
            # Get session to verify it exists
            session_result = await mcp_db_tools.get_mcp_session(session_id)
            if not session_result["success"]:
                return {
                    "status": "failed",
                    "error": "MCP session not found",
                    "session_id": session_id
                }

            # Update session status
            await mcp_db_tools.update_mcp_session_status(session_id, "generating")

            # Get input for generation
            if status == "edited":
                # Store edited requirement
                await mcp_db_tools.store_mcp_requirement(
                    session_id=session_id,
                    requirement_content=user_input,
                    requirement_type="edited_requirement",
                    source="user_edited"
                )
                input_text = user_input
            else:
                # Get original analysis from requirements
                requirements = await mcp_db_tools.get_mcp_session_requirements(session_id)
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

                # Store test cases in MCP database
                tc_result = await mcp_db_tools.store_generated_test_cases_mcp(
                    session_id=session_id,
                    test_cases_content=test_cases_text
                )

                if not tc_result["success"]:
                    print(f"Warning: Failed to store test cases in MCP database: {tc_result['error']}")

                # Update session status
                await mcp_db_tools.update_mcp_session_status(session_id, "completed")

                return {
                    "status": "done",
                    "stage": "test_cases_generated",
                    "test_cases": test_cases_text,
                    "session_id": session_id,
                    "persistence": "mcp_enabled",
                    "test_cases_stored": tc_result["success"],
                    "test_cases_created": tc_result.get("test_cases_created", 0)
                }

            except Exception as e:
                await mcp_db_tools.update_mcp_session_status(session_id, "generation_failed")
                return {
                    "status": "failed",
                    "error": f"Generation failed: {str(e)}",
                    "session_id": session_id
                }

        elif status == "rejected":
            if session_id:
                await mcp_db_tools.update_mcp_session_status(session_id, "rejected")

            return {
                "status": "failed",
                "stage": "rejected",
                "session_id": session_id,
                "persistence": "mcp_enabled"
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


# Tool to get MCP session context
async def get_mcp_session_context_tool(session_id: str) -> Dict[str, Any]:
    """Get complete MCP session context for debugging/monitoring."""
    if not MCP_AVAILABLE:
        return {"error": "MCP not available"}

    try:
        return await mcp_db_tools.get_mcp_session_context(session_id)
    except Exception as e:
        return {"error": str(e)}


# Create the workflow function (with or without MCP)
if MCP_AVAILABLE:
    execute_workflow = execute_workflow_with_mcp
else:
    execute_workflow = execute_workflow_fallback


# Create FunctionTool from the execute_workflow function
workflow_tool = FunctionTool(
    func=execute_workflow,
)

# Tool for getting MCP session context
context_tool = FunctionTool(
    func=get_mcp_session_context_tool,
)

# Create tools list - include MCP tools if available
tools = [workflow_tool, context_tool]
if MCP_AVAILABLE:
    mcp_function_tools = create_database_tools()
    tools.extend(mcp_function_tools)

# Create remote agents as sub-agents
requirement_analyzer, test_case_generator = create_remote_agents()

# Create root agent with sub-agents and tools
root_agent = Agent(
    model="gemini-2.0-flash-exp",
    name="mcp_decider_agent",
    description="Enhanced workflow decider agent using Google's MCP Toolbox for databases",
    instruction=f"""
    You are an advanced workflow orchestrator agent that manages authentication requirements analysis and test case generation with Google's MCP Toolbox for databases.

    {'🔗 GOOGLE MCP TOOLBOX ENABLED: You have access to persistent storage via Google\'s Model Context Protocol (MCP) for databases.' if MCP_AVAILABLE else '⚠️ MCP TOOLBOX DISABLED: Running in fallback mode with in-memory storage.'}

    ## Core Workflow:

    For every user message, follow this enhanced workflow:

    1. **Parse Input**: Extract status, user_input, and optional session_id from the message format:
       - "status; user_input" or "status; user_input; session_id"
       - Status can be: 'start', 'approved', 'edited', or 'rejected'

    2. **Execute Workflow**: Call the 'execute_workflow' tool with parsed parameters.

    3. **Delegate to Sub-agents**: Based on the workflow result:
       - If status is 'start': Delegate to 'requirement_analyzer' sub-agent
       - If status is 'approved'/'edited': Delegate to 'test_case_generator' sub-agent
       - If status is 'rejected': Acknowledge and offer to restart

    ## MCP Integration Features {'(ENABLED)' if MCP_AVAILABLE else '(DISABLED)'}:

    {'### Database Persistence:' if MCP_AVAILABLE else '### Fallback Mode:'}
    {'- Sessions stored in PostgreSQL via MCP protocol' if MCP_AVAILABLE else '- Sessions stored in memory only (lost on restart)'}
    {'- Requirements automatically persisted with full history' if MCP_AVAILABLE else '- No requirements persistence'}
    {'- Test cases stored in structured JSON format' if MCP_AVAILABLE else '- No test case persistence'}
    {'- Complete audit trail of all operations' if MCP_AVAILABLE else '- Limited operation tracking'}

    {'### MCP Protocol Benefits:' if MCP_AVAILABLE else ''}
    {'- Standardized database communication' if MCP_AVAILABLE else ''}
    {'- Automatic connection management' if MCP_AVAILABLE else ''}
    {'- Transaction safety and rollback' if MCP_AVAILABLE else ''}
    {'- Performance optimization' if MCP_AVAILABLE else ''}

    {'### Available MCP Tools:' if MCP_AVAILABLE else ''}
    {'- create_mcp_session: Create new persistent session' if MCP_AVAILABLE else ''}
    {'- get_mcp_session: Retrieve session data' if MCP_AVAILABLE else ''}
    {'- store_mcp_requirement: Persist requirements' if MCP_AVAILABLE else ''}
    {'- store_mcp_test_cases: Persist test cases in structured format' if MCP_AVAILABLE else ''}
    {'- get_mcp_session_context: Get complete session with all data' if MCP_AVAILABLE else ''}

    ## Test Case Format:
    When test cases are generated, they are automatically stored in this structured format:
    ```json
    {{
      "test_suite": {{
        "name": "Suite Name",
        "description": "Brief description",
        "total_tests": 0,
        "generated_date": "2025-10-31",
        "test_cases": [
          {{
            "test_id": "TC_TYPE_NNN",
            "priority": "CRITICAL|HIGH|MEDIUM|LOW",
            "type": "Functional|Security|Edge Case|Negative",
            "summary": "One-line summary",
            "preconditions": ["condition 1", "condition 2"],
            "test_steps": ["step 1", "step 2", "step 3"],
            "test_data": {{"field1": "value1", "field2": "value2"}},
            "expected_result": "Clear expected outcome",
            "requirement_traceability": "REQ_ID - description"
          }}
        ]
      }}
    }}
    ```

    ## Response Guidelines:
    - Always maintain session_id throughout the workflow
    - Provide clear status updates about persistence state
    - Use get_mcp_session_context_tool when users ask for session details
    - Inform users about the benefits of MCP-based persistence
    - When errors occur, provide clear guidance on next steps

    Remember: You're using Google's official MCP Toolbox approach for maximum reliability and standards compliance!
    """,
    sub_agents=[requirement_analyzer, test_case_generator],
    tools=tools,
)