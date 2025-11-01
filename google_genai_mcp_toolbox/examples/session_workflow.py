"""
Session Workflow Example for Google GenAI MCP Toolbox.

This example demonstrates a complete session workflow using the Toolbox
for persistent agent operations.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from adk_toolbox import ToolboxClient, create_toolbox_client
    from adk_toolbox.models import SessionContext
except ImportError:
    print("❌ ADK Toolbox not available. Please install dependencies.")
    sys.exit(1)


async def agent_requirements_analysis_workflow():
    """
    Example workflow: Requirements analysis for a software project.

    This simulates how an agent would use the Toolbox for persistent
    requirements analysis and test case generation.
    """
    print("📋 Agent Requirements Analysis Workflow")
    print("=" * 50)

    server_url = "http://localhost:5000"

    try:
        async with create_toolbox_client(server_url) as client:
            # Step 1: Create session for requirements analysis
            print("\n🎯 Step 1: Creating analysis session...")
            session = await client.create_session(
                user_id="requirements_analyst",
                user_prompt="Analyze requirements for a modern e-learning platform with video streaming, interactive quizzes, and progress tracking",
                project_name="E-Learning Platform Requirements"
            )
            session_id = str(session.session_id)
            print(f"✅ Session created: {session_id}")

            # Step 2: Store functional requirements
            print("\n⚙️ Step 2: Storing functional requirements...")
            functional_requirements = [
                "System must support video streaming with adaptive bitrate",
                "Users must be able to create and take interactive quizzes",
                "Platform must track and display learning progress",
                "System must support multiple user roles (student, instructor, admin)",
                "Content must be searchable and filterable",
                "Users must be able to download course materials for offline access"
            ]

            stored_functional = []
            for i, req_content in enumerate(functional_requirements, 1):
                req = await client.store_requirement(
                    session_id=session_id,
                    content=req_content,
                    requirement_type="functional",
                    priority="high" if i <= 3 else "medium"
                )
                stored_functional.append(req)
                print(f"   ✓ FR{i:02d}: {req_content[:60]}...")

            # Step 3: Store non-functional requirements
            print("\n🔧 Step 3: Storing non-functional requirements...")
            non_functional_requirements = [
                ("System must handle 10,000 concurrent users", "performance", "critical"),
                ("Video streaming must start within 2 seconds", "performance", "high"),
                ("System uptime must be 99.9%", "reliability", "critical"),
                ("All user data must be encrypted at rest and in transit", "security", "critical"),
                ("Platform must be accessible (WCAG 2.1 AA compliant)", "usability", "high"),
                ("System must be mobile-responsive", "usability", "medium")
            ]

            stored_non_functional = []
            for req_content, req_type, priority in non_functional_requirements:
                req = await client.store_requirement(
                    session_id=session_id,
                    content=req_content,
                    requirement_type=req_type,
                    priority=priority
                )
                stored_non_functional.append(req)
                print(f"   ✓ {req_type.upper()}: {req_content[:60]}...")

            # Step 4: Generate and store test cases
            print("\n🧪 Step 4: Generating test cases...")

            # Video streaming test cases
            video_test_cases = [
                {
                    "test_id": "TC_VID_001",
                    "priority": "CRITICAL",
                    "type": "Functional",
                    "summary": "Test adaptive bitrate video streaming",
                    "preconditions": [
                        "Video content is uploaded and processed",
                        "User has stable internet connection",
                        "Multiple bitrate versions are available"
                    ],
                    "test_steps": [
                        "Navigate to course video",
                        "Start video playback",
                        "Monitor network conditions",
                        "Verify bitrate adaptation",
                        "Check playback quality"
                    ],
                    "test_data": {
                        "video_formats": ["360p", "720p", "1080p"],
                        "network_speeds": ["1Mbps", "5Mbps", "10Mbps"],
                        "expected_adaptation_time": "3 seconds"
                    },
                    "expected_result": "Video adapts to network conditions automatically within 3 seconds",
                    "requirement_traceability": "REQ_VID_001 - Adaptive bitrate streaming"
                },
                {
                    "test_id": "TC_VID_002",
                    "priority": "HIGH",
                    "type": "Performance",
                    "summary": "Test video startup time performance",
                    "preconditions": [
                        "Video is properly encoded",
                        "CDN is configured",
                        "User has minimum required bandwidth"
                    ],
                    "test_steps": [
                        "Click play on video",
                        "Measure time to first frame",
                        "Verify initial buffering",
                        "Check for smooth playback start"
                    ],
                    "test_data": {
                        "max_startup_time": "2 seconds",
                        "min_bandwidth": "1 Mbps",
                        "test_videos": ["short_course.mp4", "long_lecture.mp4"]
                    },
                    "expected_result": "Video starts playing within 2 seconds of clicking play",
                    "requirement_traceability": "REQ_PERF_002 - Video startup performance"
                }
            ]

            # Quiz system test cases
            quiz_test_cases = [
                {
                    "test_id": "TC_QUZ_001",
                    "priority": "HIGH",
                    "type": "Functional",
                    "summary": "Test interactive quiz creation and taking",
                    "preconditions": [
                        "Instructor is logged in",
                        "Course exists",
                        "Quiz creation tools are available"
                    ],
                    "test_steps": [
                        "Create new quiz with multiple question types",
                        "Set quiz parameters (time limit, attempts)",
                        "Publish quiz to course",
                        "Take quiz as student",
                        "Verify scoring and feedback"
                    ],
                    "test_data": {
                        "question_types": ["multiple_choice", "true_false", "short_answer"],
                        "time_limit": "30 minutes",
                        "max_attempts": 3
                    },
                    "expected_result": "Quiz is created successfully and functions correctly for students",
                    "requirement_traceability": "REQ_QUZ_001 - Interactive quiz functionality"
                }
            ]

            # Progress tracking test cases
            progress_test_cases = [
                {
                    "test_id": "TC_PRG_001",
                    "priority": "MEDIUM",
                    "type": "Functional",
                    "summary": "Test learning progress tracking and display",
                    "preconditions": [
                        "Student is enrolled in course",
                        "Course has multiple learning activities",
                        "Progress tracking is enabled"
                    ],
                    "test_steps": [
                        "Complete various learning activities",
                        "Check progress dashboard",
                        "Verify completion percentages",
                        "Test progress synchronization"
                    ],
                    "test_data": {
                        "activities": ["video_watch", "quiz_complete", "assignment_submit"],
                        "expected_weights": {"videos": 40, "quizzes": 35, "assignments": 25}
                    },
                    "expected_result": "Progress is accurately tracked and displayed in real-time",
                    "requirement_traceability": "REQ_PRG_001 - Learning progress tracking"
                }
            ]

            # Store all test cases
            all_test_cases = video_test_cases + quiz_test_cases + progress_test_cases
            stored_test_cases = []

            for tc_data in all_test_cases:
                test_case = await client.store_test_case_from_json(session_id, tc_data)
                stored_test_cases.append(test_case)
                print(f"   ✓ {tc_data['test_id']}: {tc_data['summary'][:50]}...")

            # Step 5: Retrieve and analyze session context
            print("\n📊 Step 5: Analyzing complete session context...")
            context = await client.get_session_context(session_id)

            if context:
                print(f"✅ Session analysis complete:")
                print(f"   📋 Requirements: {len(context.requirements)} total")
                print(f"      - Functional: {len(context.get_requirements_by_type('functional'))}")
                print(f"      - Performance: {len(context.get_requirements_by_type('performance'))}")
                print(f"      - Security: {len(context.get_requirements_by_type('security'))}")
                print(f"      - Critical priority: {len(context.get_requirements_by_priority('critical'))}")

                print(f"   🧪 Test Cases: {len(context.test_cases)} total")
                print(f"      - Critical: {len(context.get_test_cases_by_priority('CRITICAL'))}")
                print(f"      - High: {len(context.get_test_cases_by_priority('HIGH'))}")
                print(f"      - Medium: {len(context.get_test_cases_by_priority('MEDIUM'))}")

                # Generate test suite export
                test_suite = context.to_test_suite_json()
                suite_filename = f"elearning_test_suite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

                with open(suite_filename, 'w') as f:
                    json.dump(test_suite, f, indent=2)

                print(f"   💾 Test suite exported: {suite_filename}")

                # Update session status
                await client.update_session_status(session_id, "completed")
                print(f"   🎯 Session marked as completed")

                return {
                    "success": True,
                    "session_id": session_id,
                    "requirements_count": len(context.requirements),
                    "test_cases_count": len(context.test_cases),
                    "exported_file": suite_filename,
                    "context": context.to_dict()
                }
            else:
                return {"success": False, "error": "Could not retrieve session context"}

    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        return {"success": False, "error": str(e)}


async def multi_session_management_example():
    """
    Example of managing multiple sessions for different projects.
    """
    print("\n" + "=" * 60)
    print("👥 Multi-Session Management Example")
    print("=" * 60)

    server_url = "http://localhost:5000"
    user_id = "project_manager"

    try:
        async with create_toolbox_client(server_url) as client:
            # Create multiple project sessions
            projects = [
                ("Mobile Banking App Security Analysis", "security"),
                ("IoT Device Management Platform", "iot"),
                ("Healthcare Data Analytics Dashboard", "healthcare")
            ]

            created_sessions = []

            for project_name, domain in projects:
                session = await client.create_session(
                    user_id=user_id,
                    user_prompt=f"Analyze requirements and generate test cases for {project_name.lower()}",
                    project_name=project_name
                )
                created_sessions.append((session, domain))
                print(f"✅ Created session for {project_name}")

                # Add a few requirements to each
                if domain == "security":
                    requirements = [
                        "All financial transactions must use end-to-end encryption",
                        "Biometric authentication must be supported"
                    ]
                elif domain == "iot":
                    requirements = [
                        "System must support device provisioning at scale",
                        "Real-time device monitoring must be available"
                    ]
                else:  # healthcare
                    requirements = [
                        "System must be HIPAA compliant",
                        "Data visualization must support real-time updates"
                    ]

                for req_content in requirements:
                    await client.store_requirement(
                        session_id=str(session.session_id),
                        content=req_content,
                        requirement_type=domain,
                        priority="high"
                    )

            # Get user session summary
            user_sessions = await client.get_user_sessions(user_id)
            print(f"\n📊 User {user_id} has {len(user_sessions)} total sessions:")

            for session_summary in user_sessions:
                print(f"   🎯 {session_summary.project_name or 'Unnamed Project'}")
                print(f"      Session ID: {str(session_summary.session_id)[:8]}...")
                print(f"      Requirements: {session_summary.requirement_count}")
                print(f"      Test Cases: {session_summary.test_case_count}")
                print(f"      Status: {session_summary.status}")
                print()

            return {
                "success": True,
                "sessions_created": len(created_sessions),
                "total_user_sessions": len(user_sessions)
            }

    except Exception as e:
        print(f"❌ Multi-session example failed: {e}")
        return {"success": False, "error": str(e)}


async def main():
    """Run the session workflow examples."""
    print("🚀 Google GenAI MCP Toolbox - Session Workflow Examples")
    print("=" * 60)
    print("Make sure the Toolbox server is running:")
    print("  toolbox --tools-file tools.yaml")
    print()

    # Run requirements analysis workflow
    result1 = await agent_requirements_analysis_workflow()

    if result1["success"]:
        print(f"\n🎉 Requirements analysis workflow completed successfully!")
        print(f"   Session: {result1['session_id']}")
        print(f"   Requirements: {result1['requirements_count']}")
        print(f"   Test Cases: {result1['test_cases_count']}")

    # Run multi-session example
    result2 = await multi_session_management_example()

    if result2["success"]:
        print(f"🎉 Multi-session management example completed!")
        print(f"   Sessions created: {result2['sessions_created']}")

    print("\n" + "=" * 60)
    print("📚 Examples completed! Check the generated files for exported test suites.")
    print("💡 Use these patterns in your own ADK agents for persistent workflows.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())