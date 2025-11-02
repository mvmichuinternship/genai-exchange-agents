-- COMPREHENSIVE ALTER TABLE script to align test_cases table with JSON test case format
-- This script modifies the table to perfectly match the provided JSON structure

-- Step 1: Add ALL missing columns from JSON format that don't exist in schema
-- JSON has: test_id, priority, type, summary, preconditions, test_steps, test_data, expected_result, requirement_traceability
-- Schema has: id, session_id, test_name, test_description, test_steps, expected_results, test_type, priority, status, test_data, preconditions, postconditions, estimated_duration, automation_feasible, tags, created_at, updated_at
-- MISSING: test_id, summary, expected_result (schema has expected_results), requirement_traceability

ALTER TABLE test_cases
ADD COLUMN IF NOT EXISTS test_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS summary TEXT,
ADD COLUMN IF NOT EXISTS expected_result TEXT,
ADD COLUMN IF NOT EXISTS requirement_traceability TEXT;

-- Step 2: Modify existing columns to match JSON format exactly

-- Rename test_name to align with JSON test_id (we'll keep both for compatibility)
-- The test_id will be the primary identifier from JSON

-- Modify priority column to handle JSON format values (LOW, MEDIUM, HIGH, CRITICAL)
ALTER TABLE test_cases
DROP CONSTRAINT IF EXISTS chk_priority;

ALTER TABLE test_cases
ADD CONSTRAINT chk_priority_json_format
CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'low', 'medium', 'high', 'critical'));

-- Modify test_type to handle JSON format values (Security, Functional, etc.)
ALTER TABLE test_cases
DROP CONSTRAINT IF EXISTS chk_test_type;

ALTER TABLE test_cases
ADD CONSTRAINT chk_test_type_json_format
CHECK (test_type IN ('Security', 'Functional', 'Performance', 'Integration', 'Edge', 'Negative', 'Generated', 'security', 'functional', 'performance', 'integration', 'edge', 'negative', 'generated'));

-- Step 3: Modify existing columns to better match JSON structure

-- Ensure preconditions can handle JSON array format
-- (already TEXT, which can store JSON arrays as strings)

-- Ensure test_steps is JSONB (already correct)
-- Ensure test_data is JSONB (already correct)

-- Step 4: Create indexes for performance on new and modified columns
CREATE INDEX IF NOT EXISTS idx_test_cases_test_id ON test_cases(test_id);
CREATE INDEX IF NOT EXISTS idx_test_cases_summary ON test_cases(summary);
CREATE INDEX IF NOT EXISTS idx_test_cases_expected_result ON test_cases(expected_result);
CREATE INDEX IF NOT EXISTS idx_test_cases_traceability ON test_cases(requirement_traceability);
CREATE INDEX IF NOT EXISTS idx_test_cases_priority_json ON test_cases(priority);
CREATE INDEX IF NOT EXISTS idx_test_cases_type_json ON test_cases(test_type);

-- Step 5: Add unique constraint on test_id to ensure it's unique across sessions
CREATE UNIQUE INDEX IF NOT EXISTS idx_test_cases_test_id_unique ON test_cases(test_id, session_id);

-- Step 6: Update existing data to align with new format (if any exists)

-- Set test_id from existing id if test_id is null
UPDATE test_cases
SET test_id = id
WHERE test_id IS NULL;

-- Set summary from test_name if summary is null
UPDATE test_cases
SET summary = test_name
WHERE summary IS NULL AND test_name IS NOT NULL;

-- Normalize priority values to uppercase to match JSON format
UPDATE test_cases
SET priority = UPPER(priority)
WHERE priority IN ('low', 'medium', 'high', 'critical');

-- Normalize test_type values to proper case to match JSON format
UPDATE test_cases
SET test_type = INITCAP(test_type)
WHERE test_type IN ('security', 'functional', 'performance', 'integration', 'edge', 'negative', 'generated');

-- Step 7: Add comprehensive comments to document the JSON-aligned schema
COMMENT ON COLUMN test_cases.test_id IS 'Primary test case identifier from JSON format (e.g., TC_SEC_018)';
COMMENT ON COLUMN test_cases.summary IS 'Brief summary of the test case from JSON format';
COMMENT ON COLUMN test_cases.priority IS 'Priority level: LOW, MEDIUM, HIGH, CRITICAL (matching JSON format)';
COMMENT ON COLUMN test_cases.test_type IS 'Test type: Security, Functional, Performance, etc. (matching JSON format)';
COMMENT ON COLUMN test_cases.preconditions IS 'Array of preconditions stored as TEXT (from JSON preconditions array)';
COMMENT ON COLUMN test_cases.test_steps IS 'Array of test steps stored as JSONB (from JSON test_steps array)';
COMMENT ON COLUMN test_cases.test_data IS 'Test data object stored as JSONB (from JSON test_data object)';
COMMENT ON COLUMN test_cases.expected_result IS 'Expected result description (from JSON expected_result field)';
COMMENT ON COLUMN test_cases.expected_results IS 'Legacy expected results field (use expected_result for new JSON format)';
COMMENT ON COLUMN test_cases.requirement_traceability IS 'Requirement traceability information (from JSON requirement_traceability)';

-- Step 8: Add additional constraints for data integrity (only if test_id is not null)
-- Note: Removing the NOT NULL constraint since test_id should be optional initially
-- ALTER TABLE test_cases
-- ADD CONSTRAINT IF NOT EXISTS chk_test_id_format
-- CHECK (test_id IS NOT NULL AND LENGTH(test_id) > 0);

-- Step 9: Create a view for JSON-format compatibility
CREATE OR REPLACE VIEW test_cases_json_view AS
SELECT
    test_id,
    priority,
    test_type as type,
    summary,
    preconditions,
    test_steps,
    test_data,
    expected_results as expected_result,
    requirement_traceability,
    session_id,
    created_at,
    updated_at
FROM test_cases
WHERE test_id IS NOT NULL;

COMMENT ON VIEW test_cases_json_view IS 'View providing JSON-format compatible structure for test cases';