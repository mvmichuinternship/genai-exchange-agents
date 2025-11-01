# MCP Toolbox Server

This MCP toolbox server provides Cloud SQL and Redis integration capabilities for Google ADK agents. It enables agents to persist session data, requirements, and test cases to a PostgreSQL database while using Redis for caching and session management.

## Features

### Cloud SQL Integration

- Session management with PostgreSQL database
- Requirements storage and retrieval
- Test cases storage with structured JSON format
- Database schema management
- Connection pooling and async operations

### Redis Integration

- Session caching for fast access
- Temporary data storage
- Cache invalidation strategies
- Pub/Sub capabilities for agent coordination

## Database Schema

The server uses the following database schema for test case management:

### Core Tables

- `sessions` - Core session management
- `requirements` - All types of requirements
- `test_cases` - Generated and manual test cases
- `test_case_requirements` - Many-to-many relationship mapping
- `projects` - For organizing sessions by project
- `users` - Basic user management

### Test Case Structure

Test cases are stored with the following JSON structure:

```json
{
  "test_suite": {
    "name": "Suite Name",
    "description": "Brief description",
    "total_tests": 0,
    "generated_date": "2025-10-26",
    "test_cases": [
      {
        "test_id": "TC_TYPE_NNN",
        "priority": "CRITICAL|HIGH|MEDIUM|LOW",
        "type": "Functional|Security|Edge Case|Negative",
        "summary": "One-line summary",
        "preconditions": ["condition 1", "condition 2"],
        "test_steps": ["step 1", "step 2", "step 3"],
        "test_data": {
          "field1": "value1",
          "field2": "value2"
        },
        "expected_result": "Clear expected outcome",
        "requirement_traceability": "REQ_ID - description"
      }
    ]
  }
}
```

## Setup

1. Install dependencies:

```bash
poetry install
```

2. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your database and Redis configurations
```

3. Initialize the database:

```bash
poetry run python -m mcp_tools.database.init_db
```

## Usage

The MCP toolbox provides tools that can be integrated with Google ADK agents for:

- Creating and managing sessions
- Storing and retrieving requirements
- Persisting test cases with structured format
- Caching session data in Redis
- Database operations with connection pooling

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `GOOGLE_CLOUD_PROJECT` - Google Cloud project ID
- `CLOUD_SQL_INSTANCE` - Cloud SQL instance connection name
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password
- `DB_NAME` - Database name
