"""
Deployment script for MCP Toolbox for Databases.

This script handles deployment to Google Cloud Platform with Cloud SQL
and the MCP server infrastructure.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, cwd=None):
    """Run a shell command and return the result."""
    print(f"Running: {command}")
    result = subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)

    print(result.stdout)
    return result.stdout


def setup_mcp_environment():
    """Set up MCP development environment."""
    print("Setting up MCP development environment...")

    # Install MCP dependencies
    run_command("pip install mcp mcp-server-postgres asyncpg")

    # Install project dependencies
    run_command("pip install -r requirements.txt")

    print("✅ MCP environment setup completed")


def setup_cloud_sql():
    """Set up Cloud SQL instance for MCP."""
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    instance_name = os.getenv('CLOUD_SQL_INSTANCE_NAME', 'mcp-database')
    region = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')

    print("Creating Cloud SQL instance for MCP...")
    create_instance_command = f"""
    gcloud sql instances create {instance_name} \
        --database-version POSTGRES_14 \
        --tier db-f1-micro \
        --region {region} \
        --storage-auto-increase \
        --backup-start-time 02:00 \
        --labels environment=mcp,purpose=database-toolbox
    """

    try:
        run_command(create_instance_command)
    except SystemExit:
        print("Instance might already exist, continuing...")

    print("Creating MCP database...")
    create_db_command = f"""
    gcloud sql databases create test_case_db \
        --instance {instance_name}
    """

    try:
        run_command(create_db_command)
    except SystemExit:
        print("Database might already exist, continuing...")

    # Get connection name for MCP configuration
    connection_name = run_command(f"""
    gcloud sql instances describe {instance_name} \
        --format="value(connectionName)"
    """).strip()

    print(f"✅ Cloud SQL instance created: {connection_name}")
    return connection_name


def deploy_mcp_server():
    """Deploy MCP server to Cloud Run."""
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT environment variable not set")
        sys.exit(1)

    region = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
    service_name = 'mcp-database-server'

    # Build and push container image
    image_url = f"gcr.io/{project_id}/{service_name}"

    print("Building MCP server container image...")

    # Create Dockerfile for MCP server
    dockerfile_content = """
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install MCP dependencies
RUN pip install mcp mcp-server-postgres asyncpg

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose MCP server port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
  CMD python -c "import asyncio; import database_mcp.init_database as init; asyncio.run(init.check_database_status())" || exit 1

# Start MCP server
CMD ["python", "-m", "database_mcp.server"]
"""

    with open("Dockerfile", "w") as f:
        f.write(dockerfile_content)

    run_command(f"docker build -t {image_url} .")

    print("Pushing image to Google Container Registry...")
    run_command(f"docker push {image_url}")

    # Deploy to Cloud Run
    print("Deploying MCP server to Cloud Run...")
    cloud_run_command = f"""
    gcloud run deploy {service_name} \
        --image {image_url} \
        --platform managed \
        --region {region} \
        --allow-unauthenticated \
        --set-env-vars "GOOGLE_CLOUD_PROJECT={project_id}" \
        --set-env-vars "CLOUD_SQL_INSTANCE={os.getenv('CLOUD_SQL_INSTANCE', '')}" \
        --set-env-vars "DB_USER={os.getenv('DB_USER', 'postgres')}" \
        --set-env-vars "DB_NAME={os.getenv('DB_NAME', 'test_case_db')}" \
        --set-env-vars "MCP_SERVER_PORT=8000" \
        --set-secrets "DB_PASSWORD=db-password:latest" \
        --memory 1Gi \
        --cpu 1 \
        --timeout 300 \
        --max-instances 10 \
        --port 8000 \
        --labels environment=mcp,service=database-server
    """

    run_command(cloud_run_command)

    print(f"✅ MCP server deployed! Service available at:")
    service_url = run_command(
        f"gcloud run services describe {service_name} --region {region} --format 'value(status.url)'"
    ).strip()
    print(service_url)

    return service_url


def init_mcp_database():
    """Initialize the MCP database schema."""
    print("Initializing MCP database schema...")

    try:
        run_command("python -m database_mcp.init_database")
        print("✅ MCP database schema initialized successfully")

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)


def test_mcp_integration():
    """Test MCP integration."""
    print("Testing MCP integration...")

    test_script = """
import asyncio
import sys
from database_mcp.client import MCPClientContext

async def test_mcp():
    try:
        async with MCPClientContext() as client:
            # Test session creation
            result = await client.create_session(
                session_id="test_session_123",
                user_id="test_user",
                project_name="MCP Test Project",
                user_prompt="Test MCP integration"
            )

            if result.get("success"):
                print("✅ MCP session creation test passed")
                return True
            else:
                print(f"❌ MCP session creation test failed: {result.get('error')}")
                return False

    except Exception as e:
        print(f"❌ MCP integration test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp())
    sys.exit(0 if success else 1)
"""

    with open("test_mcp.py", "w") as f:
        f.write(test_script)

    try:
        run_command("python test_mcp.py")
        print("✅ MCP integration test passed")
        os.remove("test_mcp.py")
    except SystemExit:
        print("❌ MCP integration test failed")
        os.remove("test_mcp.py")
        sys.exit(1)


def create_mcp_config():
    """Create MCP configuration files."""
    print("Creating MCP configuration...")

    # Create MCP server configuration
    mcp_config = {
        "server": {
            "name": "database-mcp-server",
            "version": "1.0.0",
            "description": "MCP server for database operations"
        },
        "capabilities": {
            "tools": True,
            "resources": False,
            "prompts": False
        },
        "database": {
            "provider": "postgresql",
            "connection_type": "cloud_sql",
            "schema_version": "1.0.0"
        }
    }

    import json
    with open("mcp_config.json", "w") as f:
        json.dump(mcp_config, f, indent=2)

    print("✅ MCP configuration created")


def main():
    """Main deployment function."""
    if len(sys.argv) < 2:
        print("Usage: python deploy.py <command>")
        print("Commands:")
        print("  setup-env        - Set up MCP development environment")
        print("  setup-cloud-sql  - Set up Cloud SQL instance")
        print("  init-db          - Initialize MCP database schema")
        print("  deploy-server    - Deploy MCP server to Cloud Run")
        print("  test-mcp         - Test MCP integration")
        print("  create-config    - Create MCP configuration files")
        print("  all              - Run all setup and deployment steps")
        sys.exit(1)

    command = sys.argv[1]

    if command == "setup-env":
        setup_mcp_environment()
    elif command == "setup-cloud-sql":
        setup_cloud_sql()
    elif command == "init-db":
        init_mcp_database()
    elif command == "deploy-server":
        deploy_mcp_server()
    elif command == "test-mcp":
        test_mcp_integration()
    elif command == "create-config":
        create_mcp_config()
    elif command == "all":
        print("🚀 Starting complete MCP Toolbox deployment process...")
        setup_mcp_environment()
        create_mcp_config()
        connection_name = setup_cloud_sql()
        init_mcp_database()
        server_url = deploy_mcp_server()
        test_mcp_integration()

        print("\n🎉 MCP Toolbox deployment completed!")
        print(f"📊 Summary:")
        print(f"  - Cloud SQL Connection: {connection_name}")
        print(f"  - MCP Server URL: {server_url}")
        print(f"  - Database Schema: Initialized")
        print(f"  - Integration Test: Passed")
        print("\n📋 Next Steps:")
        print("  1. Update your agents to use the MCP tools")
        print("  2. Configure environment variables in your deployment")
        print("  3. Test with your existing decider agent")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()