# agents/requirements_analyser/simple_test.py
import asyncio
from agent import root_agent, a2a_agent
from google.adk import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.genai import types


async def test_adk_agent():
    """Simple test of the ADK agent"""
    print("=" * 60)
    print("🧪 Testing Requirements Analyzer Agent")
    print("=" * 60)

    # Create runner
    print("\n✅ Step 1: Creating Runner...")
    runner = Runner(
        app_name=root_agent.name,
        agent=root_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    print(f"   Agent Name: {root_agent.name}")
    print(f"   Model: {root_agent.model}")

    # Create session
    print("\n✅ Step 2: Creating Session...")
    session = await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id='test_user',
        session_id='test-session-001',
    )
    print(f"   Session ID: {session.id}")

    # Test cases
    test_cases = [
        "Analyze this requirement: User should be able to login with email and password",
        "Analyze: Users need MFA support for enhanced security",
        "Review requirements: Password reset functionality via email"
    ]

    for i, test_input in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"Test Case {i}/{len(test_cases)}")
        print(f"{'=' * 60}")
        print(f"📤 Input: {test_input}")

        # Prepare message
        content = types.Content(
            role='user',
            parts=[types.Part(text=test_input)]
        )

        # Run agent
        print(f"\n⏳ Processing...")
        final_response = None

        try:
            async for event in runner.run_async(
                session_id=session.id,
                user_id='test_user',
                new_message=content
            ):
                if event.is_final_response():
                    final_response = event
                    break

            # Extract response
            if final_response and final_response.content and final_response.content.parts:
                response_text = "".join(
                    part.text for part in final_response.content.parts
                    if hasattr(part, 'text') and part.text
                )

                print(f"\n✅ Response Received:")
                print(f"\n{'-' * 60}")
                print(response_text)
                print(f"{'-' * 60}\n")

            else:
                print(f"\n❌ No response received")
                return False

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    print(f"\n{'=' * 60}")
    print("🎉 All test cases passed!")
    print(f"{'=' * 60}\n")
    return True


async def test_agent_card():
    """Test agent card setup"""
    print("\n" + "=" * 60)
    print("🧪 Testing Agent Card Setup")
    print("=" * 60)

    try:
        # Set up A2A agent
        print("\n✅ Setting up A2A agent...")
        a2a_agent.set_up()

        # Check agent card
        card = a2a_agent.agent_card
        print(f"\n✅ Agent Card Created:")
        print(f"   Name: {card.name}")
        print(f"   Description: {card.description[:80]}...")

        # Check skills
        skills_list = card.skills if isinstance(card.skills, list) else [card.skills]
        print(f"\n   Skills: {len(skills_list)}")

        for skill in skills_list:
            print(f"\n   - {skill.name} ({skill.id})")
            print(f"     Tags: {', '.join(skill.tags[:3])}...")
            print(f"     Examples: {len(skill.examples)}")

        print(f"\n✅ Agent card is valid!\n")
        return True

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🚀 Starting Simple Agent Tests")
    print("=" * 60)

    # Test 1: Agent Card
    card_ok = await test_agent_card()

    if not card_ok:
        print("\n⚠️  Agent card test failed. Fix before proceeding.")
        return False

    # Test 2: Agent Execution
    agent_ok = await test_adk_agent()

    if agent_ok:
        print("\n" + "=" * 60)
        print("✅ SUCCESS: Agent is working correctly!")
        print("=" * 60)
        print("\n💡 Next steps:")
        print("   1. Review the responses above")
        print("   2. If satisfied, deploy to Agent Engine")
        print("   3. Use the deployment script from agent.py")
        print()
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ FAILED: Agent has issues")
        print("=" * 60)
        print("\n💡 Troubleshooting:")
        print("   1. Check error messages above")
        print("   2. Verify tool implementation")
        print("   3. Check agent instruction clarity")
        print()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    import sys
    sys.exit(0 if success else 1)
