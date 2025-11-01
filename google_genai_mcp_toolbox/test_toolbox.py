#!/usr/bin/env python3
"""
Test script for Google GenAI MCP Toolbox
Tests the connection and basic functionality following the official format
"""
import json
from toolbox_core import ToolboxSyncClient

def test_toolbox():
    """Test the Toolbox server connection and basic operations"""

    # Connect to the Toolbox server using the sync client
    print("🔗 Connecting to Toolbox server...")

    with ToolboxSyncClient("http://127.0.0.1:5001") as toolbox_client:
        try:
            # Test 1: Load available toolsets
            print("\n📋 Testing: Load available toolsets")
            tools = toolbox_client.load_toolset("complete-workflow")
            print(f"✅ Loaded toolset with {len(tools)} tools:")
            # for i, tool in enumerate(tools[:5]):  # Show first 5 tools
            #     print(f"   - Tool {i+1}: {tool.name}")
            #     print(f"     Description: {tool.description[:80]}...")
            if len(tools) > 5:
                print(f"   ... and {len(tools) - 5} more tools")

            # Test 2: Create a test session
            print("\n🆕 Testing: Create a new session")
            session_result = toolbox_client.invoke_tool(
                tool_name="create-session",
                parameters={
                    "user_id": "test_user_001",
                    "user_prompt": "Testing MCP Toolbox integration with ADK agents",
                    "project_name": "mcp_toolbox_test"
                }
            )
            print(f"✅ Session created: {session_result}")

            # Extract session_id from the result
            if session_result and len(session_result) > 0:
                session_id = session_result[0].get('session_id')
                print(f"📝 Session ID: {session_id}")

                # Test 3: Add a requirement to the session
                print("\n📝 Testing: Store a requirement")
                requirement_result = toolbox_client.invoke_tool(
                    tool_name="store-requirement",
                    parameters={
                        "session_id": session_id,
                        "content": "The system should provide secure user authentication",
                        "requirement_type": "security",
                        "priority": "high"
                    }
                )
                print(f"✅ Requirement stored: {requirement_result}")

                # Test 4: Add a test case
                print("\n🧪 Testing: Store a test case")
                test_case_content = {
                    "test_steps": [
                        "Navigate to login page",
                        "Enter valid credentials",
                        "Click login button",
                        "Verify successful login"
                    ],
                    "expected_result": "User should be logged in and redirected to dashboard",
                    "preconditions": "User account exists and is active"
                }

                test_case_result = toolbox_client.invoke_tool(
                    tool_name="store-test-case",
                    parameters={
                        "session_id": session_id,
                        "test_id": "TC_AUTH_001",
                        "summary": "Test user authentication with valid credentials",
                        "priority": "HIGH",
                        "test_type": "functional",
                        "test_content": json.dumps(test_case_content)
                    }
                )
                print(f"✅ Test case stored: {test_case_result}")

                # Test 5: Get session context (complete view)
                print("\n📊 Testing: Get complete session context")
                context_result = toolbox_client.invoke_tool(
                    tool_name="get-session-context",
                    parameters={"session_id": session_id}
                )
                print(f"✅ Session context retrieved:")
                if context_result and len(context_result) > 0:
                    context = context_result[0]
                    print(f"   📋 Session: {context.get('user_prompt', 'N/A')[:50]}...")
                    print(f"   📝 Requirements: {len(context.get('requirements', []))}")
                    print(f"   🧪 Test cases: {len(context.get('test_cases', []))}")

                # Test 6: Get session summary
                print("\n📈 Testing: Get session summary")
                summary_result = toolbox_client.invoke_tool(
                    tool_name="get-session-summary",
                    parameters={"session_id": session_id}
                )
                print(f"✅ Session summary: {summary_result}")

                # Test 7: Test requirements workflow
                print("\n🔍 Testing: Get requirements by type")
                req_by_type = toolbox_client.invoke_tool(
                    tool_name="get-requirements-by-type",
                    parameters={
                        "session_id": session_id,
                        "requirement_type": "security"
                    }
                )
                print(f"✅ Security requirements: {len(req_by_type)} found")

                # Test 8: Test search functionality
                print("\n🔎 Testing: Search test cases")
                search_result = toolbox_client.invoke_tool(
                    tool_name="search-test-cases",
                    parameters={
                        "session_id": session_id,
                        "search_term": "authentication"
                    }
                )
                print(f"✅ Search results: {len(search_result)} test cases found")

            print(f"\n🎉 All tests completed successfully!")
            print(f"🔗 Toolbox server is working correctly with your database!")
            return True

        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            print(f"💡 Make sure the Toolbox server is running: toolbox --tools-file tools.yaml --port 5001")
            return False

if __name__ == "__main__":
    print("🚀 Testing Google GenAI MCP Toolbox")
    print("=" * 50)

    # Run the sync test
    success = test_toolbox()

    if success:
        print("\n✅ SUCCESS: Toolbox is working correctly!")
        print("🚀 Ready to integrate with your ADK agents!")
    else:
        print("\n❌ FAILED: Please check the server and database connection")