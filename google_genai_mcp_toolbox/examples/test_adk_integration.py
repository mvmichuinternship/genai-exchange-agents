"""
Test ADK integration with Google GenAI MCP Toolbox.

This script tests the complete integration between ADK agents and
Google's GenAI Toolbox for database persistence.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from adk_toolbox import ToolboxClient, create_adk_toolbox_tools
    from adk_toolbox.models import Session, Requirement, TestCase, SessionContext
except ImportError:
    print("❌ ADK Toolbox not available. Please install dependencies.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ToolboxIntegrationTest:
    """Test suite for Toolbox integration."""

    def __init__(self, server_url: str = "http://localhost:5000"):
        """Initialize test suite."""
        self.server_url = server_url
        self.test_session_id = None
        self.test_results = []

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite."""
        print("🧪 Google GenAI MCP Toolbox - ADK Integration Tests")
        print("=" * 60)

        tests = [
            ("Connection Test", self.test_connection),
            ("Session Management", self.test_session_management),
            ("Requirements Storage", self.test_requirements_storage),
            ("Test Case Storage", self.test_test_case_storage),
            ("Test Suite Storage", self.test_test_suite_storage),
            ("Session Context Retrieval", self.test_session_context),
            ("Search and Filtering", self.test_search_filtering),
            ("ADK Tools Integration", self.test_adk_tools),
            ("Workflow Integration", self.test_complete_workflow)
        ]

        results = {
            "total_tests": len(tests),
            "passed": 0,
            "failed": 0,
            "test_details": []
        }

        for test_name, test_func in tests:
            print(f"\n{'=' * 20} {test_name} {'=' * 20}")
            try:
                result = await test_func()
                if result["success"]:
                    print(f"✅ {test_name} PASSED")
                    results["passed"] += 1
                else:
                    print(f"❌ {test_name} FAILED: {result.get('error', 'Unknown error')}")
                    results["failed"] += 1

                results["test_details"].append({
                    "name": test_name,
                    "success": result["success"],
                    "details": result
                })

            except Exception as e:
                print(f"❌ {test_name} FAILED with exception: {e}")
                results["failed"] += 1
                results["test_details"].append({
                    "name": test_name,
                    "success": False,
                    "error": str(e)
                })

        # Summary
        print(f"\n{'=' * 60}")
        print(f"📊 Test Results Summary")
        print(f"{'=' * 60}")
        print(f"Total tests: {results['total_tests']}")
        print(f"✅ Passed: {results['passed']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"Success rate: {(results['passed'] / results['total_tests'] * 100):.1f}%")

        return results

    async def test_connection(self) -> Dict[str, Any]:
        """Test basic connection to Toolbox server."""
        try:
            async with ToolboxClient(self.server_url) as client:
                health = await client.health_check()
                return {
                    "success": health,
                    "server_url": self.server_url,
                    "message": "Connection successful" if health else "Health check failed"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "server_url": self.server_url
            }

    async def test_session_management(self) -> Dict[str, Any]:
        """Test session creation, retrieval, and updates."""
        try:
            async with ToolboxClient(self.server_url) as client:
                # Create session
                session = await client.create_session(
                    user_id="test_user_integration",
                    user_prompt="Test session management functionality",
                    project_name="Integration Test Project"
                )

                self.test_session_id = str(session.session_id)

                # Retrieve session
                retrieved_session = await client.get_session(self.test_session_id)

                # Update session status
                updated_session = await client.update_session_status(self.test_session_id, "completed")

                return {
                    "success": True,
                    "session_id": self.test_session_id,
                    "created": session.to_dict(),
                    "retrieved": retrieved_session.to_dict() if retrieved_session else None,
                    "updated": updated_session.to_dict(),
                    "status_updated": updated_session.status == "completed"
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_requirements_storage(self) -> Dict[str, Any]:
        """Test requirements storage and retrieval."""
        if not self.test_session_id:
            return {"success": False, "error": "No test session available"}

        try:
            async with ToolboxClient(self.server_url) as client:
                requirements_data = [
                    ("User authentication must support OAuth2", "security", "high"),
                    ("System must handle 1000 concurrent users", "performance", "medium"),
                    ("Data must be encrypted at rest", "security", "critical"),
                    ("UI must be responsive on mobile devices", "functional", "medium")
                ]

                stored_requirements = []
                for content, req_type, priority in requirements_data:
                    req = await client.store_requirement(
                        session_id=self.test_session_id,
                        content=content,
                        requirement_type=req_type,
                        priority=priority
                    )
                    stored_requirements.append(req)

                # Retrieve all requirements
                all_requirements = await client.get_requirements(self.test_session_id)

                # Retrieve security requirements only
                security_requirements = await client.get_requirements_by_type(
                    self.test_session_id, "security"
                )

                return {
                    "success": True,
                    "stored_count": len(stored_requirements),
                    "retrieved_count": len(all_requirements),
                    "security_count": len(security_requirements),
                    "requirements": [req.to_dict() for req in all_requirements]
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_test_case_storage(self) -> Dict[str, Any]:
        """Test individual test case storage."""
        if not self.test_session_id:
            return {"success": False, "error": "No test session available"}

        try:
            async with ToolboxClient(self.server_url) as client:
                test_content = {
                    "preconditions": [
                        "User is not authenticated",
                        "OAuth2 provider is available",
                        "Application is configured"
                    ],
                    "test_steps": [
                        "Navigate to login page",
                        "Click 'Login with OAuth2'",
                        "Complete OAuth2 flow",
                        "Verify successful authentication"
                    ],
                    "test_data": {
                        "provider": "google",
                        "client_id": "test_client_123",
                        "redirect_uri": "https://app.example.com/callback"
                    },
                    "expected_result": "User is successfully authenticated and redirected to main application",
                    "requirement_traceability": "REQ_AUTH_001 - OAuth2 Authentication"
                }

                test_case = await client.store_test_case(
                    session_id=self.test_session_id,
                    test_id="TC_AUTH_001",
                    summary="Test OAuth2 authentication flow",
                    priority="CRITICAL",
                    test_type="security",
                    test_content=test_content
                )

                # Retrieve test cases
                test_cases = await client.get_test_cases(self.test_session_id)

                return {
                    "success": True,
                    "test_case_id": str(test_case.test_case_id),
                    "stored_test_case": test_case.to_dict(),
                    "retrieved_count": len(test_cases),
                    "test_cases": [tc.to_dict() for tc in test_cases]
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_test_suite_storage(self) -> Dict[str, Any]:
        """Test storing multiple test cases from a test suite."""
        if not self.test_session_id:
            return {"success": False, "error": "No test session available"}

        try:
            async with ToolboxClient(self.server_url) as client:
                test_suite = {
                    "test_suite": {
                        "name": "Authentication Test Suite",
                        "description": "Comprehensive test cases for authentication system",
                        "total_tests": 3,
                        "generated_date": datetime.now().date().isoformat(),
                        "test_cases": [
                            {
                                "test_id": "TC_AUTH_002",
                                "priority": "HIGH",
                                "type": "Security",
                                "summary": "Test multi-factor authentication",
                                "preconditions": ["User has MFA enabled", "TOTP app configured"],
                                "test_steps": ["Login with username/password", "Enter TOTP code", "Verify access"],
                                "test_data": {"mfa_method": "totp", "backup_codes": True},
                                "expected_result": "User successfully authenticated with MFA",
                                "requirement_traceability": "REQ_MFA_001 - Multi-Factor Authentication"
                            },
                            {
                                "test_id": "TC_AUTH_003",
                                "priority": "MEDIUM",
                                "type": "Functional",
                                "summary": "Test password reset functionality",
                                "preconditions": ["User account exists", "Email service available"],
                                "test_steps": ["Click forgot password", "Enter email", "Follow reset link", "Set new password"],
                                "test_data": {"email": "test@example.com", "new_password": "NewSecure123!"},
                                "expected_result": "Password is successfully reset and user can login",
                                "requirement_traceability": "REQ_PWD_001 - Password Reset"
                            },
                            {
                                "test_id": "TC_AUTH_004",
                                "priority": "LOW",
                                "type": "Edge Case",
                                "summary": "Test login with invalid credentials",
                                "preconditions": ["Application is running", "User account does not exist"],
                                "test_steps": ["Navigate to login", "Enter invalid credentials", "Click login"],
                                "test_data": {"username": "invalid@example.com", "password": "wrongpassword"},
                                "expected_result": "Appropriate error message displayed, no access granted",
                                "requirement_traceability": "REQ_SEC_002 - Invalid Login Handling"
                            }
                        ]
                    }
                }

                test_cases = await client.store_test_suite(self.test_session_id, test_suite)

                return {
                    "success": True,
                    "test_cases_stored": len(test_cases),
                    "test_case_ids": [str(tc.test_case_id) for tc in test_cases],
                    "test_suite": test_suite
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_session_context(self) -> Dict[str, Any]:
        """Test retrieving complete session context."""
        if not self.test_session_id:
            return {"success": False, "error": "No test session available"}

        try:
            async with ToolboxClient(self.server_url) as client:
                context = await client.get_session_context(self.test_session_id)

                if context:
                    summary = await client.get_session_summary(self.test_session_id)

                    return {
                        "success": True,
                        "context": context.to_dict(),
                        "summary": summary.to_dict() if summary else None,
                        "requirements_count": len(context.requirements),
                        "test_cases_count": len(context.test_cases),
                        "critical_tests": len(context.get_critical_test_cases()),
                        "test_suite_json": context.to_test_suite_json()
                    }
                else:
                    return {"success": False, "error": "Context not found"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_search_filtering(self) -> Dict[str, Any]:
        """Test search and filtering functionality."""
        if not self.test_session_id:
            return {"success": False, "error": "No test session available"}

        try:
            async with ToolboxClient(self.server_url) as client:
                # Search test cases
                auth_tests = await client.search_test_cases(self.test_session_id, "authentication")

                # Get critical test cases
                critical_tests = await client.get_test_cases_by_priority(self.test_session_id, "CRITICAL")

                # Get security requirements
                security_reqs = await client.get_requirements_by_type(self.test_session_id, "security")

                return {
                    "success": True,
                    "auth_tests_found": len(auth_tests),
                    "critical_tests_found": len(critical_tests),
                    "security_requirements_found": len(security_reqs),
                    "search_results": {
                        "auth_tests": [tc.to_dict() for tc in auth_tests],
                        "critical_tests": [tc.to_dict() for tc in critical_tests],
                        "security_requirements": [req.to_dict() for req in security_reqs]
                    }
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_adk_tools(self) -> Dict[str, Any]:
        """Test ADK function tools integration."""
        try:
            # Create ADK tools
            tools = create_adk_toolbox_tools(self.server_url)

            # Test a few tools directly
            from adk_toolbox.tools import ADKToolboxTools
            adk_tools = ADKToolboxTools(self.server_url)

            # Test session creation via ADK tools
            session_result = await adk_tools.create_session(
                user_id="adk_test_user",
                user_prompt="Test ADK tools integration",
                project_name="ADK Integration Test"
            )

            if session_result["success"]:
                session_id = session_result["session_id"]

                # Test requirement storage via ADK tools
                req_result = await adk_tools.store_requirement(
                    session_id=session_id,
                    content="ADK tools must work seamlessly with Toolbox",
                    requirement_type="integration",
                    priority="high"
                )

                # Test context retrieval via ADK tools
                context_result = await adk_tools.get_session_context(session_id)

                return {
                    "success": True,
                    "tools_count": len(tools),
                    "session_creation": session_result,
                    "requirement_storage": req_result,
                    "context_retrieval": context_result
                }
            else:
                return {"success": False, "error": "ADK session creation failed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_complete_workflow(self) -> Dict[str, Any]:
        """Test a complete end-to-end workflow."""
        try:
            # Simulate a complete agent workflow
            workflow_steps = []

            # Step 1: Create session
            from adk_toolbox.tools import ADKToolboxTools
            adk_tools = ADKToolboxTools(self.server_url)

            session_result = await adk_tools.create_session(
                user_id="workflow_test_user",
                user_prompt="Design a complete e-commerce checkout system",
                project_name="E-commerce Checkout"
            )
            workflow_steps.append(("Create Session", session_result["success"]))

            if not session_result["success"]:
                return {"success": False, "error": "Workflow failed at session creation"}

            session_id = session_result["session_id"]

            # Step 2: Store multiple requirements
            requirements = [
                ("Payment processing must support multiple payment methods", "functional", "high"),
                ("Checkout must complete within 3 seconds", "performance", "medium"),
                ("All payment data must be encrypted", "security", "critical"),
                ("System must handle abandoned cart recovery", "business", "medium")
            ]

            for content, req_type, priority in requirements:
                req_result = await adk_tools.store_requirement(
                    session_id=session_id,
                    content=content,
                    requirement_type=req_type,
                    priority=priority
                )
                workflow_steps.append(("Store Requirement", req_result["success"]))

            # Step 3: Store test suite
            test_suite_json = json.dumps({
                "test_suite": {
                    "name": "E-commerce Checkout Test Suite",
                    "description": "Complete test coverage for checkout system",
                    "total_tests": 2,
                    "generated_date": datetime.now().date().isoformat(),
                    "test_cases": [
                        {
                            "test_id": "TC_CHK_001",
                            "priority": "CRITICAL",
                            "type": "Functional",
                            "summary": "Test successful payment processing",
                            "preconditions": ["User has items in cart", "Payment method configured"],
                            "test_steps": ["Proceed to checkout", "Enter payment details", "Confirm payment"],
                            "test_data": {"amount": 99.99, "currency": "USD", "payment_method": "card"},
                            "expected_result": "Payment processed successfully, order confirmed",
                            "requirement_traceability": "REQ_PAY_001 - Payment Processing"
                        },
                        {
                            "test_id": "TC_CHK_002",
                            "priority": "HIGH",
                            "type": "Security",
                            "summary": "Test payment data encryption",
                            "preconditions": ["SSL certificate valid", "Encryption enabled"],
                            "test_steps": ["Enter payment details", "Submit form", "Verify data encryption"],
                            "test_data": {"card_number": "4111111111111111", "encryption": "AES-256"},
                            "expected_result": "Payment data is encrypted before transmission",
                            "requirement_traceability": "REQ_SEC_001 - Payment Data Encryption"
                        }
                    ]
                }
            })

            suite_result = await adk_tools.store_test_suite(session_id, test_suite_json)
            workflow_steps.append(("Store Test Suite", suite_result["success"]))

            # Step 4: Get complete context
            context_result = await adk_tools.get_session_context(session_id)
            workflow_steps.append(("Get Context", context_result["success"]))

            # Step 5: Export test suite
            export_result = await adk_tools.get_test_suite(session_id)
            workflow_steps.append(("Export Test Suite", export_result["success"]))

            # Step 6: Update session status
            status_result = await adk_tools.update_session_status(session_id, "completed")
            workflow_steps.append(("Update Status", status_result["success"]))

            success_count = sum(1 for _, success in workflow_steps if success)
            total_steps = len(workflow_steps)

            return {
                "success": success_count == total_steps,
                "workflow_steps": workflow_steps,
                "success_rate": f"{success_count}/{total_steps}",
                "session_id": session_id,
                "final_context": context_result if context_result["success"] else None
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


async def main():
    """Run the integration tests."""
    # Check if Toolbox server URL is provided
    server_url = os.getenv("TOOLBOX_SERVER_URL", "http://localhost:5000")

    print(f"🔧 Testing against Toolbox server: {server_url}")
    print("   Make sure the Toolbox server is running with: toolbox --tools-file tools.yaml")
    print()

    # Run tests
    test_suite = ToolboxIntegrationTest(server_url)
    results = await test_suite.run_all_tests()

    # Save results
    results_file = f"integration_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Test results saved to: {results_file}")

    # Exit with appropriate code
    exit_code = 0 if results["failed"] == 0 else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())