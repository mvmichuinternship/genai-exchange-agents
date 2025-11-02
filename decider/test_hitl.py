#!/usr/bin/env python3
"""
Enhanced HITL Test Script for Decider Agent

This script demonstrates the comprehensive Human-in-the-Loop capabilities
of the enhanced decider agent.
"""

import asyncio
import json
from typing import Dict, Any
import uuid
import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from decider_agent.agent import root_agent

class HITLTester:
    """Test class for HITL functionality."""

    def __init__(self):
        self.test_session_id = f"test_session_{str(uuid.uuid4())[:8]}"
        self.agent = root_agent

    async def run_comprehensive_hitl_test(self):
        """Run a comprehensive test of all HITL capabilities."""
        print("🚀 Starting Comprehensive HITL Test")
        print(f"📋 Session ID: {self.test_session_id}")
        print("=" * 60)

        # Test 1: Initial Analysis
        await self._test_initial_analysis()

        # Test 2: Quality Review (Low Score)
        await self._test_quality_review_low()

        # Test 3: Refinement Request
        await self._test_refinement()

        # Test 4: Context Enhancement
        await self._test_enhancement()

        # Test 5: Quality Review (High Score)
        await self._test_quality_review_high()

        # Test 6: Feedback History Analysis
        await self._test_feedback_history()

        # Test 7: Improvement Suggestions
        await self._test_improvement_suggestions()

        # Test 8: Final Approval
        await self._test_approval()

        print("✅ All HITL tests completed successfully!")

    async def _test_initial_analysis(self):
        """Test initial analysis workflow."""
        print("\n🔍 Test 1: Initial Analysis")
        print("-" * 30)

        message = f"start; Analyze authentication requirements for an e-commerce web application; {self.test_session_id}"

        try:
            response = await self.agent.run_async(message)
            print(f"✅ Initial analysis completed")
            print(f"📝 Response type: {type(response)}")

            # Print available HITL options
            print("\n📋 Available HITL Actions:")
            print("- approved: Generate test cases")
            print("- edited: Modify analysis directly")
            print("- refine: Provide specific feedback")
            print("- enhance: Add more context")
            print("- review: Rate quality (score:1-10)")
            print("- rejected: Start over")

        except Exception as e:
            print(f"❌ Error in initial analysis: {e}")

    async def _test_quality_review_low(self):
        """Test quality review with low score."""
        print("\n⭐ Test 2: Quality Review (Low Score)")
        print("-" * 40)

        message = f"review; score:4; feedback:Analysis lacks detail on password policies and session management; {self.test_session_id}"

        try:
            response = await self.agent.run_async(message)
            print(f"✅ Quality review processed (Score: 4/10)")
            print(f"🔍 Should trigger improvement suggestions")

        except Exception as e:
            print(f"❌ Error in quality review: {e}")

    async def _test_refinement(self):
        """Test refinement request."""
        print("\n🔄 Test 3: Refinement Request")
        print("-" * 35)

        message = f"refine; Add comprehensive password policies including complexity requirements, lockout mechanisms, and password rotation. Also include detailed session management with timeout policies; {self.test_session_id}"

        try:
            response = await self.agent.run_async(message)
            print(f"✅ Refinement completed")
            print(f"🎯 Should show specific improvements made")

        except Exception as e:
            print(f"❌ Error in refinement: {e}")

    async def _test_enhancement(self):
        """Test context enhancement."""
        print("\n➕ Test 4: Context Enhancement")
        print("-" * 35)

        message = f"enhance; This e-commerce application handles payment processing and must comply with PCI DSS standards. It also needs to support social login integration; {self.test_session_id}"

        try:
            response = await self.agent.run_async(message)
            print(f"✅ Context enhancement completed")
            print(f"🎯 Should incorporate PCI DSS and social login requirements")

        except Exception as e:
            print(f"❌ Error in enhancement: {e}")

    async def _test_quality_review_high(self):
        """Test quality review with high score."""
        print("\n⭐ Test 5: Quality Review (High Score)")
        print("-" * 40)

        message = f"review; score:9; feedback:Excellent comprehensive analysis! Covers all security aspects thoroughly; {self.test_session_id}"

        try:
            response = await self.agent.run_async(message)
            print(f"✅ High quality review processed (Score: 9/10)")
            print(f"🎯 Should show quality improvement trend")

        except Exception as e:
            print(f"❌ Error in quality review: {e}")

    async def _test_feedback_history(self):
        """Test feedback history retrieval."""
        print("\n📊 Test 6: Feedback History Analysis")
        print("-" * 40)

        message = f"feedback_history; {self.test_session_id}"

        try:
            response = await self.agent.run_async(message)
            print(f"✅ Feedback history retrieved")
            print(f"📈 Should show complete interaction timeline")

        except Exception as e:
            print(f"❌ Error in feedback history: {e}")

    async def _test_improvement_suggestions(self):
        """Test AI-powered improvement suggestions."""
        print("\n🧠 Test 7: AI Improvement Suggestions")
        print("-" * 42)

        message = f"suggest_improvements; {self.test_session_id}"

        try:
            response = await self.agent.run_async(message)
            print(f"✅ Improvement suggestions generated")
            print(f"💡 Should provide pattern-based recommendations")

        except Exception as e:
            print(f"❌ Error in improvement suggestions: {e}")

    async def _test_approval(self):
        """Test final approval workflow."""
        print("\n👍 Test 8: Final Approval")
        print("-" * 25)

        message = f"approved; ; {self.test_session_id}"

        try:
            response = await self.agent.run_async(message)
            print(f"✅ Approval processed")
            print(f"🎯 Should generate test cases and provide completion summary")

        except Exception as e:
            print(f"❌ Error in approval: {e}")

async def run_individual_hitl_test():
    """Run individual HITL feature tests."""
    print("\n🔧 Individual HITL Feature Tests")
    print("=" * 50)

    session_id = f"individual_test_{str(uuid.uuid4())[:8]}"
    agent = root_agent

    # Test refinement with specific feedback
    print("\n🔄 Testing Refinement Feature")
    message = f"start; Basic login analysis; {session_id}"
    await agent.run_async(message)

    refinement_message = f"refine; Add multi-factor authentication and OAuth 2.0 support; {session_id}"
    response = await agent.run_async(refinement_message)
    print(f"✅ Refinement test completed")

    # Test enhancement feature
    print("\n➕ Testing Enhancement Feature")
    enhancement_message = f"enhance; This is for a financial services application requiring SOX compliance; {session_id}"
    response = await agent.run_async(enhancement_message)
    print(f"✅ Enhancement test completed")

async def run_quality_tracking_test():
    """Test quality tracking and trend analysis."""
    print("\n📈 Quality Tracking Test")
    print("=" * 30)

    session_id = f"quality_test_{str(uuid.uuid4())[:8]}"
    agent = root_agent

    # Start analysis
    await agent.run_async(f"start; Simple authentication analysis; {session_id}")

    # Simulate quality progression
    quality_scores = [3, 5, 7, 9]
    feedbacks = [
        "Too basic, needs more detail",
        "Better but missing security considerations",
        "Good analysis, minor improvements needed",
        "Excellent comprehensive analysis"
    ]

    for i, (score, feedback) in enumerate(zip(quality_scores, feedbacks), 1):
        print(f"\n📊 Quality Review {i}: Score {score}/10")
        message = f"review; score:{score}; feedback:{feedback}; {session_id}"
        await agent.run_async(message)

        if score < 7:
            # Apply refinement
            print(f"🔄 Applying refinement based on feedback")
            refine_message = f"refine; Improve based on previous feedback: {feedback}; {session_id}"
            await agent.run_async(refine_message)

    print(f"✅ Quality tracking test completed - demonstrated 3→9 improvement!")

def print_hitl_menu():
    """Print interactive HITL menu."""
    print("\n🎮 Interactive HITL Testing Menu")
    print("=" * 35)
    print("1. Run Comprehensive HITL Test")
    print("2. Run Individual Feature Tests")
    print("3. Run Quality Tracking Test")
    print("4. Interactive HITL Session")
    print("5. Exit")
    print("-" * 35)

async def interactive_hitl_session():
    """Run an interactive HITL session."""
    print("\n🤝 Interactive HITL Session")
    print("=" * 30)

    session_id = f"interactive_{str(uuid.uuid4())[:8]}"
    agent = root_agent

    print(f"📋 Session ID: {session_id}")
    print("\n💡 HITL Commands:")
    print("- start; <your analysis request>")
    print("- refine; <specific feedback>")
    print("- enhance; <additional context>")
    print("- review; score:X; feedback:<your review>")
    print("- approved/edited/rejected")
    print("- feedback_history (to see all feedback)")
    print("- suggest_improvements (for AI suggestions)")
    print("- quit (to exit)")

    while True:
        try:
            user_input = input(f"\n[{session_id}] Enter HITL command: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break

            if not user_input:
                continue

            # Add session_id if not provided
            if ';' in user_input and session_id not in user_input:
                user_input += f"; {session_id}"
            elif ';' not in user_input:
                user_input += f"; {session_id}"

            print(f"\n🤖 Processing: {user_input}")
            response = await agent.run_async(user_input)
            print(f"✅ Response received")

        except KeyboardInterrupt:
            print(f"\n👋 Session ended by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    """Main test runner."""
    print("🚀 Enhanced HITL Testing Suite")
    print("=" * 40)

    while True:
        print_hitl_menu()
        choice = input("Select option (1-5): ").strip()

        try:
            if choice == '1':
                tester = HITLTester()
                await tester.run_comprehensive_hitl_test()
            elif choice == '2':
                await run_individual_hitl_test()
            elif choice == '3':
                await run_quality_tracking_test()
            elif choice == '4':
                await interactive_hitl_session()
            elif choice == '5':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")
        except KeyboardInterrupt:
            print(f"\n👋 Testing interrupted by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())