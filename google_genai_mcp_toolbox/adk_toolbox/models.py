"""
Data models for ADK Toolbox integration.

Defines data structures for sessions, requirements, test cases, and related entities.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
import json


@dataclass
class Session:
    """Represents an agent session."""
    session_id: UUID
    user_id: str
    user_prompt: str
    project_name: Optional[str] = None
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create Session from dictionary data."""
        return cls(
            session_id=UUID(data["session_id"]) if isinstance(data["session_id"], str) else data["session_id"],
            user_id=data["user_id"],
            user_prompt=data["user_prompt"],
            project_name=data.get("project_name"),
            status=data.get("status", "active"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Session to dictionary."""
        return {
            "session_id": str(self.session_id),
            "user_id": self.user_id,
            "user_prompt": self.user_prompt,
            "project_name": self.project_name,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class Requirement:
    """Represents a requirement for a session."""
    requirement_id: UUID
    session_id: UUID
    content: str
    requirement_type: str = "functional"
    priority: str = "medium"
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Requirement":
        """Create Requirement from dictionary data."""
        return cls(
            requirement_id=UUID(data["requirement_id"]) if isinstance(data["requirement_id"], str) else data["requirement_id"],
            session_id=UUID(data["session_id"]) if isinstance(data["session_id"], str) else data["session_id"],
            content=data["content"],
            requirement_type=data.get("requirement_type", "functional"),
            priority=data.get("priority", "medium"),
            created_at=data.get("created_at")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Requirement to dictionary."""
        return {
            "requirement_id": str(self.requirement_id),
            "session_id": str(self.session_id),
            "content": self.content,
            "requirement_type": self.requirement_type,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class TestCase:
    """Represents a structured test case."""
    test_case_id: UUID
    session_id: UUID
    test_id: str
    summary: str
    priority: str = "MEDIUM"
    test_type: str = "functional"
    test_content: Dict[str, Any] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.test_content is None:
            self.test_content = {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestCase":
        """Create TestCase from dictionary data."""
        test_content = data.get("test_content", {})
        if isinstance(test_content, str):
            test_content = json.loads(test_content)

        return cls(
            test_case_id=UUID(data["test_case_id"]) if isinstance(data["test_case_id"], str) else data["test_case_id"],
            session_id=UUID(data["session_id"]) if isinstance(data["session_id"], str) else data["session_id"],
            test_id=data["test_id"],
            summary=data["summary"],
            priority=data.get("priority", "MEDIUM"),
            test_type=data.get("test_type", "functional"),
            test_content=test_content,
            created_at=data.get("created_at")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert TestCase to dictionary."""
        return {
            "test_case_id": str(self.test_case_id),
            "session_id": str(self.session_id),
            "test_id": self.test_id,
            "summary": self.summary,
            "priority": self.priority,
            "test_type": self.test_type,
            "test_content": self.test_content,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def get_preconditions(self) -> List[str]:
        """Get test preconditions from content."""
        return self.test_content.get("preconditions", [])

    def get_test_steps(self) -> List[str]:
        """Get test steps from content."""
        return self.test_content.get("test_steps", [])

    def get_test_data(self) -> Dict[str, Any]:
        """Get test data from content."""
        return self.test_content.get("test_data", {})

    def get_expected_result(self) -> str:
        """Get expected result from content."""
        return self.test_content.get("expected_result", "")

    def get_requirement_traceability(self) -> str:
        """Get requirement traceability from content."""
        return self.test_content.get("requirement_traceability", "")


@dataclass
class SessionContext:
    """Complete session context with requirements and test cases."""
    session: Session
    requirements: List[Requirement]
    test_cases: List[TestCase]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionContext":
        """Create SessionContext from dictionary data."""
        # Extract session data
        session_data = {
            "session_id": data["session_id"],
            "user_id": data["user_id"],
            "user_prompt": data["user_prompt"],
            "project_name": data.get("project_name"),
            "status": data.get("status", "active"),
            "created_at": data.get("session_created_at"),
            "updated_at": data.get("session_updated_at")
        }
        session = Session.from_dict(session_data)

        # Extract requirements
        requirements = []
        for req_data in data.get("requirements", []):
            if req_data:  # Skip null/empty entries
                requirements.append(Requirement.from_dict(req_data))

        # Extract test cases
        test_cases = []
        for tc_data in data.get("test_cases", []):
            if tc_data:  # Skip null/empty entries
                test_cases.append(TestCase.from_dict(tc_data))

        return cls(
            session=session,
            requirements=requirements,
            test_cases=test_cases
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert SessionContext to dictionary."""
        return {
            "session": self.session.to_dict(),
            "requirements": [req.to_dict() for req in self.requirements],
            "test_cases": [tc.to_dict() for tc in self.test_cases]
        }

    def get_requirements_by_type(self, requirement_type: str) -> List[Requirement]:
        """Get requirements filtered by type."""
        return [req for req in self.requirements if req.requirement_type == requirement_type]

    def get_requirements_by_priority(self, priority: str) -> List[Requirement]:
        """Get requirements filtered by priority."""
        return [req for req in self.requirements if req.priority == priority]

    def get_test_cases_by_priority(self, priority: str) -> List[TestCase]:
        """Get test cases filtered by priority."""
        return [tc for tc in self.test_cases if tc.priority == priority]

    def get_test_cases_by_type(self, test_type: str) -> List[TestCase]:
        """Get test cases filtered by type."""
        return [tc for tc in self.test_cases if tc.test_type == test_type]

    def get_critical_test_cases(self) -> List[TestCase]:
        """Get all critical priority test cases."""
        return self.get_test_cases_by_priority("CRITICAL")

    def get_high_priority_requirements(self) -> List[Requirement]:
        """Get all high priority requirements."""
        return [req for req in self.requirements if req.priority in ["high", "critical"]]

    def to_test_suite_json(self) -> Dict[str, Any]:
        """Convert test cases to structured test suite JSON format."""
        return {
            "test_suite": {
                "name": f"{self.session.project_name or 'Session'} Test Suite",
                "description": f"Test cases for session: {self.session.user_prompt[:100]}...",
                "total_tests": len(self.test_cases),
                "generated_date": datetime.now().date().isoformat(),
                "session_id": str(self.session.session_id),
                "test_cases": [
                    {
                        "test_id": tc.test_id,
                        "priority": tc.priority,
                        "type": tc.test_type,
                        "summary": tc.summary,
                        "preconditions": tc.get_preconditions(),
                        "test_steps": tc.get_test_steps(),
                        "test_data": tc.get_test_data(),
                        "expected_result": tc.get_expected_result(),
                        "requirement_traceability": tc.get_requirement_traceability()
                    }
                    for tc in self.test_cases
                ]
            }
        }


@dataclass
class SessionSummary:
    """Summary statistics for a session."""
    session_id: UUID
    user_id: str
    user_prompt: str
    project_name: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    requirement_count: int
    test_case_count: int
    critical_tests: int
    high_priority_tests: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionSummary":
        """Create SessionSummary from dictionary data."""
        return cls(
            session_id=UUID(data["session_id"]) if isinstance(data["session_id"], str) else data["session_id"],
            user_id=data["user_id"],
            user_prompt=data["user_prompt"],
            project_name=data.get("project_name"),
            status=data["status"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            requirement_count=int(data.get("requirement_count", 0)),
            test_case_count=int(data.get("test_case_count", 0)),
            critical_tests=int(data.get("critical_tests", 0)),
            high_priority_tests=int(data.get("high_priority_tests", 0))
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert SessionSummary to dictionary."""
        return {
            "session_id": str(self.session_id),
            "user_id": self.user_id,
            "user_prompt": self.user_prompt,
            "project_name": self.project_name,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "requirement_count": self.requirement_count,
            "test_case_count": self.test_case_count,
            "critical_tests": self.critical_tests,
            "high_priority_tests": self.high_priority_tests
        }