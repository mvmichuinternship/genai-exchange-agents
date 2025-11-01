# MCP Toolbox for Databases - Google ADK Integration

This implementation provides a complete **Google MCP (Model Context Protocol) Toolbox** for persistent database operations with Google ADK agents. It enables agents to store and retrieve session data, requirements, and structured test cases using Google's official MCP protocol.

## 🎯 Overview

The MCP Toolbox for Databases provides:

- **Persistent Session Management**: Store and retrieve agent workflows
- **Requirements Storage**: Persist requirements analysis from agents
- **Structured Test Cases**: Store test cases in JSON format with full traceability
- **Google MCP Protocol**: Standards-compliant MCP server and client
- **Cloud Deployment**: Ready for Google Cloud Run and Cloud SQL
- **ADK Integration**: Direct integration with Google ADK function tools

## 📁 Project Structure

```
mcp_toolbox_for_databases/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── schema.sql                   # Database schema (PostgreSQL)
├── deploy.py                    # Cloud deployment automation
├── test_mcp_setup.py           # Test suite for validation
├── example_mcp_usage.py        # Complete usage examples
├── database_mcp/
│   ├── __init__.py
│   ├── server.py               # MCP protocol server
│   ├── client.py               # MCP client for agents
│   └── tools.py                # Google ADK function tools
└── enhanced_decider_agent.py   # Example agent with MCP integration
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install MCP and database dependencies
pip install mcp mcp-server-postgres asyncpg

# Install Google ADK (if not already installed)
pip install google-adk
```

### 2. Test the Setup

```bash
# Run validation tests
python test_mcp_setup.py
```

### 3. Configure Database

Edit the database configuration in `database_mcp/server.py`:

```python
DATABASE_CONFIG = {
    "host": "localhost",        # Your database host
    "port": 5432,
    "database": "mcp_test",     # Your database name
    "user": "postgres",         # Your database user
    "password": "your_password" # Your database password
}
```

### 4. Setup Database Schema

```bash
# Create database and apply schema
python deploy.py database
```

### 5. Start MCP Server

```bash
# Start the MCP server locally
python deploy.py server
```

### 6. Test with Examples

```bash
# Run complete workflow examples
python example_mcp_usage.py
```

## 🏗️ Architecture

### MCP Protocol Flow

```
Google ADK Agent ←→ MCP Client ←→ MCP Server ←→ PostgreSQL Database
```

1. **Agent** uses function tools to interact with database
2. **MCP Client** handles protocol communication
3. **MCP Server** processes requests and manages database
4. **Database** persists all session data, requirements, and test cases

### Database Schema

The system uses three core tables:

#### `sessions` - Agent Session Management

```sql
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    user_prompt TEXT NOT NULL,
    project_name TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `requirements` - Requirements Storage

```sql
CREATE TABLE requirements (
    requirement_id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(session_id),
    content TEXT NOT NULL,
    requirement_type TEXT,
    priority TEXT DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `test_cases` - Structured Test Cases

```sql
CREATE TABLE test_cases (
    test_case_id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(session_id),
    test_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    priority TEXT DEFAULT 'medium',
    test_type TEXT,
    test_content JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🛠️ Usage Examples

### Basic Agent Integration

```python
from database_mcp.tools import mcp_db_tools

# Create a new session
session_result = await mcp_db_tools.create_mcp_session(
    user_id="user123",
    user_prompt="Create authentication system",
    project_name="Security Project"
)
session_id = session_result["session_id"]

# Store requirements
await mcp_db_tools.store_mcp_requirement(
    session_id=session_id,
    requirement_content="System must support OAuth2",
    requirement_type="security",
    priority="high"
)

# Store test cases (structured JSON)
test_suite = {
    "test_suite": {
        "name": "OAuth Test Suite",
        "total_tests": 1,
        "test_cases": [{
            "test_id": "TC_001",
            "priority": "HIGH",
            "summary": "Test OAuth2 flow",
            "test_steps": ["Login", "Authorize", "Verify token"],
            "expected_result": "User authenticated successfully"
        }]
    }
}

await mcp_db_tools.create_mcp_test_cases(
    session_id=session_id,
    test_suite_json=json.dumps(test_suite)
)
```

### Enhanced Agent with MCP Persistence

```python
from enhanced_decider_agent import EnhancedDeciderAgent

# Create agent with MCP persistence
agent = EnhancedDeciderAgent()

# Process request with automatic persistence
result = await agent.process_request_with_persistence(
    user_prompt="Create user management system",
    user_id="user123",
    project_name="User Management"
)

# Result includes session_id for tracking
session_id = result["session_id"]
```

### Using MCP Client Directly

```python
from database_mcp.client import DatabaseMCPClient, MCPClientContext

async with MCPClientContext() as client:
    # Create session workflow
    session = await client.create_session_workflow(
        user_id="user123",
        user_prompt="Build payment system",
        project_name="E-commerce"
    )

    # Get complete session context
    context = await client.get_session_with_context(session["session_id"])

    # Access all data
    session_data = context["context"]["session"]
    requirements = context["context"]["requirements"]
    test_cases = context["context"]["test_cases"]
```

## 🔧 Available Tools

The MCP Toolbox provides these Google ADK function tools:

### Session Management

- `create_mcp_session` - Create new agent session
- `get_mcp_session` - Retrieve session details
- `get_mcp_session_context` - Get complete session with all related data

### Requirements Management

- `store_mcp_requirement` - Store requirement analysis
- `get_mcp_requirements` - Retrieve requirements for session
- `update_mcp_requirement` - Update existing requirement

### Test Case Management

- `create_mcp_test_cases` - Store structured test cases from JSON
- `get_mcp_test_cases` - Retrieve test cases for session
- `create_single_mcp_test_case` - Store individual test case

### Analysis Tools

- `store_mcp_analysis` - Store agent analysis content
- `get_mcp_session_history` - Get session activity history

## 🌐 Cloud Deployment

### Deploy to Google Cloud

```bash
# Deploy everything to Google Cloud
python deploy.py all

# Deploy individual components
python deploy.py database    # Setup Cloud SQL database
python deploy.py server      # Deploy MCP server to Cloud Run
python deploy.py agent       # Deploy enhanced agent
```

### Environment Variables

Set these environment variables for cloud deployment:

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_REGION="us-central1"
export DATABASE_INSTANCE="mcp-database"
export MCP_SERVER_URL="https://your-mcp-server.run.app"
```

### Cloud SQL Configuration

The deployment script automatically:

- Creates Cloud SQL PostgreSQL instance
- Applies database schema
- Configures network access
- Sets up connection pooling

## 📋 Test Case Format

Test cases are stored in a structured JSON format:

```json
{
  "test_suite": {
    "name": "Authentication Test Suite",
    "description": "Test cases for user authentication",
    "total_tests": 1,
    "generated_date": "2024-01-15",
    "test_cases": [
      {
        "test_id": "TC_AUTH_001",
        "priority": "CRITICAL",
        "type": "Security",
        "summary": "Test OAuth2 login flow",
        "preconditions": [
          "OAuth2 server is running",
          "Client application is registered"
        ],
        "test_steps": [
          "Navigate to login page",
          "Click OAuth2 login",
          "Complete authorization",
          "Verify access token"
        ],
        "test_data": {
          "client_id": "test_client_123",
          "redirect_uri": "https://app.example.com/callback"
        },
        "expected_result": "User successfully authenticated",
        "requirement_traceability": "REQ_AUTH_001"
      }
    ]
  }
}
```

## 🔍 Monitoring and Debugging

### Check MCP Server Status

```bash
# Check if MCP server is running
curl http://localhost:8000/health

# View server logs
python deploy.py logs
```

### Test Database Connection

```python
from database_mcp.client import DatabaseMCPClient

async def test_connection():
    client = DatabaseMCPClient()
    result = await client.test_connection()
    print(f"Connection: {'✅ OK' if result else '❌ Failed'}")
```

### Validate Test Suite Format

```python
from database_mcp.client import DatabaseMCPClient

# Test suite validation
client = DatabaseMCPClient()
is_valid = client.validate_test_suite_format(test_suite_json)
```

## 🔐 Security Considerations

- **Database Access**: Use connection pooling and prepared statements
- **Authentication**: Implement proper authentication for MCP server
- **Network Security**: Use VPC for cloud deployment
- **Data Encryption**: Enable encryption at rest and in transit
- **Access Control**: Implement role-based access control

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**

   ```bash
   pip install mcp mcp-server-postgres asyncpg
   ```

2. **Database Connection Failed**

   - Check database credentials in `server.py`
   - Verify database is running
   - Check network connectivity

3. **MCP Server Not Starting**

   ```bash
   # Check if port is in use
   lsof -i :8000

   # Start with debug logging
   python -m database_mcp.server --debug
   ```

4. **Test Cases Not Storing**
   - Validate JSON format
   - Check database schema is applied
   - Verify session exists

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Additional Resources

- **Google MCP Documentation**: https://github.com/modelcontextprotocol
- **Google ADK Documentation**: https://cloud.google.com/agent-builder
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **Cloud SQL Documentation**: https://cloud.google.com/sql/docs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Ready to build persistent, intelligent agents with Google's MCP Toolbox!** 🚀
