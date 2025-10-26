# agents/test_case_generator/agent.py
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
from google.adk import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
import json
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card
from testcase_agent.templates import TestSuite, TestCase


# --- Tool: Extract context from input ---
async def extract_requirements_context_tool(
    requirements_analysis: str = "",
    tool_context: ToolContext = None
):
    """
    Extracts structured requirements context from the analyzer's output.
    This tool parses the analysis and stores it in session state for test generation.
    """
    if not requirements_analysis:
        return {
            "status": "error",
            "message": "No requirements analysis provided. Need output from Requirements Analyzer.",
        }

    if not tool_context:
        return {"status": "error", "message": "ToolContext is required"}

    try:
        # Try to parse if it's JSON
        try:
            context_data = json.loads(requirements_analysis)
        except json.JSONDecodeError:
            # If not JSON, treat as structured text and extract sections
            context_data = {
                "raw_analysis": requirements_analysis,
                "functional_requirements": [],
                "non_functional_requirements": [],
                "business_rules": [],
                "user_stories": [],
                "acceptance_criteria": [],
                "edge_cases": [],
                "risk_areas": []
            }

            # Simple extraction based on sections
            lines = requirements_analysis.split('\n')
            current_section = None

            for line in lines:
                line_lower = line.lower().strip()
                if 'functional requirement' in line_lower:
                    current_section = 'functional_requirements'
                elif 'non-functional requirement' in line_lower:
                    current_section = 'non_functional_requirements'
                elif 'business rule' in line_lower:
                    current_section = 'business_rules'
                elif 'user stor' in line_lower:
                    current_section = 'user_stories'
                elif 'acceptance' in line_lower:
                    current_section = 'acceptance_criteria'
                elif 'edge case' in line_lower:
                    current_section = 'edge_cases'
                elif 'risk' in line_lower:
                    current_section = 'risk_areas'
                elif line.strip() and current_section:
                    if line.strip().startswith('-') or line.strip().startswith('•'):
                        context_data[current_section].append(line.strip()[1:].strip())

        # Store in session state
        tool_context.state["requirements_context"] = context_data
        tool_context.state["ready_for_test_generation"] = True

        return {
            "status": "success",
            "message": "Successfully extracted requirements context",
            "context_summary": {
                "functional_requirements_count": len(context_data.get("functional_requirements", [])),
                "non_functional_requirements_count": len(context_data.get("non_functional_requirements", [])),
                "business_rules_count": len(context_data.get("business_rules", [])),
            },
            "context_stored": True
        }

    except Exception as e:
        return {"status": "error", "message": f"Context extraction failed: {str(e)}"}


# --- Root Agent ---


async def format_test_cases_tool(
    test_cases_json: str = "",
    output_format: str = "json",
    tool_context: ToolContext = None
):
    """
    Formats generated test cases into specified template format.

    Args:
        test_cases_json: JSON string of test cases
        output_format: 'json', 'csv', or 'markdown'
        tool_context: Context for session state
    """
    if not test_cases_json:
        return {"status": "error", "message": "No test cases provided"}

    try:
        # Parse and create TestSuite
        suite = TestSuite.from_json(test_cases_json)

        # Format based on requested output
        if output_format == "json":
            formatted = suite.to_json(pretty=True)
        elif output_format == "csv":
            formatted = suite.to_csv()
        elif output_format == "markdown":
            formatted = format_as_markdown(suite)
        else:
            formatted = suite.to_json()

        # Store in session
        if tool_context:
            tool_context.state["formatted_test_cases"] = formatted
            tool_context.state["test_suite"] = suite.to_dict()

        return {
            "status": "success",
            "formatted_output": formatted,
            "total_tests": suite.total_tests,
            "format": output_format
        }

    except Exception as e:
        return {"status": "error", "message": f"Formatting failed: {str(e)}"}


def format_as_markdown(suite: TestSuite) -> str:
    """Convert TestSuite to markdown format"""
    md = f"# {suite.name}\n\n"
    md += f"**Generated**: {suite.generated_date}\n"
    md += f"**Total Tests**: {suite.total_tests}\n\n"
    md += "---\n\n"

    for tc in suite.test_cases:
        md += f"## {tc.test_id}: {tc.summary}\n\n"
        md += f"**Priority**: {tc.priority} | **Type**: {tc.type}\n\n"

        md += "**Preconditions**:\n"
        for pre in tc.preconditions:
            md += f"- {pre}\n"

        md += "\n**Test Steps**:\n"
        for i, step in enumerate(tc.test_steps, 1):
            md += f"{i}. {step}\n"

        md += f"\n**Expected Result**: {tc.expected_result}\n\n"
        md += f"**Traceability**: {tc.requirement_traceability}\n\n"
        md += "---\n\n"

    return md


# Update root agent to use template
root_agent = Agent(
    model="gemini-2.5-flash",
    name="test_case_generator_agent",
    description="Generates test cases in structured template format",
    instruction="""
    You are an expert Test Case Generator that outputs STRICTLY FORMATTED JSON.

    ## Your Workflow:
    1. Use extract_requirements_context_tool to parse requirements analysis
    2. Generate test cases in JSON format following the EXACT template
    3. Optionally use format_test_cases_tool to convert to CSV or Markdown

    ## STRICT JSON Template (YOU MUST FOLLOW THIS EXACTLY):

    {
      "test_suite": {
        "name": "Suite Name",
        "description": "Brief description",
        "total_tests": 0,
        "generated_date": "2025-10-26",
        "test_cases": [
          {
            "test_id": "TC_TYPE_NNN",
            "priority": "CRITICAL|HIGH|MEDIUM|LOW",
            "type": "Functional|Security|Edge Case|Negative",
            "summary": "One-line summary",
            "preconditions": ["condition 1", "condition 2"],
            "test_steps": ["step 1", "step 2", "step 3"],
            "test_data": {
              "field1": "value1",
              "field2": "value2"
            },
            "expected_result": "Clear expected outcome",
            "requirement_traceability": "REQ_ID - description"
          }
        ]
      }
    }

    ## Naming Conventions:
    - test_id: TC_[TYPE]_[NNN] where TYPE = FUNC, SEC, EDGE, NEG
    - priority: CRITICAL (P0), HIGH (P1), MEDIUM (P2), LOW (P3)
    - type: Functional, Security, Edge Case, Negative

    ## CRITICAL:
    1. Return ONLY valid JSON (no markdown code blocks, no extra text)
    2. Start with { and end with }
    3. Use double quotes for all strings
    4. Ensure proper JSON escaping
    5. Generate 10-20 test cases minimum
    6. Every test case must have ALL fields filled

    If context is missing, return:
    {"error": "No requirements context", "test_suite": {"test_cases": []}}
    """,
    tools=[extract_requirements_context_tool, format_test_cases_tool],
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=4096,
        )
    ),
)



# --- Agent Card ---
skills = [
    AgentSkill(
        id="test_case_generation",
        name="Test Case Generation",
        description=(
            "Generates comprehensive test cases from requirements analysis. "
            "Creates functional, security, edge case, and negative test scenarios "
            "with detailed steps, test data, and expected results. "
            "Ensures full traceability to original requirements."
        ),
        tags=["testing", "test-cases", "qa", "test-generation", "security-testing"],
        examples=[
            "Generate test cases from this analysis: [requirements analysis]",
            "Create test cases for authentication requirements",
            "Generate security test cases for login functionality"
        ]
    ),
    AgentSkill(
        id="test_coverage_analysis",
        name="Test Coverage Analysis",
        description=(
            "Analyzes requirements to ensure comprehensive test coverage. "
            "Identifies gaps in test scenarios and suggests additional test cases "
            "for edge cases, negative scenarios, and security concerns."
        ),
        tags=["test-coverage", "qa-analysis", "test-planning"],
        examples=[
            "What test coverage do we have for MFA requirements?",
            "Identify missing test scenarios for password reset",
            "Suggest additional edge case tests"
        ]
    ),
]

capabilities = AgentCapabilities(
    can_handle_conversations=True,
    supports_session_state=True,
    max_message_length=16384,  # Larger for receiving full analysis
    supported_input_formats=["text", "structured_json"],
    supported_output_formats=["structured_text", "test_cases"]
)

agent_card = create_agent_card(
    agent_name="test_case_generator_agent",
    description=
        "Expert Test Case Generator that creates comprehensive, executable test cases from requirements analysis. Specializes in authentication, security, and complex business logic testing. Generates functional, security, edge case, and negative test scenarios with full traceability."
    ,
    skills=skills,
)


# --- Executor ---
class TestCaseGeneratorExecutor(AgentExecutor):
    """A2A-compliant executor for Test Case Generator Agent."""

    def __init__(self, agent: Agent):
        self.agent = agent
        self.runner = None

    def _init_runner(self):
        if self.runner is None:
            self.runner = Runner(
                app_name=self.agent.name,
                agent=self.agent,
                artifact_service=InMemoryArtifactService(),
                session_service=InMemorySessionService(),
                memory_service=InMemoryMemoryService(),
            )

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        self._init_runner()
        query = context.get_user_input()
        if not query:
            return

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.submit()
        await updater.start_work()

        try:
            session = await self.runner.session_service.get_session(
                app_name=self.runner.app_name,
                user_id='a2a_user',
                session_id=context.context_id,
            )

            if not session:
                session = await self.runner.session_service.create_session(
                    app_name=self.runner.app_name,
                    user_id='a2a_user',
                    session_id=context.context_id,
                )

            content = types.Content(role='user', parts=[types.Part(text=query)])

            final_response = None
            async for event in self.runner.run_async(
                session_id=session.id,
                user_id='a2a_user',
                new_message=content
            ):
                if event.is_final_response():
                    final_response = event
                    break

            if final_response and final_response.content and final_response.content.parts:
                response_text = "".join(
                    part.text for part in final_response.content.parts
                    if hasattr(part, 'text') and part.text
                )

                if response_text:
                    await updater.add_artifact(
                        [TextPart(text=response_text)],
                        name='test_cases'
                    )
                    await updater.complete()
                    return

            await updater.update_status(
                TaskState.failed,
                message=new_agent_text_message('Agent did not produce valid test cases'),
                final=True
            )

        except Exception as e:
            await updater.update_status(
                TaskState.failed,
                message=new_agent_text_message(f"Error: {str(e)}"),
                final=True
            )
            raise

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())


# --- A2A Agent ---
a2a_agent = A2aAgent(
    agent_card=agent_card,
    agent_executor_builder=lambda: TestCaseGeneratorExecutor(agent=root_agent)
)

# Export for deployment
__all__ = ['a2a_agent', 'root_agent']

# --- Expose your agent via A2A (exactly like the quickstart) ---
# from google.adk.a2a.utils.agent_to_a2a import to_a2a

# # Make your agent A2A-compatible (auto-generates agent card)
# a2a_app = to_a2a(root_agent, port=8002)
