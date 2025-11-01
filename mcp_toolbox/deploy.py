"""
Deployment script for MCP toolbox server.

This script handles deployment to Google Cloud Platform with Cloud SQL and Redis.
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


def deploy_to_cloud_run():
    """Deploy the MCP toolbox to Google Cloud Run."""
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT environment variable not set")
        sys.exit(1)

    region = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
    service_name = 'mcp-toolbox-server'

    # Build and push container image
    image_url = f"gcr.io/{project_id}/{service_name}"

    print("Building container image...")
    run_command(f"docker build -t {image_url} .")

    print("Pushing image to Google Container Registry...")
    run_command(f"docker push {image_url}")

    # Deploy to Cloud Run
    print("Deploying to Cloud Run...")
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
        --set-secrets "DB_PASSWORD=db-password:latest" \
        --set-secrets "REDIS_PASSWORD=redis-password:latest" \
        --memory 1Gi \
        --cpu 1 \
        --timeout 300 \
        --max-instances 10
    """

    run_command(cloud_run_command)

    print(f"✅ Deployment completed! Service available at:")
    service_url = run_command(
        f"gcloud run services describe {service_name} --region {region} --format 'value(status.url)'"
    ).strip()
    print(service_url)


def setup_cloud_sql():
    """Set up Cloud SQL instance."""
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    instance_name = os.getenv('CLOUD_SQL_INSTANCE_NAME', 'mcp-toolbox-db')
    region = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')

    print("Creating Cloud SQL instance...")
    create_instance_command = f"""
    gcloud sql instances create {instance_name} \
        --database-version POSTGRES_14 \
        --tier db-f1-micro \
        --region {region} \
        --storage-auto-increase \
        --backup-start-time 02:00
    """

    try:
        run_command(create_instance_command)
    except SystemExit:
        print("Instance might already exist, continuing...")

    print("Creating database...")
    create_db_command = f"""
    gcloud sql databases create test_case_db \
        --instance {instance_name}
    """

    try:
        run_command(create_db_command)
    except SystemExit:
        print("Database might already exist, continuing...")

    print("Setting up database user...")
    # Note: In production, you should use IAM authentication
    user_command = f"""
    gcloud sql users create mcpuser \
        --instance {instance_name} \
        --password {os.getenv('DB_PASSWORD', 'change_me_in_production')}
    """

    try:
        run_command(user_command)
    except SystemExit:
        print("User might already exist, continuing...")


def setup_redis():
    """Set up Redis instance on Google Cloud Memorystore."""
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    instance_name = os.getenv('REDIS_INSTANCE_NAME', 'mcp-toolbox-redis')
    region = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')

    print("Creating Redis instance...")
    create_redis_command = f"""
    gcloud redis instances create {instance_name} \
        --size 1 \
        --region {region} \
        --redis-version redis_6_x
    """

    try:
        run_command(create_redis_command)
    except SystemExit:
        print("Redis instance might already exist, continuing...")


def init_database():
    """Initialize the database schema."""
    print("Initializing database schema...")

    try:
        import asyncio
        from mcp_tools.database.init_db import init_database

        async def run_init():
            success = await init_database()
            if not success:
                sys.exit(1)

        asyncio.run(run_init())
        print("✅ Database schema initialized successfully")

    except ImportError:
        print("Running database initialization via Python module...")
        run_command("python -m mcp_tools.database.init_db")


def main():
    """Main deployment function."""
    if len(sys.argv) < 2:
        print("Usage: python deploy.py <command>")
        print("Commands:")
        print("  setup-cloud-sql  - Set up Cloud SQL instance")
        print("  setup-redis      - Set up Redis instance")
        print("  init-db          - Initialize database schema")
        print("  deploy           - Deploy to Cloud Run")
        print("  all              - Run all setup and deployment steps")
        sys.exit(1)

    command = sys.argv[1]

    if command == "setup-cloud-sql":
        setup_cloud_sql()
    elif command == "setup-redis":
        setup_redis()
    elif command == "init-db":
        init_database()
    elif command == "deploy":
        deploy_to_cloud_run()
    elif command == "all":
        print("🚀 Starting complete deployment process...")
        setup_cloud_sql()
        setup_redis()
        init_database()
        deploy_to_cloud_run()
        print("🎉 Deployment process completed!")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()