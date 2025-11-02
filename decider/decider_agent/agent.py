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
# URL = "http://localhost:5007"
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
    Execute enhanced HITL workflow with comprehensive human feedback capabilities.

    Args:
        status: Workflow status - 'start', 'approved', 'edited', 'rejected', 'refine', 'review', 'enhance'
        user_input: User input text for the workflow
        session_id: Required session ID for tracking workflow state

    Returns:
        Workflow result with status, stage, delegate_to, and relevant data
    """
    global agent_state

    status = status.strip().lower()
    user_input = user_input.strip()
    current_session_id = session_id.strip()

    if current_session_id not in agent_state:
        agent_state[current_session_id] = {
            "iteration_count": 0,
            "feedback_history": [],
            "quality_scores": {},
            "enhancement_requests": [],
            "approval_chain": []
        }

    session_data = agent_state[current_session_id]

    if status == "start":
        # STEP 1: Initial analysis with HITL checkpoint
        session_data["analyzer_input"] = user_input
        session_data["current_status"] = "analyzing"
        session_data["iteration_count"] = 1
        return {
            "status": "delegating",
            "stage": "analyzing_requirements",
            "delegate_to": "requirement_analyzer",
            "input": user_input,
            "session_id": current_session_id,
            "next_action": "store_original_requirements_to_db",
            "hitl_checkpoint": "analysis_review",
            "available_actions": ["approved", "edited", "rejected", "refine", "enhance"]
        }

    elif status == "refine":
        # HITL: Human requests refinement with specific feedback
        session_data["iteration_count"] += 1
        session_data["feedback_history"].append({
            "iteration": session_data["iteration_count"],
            "feedback_type": "refinement",
            "human_input": user_input,
            "timestamp": str(uuid.uuid4())[:8]  # Simple timestamp
        })

        # Re-analyze with human feedback incorporated
        enhanced_prompt = f"Original analysis needs refinement. Human feedback: {user_input}. Please re-analyze considering this feedback."
        return {
            "status": "delegating",
            "stage": "refining_analysis",
            "delegate_to": "requirement_analyzer",
            "input": enhanced_prompt,
            "session_id": current_session_id,
            "iteration": session_data["iteration_count"],
            "feedback_incorporated": True,
            "next_action": "store_refined_requirements_to_db"
        }

    elif status == "enhance":
        # HITL: Human requests enhancement with additional context
        session_data["enhancement_requests"].append({
            "enhancement_type": "context_addition",
            "details": user_input,
            "iteration": session_data["iteration_count"]
        })

        # Get current analysis and enhance it
        current_analysis = session_data.get("last_analysis", "")
        enhanced_input = f"Current analysis: {current_analysis}\n\nAdditional context from human: {user_input}\n\nPlease enhance the analysis with this new information."

        return {
            "status": "delegating",
            "stage": "enhancing_analysis",
            "delegate_to": "requirement_analyzer",
            "input": enhanced_input,
            "session_id": current_session_id,
            "enhancement_applied": True,
            "next_action": "store_enhanced_requirements_to_db"
        }

    elif status == "review":
        # HITL: Human provides quality review and scoring
        try:
            # Parse review format: "review; score:8; feedback:needs more detail"
            parts = user_input.split(';')
            score = None
            feedback = ""

            for part in parts:
                if part.strip().startswith("score:"):
                    score = int(part.split(":")[1].strip())
                elif part.strip().startswith("feedback:"):
                    feedback = part.split(":", 1)[1].strip()

            session_data["quality_scores"][f"iteration_{session_data['iteration_count']}"] = {
                "score": score,
                "feedback": feedback,
                "review_timestamp": str(uuid.uuid4())[:8]
            }

            # If score is low (< 7), suggest improvements
            if score and score < 7:
                return {
                    "status": "needs_improvement",
                    "stage": "quality_review_failed",
                    "score": score,
                    "feedback": feedback,
                    "session_id": current_session_id,
                    "suggested_actions": ["refine", "enhance", "rejected"],
                    "improvement_needed": True
                }
            else:
                return {
                    "status": "quality_approved",
                    "stage": "quality_review_passed",
                    "score": score,
                    "feedback": feedback,
                    "session_id": current_session_id,
                    "available_actions": ["approved", "generate_tests"]
                }

        except Exception as e:
            return {
                "status": "review_error",
                "error": f"Invalid review format. Use: 'score:X; feedback:your feedback'",
                "session_id": current_session_id
            }

    elif status == "edited":
        # STEP 2: Human edited content - track changes and delegate
        session_data["edited_input"] = user_input
        session_data["current_status"] = "editing"
        session_data["feedback_history"].append({
            "iteration": session_data["iteration_count"],
            "feedback_type": "direct_edit",
            "edited_content": user_input,
            "timestamp": str(uuid.uuid4())[:8]
        })

        return {
            "status": "delegating",
            "stage": "processing_edited_requirements",
            "delegate_to": "test_case_generator",
            "input": user_input,
            "session_id": current_session_id,
            "human_edited": True,
            "next_action": "store_edited_requirements_to_db_then_generate"
        }

    elif status == "approved":
        # STEP 3: Human approval - proceed to test generation
        stored_analysis = session_data.get("last_analysis", "")
        session_data["current_status"] = "approved"
        session_data["approval_chain"].append({
            "approver": "human",
            "timestamp": str(uuid.uuid4())[:8],
            "iteration": session_data["iteration_count"]
        })

        return {
            "status": "delegating",
            "stage": "generating_test_cases",
            "delegate_to": "test_case_generator",
            "input": stored_analysis,
            "session_id": current_session_id,
            "human_approved": True,
            "next_action": "store_test_cases_to_db"
        }

    elif status == "rejected":
        # STEP 4: Human rejection with optional feedback
        session_data["current_status"] = "rejected"
        session_data["feedback_history"].append({
            "iteration": session_data["iteration_count"],
            "feedback_type": "rejection",
            "rejection_reason": user_input if user_input else "No reason provided",
            "timestamp": str(uuid.uuid4())[:8]
        })

        return {
            "status": "rejected",
            "stage": "workflow_rejected",
            "session_id": current_session_id,
            "rejection_reason": user_input,
            "restart_options": ["start", "refine"],
            "feedback_available": True
        }

    else:
        return {
            "status": "failed",
            "reason": "invalid_status",
            "valid_statuses": ["start", "approved", "edited", "rejected", "refine", "review", "enhance"],
            "session_id": current_session_id,
            "hitl_help": "Use 'refine' for feedback-based improvements, 'enhance' to add context, 'review' to score quality"
        }

async def get_session_feedback_history(session_id: str) -> Dict[str, Any]:
    """
    Get comprehensive feedback history for a session to enable HITL analysis.

    Args:
        session_id: Session ID to retrieve history for

    Returns:
        Dictionary containing complete feedback history and analytics
    """
    global agent_state

    if session_id not in agent_state:
        return {
            "session_id": session_id,
            "status": "not_found",
            "message": "No session data found"
        }

    session_data = agent_state[session_id]

    return {
        "session_id": session_id,
        "status": "found",
        "iteration_count": session_data.get("iteration_count", 0),
        "feedback_history": session_data.get("feedback_history", []),
        "quality_scores": session_data.get("quality_scores", {}),
        "enhancement_requests": session_data.get("enhancement_requests", []),
        "approval_chain": session_data.get("approval_chain", []),
        "current_status": session_data.get("current_status", "unknown"),
        "analytics": {
            "total_feedback_items": len(session_data.get("feedback_history", [])),
            "average_quality_score": _calculate_average_score(session_data.get("quality_scores", {})),
            "enhancement_count": len(session_data.get("enhancement_requests", [])),
            "approval_count": len(session_data.get("approval_chain", []))
        }
    }

def _calculate_average_score(quality_scores: Dict[str, Any]) -> float:
    """Calculate average quality score from session data."""
    scores = [item.get("score", 0) for item in quality_scores.values() if item.get("score")]
    return sum(scores) / len(scores) if scores else 0.0

async def suggest_improvements(session_id: str, current_output: str) -> Dict[str, Any]:
    """
    AI-powered suggestion system for HITL improvements based on feedback history.

    Args:
        session_id: Session ID to analyze
        current_output: Current agent output to improve

    Returns:
        Improvement suggestions and recommendations
    """
    global agent_state

    if session_id not in agent_state:
        return {"error": "Session not found"}

    session_data = agent_state[session_id]
    feedback_history = session_data.get("feedback_history", [])
    quality_scores = session_data.get("quality_scores", {})

    # Analyze patterns in feedback
    common_issues = []
    improvement_areas = []

    for feedback in feedback_history:
        if feedback.get("feedback_type") == "refinement":
            common_issues.append(feedback.get("human_input", ""))
        elif feedback.get("feedback_type") == "rejection":
            improvement_areas.append(feedback.get("rejection_reason", ""))

    # Analyze quality scores for trends
    low_score_feedback = []
    for score_data in quality_scores.values():
        if score_data.get("score", 10) < 7:
            low_score_feedback.append(score_data.get("feedback", ""))

    return {
        "session_id": session_id,
        "suggestions": {
            "common_issues_identified": common_issues,
            "improvement_areas": improvement_areas,
            "low_score_patterns": low_score_feedback,
            "recommended_actions": _generate_action_recommendations(feedback_history, quality_scores),
            "quality_trend": _analyze_quality_trend(quality_scores)
        },
        "hitl_insights": {
            "feedback_frequency": len(feedback_history),
            "refinement_cycles": len([f for f in feedback_history if f.get("feedback_type") == "refinement"]),
            "human_engagement_level": "high" if len(feedback_history) > 3 else "medium" if len(feedback_history) > 1 else "low"
        }
    }

def _generate_action_recommendations(feedback_history: list, quality_scores: dict) -> list:
    """Generate action recommendations based on HITL patterns."""
    recommendations = []

    if len(feedback_history) > 3:
        recommendations.append("Consider breaking down the analysis into smaller, more focused sections")

    if any(score.get("score", 10) < 6 for score in quality_scores.values()):
        recommendations.append("Quality scores are low - consider requesting more specific human feedback")

    refinement_count = len([f for f in feedback_history if f.get("feedback_type") == "refinement"])
    if refinement_count > 2:
        recommendations.append("Multiple refinements detected - consider asking for clearer initial requirements")

    return recommendations

def _analyze_quality_trend(quality_scores: dict) -> str:
    """Analyze quality score trends."""
    scores = [item.get("score", 0) for item in quality_scores.values() if item.get("score")]
    if len(scores) < 2:
        return "insufficient_data"

    if scores[-1] > scores[0]:
        return "improving"
    elif scores[-1] < scores[0]:
        return "declining"
    else:
        return "stable"

# Create FunctionTools for all HITL functions
workflow_tool = FunctionTool(
    func=execute_workflow,
)

feedback_history_tool = FunctionTool(
    func=get_session_feedback_history,
)

improvement_suggestions_tool = FunctionTool(
    func=suggest_improvements,
)

# Create remote agents as sub-agents
requirement_analyzer, test_case_generator = create_remote_agents()
# Create root agent with enhanced HITL capabilities
root_agent = Agent(
    model="gemini-2.5-pro",
    name="enhanced_hitl_decider_agent",
    description="Advanced HITL workflow orchestrator for authentication requirements analysis and test case generation with comprehensive human feedback integration",
    instruction="""You are a WORKFLOW ORCHESTRATOR AGENT that manages authentication requirements analysis and test case generation.
    MANDATORY: You MUST ALWAYS call the tools with the parameters in the order of the parameters specified in the EXECUTION RULES section below.
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
    Step 3: AWAIT the analyzer agent response and 🚨 IMMEDIATELY after receiving analyzer response, ANALYZE if the response is GDPR COMPLIANT. If yes, CALL TOOL store-original-requirements:
       - session_id: session_id from request
       - analysis_response: [full text from analyzer response]
    Step 4: After database confirms storage, extract cache_data from response and CALL TOOL cache-requirements-data:
       - session_id: session_id
       - requirements_data: [cache_data from Step 3 response]
    Step 5: After cache update, respond to user with database_result from Step 3

    **STATUS = 'refine':**
    Step 1: Call execute_workflow("refine", user_input, session_id)
    Step 2: Delegate to requirement_analyzer with enhanced prompt
    Step 3: 🚨 IMMEDIATELY after receiving analyzer response, CALL TOOL hitl-refine-analysis-workflow:
       - session_id: session_id from request
       - refined_analysis: [analyzer response]
       - human_feedback: user_input
       - iteration_count: [from execute_workflow response]
    Step 4: After database confirms storage, extract cache_data from response and CALL TOOL cache-requirements-data:
       - session_id: session_id
       - requirements_data: [cache_data from Step 3 response]
    Step 5: After cache update, respond to user with database_result from Step 3

    **STATUS = 'enhance':**
    Step 1: Call execute_workflow("enhance", user_input, session_id)
    Step 2: Delegate to requirement_analyzer with enhanced prompt
    Step 3: 🚨 IMMEDIATELY after receiving analyzer response, CALL TOOL hitl-enhance-analysis-workflow:
       - session_id: session_id from request
       - enhanced_analysis: [analyzer response]
       - enhancement_context: user_input
    Step 4: After database confirms storage, extract cache_data from response and CALL TOOL cache-requirements-data:
       - session_id: session_id
       - requirements_data: [cache_data from Step 3 response]
    Step 5: After cache update, respond to user with database_result from Step 3

    **STATUS = 'edited':**
    Step 1: Call execute_workflow("edited", user_input, session_id)
    Step 2: Call hitl-process-edited-requirements tool with edited content:
       - session_id: session_id from request
       - edited_content: user_input
    Step 3: After database confirms storage, extract cache_data from response and CALL TOOL cache-requirements-data:
       - session_id: session_id
       - requirements_data: [cache_data from Step 2 response]
    Step 4: After cache update, respond to user with database_result from Step 2

    **STATUS = 'approved':**
    Step 1: Call execute_workflow("approved", "", session_id)
    Step 2: Call hitl-approve-and-generate-tests tool with session_id
    Step 3: CHECK if requirements are available from Step 2 response:
       - If requirements_available = true: Delegate to test_case_generator with combined_requirements
       - If requirements_available = false: Respond with error about missing requirements
    Step 4: 🚨 ONLY if requirements were available and generator responded, CALL TOOL parse-and-store-test-cases(session_id, structured_test_cases, test_types_requested) in the following order of parameters:
       - session_id: session_id from request
       - structured_test_cases: [generator response]
       - test_types_requested: ["functional", "security","performance", "edge_case", "regression", "integration", "negative"]
    Step 5: After database confirms storage, extract cache_data from response and CALL TOOL cache-test-cases-data:
       - session_id: session_id
       - test_cases_data: [cache_data from Step 4 response]
    Step 6: After cache update, respond to user with database_result from Step 4

    **STATUS = 'rejected':**
    Step 1: Call execute_workflow("rejected", user_input, session_id)
    Step 2: Call hitl-reject-workflow tool:
       - session_id: session_id from request
       - rejection_reason: user_input
    Step 3: After database confirms, respond with rejection acknowledgment

    🚨 CRITICAL BEHAVIOR RULES 🚨

    1. **DO NOT say anything to the user until database storage AND cache update are complete**
    2. **Sub-agent responses are intermediate data - NOT final responses**
    3. **Every sub-agent call must be followed by: database tool call → cache tool call → user response**
    4. **The database and cache tool calls happen AUTOMATICALLY - you don't wait for user permission**
    5. **Always return the database_result from the database tool response, not your own summary**
    6. **Cache operations ensure data consistency between database and Redis cache**
    7. **Extract cache_data from database tool response JSON and pass as requirements_data/test_cases_data to cache tools**
    8. **Database tool responses contain: database_result (for user), cache_data (for caching), next_action (instruction)**
    5. **Your thinking process:**
       - "Got sub-agent response" → "Now I must call database tool" → "Database confirmed" → "Now I can respond to user"

    🔒 CORRECT BEHAVIOR EXAMPLE:
    - User: "start; Analyze OAuth flow; session_123"
    - You: [Call execute_workflow]
    - You: [Call requirement_analyzer sub-agent]
    - You: [Receive analyzer response: "Authentication requires OAuth 2.0..."]
    - You: [IMMEDIATELY call hitl-store-original-requirements with that response]
    - You: [Get database confirmation]
    - You: "I've analyzed and stored your requirements. The analysis shows authentication requires OAuth 2.0..."

    ❌ WRONG BEHAVIOR (what you're doing now):
    - You: [Call requirement_analyzer]
    - You: "Here's the analysis: [analyzer response]" ← WRONG! Database not called yet!

    The key is: Think of the sub-agent response as data you need to process (store in DB) before reporting to the user.
    You are a DATA PROCESSOR, not a messenger. Process first, report after.

    Remember: execute_workflow → sub-agent → database tool → user response
    NEVER skip the database tool step!

    Enhanced HITL statuses: start, refine, enhance, review, edited, approved, rejected
    """,
    sub_agents=[],
    tools=[workflow_tool, feedback_history_tool, improvement_suggestions_tool, *tools, requirement_analyzer, test_case_generator],
)
