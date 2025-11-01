#!/usr/bin/env python3
"""
Setup script for MCP toolbox development environment.

This script helps set up the development environment with proper dependencies
and configuration.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, cwd=None):
    """Run a shell command."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"Error running command: {command}")
        sys.exit(1)


def setup_virtual_environment():
    """Set up Python virtual environment."""
    venv_path = Path("venv")

    if not venv_path.exists():
        print("Creating virtual environment...")
        run_command(f"{sys.executable} -m venv venv")

    # Activate virtual environment (instructions for user)
    if os.name == 'nt':  # Windows
        activate_script = "venv\\Scripts\\activate"
    else:  # Unix/Linux/macOS
        activate_script = "source venv/bin/activate"

    print(f"\n✅ Virtual environment created!")
    print(f"Activate it with: {activate_script}")

    return venv_path


def install_dependencies():
    """Install project dependencies."""
    print("Installing dependencies...")

    # Determine pip command
    if os.path.exists("venv"):
        if os.name == 'nt':  # Windows
            pip_cmd = "venv\\Scripts\\pip"
        else:  # Unix/Linux/macOS
            pip_cmd = "venv/bin/pip"
    else:
        pip_cmd = "pip"

    # Install requirements
    run_command(f"{pip_cmd} install --upgrade pip")
    run_command(f"{pip_cmd} install -r requirements.txt")

    # Install in development mode
    run_command(f"{pip_cmd} install -e .")

    print("✅ Dependencies installed successfully!")


def create_env_file():
    """Create .env file from template."""
    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists() and env_example.exists():
        print("Creating .env file from template...")
        env_file.write_text(env_example.read_text())
        print("✅ .env file created!")
        print("⚠️  Please edit .env file with your actual configuration values")
    else:
        print("📝 .env file already exists or template not found")


def check_docker():
    """Check if Docker is available."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Docker found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass

    print("⚠️  Docker not found. Install Docker for containerization support.")
    return False


def check_gcloud():
    """Check if Google Cloud SDK is available."""
    try:
        result = subprocess.run(
            ["gcloud", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ Google Cloud SDK found")
            return True
    except FileNotFoundError:
        pass

    print("⚠️  Google Cloud SDK not found. Install it for deployment support.")
    return False


def run_tests():
    """Run basic tests to verify setup."""
    print("Running basic tests...")

    try:
        # Test imports
        import mcp_tools
        print("✅ MCP tools package imported successfully")

        # Test database initialization
        from mcp_tools.database.init_db import get_create_tables_sql
        sql = get_create_tables_sql()
        if sql and "CREATE TABLE sessions" in sql:
            print("✅ Database schema loaded successfully")

        print("✅ All tests passed!")

    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        print("Some dependencies might be missing. Check requirements.txt")
    except Exception as e:
        print(f"❌ Test failed: {e}")


def main():
    """Main setup function."""
    print("🚀 Setting up MCP Toolbox development environment...")
    print("=" * 50)

    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required")
        sys.exit(1)

    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

    # Setup steps
    setup_virtual_environment()
    install_dependencies()
    create_env_file()

    # Check optional tools
    print("\nChecking optional tools:")
    check_docker()
    check_gcloud()

    # Run tests
    print("\nRunning verification tests:")
    run_tests()

    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Activate your virtual environment")
    print("2. Edit .env file with your configuration")
    print("3. Set up your database and Redis instances")
    print("4. Run: python -m mcp_tools.database.init_db")
    print("5. Start developing with the MCP toolbox!")

    print("\nUseful commands:")
    print("- Initialize database: python -m mcp_tools.database.init_db")
    print("- Run example: python example_agent.py")
    print("- Deploy: python deploy.py all")


if __name__ == "__main__":
    main()