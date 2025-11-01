# from google.adk.agents import Agent

# from a2a.client import ClientFactory, ClientConfig
# from a2a.types import TransportProtocol
# from google.adk.tools import FunctionTool
# import httpx
# from google.auth import default
# from google.auth.transport.requests import Request
# from google.adk.tools import ToolContext
# from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
# from typing import Optional, Dict, Any
# import asyncio
# import json
# import uuid


# PROJECT_ID = "195472357560"
# LOCATION = "us-central1"
# ANALYZER_RESOURCE_ID = "5155975060502085632"
# GENERATOR_RESOURCE_ID = "5036488932888412160"

# ANALYZER_CARD_URL = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ANALYZER_RESOURCE_ID}/a2a/v1/card"
# GENERATOR_CARD_URL = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{GENERATOR_RESOURCE_ID}/a2a/v1/card"

# agent_state: Dict[str, Any] = {}

# def create_client_factory():
#     credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
#     credentials.refresh(Request())
#     httpx_client = httpx.Client(
#         headers={
#             "Authorization": f"Bearer {credentials.token}",
#             "Content-Type": "application/json",
#         },
#         timeout=60.0,
#     )
#     return ClientFactory(
#         ClientConfig(
#             supported_transports=[TransportProtocol.http_json],
#             use_client_preference=True,
#             httpx_client=httpx_client,
#         ),
#     )

# analyzer_agent = None
# generator_agent = None

# def get_remote_agents():
#     global analyzer_agent, generator_agent

#     if analyzer_agent is None:
#         analyzer_agent = RemoteA2aAgent(
#             name="requirement_analyzer",
#             description="Auth requirements analyzer",
#             agent_card=ANALYZER_CARD_URL,
#             a2a_client_factory=create_client_factory(),
#         )

#     if generator_agent is None:
#         generator_agent = RemoteA2aAgent(
#             name="test_case_generator",
#             description="Test case generator",
#             agent_card=GENERATOR_CARD_URL,
#             a2a_client_factory=create_client_factory(),
#         )

#     return analyzer_agent, generator_agent

# async def execute_workflow(status: str, user_input: str, session_id: Optional[str] = None) -> Dict[str, Any]:
#     """
#     Execute workflow based on status.

#     Args:
#         status: Workflow status - 'start', 'approved', 'edited', or 'rejected'
#         user_input: User input text for the workflow
#         session_id: Optional session ID for tracking workflow state

#     Returns:
#         Workflow result with status, stage, and relevant data
#     """
#     global agent_state

#     analyzer, generator = get_remote_agents()

#     status = status.strip().lower()
#     user_input = user_input.strip()

#     if session_id is None:
#         session_id = str(uuid.uuid4())

#     if session_id not in agent_state:
#         agent_state[session_id] = {}

#     session_data = agent_state[session_id]

#     if status == "start":
#         analysis_response = await analyzer.send_message(user_input, session_id=session_id)
#         analysis_text = (
#             analysis_response.message.parts[0].text
#             if analysis_response.message.parts
#             else "<no analysis>"
#         )
#         session_data["last_analysis"] = analysis_text
#         return {
#             "status": "pending",
#             "stage": "awaiting_human_review",
#             "analysis": analysis_text,
#             "session_id": session_id
#         }

#     elif status in {"approved", "edited"}:
#         input_text = user_input if status == "edited" else session_data.get("last_analysis", "")
#         generated_response = await generator.send_message(input_text, session_id=session_id)
#         test_cases_text = (
#             generated_response.message.parts[0].text
#             if generated_response.message.parts
#             else "<no test cases>"
#         )
#         return {
#             "status": "done",
#             "stage": "test_cases_generated",
#             "test_cases": test_cases_text,
#             "session_id": session_id
#         }

#     elif status == "rejected":
#         return {
#             "status": "failed",
#             "stage": "rejected",
#             "session_id": session_id
#         }

#     else:
#         return {
#             "status": "failed",
#             "reason": "invalid_status",
#             "session_id": session_id
#         }

# # Create FunctionTool from the execute_workflow function
# workflow_tool = FunctionTool(
#     func=execute_workflow,
# )

# root_agent = Agent(
#     model="gemini-2.0-flash-exp",
#     name="decider_agent",
#     description="Workflow decider agent",
#     instruction="""You are a workflow orchestrator. When you receive a message in the format "status; user_input",
#     you MUST call the execute_workflow tool with the parsed status and user_input parameters.

#     Always extract the status and user_input from the message and call execute_workflow.
#     Return the exact response from execute_workflow to the user.""",
#     tools=[workflow_tool],
# )



# from google.adk.agents import Agent
# from a2a.client import ClientFactory, ClientConfig
# from a2a.types import TransportProtocol
# from google.adk.tools import FunctionTool
# import httpx
# from google.auth import default
# from google.auth.transport.requests import Request
# from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
# from typing import Optional, Dict, Any
# import uuid


# PROJECT_ID = "195472357560"
# LOCATION = "us-central1"
# ANALYZER_RESOURCE_ID = "5155975060502085632"
# GENERATOR_RESOURCE_ID = "5036488932888412160"

# ANALYZER_CARD_URL = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ANALYZER_RESOURCE_ID}/a2a/v1/card"
# GENERATOR_CARD_URL = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{GENERATOR_RESOURCE_ID}/a2a/v1/card"

# agent_state: Dict[str, Any] = {}

# def create_client_factory():
#     credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
#     credentials.refresh(Request())
#     httpx_client = httpx.Client(
#         headers={
#             "Authorization": f"Bearer {credentials.token}",
#             "Content-Type": "application/json",
#         },
#         timeout=60.0,
#     )
#     return ClientFactory(
#         ClientConfig(
#             supported_transports=[TransportProtocol.http_json],
#             use_client_preference=True,
#             httpx_client=httpx_client,
#         ),
#     )

# analyzer_agent = None
# generator_agent = None

# def get_remote_agents():
#     global analyzer_agent, generator_agent

#     if analyzer_agent is None:
#         analyzer_agent = RemoteA2aAgent(
#             name="requirement_analyzer",
#             description="Auth requirements analyzer",
#             agent_card=ANALYZER_CARD_URL,
#             a2a_client_factory=create_client_factory(),
#         )

#     if generator_agent is None:
#         generator_agent = RemoteA2aAgent(
#             name="test_case_generator",
#             description="Test case generator",
#             agent_card=GENERATOR_CARD_URL,
#             a2a_client_factory=create_client_factory(),
#         )

#     return analyzer_agent, generator_agent

# async def execute_workflow(status: str, user_input: str, session_id: Optional[str] = None) -> Dict[str, Any]:
#     """
#     Execute workflow based on status.

#     Args:
#         status: Workflow status - 'start', 'approved', 'edited', or 'rejected'
#         user_input: User input text for the workflow
#         session_id: Optional session ID for tracking workflow state

#     Returns:
#         Workflow result with status, stage, and relevant data
#     """
#     global agent_state

#     analyzer, generator = get_remote_agents()

#     status = status.strip().lower()
#     user_input = user_input.strip()

#     if session_id is None:
#         session_id = str(uuid.uuid4())

#     if session_id not in agent_state:
#         agent_state[session_id] = {}

#     session_data = agent_state[session_id]

#     if status == "start":
#         # Call analyzer agent using run_async
#         analysis_response = await analyzer.run_async(
#             user_input=user_input,
#             session_id=session_id
#         )

#         # Extract text from response
#         analysis_text = ""
#         if hasattr(analysis_response, 'output') and analysis_response.output:
#             analysis_text = str(analysis_response.output)
#         elif hasattr(analysis_response, 'message') and analysis_response.message:
#             if hasattr(analysis_response.message, 'parts') and analysis_response.message.parts:
#                 analysis_text = analysis_response.message.parts[0].text
#         else:
#             analysis_text = str(analysis_response)

#         session_data["last_analysis"] = analysis_text
#         return {
#             "status": "pending",
#             "stage": "awaiting_human_review",
#             "analysis": analysis_text,
#             "session_id": session_id
#         }

#     elif status in {"approved", "edited"}:
#         input_text = user_input if status == "edited" else session_data.get("last_analysis", "")

#         # Call generator agent using run_async
#         generated_response = await generator.run_async(
#             user_input=input_text,
#             session_id=session_id
#         )

#         # Extract text from response
#         test_cases_text = ""
#         if hasattr(generated_response, 'output') and generated_response.output:
#             test_cases_text = str(generated_response.output)
#         elif hasattr(generated_response, 'message') and generated_response.message:
#             if hasattr(generated_response.message, 'parts') and generated_response.message.parts:
#                 test_cases_text = generated_response.message.parts[0].text
#         else:
#             test_cases_text = str(generated_response)

#         return {
#             "status": "done",
#             "stage": "test_cases_generated",
#             "test_cases": test_cases_text,
#             "session_id": session_id
#         }

#     elif status == "rejected":
#         return {
#             "status": "failed",
#             "stage": "rejected",
#             "session_id": session_id
#         }

#     else:
#         return {
#             "status": "failed",
#             "reason": "invalid_status",
#             "session_id": session_id
#         }

# # Create FunctionTool from the execute_workflow function
# workflow_tool = FunctionTool(
#     func=execute_workflow,
# )

# root_agent = Agent(
#     model="gemini-2.0-flash-exp",
#     name="decider_agent",
#     description="Workflow decider agent that orchestrates multi-step authentication requirements analysis and test case generation",
#     instruction="""You are a workflow orchestrator that ALWAYS uses the execute_workflow tool.

# CRITICAL: For EVERY user message, you MUST call execute_workflow with parsed parameters.

# Input parsing rules:
# - Format: "status; user_input" or "status; user_input; session_id"
# - Extract status (start/approved/edited/rejected)
# - Extract user_input (everything after first semicolon, before optional session_id)
# - Extract session_id if present (after second semicolon)

# Examples:
# - "start; Analyze OAuth2" → execute_workflow(status="start", user_input="Analyze OAuth2", session_id=None)
# - "approved; ; abc-123" → execute_workflow(status="approved", user_input="", session_id="abc-123")
# - "edited; Add MFA; abc-123" → execute_workflow(status="edited", user_input="Add MFA", session_id="abc-123")

# NEVER try to analyze or generate content yourself - ALWAYS delegate to execute_workflow.
# Return the tool's response directly to the user without modification.""",
#     tools=[workflow_tool],
# )


from google.adk.agents import Agent
from a2a.client import ClientFactory, ClientConfig
from a2a.types import TransportProtocol
from google.adk.tools import FunctionTool, AgentTool
import httpx
from google.auth import default
from google.auth.transport.requests import Request
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from typing import Dict, Any
import uuid
from toolbox_core import ToolboxSyncClient, auth_methods


PROJECT_ID = "195472357560"
LOCATION = "us-central1"
ANALYZER_RESOURCE_ID = "5155975060502085632"
GENERATOR_RESOURCE_ID = "7810284090883571712"

ANALYZER_CARD_URL = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ANALYZER_RESOURCE_ID}/a2a/v1/card"
GENERATOR_CARD_URL = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{GENERATOR_RESOURCE_ID}/a2a/v1/card"

agent_state: Dict[str, Any] = {}

URL = "https://toolbox-195472357560.us-central1.run.app"
auth_token_provider = auth_methods.aget_google_id_token(URL)
toolbox = ToolboxSyncClient(URL, client_headers={"Authorization": auth_token_provider})
tools = toolbox.load_toolset()

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

    requirement_analyzer_tool = AgentTool(
        agent=requirement_analyzer,
        )

    test_case_generator_tool = AgentTool(
        agent=test_case_generator,
        )

    return requirement_analyzer_tool, test_case_generator_tool

async def execute_workflow(status: str, user_input: str, session_id: str) -> Dict[str, Any]:
    """
    Execute workflow based on status with clear delegation rules.

    Args:
        status: Workflow status - 'start', 'approved', 'edited', or 'rejected'
        user_input: User input text for the workflow
        session_id: Required session ID for tracking workflow state (no longer optional)

    Returns:
        Workflow result with status, stage, delegate_to, and relevant data
    """
    global agent_state

    status = status.strip().lower()
    user_input = user_input.strip()

    # Store session_id as a variable for consistent usage
    current_session_id = session_id.strip()

    if current_session_id not in agent_state:
        agent_state[current_session_id] = {}

    session_data = agent_state[current_session_id]

    if status == "start":
        # STEP 1: Delegate to requirement_analyzer, then store response in requirements table (original_content)
        session_data["analyzer_input"] = user_input
        session_data["current_status"] = "analyzing"
        return {
            "status": "delegating",
            "stage": "analyzing_requirements",
            "delegate_to": "requirement_analyzer",
            "input": user_input,
            "session_id": current_session_id,
            "next_action": "store_original_requirements_to_db"
        }

    elif status == "edited":
        # STEP 2: Update requirements table (edited_content) then delegate to test_case_generator
        session_data["edited_input"] = user_input
        session_data["current_status"] = "editing"
        return {
            "status": "delegating",
            "stage": "updating_edited_requirements",
            "delegate_to": "test_case_generator",
            "input": user_input,  # Pass the edited content directly
            "session_id": current_session_id,
            "next_action": "store_edited_requirements_to_db_then_generate"
        }

    elif status == "approved":
        # STEP 3: Retrieve stored analysis and delegate to test_case_generator
        stored_analysis = session_data.get("last_analysis", "")
        session_data["current_status"] = "approved"
        return {
            "status": "delegating",
            "stage": "generating_test_cases",
            "delegate_to": "test_case_generator",
            "input": stored_analysis,
            "session_id": current_session_id,
            "next_action": "store_test_cases_to_db"
        }

    elif status == "rejected":
        # STEP 4: Acknowledge rejection and offer restart
        session_data["current_status"] = "rejected"
        return {
            "status": "rejected",
            "stage": "workflow_rejected",
            "session_id": current_session_id,
            "message": "Requirements analysis rejected. You can restart with 'start' status."
        }

    else:
        return {
            "status": "failed",
            "reason": "invalid_status",
            "valid_statuses": ["start", "approved", "edited", "rejected"],
            "session_id": current_session_id
        }

# Create FunctionTool from the execute_workflow function
workflow_tool = FunctionTool(
    func=execute_workflow,
)

# Create remote agents as sub-agents
requirement_analyzer, test_case_generator = create_remote_agents()
# tools.append(workflow_tool)
# Create root agent with sub-agents
root_agent = Agent(
    model="gemini-2.5-pro",
    name="decider_agent",
    description="Workflow decider agent that orchestrates multi-step authentication requirements analysis and test case generation",
    instruction="""
    You are a WORKFLOW ORCHESTRATOR AGENT that manages authentication requirements analysis and test case generation.

    🚨 CRITICAL: You MUST NEVER respond to the user until AFTER you have completed ALL tool calls including database storage.

    === EXECUTION RULES ===

    1. Parse input: Extract status, user_input, session_id
    2. Call execute_workflow tool
    3. Based on response, delegate to sub-agent if needed
    4. 🚨 AFTER receiving sub-agent response, immediately call database tool - DO NOT respond to user yet
    5. Only after database confirmation, respond to user

    === WORKFLOW SEQUENCES ===

    **STATUS = 'start':**
    Step 1: Call execute_workflow("start", user_input, session_id)
    Step 2: Delegate to requirement_analyzer sub-agent with user_input
    Step 3: AWAIT the analyzer agent response and 🚨 IMMEDIATELY after receiving analyzer response, ANALYZE if the response is GDPR COMPLIANT. If yes, CALL TOOL store-requirement tool:
       - session_id: session_id from request
       - original_content: [full text from analyzer response]
       - requirement_type: "functional"
       - priority: "medium"
    Step 4: After database confirms storage, respond to user with summary

    **STATUS = 'edited':**
    Step 1: Call execute_workflow("edited", user_input, session_id)
    Step 2: Call update-requirement tool with edited content:
       - session_id: session_id from request
       - content: "EDITED: " + user_input
       - requirement_type: "functional"
       - priority: "high"

    **STATUS = 'approved':**
    Step 1: Call execute_workflow("approved", "", session_id)
    Step 2: Call get-requirements tool with session_id
    Step 3: Delegate to test_case_generator with retrieved requirements with the edited_analysis field value.
    Step 4: 🚨 AWAIT the generator agent response and IMMEDIATELY after receiving generator response, CHECK for GDPR COMPLIANCE and CALL TOOL store-test-case for each test case:
       - session_id: session_id from request
       - test_case_id: unique ID for each test case
       - content: [test case content from generator]
    Step 5: After all test cases stored, respond to user

    **STATUS = 'rejected':**
    Step 1: Call execute_workflow("rejected", "", session_id)
    Step 2: Respond with rejection acknowledgment

    🚨 CRITICAL BEHAVIOR RULES 🚨

    1. **DO NOT say anything to the user until database storage is complete**
    2. **Sub-agent responses are intermediate data - NOT final responses**
    3. **Every sub-agent call must be followed by a database tool call**
    4. **The database tool call happens AUTOMATICALLY - you don't wait for user permission**
    5. **Your thinking process:**
       - "Got sub-agent response" → "Now I must call database tool" → "Database confirmed" → "Now I can respond to user"

    🔒 CORRECT BEHAVIOR EXAMPLE:
    - User: "start session_123 analyze login flow"
    - You: [Call execute_workflow]
    - You: [Call requirement_analyzer sub-agent]
    - You: [Receive analyzer response: "Authentication requires OAuth 2.0..."]
    - You: [IMMEDIATELY call store-requirement with that response]
    - You: [Get database confirmation]
    - You: "I've analyzed and stored your requirements. The analysis shows authentication requires OAuth 2.0..."

    ❌ WRONG BEHAVIOR (what you're doing now):
    - You: [Call requirement_analyzer]
    - You: "Here's the analysis: [analyzer response]" ← WRONG! Database not called yet!

    The key is: Think of the sub-agent response as data you need to process (store in DB) before reporting to the user.
    You are a DATA PROCESSOR, not a messenger. Process first, report after.

    Remember: execute_workflow → sub-agent → database tool → user response
    NEVER skip the database tool step!""",
    sub_agents=[],
    tools=[workflow_tool, *tools, requirement_analyzer, test_case_generator],
)