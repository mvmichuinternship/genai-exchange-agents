"""
Database models for the MCP toolbox.

This module defines SQLAlchemy models for sessions, requirements, test cases,
and their relationships.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Text, Integer, Boolean, TIMESTAMP,
    ForeignKey, DECIMAL, JSON, UUID, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel, Field
import uuid

Base = declarative_base()


class Session(Base):
    """Core session management table."""
    __tablename__ = 'sessions'

    session_id = Column(String(255), primary_key=True)
    user_id = Column(String(255), nullable=False)
    project_name = Column(String(255))
    user_prompt = Column(Text)
    status = Column(String(50), default='created')
    rag_context_loaded = Column(Integer, default=0)
    rag_enabled = Column(Boolean, default=True)
    agent_used = Column(String(100), default='sequential_workflow')
    workflow_type = Column(String(50), default='full')
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    requirements = relationship("Requirement", back_populates="session", cascade="all, delete-orphan")
    test_cases = relationship("TestCase", back_populates="session", cascade="all, delete-orphan")


class Requirement(Base):
    """All types of requirements table."""
    __tablename__ = 'requirements'

    id = Column(String(255), primary_key=True)
    session_id = Column(String(255), ForeignKey('sessions.session_id', ondelete='CASCADE'))
    original_content = Column(Text, nullable=False)
    edited_content = Column(Text)
    requirement_type = Column(String(50), default='functional')
    priority = Column(String(10), default='medium')
    status = Column(String(20), default='active')
    version = Column(Integer, default=1)
    source = Column(String(20), default='agent_generated')
    tags = Column(JSONB, default=list)
    metadata = Column(JSONB, default=dict)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    session = relationship("Session", back_populates="requirements")
    test_case_requirements = relationship("TestCaseRequirement", back_populates="requirement")


class TestCase(Base):
    """Generated and manual test cases table."""
    __tablename__ = 'test_cases'

    id = Column(String(255), primary_key=True)
    session_id = Column(String(255), ForeignKey('sessions.session_id', ondelete='CASCADE'))
    test_name = Column(String(255), nullable=False)
    test_description = Column(Text)
    test_steps = Column(JSONB)
    expected_results = Column(Text)
    test_type = Column(String(50), default='functional')
    priority = Column(String(10), default='medium')
    status = Column(String(20), default='active')
    test_data = Column(JSONB, default=dict)
    preconditions = Column(Text)
    postconditions = Column(Text)
    estimated_duration = Column(Integer, default=30)  # minutes
    automation_feasible = Column(Boolean, default=True)
    tags = Column(JSONB, default=list)

    # New fields for structured test case format
    test_suite_name = Column(String(255))
    test_suite_description = Column(Text)
    test_id = Column(String(50))  # TC_TYPE_NNN format
    summary = Column(Text)
    requirement_traceability = Column(String(255))

    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    session = relationship("Session", back_populates="test_cases")
    test_case_requirements = relationship("TestCaseRequirement", back_populates="test_case")


class TestCaseRequirement(Base):
    """Test case to requirements mapping - Many-to-many relationship."""
    __tablename__ = 'test_case_requirements'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_case_id = Column(String(255), ForeignKey('test_cases.id', ondelete='CASCADE'))
    requirement_id = Column(String(255), ForeignKey('requirements.id', ondelete='CASCADE'))
    coverage_type = Column(String(50), default='direct')
    confidence_score = Column(DECIMAL(3, 2), default=1.0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    test_case = relationship("TestCase", back_populates="test_case_requirements")
    requirement = relationship("Requirement", back_populates="test_case_requirements")


class Project(Base):
    """Projects table for organizing sessions by project."""
    __tablename__ = 'projects'

    project_id = Column(String(255), primary_key=True)
    project_name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_user_id = Column(String(255))
    status = Column(String(20), default='active')
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    """Users table for basic user management."""
    __tablename__ = 'users'

    user_id = Column(String(255), primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default='tester')
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    last_login = Column(TIMESTAMP)


# Create indexes for better performance
Index('idx_sessions_user_id', Session.user_id)
Index('idx_sessions_status', Session.status)
Index('idx_sessions_created_at', Session.created_at)

Index('idx_requirements_session', Requirement.session_id)
Index('idx_requirements_type', Requirement.requirement_type)
Index('idx_requirements_status', Requirement.status)

Index('idx_test_cases_session', TestCase.session_id)
Index('idx_test_cases_type', TestCase.test_type)
Index('idx_test_cases_status', TestCase.status)

Index('idx_tcr_test_case', TestCaseRequirement.test_case_id)
Index('idx_tcr_requirement', TestCaseRequirement.requirement_id)


# Pydantic models for API validation
class SessionCreate(BaseModel):
    session_id: str
    user_id: str
    project_name: Optional[str] = None
    user_prompt: Optional[str] = None
    status: str = 'created'
    rag_enabled: bool = True
    agent_used: str = 'sequential_workflow'
    workflow_type: str = 'full'


class SessionUpdate(BaseModel):
    user_prompt: Optional[str] = None
    status: Optional[str] = None
    rag_context_loaded: Optional[int] = None
    rag_enabled: Optional[bool] = None
    agent_used: Optional[str] = None
    workflow_type: Optional[str] = None


class RequirementCreate(BaseModel):
    id: str
    session_id: str
    original_content: str
    edited_content: Optional[str] = None
    requirement_type: str = 'functional'
    priority: str = 'medium'
    status: str = 'active'
    source: str = 'agent_generated'
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RequirementUpdate(BaseModel):
    edited_content: Optional[str] = None
    requirement_type: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class TestCaseCreate(BaseModel):
    id: str
    session_id: str
    test_name: str
    test_description: Optional[str] = None
    test_steps: Optional[List[str]] = None
    expected_results: Optional[str] = None
    test_type: str = 'functional'
    priority: str = 'medium'
    status: str = 'active'
    test_data: Dict[str, Any] = Field(default_factory=dict)
    preconditions: Optional[str] = None
    postconditions: Optional[str] = None
    estimated_duration: int = 30
    automation_feasible: bool = True
    tags: List[str] = Field(default_factory=list)

    # Structured test case fields
    test_suite_name: Optional[str] = None
    test_suite_description: Optional[str] = None
    test_id: Optional[str] = None
    summary: Optional[str] = None
    requirement_traceability: Optional[str] = None


class TestCaseUpdate(BaseModel):
    test_name: Optional[str] = None
    test_description: Optional[str] = None
    test_steps: Optional[List[str]] = None
    expected_results: Optional[str] = None
    test_type: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    test_data: Optional[Dict[str, Any]] = None
    preconditions: Optional[str] = None
    postconditions: Optional[str] = None
    estimated_duration: Optional[int] = None
    automation_feasible: Optional[bool] = None
    tags: Optional[List[str]] = None


class TestSuite(BaseModel):
    """Pydantic model for the structured test suite format."""
    name: str
    description: str
    total_tests: int
    generated_date: str
    test_cases: List[Dict[str, Any]]


class StructuredTestCase(BaseModel):
    """Pydantic model for individual test case in the structured format."""
    test_id: str
    priority: str  # CRITICAL|HIGH|MEDIUM|LOW
    type: str  # Functional|Security|Edge Case|Negative
    summary: str
    preconditions: List[str]
    test_steps: List[str]
    test_data: Dict[str, Any]
    expected_result: str
    requirement_traceability: str