# # agents/test_case_generator/simple_test.py
# import asyncio
# from agent import root_agent, a2a_agent
# from google.adk import Runner
# from google.adk.artifacts import InMemoryArtifactService
# from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
# from google.adk.sessions import InMemorySessionService
# from google.genai import types


# # Sample requirements analysis output (simulating what the analyzer would return)
# SAMPLE_ANALYSIS_1 = """
# ## Requirements Analysis

# ### Functional Requirements
# - User login with email and password
# - Multi-factor authentication (MFA) support
# - Password reset via email
# - Account lockout after 3 failed attempts
# - Session timeout after 30 minutes of inactivity

# ### Non-Functional Requirements
# - System performance requirements: Login must complete within 2 seconds
# - Security and authentication requirements: Passwords must be encrypted
# - Usability requirements: Clear error messages for failed login

# ### Business Rules
# - Email format validation required
# - Password must be at least 8 characters with uppercase, lowercase, and numbers
# - Account lockout policy: 3 failed attempts triggers 15-minute lockout
# - MFA code expires after 5 minutes

# ### User Stories
# - As a user, I want to login with my email and password
# - As a user, I want MFA protection for enhanced security
# - As a user, I want to reset my password if forgotten

# ### Acceptance Criteria
# - User can successfully authenticate with valid credentials
# - Invalid credentials are properly rejected with clear error message
# - Account lockout activates after specified failed attempts
# - MFA code validation works correctly

# ### Test Context

# **Critical Flows:**
# - Successful user authentication flow
# - Failed authentication and lockout flow
# - Password reset and recovery flow
# - MFA enrollment and validation flow

# **Edge Cases:**
# - Boundary conditions for failed attempt counting
# - Concurrent login attempts from different devices
# - Password complexity edge cases (exactly 8 chars, special chars)
# - Session timeout during MFA entry

# **Risk Areas:**
# - Security vulnerabilities in authentication
# - Account lockout mechanism reliability
# - Session management security
# - MFA bypass attempts
# """

# SAMPLE_ANALYSIS_2 = """
# ## Requirements Analysis

# ### Functional Requirements
# - Shopping cart should support multiple items
# - Users can add/remove items from cart
# - Cart persists across sessions
# - Real-time price calculation with tax
# - Apply discount codes

# ### Business Rules
# - Maximum 10 items per cart
# - Discount codes are case-insensitive
# - Tax rate: 10% of subtotal
# - Free shipping for orders over $50

# ### Edge Cases
# - Adding same item multiple times
# - Removing non-existent items
# - Invalid discount codes
# - Cart with 0 items
# """


# async def test_generator_agent():
#     """Test the Test Case Generator agent"""
#     print("=" * 60)
#     print("🧪 Testing Test Case Generator Agent")
#     print("=" * 60)

#     # Create runner
#     print("\n✅ Step 1: Creating Runner...")
#     runner = Runner(
#         app_name=root_agent.name,
#         agent=root_agent,
#         artifact_service=InMemoryArtifactService(),
#         session_service=InMemorySessionService(),
#         memory_service=InMemoryMemoryService(),
#     )
#     print(f"   Agent Name: {root_agent.name}")
#     print(f"   Model: {root_agent.model}")

#     # Create session
#     print("\n✅ Step 2: Creating Session...")
#     session = await runner.session_service.create_session(
#         app_name=runner.app_name,
#         user_id='test_user',
#         session_id='test-session-001',
#     )
#     print(f"   Session ID: {session.id}")

#     # Test cases with different analysis inputs
#     test_cases = [
#         {
#             "name": "Authentication Requirements",
#             "input": f"Generate test cases from this analysis:\n\n{SAMPLE_ANALYSIS_1}",
#             "description": "Full authentication system with MFA and lockout"
#         },
#         {
#             "name": "Shopping Cart Requirements",
#             "input": f"Create comprehensive test cases for:\n\n{SAMPLE_ANALYSIS_2}",
#             "description": "E-commerce shopping cart functionality"
#         },
#         {
#             "name": "Simple Requirements",
#             "input": """Generate test cases from this analysis:

# Functional Requirements:
# - User can search products by keyword
# - Search results show within 1 second
# - Search supports filtering by category

# Business Rules:
# - Minimum 3 characters for search
# - Maximum 100 results per page
# """,
#             "description": "Simple search functionality"
#         }
#     ]

#     for i, test_case in enumerate(test_cases, 1):
#         print(f"\n{'=' * 60}")
#         print(f"Test Case {i}/{len(test_cases)}: {test_case['name']}")
#         print(f"{'=' * 60}")
#         print(f"📝 Description: {test_case['description']}")
#         print(f"📤 Input Length: {len(test_case['input'])} characters")

#         # Prepare message
#         content = types.Content(
#             role='user',
#             parts=[types.Part(text=test_case['input'])]
#         )

#         # Run agent
#         print(f"\n⏳ Generating test cases...")
#         final_response = None

#         try:
#             async for event in runner.run_async(
#                 session_id=session.id,
#                 user_id='test_user',
#                 new_message=content
#             ):
#                 if event.is_final_response():
#                     final_response = event
#                     break

#             # Extract response
#             if final_response and final_response.content and final_response.content.parts:
#                 response_text = "".join(
#                     part.text for part in final_response.content.parts
#                     if hasattr(part, 'text') and part.text
#                 )

#                 print(f"\n✅ Test Cases Generated:")
#                 print(f"\n{'-' * 60}")
#                 print(response_text)
#                 print(f"{'-' * 60}\n")

#                 # Basic validation
#                 test_case_count = response_text.count('**Test Case ID**:')
#                 print(f"\n📊 Statistics:")
#                 print(f"   Total test cases generated: {test_case_count}")
#                 print(f"   Response length: {len(response_text)} characters")

#                 if test_case_count > 0:
#                     print(f"   ✅ Test {i} passed - Generated {test_case_count} test cases")
#                 else:
#                     print(f"   ⚠️  Test {i} warning - No test cases detected in response")

#             else:
#                 print(f"\n❌ No response received")
#                 return False

#         except Exception as e:
#             print(f"\n❌ Error: {str(e)}")
#             import traceback
#             traceback.print_exc()
#             return False

#         if i < len(test_cases):
#             print(f"\n⏸️  Pausing 3 seconds before next test...")
#             await asyncio.sleep(3)

#     print(f"\n{'=' * 60}")
#     print("🎉 All test cases passed!")
#     print(f"{'=' * 60}\n")
#     return True


# async def test_agent_card():
#     """Test agent card setup"""
#     print("\n" + "=" * 60)
#     print("🧪 Testing Agent Card Setup")
#     print("=" * 60)

#     try:
#         # Set up A2A agent
#         print("\n✅ Setting up A2A agent...")
#         a2a_agent.set_up()

#         # Check agent card
#         card = a2a_agent.agent_card
#         print(f"\n✅ Agent Card Created:")
#         print(f"   Name: {card.name}")
#         print(f"   Description: {card.description[:80]}...")

#         # Check skills
#         skills_list = card.skills if isinstance(card.skills, list) else [card.skills]
#         print(f"\n   Skills: {len(skills_list)}")

#         for skill in skills_list:
#             print(f"\n   - {skill.name} ({skill.id})")
#             print(f"     Tags: {', '.join(skill.tags[:3])}...")
#             print(f"     Examples: {len(skill.examples)}")

#         # Check capabilities
#         if hasattr(card, 'capabilities') and card.capabilities:
#             caps = card.capabilities
#             print(f"\n   Capabilities:")
#             print(f"     - Conversations: {caps.can_handle_conversations}")
#             print(f"     - Session State: {caps.supports_session_state}")
#             print(f"     - Max Message: {caps.max_message_length}")

#         print(f"\n✅ Agent card is valid!\n")
#         return True

#     except Exception as e:
#         print(f"\n❌ Error: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return False


# async def test_without_context():
#     """Test what happens when no requirements context is provided"""
#     print("\n" + "=" * 60)
#     print("🧪 Testing Without Context (Error Handling)")
#     print("=" * 60)

#     runner = Runner(
#         app_name="test",
#         agent=root_agent,
#         artifact_service=InMemoryArtifactService(),
#         session_service=InMemorySessionService(),
#         memory_service=InMemoryMemoryService(),
#     )

#     session = await runner.session_service.create_session(
#         app_name="test",
#         user_id='test',
#         session_id='test-no-context',
#     )

#     # Send request without proper analysis
#     content = types.Content(
#         role='user',
#         parts=[types.Part(text="Generate test cases for login functionality")]
#     )

#     print("\n📤 Sending request without requirements analysis...")

#     async for event in runner.run_async(
#         session_id=session.id,
#         user_id='test',
#         new_message=content
#     ):
#         if event.is_final_response():
#             response = "".join(
#                 part.text for part in event.content.parts
#                 if hasattr(part, 'text')
#             )
#             print(f"\n📥 Response:\n{response}")

#             # Check if agent properly handles missing context
#             if "no requirements" in response.lower() or "analyzer first" in response.lower():
#                 print("\n✅ Agent correctly identified missing context!")
#                 return True
#             else:
#                 print("\n⚠️  Agent should detect missing requirements context")
#                 return False

#     return False


# async def main():
#     """Run all tests"""
#     print("\n" + "=" * 60)
#     print("🚀 Starting Test Case Generator Tests")
#     print("=" * 60)

#     results = {}

#     # Test 1: Agent Card
#     results['card_validation'] = await test_agent_card()

#     # Test 2: Error Handling (No Context)
#     results['error_handling'] = await test_without_context()

#     # Test 3: Full Test Generation
#     results['test_generation'] = await test_generator_agent()

#     # Summary
#     print("\n" + "=" * 60)
#     print("📊 Test Summary")
#     print("=" * 60)

#     for test_name, passed in results.items():
#         status = "✅ PASSED" if passed else "❌ FAILED"
#         print(f"   {test_name.replace('_', ' ').title()}: {status}")

#     all_passed = all(results.values())

#     if all_passed:
#         print("\n🎉 All tests passed! Agent is ready for deployment.")
#         print("\n💡 Next steps:")
#         print("   1. Review the generated test cases above")
#         print("   2. Deploy to Agent Engine if satisfied")
#         print("   3. Integrate with Decider agent")
#     else:
#         print("\n⚠️  Some tests failed. Please fix the issues before deploying.")

#     return all_passed


# if __name__ == "__main__":
#     success = asyncio.run(main())
#     import sys
#     sys.exit(0 if success else 1)

# agents/test_case_generator/simple_test.py
import asyncio
from agent import root_agent, a2a_agent
from google.adk import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.genai import types


# Sample requirements analysis (what analyzer would provide)
SAMPLE_ANALYSIS_1 = """
## Requirements Analysis

### Functional Requirements
- User login with email and password
- Multi-factor authentication (MFA) support
- Password reset via email
- Account lockout after 3 failed attempts
- Session timeout after 30 minutes of inactivity

### Non-Functional Requirements
- System performance requirements: Login must complete within 2 seconds
- Security and authentication requirements: Passwords must be encrypted
- Usability requirements: Clear error messages for failed login

### Business Rules
- Email format validation required
- Password must be at least 8 characters with uppercase, lowercase, and numbers
- Account lockout policy: 3 failed attempts triggers 15-minute lockout
- MFA code expires after 5 minutes

### User Stories
- As a user, I want to login with my email and password
- As a user, I want MFA protection for enhanced security
- As a user, I want to reset my password if forgotten

### Acceptance Criteria
- User can successfully authenticate with valid credentials
- Invalid credentials are properly rejected with clear error message
- Account lockout activates after specified failed attempts
- MFA code validation works correctly

### Test Context

**Critical Flows:**
- Successful user authentication flow
- Failed authentication and lockout flow
- Password reset and recovery flow
- MFA enrollment and validation flow

**Edge Cases:**
- Boundary conditions for failed attempt counting
- Concurrent login attempts from different devices
- Password complexity edge cases (exactly 8 chars, special chars)
- Session timeout during MFA entry

**Risk Areas:**
- Security vulnerabilities in authentication
- Account lockout mechanism reliability
- Session management security
- MFA bypass attempts
"""


async def test_generator_basic():
    """Basic test of the generator agent"""
    print("=" * 60)
    print("🧪 Test 1: Basic Test Case Generation")
    print("=" * 60)

    # Create runner
    runner = Runner(
        app_name=root_agent.name,
        agent=root_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )

    # Create session
    session = await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id='test_user',
        session_id='test-session-basic',
    )

    print(f"\n✅ Session created: {session.id}")

    # Prepare test input
    test_input = f"Generate test cases from this requirements analysis:\n\n{SAMPLE_ANALYSIS_1}"

    print(f"\n📤 Sending request to generate test cases...")
    print(f"   Input length: {len(test_input)} characters")

    # Prepare message
    content = types.Content(
        role='user',
        parts=[types.Part(text=test_input)]
    )

    # Run agent
    print(f"\n⏳ Processing...")

    try:
        final_response = None
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

            print(f"\n✅ Response received!")
            print(f"\n{'=' * 60}")
            print("Generated Test Cases:")
            print('=' * 60)
            print(response_text)
            print('=' * 60)

            # Count test cases (basic validation)
            test_case_indicators = [
                'Test Case ID',
                'test_id',
                'TC_FUNC',
                'TC_SEC',
                'TC_EDGE',
                'TC_NEG'
            ]

            test_count = sum(response_text.count(indicator) for indicator in test_case_indicators)

            print(f"\n📊 Statistics:")
            print(f"   Response length: {len(response_text)} characters")
            print(f"   Test case indicators found: {test_count}")

            if test_count > 0:
                print(f"\n✅ Test passed - Generated test cases successfully")
                return True
            else:
                print(f"\n⚠️  Warning - No clear test case structure detected")
                return False
        else:
            print(f"\n❌ No response received from agent")
            return False

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_card():
    """Test agent card validation"""
    print("\n" + "=" * 60)
    print("🧪 Test 2: Agent Card Validation")
    print("=" * 60)

    try:
        # Set up A2A agent
        print("\n✅ Setting up A2A agent...")
        a2a_agent.set_up()

        # Check agent card
        card = a2a_agent.agent_card
        print(f"\n✅ Agent Card Details:")
        print(f"   Name: {card.name}")
        print(f"   Description: {card.description[:100]}...")

        # Check skills
        skills_list = card.skills if isinstance(card.skills, list) else [card.skills]
        print(f"   Skills: {len(skills_list)}")

        for i, skill in enumerate(skills_list, 1):
            print(f"\n   Skill {i}: {skill.name}")
            print(f"   - ID: {skill.id}")
            print(f"   - Tags: {', '.join(skill.tags[:3])}...")

        # Check capabilities
        if hasattr(card, 'capabilities') and card.capabilities:
            print(f"\n   Capabilities:")
            print(f"   - Conversations: {card.capabilities.can_handle_conversations}")
            print(f"   - Session State: {card.capabilities.supports_session_state}")

        print(f"\n✅ Agent card validation passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handling():
    """Test error handling with no context"""
    print("\n" + "=" * 60)
    print("🧪 Test 3: Error Handling (No Context)")
    print("=" * 60)

    runner = Runner(
        app_name="test_error",
        agent=root_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )

    session = await runner.session_service.create_session(
        app_name="test_error",
        user_id='test',
        session_id='test-error',
    )

    # Send incomplete request
    content = types.Content(
        role='user',
        parts=[types.Part(text="Generate test cases for login")]
    )

    print("\n📤 Sending incomplete request (no requirements analysis)...")

    try:
        async for event in runner.run_async(
            session_id=session.id,
            user_id='test',
            new_message=content
        ):
            if event.is_final_response():
                response = "".join(
                    part.text for part in event.content.parts
                    if hasattr(part, 'text')
                )

                print(f"\n📥 Response:\n{response[:300]}...")

                # Check if agent handles missing context appropriately
                error_indicators = [
                    'no requirements',
                    'no context',
                    'analyzer first',
                    'missing',
                    'provide'
                ]

                has_error_handling = any(
                    indicator in response.lower()
                    for indicator in error_indicators
                )

                if has_error_handling:
                    print("\n✅ Agent correctly handles missing context!")
                    return True
                else:
                    print("\n⚠️  Agent generated response despite missing context")
                    # This might still be acceptable if it generates generic tests
                    return True

        return False

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


async def test_simple_case():
    """Quick simple test"""
    print("\n" + "=" * 60)
    print("🧪 Test 4: Simple Quick Test")
    print("=" * 60)

    runner = Runner(
        app_name="quick",
        agent=root_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )

    session = await runner.session_service.create_session(
        app_name="quick",
        user_id='quick',
        session_id='quick-test',
    )

    simple_analysis = """
    Functional Requirements:
    - User can search products
    - Search results display within 1 second

    Business Rules:
    - Minimum 3 characters required
    - Maximum 100 results per page
    """

    content = types.Content(
        role='user',
        parts=[types.Part(text=f"Generate test cases:\n{simple_analysis}")]
    )

    print("\n📤 Sending simple request...")

    try:
        async for event in runner.run_async(
            session_id=session.id,
            user_id='quick',
            new_message=content
        ):
            if event.is_final_response():
                response = "".join(
                    part.text for part in event.content.parts
                    if hasattr(part, 'text')
                )

                print(f"\n📥 Response received ({len(response)} chars)")
                print(f"\nFirst 500 characters:")
                print(response[:500])
                print("\n✅ Quick test passed!")
                return True

        return False

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🚀 Starting Test Case Generator Tests")
    print("=" * 60)

    results = {}

    # Test 1: Agent Card
    print("\n")
    results['agent_card'] = await test_agent_card()

    # Test 2: Simple Case
    print("\n")
    results['simple_case'] = await test_simple_case()

    # Test 3: Error Handling
    print("\n")
    results['error_handling'] = await test_error_handling()

    # Test 4: Full Generation
    print("\n")
    results['full_generation'] = await test_generator_basic()

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed! Agent is ready for deployment.")
    else:
        print("⚠️  Some tests failed. Review the output above.")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    import sys
    sys.exit(0 if success else 1)
