-- Complete database schema for Test Case Generator using Google MCP Toolbox


-- Drop tables if they exist (in correct order due to foreign keys)
DROP TABLE IF EXISTS test_case_requirements CASCADE;
DROP TABLE IF EXISTS test_cases CASCADE;
DROP TABLE IF EXISTS requirements CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS users CASCADE;


-- Sessions table - Core session management
CREATE TABLE sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    project_name VARCHAR(255),
    user_prompt TEXT,
    status VARCHAR(50) DEFAULT 'created',
    rag_context_loaded INTEGER DEFAULT 0,
    rag_enabled BOOLEAN DEFAULT true,
    agent_used VARCHAR(100) DEFAULT 'sequential_workflow',
    workflow_type VARCHAR(50) DEFAULT 'full',
    mcp_session_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);


-- Requirements table - All types of requirements
CREATE TABLE requirements (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES sessions(session_id) ON DELETE CASCADE,
    original_content TEXT NOT NULL,
    edited_content TEXT,
    requirement_type VARCHAR(50) DEFAULT 'functional',
    priority VARCHAR(10) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'active',
    version INTEGER DEFAULT 1,
    source VARCHAR(20) DEFAULT 'agent_generated', -- 'agent_generated', 'user_created', 'rag_context'
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    mcp_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);


-- Test cases table - Generated and manual test cases with MCP support
CREATE TABLE test_cases (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES sessions(session_id) ON DELETE CASCADE,
    test_name VARCHAR(255) NOT NULL,
    test_description TEXT,
    test_steps JSONB,
    expected_results TEXT,
    test_type VARCHAR(50) DEFAULT 'functional',
    priority VARCHAR(10) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'active',
    test_data JSONB DEFAULT '{}',
    preconditions TEXT,
    postconditions TEXT,
    estimated_duration INTEGER DEFAULT 30, -- minutes
    automation_feasible BOOLEAN DEFAULT true,
    tags JSONB DEFAULT '[]',

    -- Additional fields for structured test case format
    test_suite_name VARCHAR(255),
    test_suite_description TEXT,
    test_id VARCHAR(50), -- TC_TYPE_NNN format
    summary TEXT,
    requirement_traceability VARCHAR(255),

    -- MCP specific fields
    mcp_generated BOOLEAN DEFAULT false,
    mcp_metadata JSONB DEFAULT '{}',
    mcp_version VARCHAR(50),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);


-- Test case to requirements mapping - Many-to-many relationship
CREATE TABLE test_case_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_case_id VARCHAR(255) REFERENCES test_cases(id) ON DELETE CASCADE,
    requirement_id VARCHAR(255) REFERENCES requirements(id) ON DELETE CASCADE,
    coverage_type VARCHAR(50) DEFAULT 'direct',
    confidence_score DECIMAL(3,2) DEFAULT 1.0,
    mcp_traced BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(test_case_id, requirement_id)
);


-- Projects table - For organizing sessions by project
CREATE TABLE projects (
    project_id VARCHAR(255) PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_user_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    mcp_config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);


-- Users table - Basic user management
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'tester',
    is_active BOOLEAN DEFAULT true,
    mcp_permissions JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);


-- MCP specific tables for protocol management
CREATE TABLE mcp_sessions (
    mcp_session_id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES sessions(session_id) ON DELETE CASCADE,
    client_info JSONB DEFAULT '{}',
    server_info JSONB DEFAULT '{}',
    protocol_version VARCHAR(50) DEFAULT '1.0.0',
    connection_status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP DEFAULT NOW()
);


CREATE TABLE mcp_operations (
    operation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mcp_session_id VARCHAR(255) REFERENCES mcp_sessions(mcp_session_id) ON DELETE CASCADE,
    operation_type VARCHAR(50) NOT NULL, -- 'query', 'insert', 'update', 'delete'
    table_name VARCHAR(100),
    operation_data JSONB,
    result_data JSONB,
    status VARCHAR(20) DEFAULT 'completed',
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);


-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_mcp_data ON sessions USING GIN(mcp_session_data);

CREATE INDEX IF NOT EXISTS idx_requirements_session ON requirements(session_id);
CREATE INDEX IF NOT EXISTS idx_requirements_type ON requirements(requirement_type);
CREATE INDEX IF NOT EXISTS idx_requirements_status ON requirements(status);
CREATE INDEX IF NOT EXISTS idx_requirements_mcp_meta ON requirements USING GIN(mcp_metadata);

CREATE INDEX IF NOT EXISTS idx_test_cases_session ON test_cases(session_id);
CREATE INDEX IF NOT EXISTS idx_test_cases_type ON test_cases(test_type);
CREATE INDEX IF NOT EXISTS idx_test_cases_status ON test_cases(status);
CREATE INDEX IF NOT EXISTS idx_test_cases_mcp_generated ON test_cases(mcp_generated);
CREATE INDEX IF NOT EXISTS idx_test_cases_mcp_meta ON test_cases USING GIN(mcp_metadata);

CREATE INDEX IF NOT EXISTS idx_tcr_test_case ON test_case_requirements(test_case_id);
CREATE INDEX IF NOT EXISTS idx_tcr_requirement ON test_case_requirements(requirement_id);
CREATE INDEX IF NOT EXISTS idx_tcr_mcp_traced ON test_case_requirements(mcp_traced);

CREATE INDEX IF NOT EXISTS idx_mcp_sessions_session ON mcp_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_mcp_sessions_status ON mcp_sessions(connection_status);
CREATE INDEX IF NOT EXISTS idx_mcp_sessions_activity ON mcp_sessions(last_activity);

CREATE INDEX IF NOT EXISTS idx_mcp_operations_session ON mcp_operations(mcp_session_id);
CREATE INDEX IF NOT EXISTS idx_mcp_operations_type ON mcp_operations(operation_type);
CREATE INDEX IF NOT EXISTS idx_mcp_operations_created ON mcp_operations(created_at);