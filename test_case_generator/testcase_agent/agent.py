from google.adk.agents import Agent
from google.adk.planners import BuiltInPlanner
from google.genai import types
from google.adk.tools import ToolContext
from typing import List, Dict, Any

# --- Retrieve requirements context tool (as provided) ---
async def retrieve_requirements_context_tool(
    requirements_input: str = "",
    tool_context: ToolContext = None
):
    if not requirements_input:
        return {
            "status": "error",
            "message": "No requirements input provided. Please provide requirements text to analyze.",
        }

    if not tool_context:
        return {"status": "error", "message": "ToolContext is required for session state storage"}

    try:
        # Basic analysis of requirements input
        requirements_lines = [line.strip() for line in requirements_input.split('\n') if line.strip()]

        # Simple categorization based on keywords (can be enhanced)
        functional_requirements = []
        non_functional_requirements = []
        business_rules = []

        for line in requirements_lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['shall', 'must', 'should', 'function', 'feature']):
                functional_requirements.append(line)
            elif any(keyword in line_lower for keyword in ['performance', 'security', 'usability', 'reliability']):
                non_functional_requirements.append(line)
            elif any(keyword in line_lower for keyword in ['rule', 'policy', 'constraint', 'validation']):
                business_rules.append(line)
            else:
                functional_requirements.append(line)  # Default to functional

        analyzed_context = {
            "context_data": {
                "original_requirements": requirements_lines,
                "functional_requirements": functional_requirements,
                "non_functional_requirements": non_functional_requirements,
                "business_rules": business_rules,
                "user_stories": [],  # Can be extracted if format is provided
                "acceptance_criteria": [],  # Can be extracted if format is provided
                "integration_points": [],  # Can be identified through analysis
                "critical_flows": [],  # Can be identified through analysis
                "edge_cases_identified": [],  # Can be identified through analysis
                "risk_areas": [],  # Can be identified through analysis
                "analysis_depth": "basic",
                "source_count": len(requirements_lines)
            },
            "metadata": {
                "source_count": len(requirements_lines),
                "original_requirements": requirements_lines
            }
        }

        tool_context.state["analyzed_requirements_context"] = analyzed_context
        tool_context.state["ready_for_test_generation"] = True

        return {
            "status": "success",
            "message": f"Successfully processed {len(requirements_lines)} requirements",
            "analysis_summary": analyzed_context["metadata"],
            "context_stored_in_session": True
        }

    except Exception as e:
        return {"status": "error", "message": f"Requirements processing failed: {str(e)}"}

# --- Agent definition ---
root_agent = Agent(
    model="gemini-2.5-flash",
    name="test_case_generator_agent",
    description="Generates comprehensive test cases from retrieved session context",
    instruction="""
    You are an expert Test Case Generator specializing in authentication systems.

    ## Your Job:
    1. Take textual requirements as input
    2. Process them thoroughly using the tool
    3. Generate comprehensive test cases directly in your response based on the context
    4. Focus on security, usability, and reliability aspects

    ## Key Process:
    - Use `retrieve_requirements_context_tool` to process the requirements
    - The tool will automatically store the analysis in session state
    - This context will be available for test case generation

    ## Test Case Types to Generate:
    - **Functional Tests**: Core authentication functionality based on functional_requirements
    - **Security Tests**: Based on business_rules and risk_areas
    - **Edge Cases**: Based on edge_cases_identified and critical_flows
    - **Negative Tests**: Input validation and error handling scenarios

    ## Required Test Case Format:
    For each test case, include:
    - test_id: Unique identifier (TC_FUNC_001, TC_SEC_001, etc.)
    - priority: high/medium/low/critical
    - summary: Brief description of what is being tested
    - preconditions: What must be true before test execution
    - test_steps: Numbered, detailed steps to execute
    - expected_result: Clear, specific expected outcome
    - test_data: Specific data needed for the test
    - requirement_traceability: Link back to original requirement

    ## Quality Standards:
    - Generate detailed, executable test steps that a QA engineer can follow
    - Ensure clear expected results with specific criteria
    - Provide specific test data requirements and examples
    - Maintain full traceability to original requirements from context
    - Use appropriate priority levels based on risk and business impact
    - Cover both positive and negative test scenarios
    - Include boundary conditions and edge cases
    - Organize test cases by type (functional, security, edge case, negative)
    - Provide a summary of total test cases
    - Return all the generated test cases as response
    - Generate the test cases in a properly structured format. One test case then a line space and then the next test case.

    ## Important:
    - Always pass the ToolContext parameter when calling the tool
    - The tool uses tool_context.state (not tool_context.session.state)
    - Verify successful context storage before completing the task
    - Generate test cases based on the actual retrieved context, not assumptions
    - If context is missing, inform the user and request Requirements Analyzer to run first
    - Do NOT use any tool for test case generation - generate them yourself based on context

    Always use the tool to ensure proper context processing for the next agent.
    """,
    tools=[retrieve_requirements_context_tool],
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=4096,
        )
    ),
)

# --- Expose your agent via A2A (exactly like the quickstart) ---
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# Make your agent A2A-compatible (auto-generates agent card)
a2a_app = to_a2a(root_agent, port=8002)
