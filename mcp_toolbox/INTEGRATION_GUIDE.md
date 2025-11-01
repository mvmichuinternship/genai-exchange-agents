# MCP Toolbox Integration Guide

This guide explains how to integrate the MCP toolbox with your Google ADK agents for persistent session management, requirements storage, and test case persistence.

## Overview

The MCP toolbox provides:

- **Cloud SQL integration** for persistent data storage
- **Redis caching** for performance optimization
- **Structured test case format** support
- **Session workflow tracking**
- **Requirements management** with versioning
- **Automatic database schema management**

## Quick Start

### 1. Set up the MCP Toolbox

```bash
cd /path/to/agents/mcp_toolbox
python setup.py
```

This will:

- Create a virtual environment
- Install all dependencies
- Create `.env` file from template
- Run basic verification tests

### 2. Configure Environment

Edit the `.env` file with your configuration:

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/test_case_db
CLOUD_SQL_INSTANCE=your-project:region:instance-name
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_NAME=test_case_db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
```

### 3. Initialize Database

```bash
python -m mcp_tools.database.init_db
```

### 4. Integration Pattern

Here's how to integrate MCP toolbox with your existing agents:

```python
import sys
import os

# Add MCP toolbox to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mcp_toolbox'))

try:
    from mcp_tools.tools import create_function_tools, mcp_tools
    MCP_AVAILABLE = True
except ImportError:
    print("Warning: MCP toolbox not available")
    MCP_AVAILABLE = False
    mcp_tools = None

# Your existing agent code...
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

# Create your workflow function with MCP integration
async def enhanced_workflow(status: str, user_input: str, session_id: str = None):
    if MCP_AVAILABLE:
        # Initialize MCP tools
        await mcp_tools.initialize()

        # Create session if starting
        if status == "start" and session_id is None:
            session_id = str(uuid.uuid4())
            await mcp_tools.create_session_tool(
                session_id=session_id,
                user_id="user123",
                user_prompt=user_input
            )

        # Track workflow steps
        await mcp_tools.track_workflow_step_tool(
            session_id=session_id,
            step_name=f"workflow_{status}",
            step_result={"input": user_input}
        )

        # Your workflow logic here...

        # Store requirements
        await mcp_tools.create_requirement_tool(
            session_id=session_id,
            requirement_content=analyzed_requirements,
            requirement_type="functional"
        )

        # Store test cases
        await mcp_tools.create_test_cases_from_suite_tool(
            session_id=session_id,
            test_suite_json=generated_test_suite
        )

    # Your existing workflow logic as fallback...

# Create tools list
tools = [FunctionTool(func=enhanced_workflow)]
if MCP_AVAILABLE:
    tools.extend(create_function_tools())

# Create agent with enhanced tools
agent = Agent(
    model="gemini-2.0-flash-exp",
    name="enhanced_agent",
    description="Agent with MCP toolbox integration",
    tools=tools
)
```

## Available MCP Tools

The MCP toolbox provides these function tools for your agents:

### Session Management

- `create_session` - Create a new session
- `get_session` - Retrieve session by ID
- `update_session_status` - Update session status
- `get_session_with_full_context` - Get complete session data

### Requirements Management

- `create_requirement` - Store a new requirement
- `update_requirement` - Update existing requirement
- `get_session_requirements` - Get all requirements for a session

### Test Case Management

- `create_test_cases_from_suite` - Store structured test cases
- `get_session_test_cases` - Retrieve test cases (optionally as suite)

### Workflow Tracking

- `track_workflow_step` - Track workflow execution steps

## Test Case Structure

The MCP toolbox supports this structured test case format:

```json
{
  "test_suite": {
    "name": "Suite Name",
    "description": "Brief description",
    "total_tests": 2,
    "generated_date": "2025-10-31",
    "test_cases": [
      {
        "test_id": "TC_FUNC_001",
        "priority": "HIGH",
        "type": "Functional",
        "summary": "Test user authentication",
        "preconditions": ["User account exists", "System is running"],
        "test_steps": [
          "Navigate to login page",
          "Enter valid credentials",
          "Click login button"
        ],
        "test_data": {
          "username": "testuser@example.com",
          "password": "TestPassword123!"
        },
        "expected_result": "User is successfully authenticated",
        "requirement_traceability": "REQ_001 - User Authentication"
      }
    ]
  }
}
```

## Database Schema

The MCP toolbox automatically creates these tables:

- `sessions` - Core session management
- `requirements` - Requirements storage with versioning
- `test_cases` - Test cases with structured format support
- `test_case_requirements` - Many-to-many mapping
- `projects` - Project organization
- `users` - Basic user management

## Deployment

### Local Development

```bash
# Start local PostgreSQL and Redis
docker-compose up -d  # (if using Docker)

# Initialize database
python -m mcp_tools.database.init_db

# Run your agent
python your_agent.py
```

### Google Cloud Deployment

```bash
# Set up Cloud SQL and Redis
python deploy.py setup-cloud-sql
python deploy.py setup-redis

# Initialize database
python deploy.py init-db

# Deploy to Cloud Run
python deploy.py deploy

# Or run all steps
python deploy.py all
```

## Example: Enhanced Decider Agent

See `decider_agent/agent_with_mcp.py` for a complete example of integrating MCP toolbox with the existing decider agent.

Key features:

- **Persistent sessions** stored in Cloud SQL
- **Requirements tracking** with edit history
- **Test case storage** in structured format
- **Workflow audit trail** with Redis caching
- **Graceful fallback** when MCP is unavailable

## Error Handling

The MCP toolbox includes graceful error handling:

```python
# Check if MCP is available
if MCP_AVAILABLE:
    # Use enhanced features
    result = await mcp_tools.create_session_tool(...)
    if not result["success"]:
        # Handle error
        print(f"Error: {result['error']}")
else:
    # Use fallback logic
    print("MCP not available, using in-memory storage")
```

## Performance Considerations

- **Redis caching** reduces database queries
- **Connection pooling** for Cloud SQL
- **Async operations** throughout
- **Batch operations** for multiple test cases
- **Index optimization** on frequently queried fields

## Security

- **IAM authentication** for Cloud SQL
- **VPC networking** for Redis
- **Environment variable** based configuration
- **SQL injection prevention** via SQLAlchemy ORM
- **Connection encryption** in transit

## Monitoring

The MCP toolbox provides:

- **Workflow step tracking** in Redis
- **Session state monitoring**
- **Cache hit/miss metrics**
- **Database connection health checks**
- **Error tracking and logging**

## Troubleshooting

### Common Issues

1. **Import errors**: Install dependencies with `pip install -r requirements.txt`
2. **Database connection**: Check `DATABASE_URL` in `.env`
3. **Redis connection**: Check `REDIS_URL` in `.env`
4. **Cloud SQL**: Verify instance name and credentials
5. **Schema errors**: Run `python -m mcp_tools.database.init_db`

### Debug Mode

Enable debug logging:

```bash
export DATABASE_ECHO=true
export LOG_LEVEL=DEBUG
```

### Health Checks

```python
# Test database connection
from mcp_tools.database import db_manager
await db_manager.initialize()

# Test Redis connection
from mcp_tools.redis_client import redis_manager
await redis_manager.initialize()
```

## Next Steps

1. Review the example agent integration
2. Set up your database and Redis instances
3. Configure your environment variables
4. Initialize the database schema
5. Start integrating MCP tools with your agents
6. Deploy to Google Cloud when ready

For more examples and detailed API documentation, see the individual module files in the `mcp_tools/` directory.
