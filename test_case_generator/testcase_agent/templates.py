# agents/test_case_generator/templates.py
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import json
from datetime import datetime


@dataclass
class TestData:
    """Test data structure"""
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class AuthTestData(TestData):
    """Authentication test data"""
    email: str = ""
    password: str = ""
    mfa_code: str = ""
    expected_response_time: str = "< 2 seconds"


@dataclass
class TestCase:
    """Structured test case template"""
    test_id: str
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    type: str  # Functional, Security, Edge Case, Negative
    summary: str
    preconditions: List[str]
    test_steps: List[str]
    test_data: Dict[str, Any]
    expected_result: str
    requirement_traceability: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class TestSuite:
    """Collection of test cases"""
    name: str
    description: str
    total_tests: int
    generated_date: str
    test_cases: List[TestCase]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_suite": {
                "name": self.name,
                "description": self.description,
                "total_tests": self.total_tests,
                "generated_date": self.generated_date,
                "test_cases": [tc.to_dict() for tc in self.test_cases]
            }
        }

    def to_json(self, pretty: bool = True) -> str:
        indent = 2 if pretty else None
        return json.dumps(self.to_dict(), indent=indent)

    def to_csv(self) -> str:
        """Export to CSV format"""
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'Test ID', 'Priority', 'Type', 'Summary',
            'Preconditions', 'Test Steps', 'Expected Result',
            'Requirement Traceability'
        ])

        # Rows
        for tc in self.test_cases:
            writer.writerow([
                tc.test_id,
                tc.priority,
                tc.type,
                tc.summary,
                '; '.join(tc.preconditions),
                '; '.join(tc.test_steps),
                tc.expected_result,
                tc.requirement_traceability
            ])

        return output.getvalue()

    @classmethod
    def from_json(cls, json_str: str) -> 'TestSuite':
        """Create TestSuite from JSON string"""
        data = json.loads(json_str)
        suite_data = data.get('test_suite', data)

        test_cases = [
            TestCase(**tc) for tc in suite_data.get('test_cases', [])
        ]

        return cls(
            name=suite_data.get('name', ''),
            description=suite_data.get('description', ''),
            total_tests=suite_data.get('total_tests', len(test_cases)),
            generated_date=suite_data.get('generated_date', datetime.now().isoformat()),
            test_cases=test_cases
        )


# Example usage helper
def create_test_case(
    test_id: str,
    summary: str,
    test_steps: List[str],
    expected_result: str,
    priority: str = "MEDIUM",
    test_type: str = "Functional",
    preconditions: List[str] = None,
    test_data: Dict[str, Any] = None,
    requirement_traceability: str = ""
) -> TestCase:
    """Helper function to create a test case"""
    return TestCase(
        test_id=test_id,
        priority=priority,
        type=test_type,
        summary=summary,
        preconditions=preconditions or [],
        test_steps=test_steps,
        test_data=test_data or {},
        expected_result=expected_result,
        requirement_traceability=requirement_traceability
    )
