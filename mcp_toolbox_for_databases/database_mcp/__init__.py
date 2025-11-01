"""
Database MCP package for Google ADK agents.

This package provides MCP (Model Context Protocol) integration for database operations,
session management, and test case persistence using Google's MCP Toolbox approach.
"""

__version__ = "0.1.0"
__author__ = "Mridula Vinod"

from .client import DatabaseMCPClient
from .server import DatabaseMCPServer
from .tools import create_database_tools

__all__ = [
    "DatabaseMCPClient",
    "DatabaseMCPServer",
    "create_database_tools",
]