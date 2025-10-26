# agents/decider/agent.py
from google.adk.agents import Agent
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.auth import default
from google.auth.transport.requests import Request
from a2a.client import ClientConfig, ClientFactory
from a2a.types import TransportProtocol
import httpx
import logging
import asyncio
import vertexai

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = "195472357560"
LOCATION = "us-central1"
ANALYZER_RESOURCE_ID = "5155975060502085632"  # Your deployed analyzer
GENERATOR_RESOURCE_ID = "5036488932888412160"  # Your deployed generator (if available)
STAGING_BUCKET = "gs://requirements-bucket"

# Initialize Vertex AI
vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET
)

# ✅ Set up authentication (using Application Default Credentials)
credentials, _ = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
credentials.refresh(Request())

# ✅ Build A2A URLs
analyzer_card_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ANALYZER_RESOURCE_ID}/a2a/v1/card"
generator_card_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{GENERATOR_RESOURCE_ID}/a2a/v1/card"

# ✅ Create authenticated A2A client factory
def create_client_factory():
    """Create ClientFactory with fresh credentials"""
    # Refresh credentials to ensure they're valid
    credentials.refresh(Request())

    return ClientFactory(
        ClientConfig(
            supported_transports=[TransportProtocol.http_json],
            use_client_preference=True,
            httpx_client=httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {credentials.token}",
                    "Content-Type": "application/json",
                },
                timeout=60.0  # Increased timeout for remote agents
            ),
        )
    )

# ✅ Fetch agent card with authentication
async def fetch_agent_card(card_url: str):
    """Fetch agent card via authenticated HTTP request"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            card_url,
            headers={
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json",
            }
        )
        response.raise_for_status()
        return response.json()

# ✅ Create RemoteA2aAgent for Analyzer with authentication
async def create_analyzer_agent():
    """Create authenticated analyzer agent"""
    try:
        # Fetch the agent card
        agent_card = await fetch_agent_card(analyzer_card_url)
        logger.info(f"✅ Fetched analyzer agent card: {agent_card.get('name', 'Unknown')}")

        # Create the remote agent with factory
        analyzer_agent = RemoteA2aAgent(
            name="requirement_analyzer",
            description="Expert Requirements Analyzer specializing in authentication systems",
            agent_card=analyzer_card_url,
            a2a_client_factory=create_client_factory(),
        )

        return analyzer_agent

    except Exception as e:
        logger.error(f"❌ Failed to create analyzer agent: {e}")
        # Fallback: try URL-only approach (less reliable but worth a try)
        logger.info("⚠️  Attempting fallback URL-only approach...")
        return RemoteA2aAgent(
            name="requirement_analyzer",
            description="Expert Requirements Analyzer",
            agent_card=analyzer_card_url,
            a2a_client_factory=create_client_factory(),
        )

# ✅ Initialize the analyzer agent
# Note: This is async, so we'll handle it in the main flow
analyzer_agent = None

# ✅ Root Decider Agent (Simplified)
def create_root_agent(sub_agents):
    """Create root agent with given sub-agents"""
    return Agent(
        model="gemini-2.0-flash-exp",
        name="decider_agent",
        description="Intelligent router that delegates work to specialized A2A agents",
        instruction="""
        You are an intelligent decider agent that routes user requests to specialized agents.

        ## Your Sub-Agents:
        - **requirement_analyzer**: Analyzes requirements, extracts functional/non-functional requirements,
          identifies security requirements, business rules, user stories, and test contexts.

        ## Your Decision Process:
        1. **Understand the user's request**
           - Are they asking to analyze requirements?
           - Are they asking to generate test cases?
           - Do they want both?

        2. **Route appropriately**
           - For analysis requests: Delegate to requirement_analyzer sub-agent
           - For test generation: (Note: generator not yet connected, acknowledge this)
           - For both: Start with requirement_analyzer, then acknowledge generator not ready

        3. **Present results clearly**
           - State which agent you're using
           - Show the agent's response
           - Summarize the outcome

        ## Example Routing:
        - "Analyze login requirements" → Use requirement_analyzer
        - "What requirements does the payment system need?" → Use requirement_analyzer
        - "Review authentication requirements" → Use requirement_analyzer
        - "Generate test cases" → Acknowledge generator not yet available

        ## Response Format:
        1. "I'm routing this to [agent_name] because..."
        2. [Show agent response]
        3. "Analysis completed. [Brief summary]"

        Always be clear about which agent is handling the work.
        """,
        sub_agents=sub_agents,
    )

# ✅ Process Query Function
async def process_query(user_query: str, user_id: str = "user") -> str:
    """
    Process a user query through the decider agent system.
    """
    global analyzer_agent

    # Initialize analyzer agent if not already done
    if analyzer_agent is None:
        logger.info("🔧 Initializing analyzer agent...")
        analyzer_agent = await create_analyzer_agent()

    # Create root agent with initialized sub-agents
    root_agent = create_root_agent([analyzer_agent])

    print(f"\n{'='*60}")
    print(f"Query: {user_query}")
    print('='*60)

    try:
        # Create session service
        session_service = InMemorySessionService()
        session = await session_service.create_session(
            app_name="decider_app",
            user_id=user_id,
            session_id=f"session-{user_id}"
        )

        # Create runner for root agent
        runner = Runner(
            agent=root_agent,
            app_name="decider_app",
            session_service=session_service,
            artifact_service=InMemoryArtifactService(),
            memory_service=InMemoryMemoryService(),
        )

        # Prepare user message
        content = types.Content(
            role='user',
            parts=[types.Part(text=user_query)]
        )

        # Run agent and collect responses
        print("\n[AGENT RESPONSE]")
        print("-" * 60)

        final_response = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=content
        ):
            # Check if this is the final response
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = "".join(
                        part.text for part in event.content.parts
                        if hasattr(part, 'text') and part.text
                    )
                    print(final_response)
                    break

        print("-" * 60)
        print(f"\n✅ Task completed\n")
        print("=" * 60)
        return final_response

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


# ✅ Test Script
async def run_tests():
    """Run test queries"""
    test_queries = [
        "Analyze these login requirements: Users need email and password authentication",
        # "Review security requirements for user authentication with MFA support",
        # "What are the key requirements for a password reset feature?",
    ]

    print("\n" + "="*60)
    print("🚀 Starting Decider Agent Tests")
    print("="*60)

    for i, query in enumerate(test_queries, 1):
        print(f"\n\n{'#'*60}")
        print(f"# Test {i}/{len(test_queries)}")
        print(f"{'#'*60}")

        response = await process_query(query, user_id=f"test_user_{i:03d}")

        if response:
            print(f"✅ Test {i} passed")
        else:
            print(f"❌ Test {i} failed")

        if i < len(test_queries):
            await asyncio.sleep(2)  # Pause between tests

    print("\n" + "="*60)
    print("🎉 All tests completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(run_tests())

