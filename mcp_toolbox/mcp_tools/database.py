"""
Database manager for Cloud SQL integration.

This module provides database connectivity, session management, and CRUD operations
for the MCP toolbox.
"""

import os
import asyncio
from typing import Optional, List, Dict, Any, Union
from contextlib import asynccontextmanager
from datetime import datetime
import json

try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select, update, delete, and_, or_
    from google.cloud.sql.connector import Connector
    import asyncpg
except ImportError:
    # Graceful degradation when dependencies are not installed
    print("Warning: Some database dependencies are not installed. Install them with: pip install sqlalchemy asyncpg google-cloud-sql-connector")

from .models import (
    Base, Session, Requirement, TestCase, TestCaseRequirement,
    Project, User, SessionCreate, SessionUpdate, RequirementCreate,
    RequirementUpdate, TestCaseCreate, TestCaseUpdate, TestSuite
)


class DatabaseManager:
    """Manages database connections and operations for Cloud SQL."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the database manager.

        Args:
            database_url: Database connection URL. If None, uses environment variables.
        """
        self.database_url = database_url or self._build_database_url()
        self.engine = None
        self.async_session_maker = None
        self.connector = None

    def _build_database_url(self) -> str:
        """Build database URL from environment variables."""
        if os.getenv('DATABASE_URL'):
            return os.getenv('DATABASE_URL')

        # Build from individual components
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', '')
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME', 'test_case_db')

        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"

    async def initialize(self):
        """Initialize database connection and create tables."""
        if 'cloud_sql_instance' in os.environ:
            # Use Cloud SQL Connector for Google Cloud
            await self._initialize_cloud_sql()
        else:
            # Use direct connection for local development
            await self._initialize_direct()

        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _initialize_cloud_sql(self):
        """Initialize connection using Cloud SQL Connector."""
        self.connector = Connector()

        async def getconn():
            conn = await self.connector.connect_async(
                os.getenv('CLOUD_SQL_INSTANCE'),
                "asyncpg",
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                db=os.getenv('DB_NAME')
            )
            return conn

        self.engine = create_async_engine(
            "postgresql+asyncpg://",
            async_creator=getconn,
            echo=os.getenv('DATABASE_ECHO', 'false').lower() == 'true'
        )

        self.async_session_maker = async_sessionmaker(
            self.engine,
            expire_on_commit=False
        )

    async def _initialize_direct(self):
        """Initialize direct database connection."""
        self.engine = create_async_engine(
            self.database_url,
            echo=os.getenv('DATABASE_ECHO', 'false').lower() == 'true'
        )

        self.async_session_maker = async_sessionmaker(
            self.engine,
            expire_on_commit=False
        )

    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
        if self.connector:
            await self.connector.close_async()

    @asynccontextmanager
    async def get_session(self):
        """Get an async database session."""
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    # Session operations
    async def create_session(self, session_data: SessionCreate) -> Session:
        """Create a new session."""
        async with self.get_session() as db_session:
            db_obj = Session(**session_data.dict())
            db_session.add(db_obj)
            await db_session.flush()
            await db_session.refresh(db_obj)
            return db_obj

    async def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        async with self.get_session() as db_session:
            result = await db_session.execute(
                select(Session).where(Session.session_id == session_id)
            )
            return result.scalar_one_or_none()

    async def update_session(self, session_id: str, session_data: SessionUpdate) -> Optional[Session]:
        """Update a session."""
        async with self.get_session() as db_session:
            stmt = (
                update(Session)
                .where(Session.session_id == session_id)
                .values(**session_data.dict(exclude_unset=True), updated_at=datetime.utcnow())
            )
            await db_session.execute(stmt)
            return await self.get_session_by_id(session_id)

    async def get_sessions_by_user(self, user_id: str, limit: int = 100) -> List[Session]:
        """Get sessions by user ID."""
        async with self.get_session() as db_session:
            result = await db_session.execute(
                select(Session)
                .where(Session.user_id == user_id)
                .order_by(Session.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()

    # Requirement operations
    async def create_requirement(self, req_data: RequirementCreate) -> Requirement:
        """Create a new requirement."""
        async with self.get_session() as db_session:
            db_obj = Requirement(**req_data.dict())
            db_session.add(db_obj)
            await db_session.flush()
            await db_session.refresh(db_obj)
            return db_obj

    async def get_requirement_by_id(self, requirement_id: str) -> Optional[Requirement]:
        """Get requirement by ID."""
        async with self.get_session() as db_session:
            result = await db_session.execute(
                select(Requirement).where(Requirement.id == requirement_id)
            )
            return result.scalar_one_or_none()

    async def update_requirement(self, requirement_id: str, req_data: RequirementUpdate) -> Optional[Requirement]:
        """Update a requirement."""
        async with self.get_session() as db_session:
            stmt = (
                update(Requirement)
                .where(Requirement.id == requirement_id)
                .values(**req_data.dict(exclude_unset=True), updated_at=datetime.utcnow())
            )
            await db_session.execute(stmt)
            return await self.get_requirement_by_id(requirement_id)

    async def get_requirements_by_session(self, session_id: str) -> List[Requirement]:
        """Get requirements by session ID."""
        async with self.get_session() as db_session:
            result = await db_session.execute(
                select(Requirement)
                .where(Requirement.session_id == session_id)
                .order_by(Requirement.created_at)
            )
            return result.scalars().all()

    # Test case operations
    async def create_test_case(self, test_case_data: TestCaseCreate) -> TestCase:
        """Create a new test case."""
        async with self.get_session() as db_session:
            db_obj = TestCase(**test_case_data.dict())
            db_session.add(db_obj)
            await db_session.flush()
            await db_session.refresh(db_obj)
            return db_obj

    async def create_test_cases_from_suite(self, session_id: str, test_suite: TestSuite) -> List[TestCase]:
        """Create test cases from a structured test suite."""
        test_cases = []

        for i, test_case_data in enumerate(test_suite.test_cases):
            test_case = TestCaseCreate(
                id=f"{session_id}_tc_{i+1}",
                session_id=session_id,
                test_name=test_case_data.get('summary', f'Test Case {i+1}'),
                test_description=test_case_data.get('summary', ''),
                test_steps=test_case_data.get('test_steps', []),
                expected_results=test_case_data.get('expected_result', ''),
                test_type=test_case_data.get('type', 'functional').lower(),
                priority=test_case_data.get('priority', 'medium').lower(),
                test_data=test_case_data.get('test_data', {}),
                preconditions='; '.join(test_case_data.get('preconditions', [])),
                test_suite_name=test_suite.name,
                test_suite_description=test_suite.description,
                test_id=test_case_data.get('test_id', f'TC_AUTO_{i+1:03d}'),
                summary=test_case_data.get('summary', ''),
                requirement_traceability=test_case_data.get('requirement_traceability', '')
            )

            created_test_case = await self.create_test_case(test_case)
            test_cases.append(created_test_case)

        return test_cases

    async def get_test_case_by_id(self, test_case_id: str) -> Optional[TestCase]:
        """Get test case by ID."""
        async with self.get_session() as db_session:
            result = await db_session.execute(
                select(TestCase).where(TestCase.id == test_case_id)
            )
            return result.scalar_one_or_none()

    async def update_test_case(self, test_case_id: str, test_case_data: TestCaseUpdate) -> Optional[TestCase]:
        """Update a test case."""
        async with self.get_session() as db_session:
            stmt = (
                update(TestCase)
                .where(TestCase.id == test_case_id)
                .values(**test_case_data.dict(exclude_unset=True), updated_at=datetime.utcnow())
            )
            await db_session.execute(stmt)
            return await self.get_test_case_by_id(test_case_id)

    async def get_test_cases_by_session(self, session_id: str) -> List[TestCase]:
        """Get test cases by session ID."""
        async with self.get_session() as db_session:
            result = await db_session.execute(
                select(TestCase)
                .where(TestCase.session_id == session_id)
                .order_by(TestCase.created_at)
            )
            return result.scalars().all()

    async def get_test_cases_as_suite(self, session_id: str) -> Optional[TestSuite]:
        """Get test cases formatted as a test suite."""
        test_cases = await self.get_test_cases_by_session(session_id)

        if not test_cases:
            return None

        # Group by test suite
        suite_name = test_cases[0].test_suite_name or f"Test Suite for Session {session_id}"
        suite_description = test_cases[0].test_suite_description or "Generated test suite"

        formatted_test_cases = []
        for tc in test_cases:
            formatted_tc = {
                "test_id": tc.test_id or tc.id,
                "priority": tc.priority.upper() if tc.priority else "MEDIUM",
                "type": tc.test_type.title() if tc.test_type else "Functional",
                "summary": tc.summary or tc.test_name,
                "preconditions": tc.preconditions.split('; ') if tc.preconditions else [],
                "test_steps": tc.test_steps or [],
                "test_data": tc.test_data or {},
                "expected_result": tc.expected_results or "",
                "requirement_traceability": tc.requirement_traceability or ""
            }
            formatted_test_cases.append(formatted_tc)

        return TestSuite(
            name=suite_name,
            description=suite_description,
            total_tests=len(formatted_test_cases),
            generated_date=datetime.utcnow().date().isoformat(),
            test_cases=formatted_test_cases
        )

    # Session management with full context
    async def get_session_with_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session with all related requirements and test cases."""
        async with self.get_session() as db_session:
            # Get session
            session_result = await db_session.execute(
                select(Session)
                .options(
                    selectinload(Session.requirements),
                    selectinload(Session.test_cases)
                )
                .where(Session.session_id == session_id)
            )
            session = session_result.scalar_one_or_none()

            if not session:
                return None

            # Format response
            return {
                "session": {
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "project_name": session.project_name,
                    "user_prompt": session.user_prompt,
                    "status": session.status,
                    "rag_context_loaded": session.rag_context_loaded,
                    "rag_enabled": session.rag_enabled,
                    "agent_used": session.agent_used,
                    "workflow_type": session.workflow_type,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat()
                },
                "requirements": [
                    {
                        "id": req.id,
                        "original_content": req.original_content,
                        "edited_content": req.edited_content,
                        "requirement_type": req.requirement_type,
                        "priority": req.priority,
                        "status": req.status,
                        "version": req.version,
                        "source": req.source,
                        "tags": req.tags,
                        "metadata": req.metadata,
                        "created_at": req.created_at.isoformat(),
                        "updated_at": req.updated_at.isoformat()
                    }
                    for req in session.requirements
                ],
                "test_cases": [
                    {
                        "id": tc.id,
                        "test_name": tc.test_name,
                        "test_description": tc.test_description,
                        "test_steps": tc.test_steps,
                        "expected_results": tc.expected_results,
                        "test_type": tc.test_type,
                        "priority": tc.priority,
                        "status": tc.status,
                        "test_data": tc.test_data,
                        "preconditions": tc.preconditions,
                        "postconditions": tc.postconditions,
                        "estimated_duration": tc.estimated_duration,
                        "automation_feasible": tc.automation_feasible,
                        "tags": tc.tags,
                        "test_suite_name": tc.test_suite_name,
                        "test_id": tc.test_id,
                        "summary": tc.summary,
                        "requirement_traceability": tc.requirement_traceability,
                        "created_at": tc.created_at.isoformat(),
                        "updated_at": tc.updated_at.isoformat()
                    }
                    for tc in session.test_cases
                ]
            }

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all related data."""
        async with self.get_session() as db_session:
            result = await db_session.execute(
                delete(Session).where(Session.session_id == session_id)
            )
            return result.rowcount > 0


# Global database manager instance
db_manager = DatabaseManager()