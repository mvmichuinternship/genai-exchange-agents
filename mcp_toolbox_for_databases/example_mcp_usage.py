"""
Example demonstrating Google's MCP Toolbox for databases integration.

This example shows how to use the MCP approach for persistent database operations
with Google ADK agents.
"""

import asyncio
import json
import uuid
from datetime import datetime

try:
    from database_mcp.client import DatabaseMCPClient, MCPClientContext
    from database_mcp.tools import create_database_tools, mcp_db_tools
except ImportError:
    print("Warning: MCP Toolbox for databases not available")
    print("Install dependencies with: pip install mcp mcp-server-postgres asyncpg")
    DatabaseMCPClient = None


async def example_mcp_workflow():
    """Example of complete MCP workflow."""
    if DatabaseMCPClient is None:
        print("❌ MCP dependencies not available")
        return

    print("🚀 MCP Toolbox for Databases - Example Workflow")
    print("=" * 60)

    try:
        # Use context manager for automatic connection management
        async with MCPClientContext() as client:
            print("✅ Connected to MCP database server")

            # Step 1: Create a new session
            print("\n📝 Step 1: Creating MCP session...")
            session_result = await client.create_session_workflow(
                user_id="example_user_123",
                user_prompt="Create authentication system with OAuth2 and MFA support",
                project_name="Security Enhancement Project"
            )

            if not session_result.get("success"):
                print(f"❌ Failed to create session: {session_result.get('error')}")
                return

            session_id = session_result["session_id"]
            print(f"✅ Session created: {session_id}")

            # Step 2: Store agent analysis (simulating requirement analyzer output)
            print("\n🔍 Step 2: Storing agent analysis...")
            analysis_content = """
            Authentication Requirements Analysis:
            1. System must support OAuth2 authorization code flow with PKCE
            2. Multi-factor authentication (MFA) must be implemented
            3. Session management with secure token handling
            4. Role-based access control (RBAC) implementation
            5. Password policy enforcement with complexity requirements
            """

            analysis_result = await client.store_agent_analysis(
                session_id=session_id,
                analysis_content=analysis_content.strip(),
                requirement_type="security_requirements"
            )

            if analysis_result.get("success"):
                print(f"✅ Analysis stored with ID: {analysis_result['requirement_id']}")
            else:
                print(f"❌ Failed to store analysis: {analysis_result.get('error')}")

            # Step 3: Store structured test cases
            print("\n🧪 Step 3: Storing structured test cases...")
            test_suite = {
                "test_suite": {
                    "name": "OAuth2 and MFA Test Suite",
                    "description": "Comprehensive test cases for authentication system",
                    "total_tests": 3,
                    "generated_date": datetime.now().date().isoformat(),
                    "test_cases": [
                        {
                            "test_id": "TC_AUTH_001",
                            "priority": "CRITICAL",
                            "type": "Security",
                            "summary": "Test OAuth2 authorization code flow with PKCE",
                            "preconditions": [
                                "OAuth2 server is running",
                                "Client application is registered",
                                "PKCE is enabled"
                            ],
                            "test_steps": [
                                "Navigate to login page",
                                "Click 'Login with OAuth2'",
                                "Verify PKCE challenge generation",
                                "Complete authorization flow",
                                "Verify access token received"
                            ],
                            "test_data": {
                                "client_id": "test_client_123",
                                "redirect_uri": "https://app.example.com/callback",
                                "scope": "read write"
                            },
                            "expected_result": "User successfully authenticated with valid access token",
                            "requirement_traceability": "REQ_AUTH_001 - OAuth2 PKCE Implementation"
                        },
                        {
                            "test_id": "TC_MFA_001",
                            "priority": "HIGH",
                            "type": "Security",
                            "summary": "Test multi-factor authentication flow",
                            "preconditions": [
                                "User has MFA enabled",
                                "TOTP authenticator app configured",
                                "SMS service is available"
                            ],
                            "test_steps": [
                                "Complete primary authentication",
                                "System prompts for second factor",
                                "Enter TOTP code from authenticator",
                                "Verify MFA completion",
                                "Access protected resource"
                            ],
                            "test_data": {
                                "username": "testuser@example.com",
                                "mfa_method": "totp",
                                "backup_method": "sms"
                            },
                            "expected_result": "MFA completed successfully, user gains access",
                            "requirement_traceability": "REQ_MFA_001 - Multi-Factor Authentication"
                        },
                        {
                            "test_id": "TC_RBAC_001",
                            "priority": "MEDIUM",
                            "type": "Functional",
                            "summary": "Test role-based access control",
                            "preconditions": [
                                "User has specific role assigned",
                                "Resources have role-based permissions",
                                "RBAC system is configured"
                            ],
                            "test_steps": [
                                "Authenticate as user with 'viewer' role",
                                "Attempt to access read-only resource",
                                "Verify access granted",
                                "Attempt to access admin resource",
                                "Verify access denied"
                            ],
                            "test_data": {
                                "user_role": "viewer",
                                "allowed_resource": "/api/data/read",
                                "forbidden_resource": "/api/admin/users"
                            },
                            "expected_result": "Role-based access control enforced correctly",
                            "requirement_traceability": "REQ_RBAC_001 - Role-Based Access Control"
                        }
                    ]
                }
            }

            test_cases_result = await client.create_test_cases_from_suite(
                session_id=session_id,
                test_suite_json=json.dumps(test_suite)
            )

            if test_cases_result.get("success"):
                print(f"✅ Test cases stored: {test_cases_result['test_cases_created']} cases created")
                print(f"   Test case IDs: {', '.join(test_cases_result['test_case_ids'])}")
            else:
                print(f"❌ Failed to store test cases: {test_cases_result.get('error')}")

            # Step 4: Retrieve complete session context
            print("\n📊 Step 4: Retrieving complete session context...")
            context_result = await client.get_session_with_context(session_id)

            if context_result.get("success"):
                context = context_result["context"]
                session_data = context["session"]
                requirements = context["requirements"]
                test_cases = context["test_cases"]

                print(f"✅ Session context retrieved:")
                print(f"   📋 Session: {session_data['session_id'][:16]}...")
                print(f"   📝 Requirements: {len(requirements)} stored")
                print(f"   🧪 Test cases: {len(test_cases)} stored")
                print(f"   📅 Created: {session_data['created_at']}")
                print(f"   🔄 Status: {session_data['status']}")

                # Show test case summary
                if test_cases:
                    print(f"\n   🎯 Test Case Summary:")
                    for tc in test_cases:
                        print(f"      - {tc['test_id']}: {tc['summary'][:50]}...")

            else:
                print(f"❌ Failed to retrieve context: {context_result.get('error')}")

            # Step 5: Demonstrate test case retrieval as suite
            print("\n📋 Step 5: Retrieving test cases as structured suite...")
            suite_result = await client.get_session_test_cases(session_id, as_suite=True)

            if suite_result.get("success"):
                test_suite = suite_result["test_suite"]
                print(f"✅ Test suite retrieved:")
                print(f"   📦 Suite: {test_suite['name']}")
                print(f"   📊 Total tests: {test_suite['total_tests']}")
                print(f"   📅 Generated: {test_suite['generated_date']}")

                # Show test case priorities
                priorities = {}
                for tc in test_suite["test_cases"]:
                    priority = tc["priority"]
                    priorities[priority] = priorities.get(priority, 0) + 1

                print(f"   🎯 Priority breakdown: {dict(priorities)}")

            else:
                print(f"❌ Failed to retrieve test suite: {suite_result.get('error')}")

            print("\n🎉 MCP workflow completed successfully!")
            print("\nKey Benefits Demonstrated:")
            print("✓ Persistent session management")
            print("✓ Structured requirements storage")
            print("✓ Standardized test case format")
            print("✓ Complete audit trail")
            print("✓ Google MCP protocol compliance")

    except Exception as e:
        print(f"❌ MCP workflow failed: {e}")


async def example_mcp_tools_usage():
    """Example of using MCP tools directly."""
    print("\n" + "=" * 60)
    print("🔧 MCP Tools Direct Usage Example")
    print("=" * 60)

    try:
        # Example using the tools directly (as agents would)
        session_result = await mcp_db_tools.create_mcp_session(
            user_id="tool_user_456",
            user_prompt="Test direct tool usage",
            project_name="MCP Tools Test"
        )

        if session_result["success"]:
            session_id = session_result["session_id"]
            print(f"✅ Session created via tools: {session_id}")

            # Store a requirement
            req_result = await mcp_db_tools.store_mcp_requirement(
                session_id=session_id,
                requirement_content="System must provide API rate limiting",
                requirement_type="performance",
                priority="high"
            )

            if req_result["success"]:
                print(f"✅ Requirement stored: {req_result['requirement_id']}")

            # Get session context
            context_result = await mcp_db_tools.get_mcp_session_context(session_id)
            if context_result["success"]:
                print("✅ Session context retrieved via tools")

        print("✅ MCP tools usage example completed")

    except Exception as e:
        print(f"❌ MCP tools example failed: {e}")
    finally:
        # Cleanup tools
        await mcp_db_tools.close()


async def main():
    """Main example function."""
    print("Google's MCP Toolbox for Databases - Examples")
    print("=" * 60)

    # Run the complete workflow example
    await example_mcp_workflow()

    # Run the tools usage example
    await example_mcp_tools_usage()

    print("\n" + "=" * 60)
    print("📚 Learn More:")
    print("- Google MCP Documentation: https://github.com/modelcontextprotocol")
    print("- Integration Guide: See README.md")
    print("- Deploy to Cloud: python deploy.py all")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())