"""
MCP Toolbox for Cloud SQL and Redis integration with Google ADK agents.

This package provides tools for:
- Session management with Cloud SQL
- Requirements storage and retrieval
- Test cases persistence with structured JSON format
- Redis caching and session management
"""

__version__ = "0.1.0"
__author__ = "Mridula Vinod"

try:
    from .database import DatabaseManager
    from .redis_client import RedisManager
    from .models import Session, Requirement, TestCase, TestCaseRequirement

    __all__ = [
        "DatabaseManager",
        "RedisManager",
        "Session",
        "Requirement",
        "TestCase",
        "TestCaseRequirement",
    ]
except ImportError as e:
    print(f"Warning: Some MCP toolbox dependencies are not installed: {e}")
    print("Install dependencies with: pip install -r requirements.txt")

    __all__ = []