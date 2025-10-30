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
from google.adk.tools import FunctionTool
import httpx
from google.auth import default
from google.auth.transport.requests import Request
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from typing import Optional, Dict, Any
import uuid


PROJECT_ID = "195472357560"
LOCATION = "us-central1"
ANALYZER_RESOURCE_ID = "5155975060502085632"
GENERATOR_RESOURCE_ID = "7810284090883571712"

ANALYZER_CARD_URL = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ANALYZER_RESOURCE_ID}/a2a/v1/card"
GENERATOR_CARD_URL = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{GENERATOR_RESOURCE_ID}/a2a/v1/card"

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

async def execute_workflow(status: str, user_input: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute workflow based on status.

    Args:
        status: Workflow status - 'start', 'approved', 'edited', or 'rejected'
        user_input: User input text for the workflow
        session_id: Optional session ID for tracking workflow state

    Returns:
        Workflow result with status, stage, and relevant data
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
        # Store the user input for the analyzer
        session_data["analyzer_input"] = user_input
        return {
            "status": "delegating",
            "stage": "analyzing",
            "delegate_to": "requirement_analyzer",
            "input": user_input,
            "session_id": session_id
        }

    elif status in {"approved", "edited"}:
        input_text = user_input if status == "edited" else session_data.get("last_analysis", "")

        # The root agent will delegate to test_case_generator sub-agent
        return {
            "status": "delegating",
            "stage": "generating",
            "delegate_to": "test_case_generator",
            "input": input_text,
            "session_id": session_id
        }

    elif status == "rejected":
        return {
            "status": "failed",
            "stage": "rejected",
            "session_id": session_id
        }

    else:
        return {
            "status": "failed",
            "reason": "invalid_status",
            "session_id": session_id
        }

# Create FunctionTool from the execute_workflow function
workflow_tool = FunctionTool(
    func=execute_workflow,
)

# Create remote agents as sub-agents
requirement_analyzer, test_case_generator = create_remote_agents()

# Create root agent with sub-agents
root_agent = Agent(
    model="gemini-2.0-flash-exp",
    name="decider_agent",
    description="Workflow decider agent that orchestrates multi-step authentication requirements analysis and test case generation",
    instruction="""
    You are a workflow orchestrator agent managing a two-step process involving requirements analysis and test case generation.

    For every user message:

    1. You MUST first call the 'execute_workflow' tool with the parsed parameters extracted from the user message. The parameters include:
    - status (e.g., 'start', 'approved', 'edited', or 'rejected')
    - user input text
    - session_id (if provided, else generate a new one)

    2. Based on the result returned from 'execute_workflow', you MUST then delegate the task to exactly one of the following sub-agents:
    - If status is 'start', call the 'requirement_analyzer' sub-agent with the user input.
    - If status is 'approved', retrieve the stored analysis from the workflow result and call the 'test_case_generator' sub-agent with that analysis.
    - If status is 'edited', pass the edited user input to the 'test_case_generator' sub-agent.
    - If status is 'rejected', acknowledge the rejection and offer to restart the process without invoking a sub-agent.

    3. Always maintain and pass the correct session_id to both the tool and the sub-agents.

    4. You MUST NOT perform any analysis or generation yourself outside of these steps.

    5. Return all responses from both the tool and sub-agent calls back to the user.

    Follow this flow strictly to ensure proper sequential execution.

    Always track session_id throughout the workflow. Extract it from user messages or generate a new one.
    When responding to the user, always provide a clear, concise English explanation, followed by any relevant details.
    NEVER attempt to analyze or generate content yourself - ALWAYS delegate to the appropriate sub-agent as per the workflow.""",
    sub_agents=[requirement_analyzer, test_case_generator],
    tools=[workflow_tool],
)