# Google GenAI MCP Toolbox for ADK Agents

This implementation uses **Google's official GenAI Toolbox** (https://github.com/googleapis/genai-toolbox) as an MCP server for database operations with ADK agents. This approach leverages Google's maintained MCP server written in Go, providing robust database connectivity and tool management.

## 🎯 Overview

This implementation provides:

- **Official Google MCP Toolbox**: Uses the maintained Go-based MCP server
- **Gemini CLI Extension**: Integrates with Gemini CLI for easy development
- **Database Tools**: Pre-built tools for PostgreSQL/Cloud SQL operations
- **ADK Integration**: Custom toolbox client for Google ADK agents
- **Session Management**: Persistent storage for agent workflows
- **Test Case Storage**: Structured JSON format for test case persistence

## 🏗️ Architecture

```
ADK Agent → Toolbox Client → MCP Toolbox (Go) → PostgreSQL/Cloud SQL
                                    ↓
                            tools.yaml (Configuration)
```

### Components

1. **MCP Toolbox Server** (Go binary from Google)
2. **tools.yaml** - Configuration file defining database sources and tools
3. **Toolbox Client** - Python client for ADK agents using toolbox-core SDK
4. **Database Schema** - PostgreSQL schema for sessions, requirements, test cases
5. **ADK Tools** - Function tools that wrap the toolbox client

## 📋 Database Schema

Using the exact schema you specified:

```sql
-- Core session management
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    user_prompt TEXT NOT NULL,
    project_name TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Requirements storage
CREATE TABLE requirements (
    requirement_id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(session_id),
    content TEXT NOT NULL,
    requirement_type TEXT,
    priority TEXT DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Test cases with structured JSON
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

## 🚀 Quick Start

### 1. Install Google's MCP Toolbox

```bash
# Install the Toolbox binary
# For macOS Apple Silicon
curl -L -o toolbox https://github.com/googleapis/genai-toolbox/releases/latest/download/toolbox-darwin-arm64
chmod +x toolbox
sudo mv toolbox /usr/local/bin/

# For Linux AMD64
curl -L -o toolbox https://github.com/googleapis/genai-toolbox/releases/latest/download/toolbox-linux-amd64
chmod +x toolbox
sudo mv toolbox /usr/local/bin/

# Verify installation
toolbox --version
```

### 2. Install Python Dependencies

```bash
pip install toolbox-core google-adk asyncpg
```

### 3. Setup Database

```bash
# Create PostgreSQL database
createdb testgendb

# Apply schema
psql testgendb < schema.sql
```

### 4. Configure tools.yaml

```bash
# Copy and edit the configuration
cp tools.yaml.example tools.yaml
# Edit database connection details
```

### 5. Start MCP Toolbox Server

```bash
# Start the server
toolbox --tools-file "tools.yaml"
```

### 6. Test with ADK Agents

```bash
python test_adk_integration.py
```

## 📁 Project Structure

```
google_genai_mcp_toolbox/
├── README.md                 # This file
├── schema.sql               # Database schema
├── tools.yaml.example       # MCP Toolbox configuration template
├── setup.sh                # Installation script
├── requirements.txt         # Python dependencies
├── adk_toolbox/
│   ├── __init__.py
│   ├── client.py           # Toolbox client wrapper
│   ├── tools.py            # ADK function tools
│   └── models.py           # Data models
├── examples/
│   ├── enhanced_decider_agent.py  # Example agent integration
│   ├── test_adk_integration.py    # Test integration
│   └── session_workflow.py       # Session management example
└── deployment/
    ├── deploy_cloud_sql.sh       # Cloud SQL setup
    └── deploy_cloud_run.sh       # Cloud Run deployment
```

## ⚙️ Configuration

### tools.yaml Configuration

The `tools.yaml` file defines your database sources and available tools:

```yaml
# Database sources
sources:
  postgres-main:
    kind: postgres
    host: localhost # or Cloud SQL connection name
    port: 5432
    database: testgendb
    user: your_user
    password: your_password
    # For Cloud SQL:
    # connection_name: project:region:instance

# Available tools
tools:
  # Session management
  create-session:
    kind: postgres-sql
    source: postgres-main
    description: Create a new agent session
    parameters:
      - name: user_id
        type: string
        description: User identifier
      - name: user_prompt
        type: string
        description: Initial user prompt
      - name: project_name
        type: string
        description: Project name (optional)
    statement: |
      INSERT INTO sessions (session_id, user_id, user_prompt, project_name)
      VALUES (gen_random_uuid(), $1, $2, $3)
      RETURNING session_id, created_at;

  get-session:
    kind: postgres-sql
    source: postgres-main
    description: Retrieve session details
    parameters:
      - name: session_id
        type: string
        description: Session UUID
    statement: |
      SELECT * FROM sessions WHERE session_id = $1::uuid;

  # Requirements management
  store-requirement:
    kind: postgres-sql
    source: postgres-main
    description: Store a requirement for a session
    parameters:
      - name: session_id
        type: string
        description: Session UUID
      - name: content
        type: string
        description: Requirement content
      - name: requirement_type
        type: string
        description: Type of requirement
      - name: priority
        type: string
        description: Priority level
    statement: |
      INSERT INTO requirements (requirement_id, session_id, content, requirement_type, priority)
      VALUES (gen_random_uuid(), $1::uuid, $2, $3, $4)
      RETURNING requirement_id, created_at;

  get-requirements:
    kind: postgres-sql
    source: postgres-main
    description: Get all requirements for a session
    parameters:
      - name: session_id
        type: string
        description: Session UUID
    statement: |
      SELECT * FROM requirements WHERE session_id = $1::uuid ORDER BY created_at;

  # Test case management
  store-test-case:
    kind: postgres-sql
    source: postgres-main
    description: Store a test case with structured JSON content
    parameters:
      - name: session_id
        type: string
        description: Session UUID
      - name: test_id
        type: string
        description: Test case identifier
      - name: summary
        type: string
        description: Test case summary
      - name: priority
        type: string
        description: Test priority
      - name: test_type
        type: string
        description: Test type
      - name: test_content
        type: string
        description: JSON content of the test case
    statement: |
      INSERT INTO test_cases (test_case_id, session_id, test_id, summary, priority, test_type, test_content)
      VALUES (gen_random_uuid(), $1::uuid, $2, $3, $4, $5, $6::jsonb)
      RETURNING test_case_id, created_at;

  get-test-cases:
    kind: postgres-sql
    source: postgres-main
    description: Get all test cases for a session
    parameters:
      - name: session_id
        type: string
        description: Session UUID
    statement: |
      SELECT * FROM test_cases WHERE session_id = $1::uuid ORDER BY created_at;

  # Session context (complete workflow data)
  get-session-context:
    kind: postgres-sql
    source: postgres-main
    description: Get complete session with requirements and test cases
    parameters:
      - name: session_id
        type: string
        description: Session UUID
    statement: |
      SELECT
        s.*,
        COALESCE(
          json_agg(
            json_build_object(
              'requirement_id', r.requirement_id,
              'content', r.content,
              'requirement_type', r.requirement_type,
              'priority', r.priority,
              'created_at', r.created_at
            )
          ) FILTER (WHERE r.requirement_id IS NOT NULL),
          '[]'::json
        ) as requirements,
        COALESCE(
          json_agg(
            json_build_object(
              'test_case_id', tc.test_case_id,
              'test_id', tc.test_id,
              'summary', tc.summary,
              'priority', tc.priority,
              'test_type', tc.test_type,
              'test_content', tc.test_content,
              'created_at', tc.created_at
            )
          ) FILTER (WHERE tc.test_case_id IS NOT NULL),
          '[]'::json
        ) as test_cases
      FROM sessions s
      LEFT JOIN requirements r ON s.session_id = r.session_id
      LEFT JOIN test_cases tc ON s.session_id = tc.session_id
      WHERE s.session_id = $1::uuid
      GROUP BY s.session_id;

# Tool groups
toolsets:
  session-management:
    - create-session
    - get-session
    - get-session-context

  requirements-tools:
    - store-requirement
    - get-requirements

  test-case-tools:
    - store-test-case
    - get-test-cases

  complete-workflow:
    - create-session
    - get-session
    - store-requirement
    - get-requirements
    - store-test-case
    - get-test-cases
    - get-session-context
```

## 🛠️ Usage Examples

### Basic ADK Agent Integration

```python
from adk_toolbox.client import ToolboxClient
from adk_toolbox.tools import create_adk_toolbox_tools

# Create toolbox client
client = ToolboxClient("http://localhost:5000")

# Load tools for ADK agent
tools = create_adk_toolbox_tools(client)

# Use in your ADK agent
from google.adk.agents import Agent

agent = Agent(
    name="persistent_agent",
    tools=tools,
    instructions="You can now store and retrieve session data persistently."
)
```

### Session Workflow

```python
from adk_toolbox.client import ToolboxClient

async def agent_workflow():
    client = ToolboxClient("http://localhost:5000")

    # Create session
    session = await client.invoke_tool("create-session", {
        "user_id": "user123",
        "user_prompt": "Create authentication system",
        "project_name": "Security Project"
    })
    session_id = session[0]["session_id"]

    # Store requirements
    await client.invoke_tool("store-requirement", {
        "session_id": session_id,
        "content": "System must support OAuth2 with PKCE",
        "requirement_type": "security",
        "priority": "high"
    })

    # Store test case
    test_content = {
        "test_id": "TC_AUTH_001",
        "priority": "CRITICAL",
        "type": "Security",
        "summary": "Test OAuth2 authorization flow",
        "preconditions": ["OAuth2 server running"],
        "test_steps": ["Navigate to login", "Complete auth flow"],
        "expected_result": "User authenticated successfully"
    }

    await client.invoke_tool("store-test-case", {
        "session_id": session_id,
        "test_id": "TC_AUTH_001",
        "summary": "Test OAuth2 authorization flow",
        "priority": "CRITICAL",
        "test_type": "Security",
        "test_content": json.dumps(test_content)
    })

    # Get complete context
    context = await client.invoke_tool("get-session-context", {
        "session_id": session_id
    })

    return context[0]
```

## 🌐 Cloud Deployment

### Deploy to Google Cloud

```bash
# Setup Cloud SQL
./deployment/deploy_cloud_sql.sh

# Deploy MCP Toolbox to Cloud Run
./deployment/deploy_cloud_run.sh

# Update tools.yaml for cloud configuration
# Point to Cloud SQL instance
```

### Environment Variables

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export CLOUD_SQL_INSTANCE="your-instance-connection-name"
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export TOOLBOX_SERVER_URL="http://localhost:5000"
```

## 🔧 Development with Gemini CLI

You can also use this with Gemini CLI extension for development:

```bash
# Install Gemini CLI extension
gemini extensions install https://github.com/gemini-cli-extensions/mcp-toolbox

# Ensure tools.yaml is in your current directory
# Start Gemini CLI
gemini

# Now you can interact with your database tools using natural language
```

## 📋 Test Case Format

Test cases are stored in the structured JSON format you specified:

```json
{
  "test_id": "TC_AUTH_001",
  "priority": "CRITICAL",
  "type": "Security",
  "summary": "Test OAuth2 authorization flow with PKCE",
  "preconditions": [
    "OAuth2 server is running",
    "Client application is registered",
    "PKCE is enabled"
  ],
  "test_steps": [
    "Navigate to login page",
    "Click 'Login with OAuth2'",
    "Verify PKCE challenge generation",
    "Complete authorization flow",
    "Verify access token received"
  ],
  "test_data": {
    "client_id": "test_client_123",
    "redirect_uri": "https://app.example.com/callback",
    "scope": "read write"
  },
  "expected_result": "User successfully authenticated with valid access token",
  "requirement_traceability": "REQ_AUTH_001 - OAuth2 PKCE Implementation"
}
```

## 🔍 Benefits of Google's GenAI Toolbox Approach

1. **Official Google Implementation**: Maintained by Google, ensuring compatibility and updates
2. **Performance**: Go-based server provides excellent performance and low latency
3. **Reliability**: Production-ready with proper error handling and connection management
4. **Flexibility**: YAML-based configuration allows easy tool definition and modification
5. **Scalability**: Built for enterprise workloads with connection pooling and optimization
6. **Integration**: Works seamlessly with Gemini CLI and other Google AI tools
7. **Security**: Built-in authentication and secure database connection handling

## 🐛 Troubleshooting

### Common Issues

1. **Toolbox binary not found**

   ```bash
   # Ensure correct binary for your OS/architecture
   toolbox --version
   ```

2. **Database connection failed**

   ```bash
   # Test database connection
   psql -h localhost -U your_user -d testgendb -c "SELECT 1;"
   ```

3. **Tools not loading**

   ```bash
   # Validate tools.yaml syntax
   toolbox --tools-file "tools.yaml" --validate
   ```

4. **ADK integration issues**
   ```bash
   # Test toolbox client
   python -c "from adk_toolbox.client import ToolboxClient; print('OK')"
   ```

## 📚 Additional Resources

- **Google GenAI Toolbox**: https://github.com/googleapis/genai-toolbox
- **Toolbox Documentation**: https://googleapis.github.io/genai-toolbox/
- **Gemini CLI Extensions**: https://github.com/gemini-cli-extensions
- **Google ADK**: https://cloud.google.com/agent-builder
- **Cloud SQL**: https://cloud.google.com/sql

---

**Ready to build persistent ADK agents with Google's official GenAI Toolbox!** 🚀
