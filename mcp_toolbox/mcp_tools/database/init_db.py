"""
Database initialization script for the MCP toolbox.

This module provides utilities to initialize the database schema and manage
database setup.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional

try:
    import asyncpg
    from sqlalchemy.ext.asyncio import create_async_engine
except ImportError:
    print("Warning: Database dependencies not installed. Install with: pip install asyncpg sqlalchemy")
    asyncpg = None


async def init_database(database_url: Optional[str] = None) -> bool:
    """
    Initialize the database with the required schema.

    Args:
        database_url: Database connection URL. If None, uses environment variables.

    Returns:
        True if successful, False otherwise
    """
    if asyncpg is None:
        print("Error: Database dependencies not available")
        return False

    try:
        # Get database URL
        if not database_url:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                user = os.getenv('DB_USER', 'postgres')
                password = os.getenv('DB_PASSWORD', '')
                host = os.getenv('DB_HOST', 'localhost')
                port = os.getenv('DB_PORT', '5432')
                database = os.getenv('DB_NAME', 'test_case_db')
                database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        # Read SQL schema
        sql_file = Path(__file__).parent / "create_tables.sql"
        with open(sql_file, 'r') as f:
            create_tables_sql = f.read()

        # Connect and execute
        conn = await asyncpg.connect(database_url)
        try:
            await conn.execute(create_tables_sql)
            print("Database schema initialized successfully")
            return True
        finally:
            await conn.close()

    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


def get_create_tables_sql() -> str:
    """Get the SQL for creating tables."""
    sql_file = Path(__file__).parent / "create_tables.sql"
    with open(sql_file, 'r') as f:
        return f.read()


# Export for convenience
create_tables_sql = get_create_tables_sql()


if __name__ == "__main__":
    """Run database initialization when called directly."""
    import sys

    async def main():
        success = await init_database()
        if success:
            print("✅ Database initialization completed successfully")
            sys.exit(0)
        else:
            print("❌ Database initialization failed")
            sys.exit(1)

    asyncio.run(main())