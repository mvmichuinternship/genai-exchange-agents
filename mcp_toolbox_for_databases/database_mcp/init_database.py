"""
Database initialization script for MCP Toolbox.

This script initializes the PostgreSQL database with the required schema
for the MCP Toolbox for databases.
"""

import asyncio
import os
import logging
from pathlib import Path

try:
    import asyncpg
except ImportError:
    print("Error: asyncpg not installed. Install with: pip install asyncpg")
    asyncpg = None


async def init_database(database_url: str = None) -> bool:
    """
    Initialize the database with the MCP schema.

    Args:
        database_url: Database connection URL

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
                # Build from components
                user = os.getenv('DB_USER', 'postgres')
                password = os.getenv('DB_PASSWORD', '')
                host = os.getenv('DB_HOST', 'localhost')
                port = os.getenv('DB_PORT', '5432')
                database = os.getenv('DB_NAME', 'test_case_db')
                database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        print(f"Connecting to database: {database_url.split('@')[1] if '@' in database_url else database_url}")

        # Read schema SQL
        schema_file = Path(__file__).parent / "schema.sql"
        if not schema_file.exists():
            print(f"Error: Schema file not found at {schema_file}")
            return False

        with open(schema_file, 'r') as f:
            schema_sql = f.read()

        # Connect and execute
        conn = await asyncpg.connect(database_url)
        try:
            print("Executing database schema...")
            await conn.execute(schema_sql)
            print("✅ Database schema initialized successfully")

            # Verify tables were created
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)

            print(f"✅ Created {len(tables)} tables:")
            for table in tables:
                print(f"  - {table['table_name']}")

            return True

        finally:
            await conn.close()

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False


async def check_database_status(database_url: str = None) -> dict:
    """
    Check database status and return information.

    Args:
        database_url: Database connection URL

    Returns:
        Dictionary with database status information
    """
    if asyncpg is None:
        return {"error": "Database dependencies not available"}

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

        conn = await asyncpg.connect(database_url)
        try:
            # Check tables
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)

            # Check MCP-specific tables
            mcp_tables = ['sessions', 'requirements', 'test_cases', 'mcp_sessions', 'mcp_operations']
            existing_mcp_tables = [t['table_name'] for t in tables if t['table_name'] in mcp_tables]

            # Get record counts
            counts = {}
            for table_name in existing_mcp_tables:
                count_result = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                counts[table_name] = count_result

            return {
                "status": "connected",
                "total_tables": len(tables),
                "mcp_tables": existing_mcp_tables,
                "missing_mcp_tables": [t for t in mcp_tables if t not in existing_mcp_tables],
                "record_counts": counts,
                "database_url": database_url.split('@')[1] if '@' in database_url else database_url
            }

        finally:
            await conn.close()

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    """Run database initialization when called directly."""
    import sys

    async def main():
        logging.basicConfig(level=logging.INFO)

        print("🚀 MCP Toolbox Database Initialization")
        print("=" * 50)

        # Check current status
        print("Checking current database status...")
        status = await check_database_status()

        if "error" in status:
            print(f"❌ Database connection error: {status['error']}")
            print("\nPlease check your database configuration:")
            print("- DATABASE_URL environment variable")
            print("- Or DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME variables")
            sys.exit(1)

        print(f"📊 Database Status:")
        print(f"  - Connection: {status['status']}")
        print(f"  - Database: {status['database_url']}")
        print(f"  - Total tables: {status['total_tables']}")
        print(f"  - MCP tables: {len(status['mcp_tables'])}/{len(status['mcp_tables']) + len(status['missing_mcp_tables'])}")

        if status['missing_mcp_tables']:
            print(f"  - Missing tables: {', '.join(status['missing_mcp_tables'])}")
            print("\n🔄 Initializing missing tables...")

            success = await init_database()
            if success:
                print("\n✅ Database initialization completed successfully!")

                # Check status again
                final_status = await check_database_status()
                if final_status.get('record_counts'):
                    print("\n📈 Table Record Counts:")
                    for table, count in final_status['record_counts'].items():
                        print(f"  - {table}: {count} records")

                sys.exit(0)
            else:
                print("\n❌ Database initialization failed!")
                sys.exit(1)
        else:
            print("\n✅ All MCP tables are present!")

            if status.get('record_counts'):
                print("\n📈 Current Record Counts:")
                for table, count in status['record_counts'].items():
                    print(f"  - {table}: {count} records")

            print("\n🎉 Database is ready for MCP operations!")
            sys.exit(0)

    asyncio.run(main())