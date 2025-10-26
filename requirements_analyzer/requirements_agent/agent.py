# agents/requirements_analyser/agent.py
from google.adk.agents import Agent
from google.adk.planners import BuiltInPlanner
from google.genai import types
from google.adk.tools import ToolContext
from typing import List, Dict, Any
from vertexai.preview.reasoning_engines import A2aAgent
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, TextPart, UnsupportedOperationError
from a2a.utils import new_agent_text_message
from a2a.utils.errors import ServerError
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card
from google.adk import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
import vertexai
import asyncio


# --- Your analysis tool (exactly as you provided) ---
async def analyze_requirements_context_tool(
    text_array: List[str],
    analysis_depth: str = "comprehensive",
    tool_context: ToolContext = None
):
    if not text_array:
        return {"status": "error", "message": "No requirements provided for analysis"}

    if not tool_context:
        return {"status": "error", "message": "ToolContext is required for session state storage"}

    try:
        analyzed_context = {
            "requirements_analysis": {
                "functional_requirements": [f"Functional requirement: {req}" for req in text_array],
                "non_functional_requirements": [
                    "System performance requirements",
                    "Security and authentication requirements",
                    "Usability and accessibility requirements"
                ],
                "business_rules": [
                    "Email format validation required",
                    "Password complexity rules must be enforced",
                    "Account lockout policy after failed attempts"
                ],
                "user_stories": [f"As a user, I want to {req.lower()}" for req in text_array],
                "acceptance_criteria": [
                    "User can successfully authenticate with valid credentials",
                    "Invalid credentials are properly rejected",
                    "Account lockout activates after specified failed attempts"
                ],
                "integration_points": [
                    "Email service for notifications",
                    "User database for credential storage",
                    "Session management service"
                ]
            },
            "test_context": {
                "critical_flows": [
                    "Successful user authentication flow",
                    "Failed authentication and lockout flow",
                    "Password reset and recovery flow"
                ],
                "edge_cases_identified": [
                    "Boundary conditions for failed attempt counting",
                    "Concurrent login attempts",
                    "Password complexity edge cases"
                ],
                "risk_areas": [
                    "Security vulnerabilities in authentication",
                    "Account lockout mechanism reliability",
                    "Session management security"
                ]
            },
            "metadata": {
                "analysis_depth": analysis_depth,
                "source_count": len(text_array),
                "original_requirements": text_array
            }
        }

        tool_context.state["analyzed_requirements_context"] = analyzed_context
        tool_context.state["ready_for_test_generation"] = True

        return {
            "status": "success",
            "message": f"Successfully analyzed {len(text_array)} requirements",
            "analysis_summary": analyzed_context["metadata"],
            "context_stored_in_session": True
        }

    except Exception as e:
        return {"status": "error", "message": f"Requirements analysis failed: {str(e)}"}

# --- Your agent definition (exactly as you provided) ---
root_agent = Agent(
    model="gemini-2.5-flash",
    name="requirement_analyzer_agent",
    description="Analyzes requirements and stores context in session state",
    instruction="""
    You are an expert Requirements Analyzer specializing in authentication systems.

    ## Your Job:
    1. Take textual requirements as input
    2. Analyze them thoroughly using domain expertise
    3. Store structured context in session state for the Test Case Generator
    4. Focus on security, usability, and reliability aspects

    ## Key Process:
    - Use `analyze_requirements_context_tool` to process the requirements
    - The tool will automatically store the analysis in session state
    - This context will be available to the next agent in the sequential workflow

    ## Analysis Focus:
    - Extract functional and non-functional requirements
    - Identify security requirements and business rules
    - Map critical user flows and edge cases
    - Identify integration points and risk areas

    ## Important:
    - Always pass the ToolContext parameter when calling the tool
    - The tool uses tool_context.state (not tool_context.session.state)
    - Verify successful context storage before completing the task
    - Return the complete requirement analysis you have done in a structured format as the response.

    Always use the tool to ensure proper context storage for the next agent.
    """,
    tools=[analyze_requirements_context_tool],
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=3072,
        )
    ),
)

skills = AgentSkill(
            id="requirements_analysis",
            name="Requirements Analysis",
            description=(
                "Analyzes authentication system requirements and produces structured output "
                "including functional requirements, non-functional requirements, business rules, "
                "user stories, acceptance criteria, and integration points."
            ),
            tags=["requirements", "analysis", "authentication", "security"],
            examples=[
                "Analyze these authentication requirements: User login with email and password",
                "Review security requirements for user authentication system",
                "Extract test scenarios from authentication requirements"
            ]
        ),

agent_card = create_agent_card(
    agent_name="requirement_analyzer_agent",
    description="Expert Requirements Analyzer specializing in authentication systems. Analyzes textual requirements, extracts functional/non-functional requirements, identifies security requirements, business rules, user stories, and critical test scenarios. Stores comprehensive analysis in session state for downstream agents.",
    skills=skills,
)
# ============================================================================
# A2A AGENT EXECUTOR - Handles the execution of tasks
# ============================================================================

class RequirementAnalyzerExecutor(AgentExecutor):
    """
    Simplified A2A-compliant executor for Requirements Analyzer Agent.
    """

    def __init__(self, agent: Agent):
        """Initialize with the ADK agent."""
        self.agent = agent
        self.runner = None

    def _init_runner(self):
        """Lazy-load the ADK Runner on first execution."""
        if self.runner is None:
            self.runner = Runner(
                app_name=self.agent.name,
                agent=self.agent,
                artifact_service=InMemoryArtifactService(),
                session_service=InMemorySessionService(),
                memory_service=InMemoryMemoryService(),
            )

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Execute the agent with the user's message.

        This is called when A2A receives a message:send request.
        """
        # Initialize runner on first use
        self._init_runner()

        # Extract user input from A2A request
        query = context.get_user_input()
        if not query:
            return

        # Create TaskUpdater to manage task lifecycle
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        # Update task status: submitted -> working
        await updater.submit()
        await updater.start_work()

        try:
            # Get or create session for this context
            session = await self.runner.session_service.get_session(
                app_name=self.runner.app_name,
                user_id='a2a_user',  # Use context-specific user_id if available
                session_id=context.context_id,
            )

            if not session:
                session = await self.runner.session_service.create_session(
                    app_name=self.runner.app_name,
                    user_id='a2a_user',
                    session_id=context.context_id,
                )

            # Prepare message in ADK format
            content = types.Content(role='user', parts=[types.Part(text=query)])

            # Run agent asynchronously and listen for final response
            final_response = None
            async for event in self.runner.run_async(
                session_id=session.id,
                user_id='a2a_user',
                new_message=content
            ):
                # Check if this is the final response from the agent
                if event.is_final_response():
                    final_response = event
                    break

            # Extract text from final response
            if final_response and final_response.content and final_response.content.parts:
                response_text = "".join(
                    part.text for part in final_response.content.parts
                    if hasattr(part, 'text') and part.text
                )

                if response_text:
                    # Add result as A2A artifact
                    await updater.add_artifact(
                        [TextPart(text=response_text)],
                        name='analysis_result'
                    )

                    # Mark task as complete
                    await updater.complete()
                    return

            # If we got here, no valid response was generated
            await updater.update_status(
                TaskState.failed,
                message=new_agent_text_message('Agent did not produce a valid response'),
                final=True
            )

        except Exception as e:
            # Handle any errors during execution
            await updater.update_status(
                TaskState.failed,
                message=new_agent_text_message(f"Error: {str(e)}"),
                final=True
            )
            raise

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Handle task cancellation requests.

        For this simple agent, we don't support cancellation.
        """
        raise ServerError(error=UnsupportedOperationError())



a2a_agent =  A2aAgent(
        agent_card=agent_card,
        agent_executor_builder=lambda: RequirementAnalyzerExecutor(agent=root_agent)
    )
a2a_agent.set_up()

# Export for deployment
__all__ = ['a2a_agent']

# --- Expose your agent via A2A (exactly like the quickstart) ---
# from google.adk.a2a.utils.agent_to_a2a import to_a2a

# # Make your agent A2A-compatible (auto-generates agent card)
# a2a_app = to_a2a(root_agent)
