#!/usr/bin/env python3
"""
Test script for MCP Toolbox for databases implementation.

This script performs basic validation of the MCP setup without requiring
a full database connection.
"""

import sys
import asyncio
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test if all required modules can be imported."""
    print("🔍 Testing imports...")

    try:
        # Test MCP imports
        import mcp
        print("✅ mcp package available")
    except ImportError:
        print("❌ mcp package not available - install with: pip install mcp")
        return False

    try:
        import asyncpg
        print("✅ asyncpg package available")
    except ImportError:
        print("❌ asyncpg package not available - install with: pip install asyncpg")
        return False

    try:
        # Test our modules
        from database_mcp import server, client, tools
        print("✅ Local MCP modules available")
    except ImportError as e:
        print(f"❌ Local MCP modules not available: {e}")
        return False

    return True


def test_configuration():
    """Test configuration setup."""
    print("\n🔧 Testing configuration...")

    try:
        from database_mcp.server import get_database_config
        config = get_database_config()
        print("✅ Database configuration loaded")
        print(f"   Host: {config.get('host', 'localhost')}")
        print(f"   Database: {config.get('database', 'mcp_test')}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


async def test_server_setup():
    """Test server module setup."""
    print("\n🖥️  Testing server setup...")

    try:
        from database_mcp.server import MCPDatabaseServer
        server = MCPDatabaseServer()
        print("✅ MCP server can be instantiated")

        # Test tool listing
        tools = server.list_tools()
        print(f"✅ Server has {len(tools)} tools available:")
        for tool in tools[:3]:  # Show first 3 tools
            print(f"   - {tool.name}: {tool.description[:50]}...")
        if len(tools) > 3:
            print(f"   ... and {len(tools) - 3} more")

        return True
    except Exception as e:
        print(f"❌ Server setup error: {e}")
        return False


async def test_client_setup():
    """Test client module setup."""
    print("\n💻 Testing client setup...")

    try:
        from database_mcp.client import DatabaseMCPClient

        # Test client instantiation (without connection)
        client = DatabaseMCPClient(connect=False)
        print("✅ MCP client can be instantiated")

        # Test tool creation
        from database_mcp.tools import create_database_tools
        tools = create_database_tools()
        print(f"✅ Database tools created: {len(tools)} tools")

        return True
    except Exception as e:
        print(f"❌ Client setup error: {e}")
        return False


def test_schema_validation():
    """Test database schema validation."""
    print("\n📋 Testing schema validation...")

    try:
        # Read and validate schema file
        schema_file = Path(__file__).parent / "schema.sql"
        if not schema_file.exists():
            print("❌ schema.sql file not found")
            return False

        schema_content = schema_file.read_text()

        # Check for required tables
        required_tables = ["sessions", "requirements", "test_cases"]
        tables_found = []

        for table in required_tables:
            if f"CREATE TABLE {table}" in schema_content:
                tables_found.append(table)

        if len(tables_found) == len(required_tables):
            print("✅ All required tables found in schema")
            for table in tables_found:
                print(f"   - {table}")
        else:
            missing = set(required_tables) - set(tables_found)
            print(f"❌ Missing tables in schema: {missing}")
            return False

        return True
    except Exception as e:
        print(f"❌ Schema validation error: {e}")
        return False


async def test_deployment_config():
    """Test deployment configuration."""
    print("\n🚀 Testing deployment configuration...")

    try:
        # Check if deploy.py exists and is valid
        deploy_file = Path(__file__).parent / "deploy.py"
        if not deploy_file.exists():
            print("❌ deploy.py file not found")
            return False

        print("✅ deploy.py file exists")

        # Try to import deployment functions
        import deploy
        if hasattr(deploy, 'setup_database') and hasattr(deploy, 'deploy_mcp_server'):
            print("✅ Deployment functions available")
        else:
            print("❌ Deployment functions missing")
            return False

        return True
    except Exception as e:
        print(f"❌ Deployment configuration error: {e}")
        return False


async def run_all_tests():
    """Run all tests."""
    print("🧪 MCP Toolbox for Databases - Test Suite")
    print("=" * 60)

    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_configuration),
        ("Server Setup Test", test_server_setup),
        ("Client Setup Test", test_client_setup),
        ("Schema Validation Test", test_schema_validation),
        ("Deployment Config Test", test_deployment_config)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {test_name}")
        if result:
            passed += 1

    print(f"\n📈 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! MCP Toolbox is ready to use.")
        print("\n📋 Next steps:")
        print("1. Install dependencies: pip install mcp mcp-server-postgres asyncpg")
        print("2. Configure database: Update config in server.py")
        print("3. Deploy to Cloud: python deploy.py all")
        print("4. Test with agents: python example_mcp_usage.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\n📋 Troubleshooting:")
        print("- Install missing dependencies")
        print("- Check file permissions")
        print("- Verify configuration settings")

    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)