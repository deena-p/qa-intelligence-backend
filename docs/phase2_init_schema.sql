

-- =================================================================================
-- ENPL QA Intelligence Platform - Phase 2 Database Schema
-- Database: PostgreSQL
-- Purpose: Normalize Allure JSON results for fast, deterministic LLM MCP querying
-- =================================================================================

-- 1. TEST RUNS TABLE
-- Captures the high-level metadata of a single GitHub Actions pipeline execution.
-- Data maps to your 'env-info-*.txt' files (SIT/UAT, Smoke/Regression).
CREATE TABLE test_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_run_id VARCHAR(255) NOT NULL,       -- e.g., "23992879054"
    environment VARCHAR(50) NOT NULL,          -- 'SIT' or 'UAT'
    test_suite VARCHAR(100) NOT NULL,          -- 'Regression Testing' or 'Smoke Testing'
    is_dry_run BOOLEAN DEFAULT FALSE,          -- True if triggered by dev-workflow.yml
    execution_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_tests INTEGER DEFAULT 0,
    passed_tests INTEGER DEFAULT 0,
    failed_tests INTEGER DEFAULT 0,
    flaky_tests INTEGER DEFAULT 0,
    duration_ms BIGINT
);

-- Index for fast lookup of recent nightly runs
CREATE INDEX idx_test_runs_env_date ON test_runs(environment, execution_date DESC);

-- 2. TEST CASES TABLE
-- A static dictionary of your Cucumber scenarios. This prevents data duplication.
CREATE TABLE test_cases (
    case_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module VARCHAR(100) NOT NULL,              -- 'UI' or 'API'
    feature_file VARCHAR(500) NOT NULL,        -- e.g., 'DemandManagement/CreateDemand.feature'
    scenario_name VARCHAR(500) NOT NULL,       -- The actual text of the Gherkin scenario
    tags TEXT[],                               -- Array of tags: {'@CreateDemand1', '@smoke'}
    
    -- Ensure we don't insert the same scenario twice
    CONSTRAINT uq_feature_scenario UNIQUE (feature_file, scenario_name)
);

-- Index for fast tag-based querying (e.g., "What is the pass rate of @CreateDemand1?")
CREATE INDEX idx_test_cases_tags ON test_cases USING GIN (tags);

-- 3. TEST RESULTS TABLE
-- The outcome of a specific Test Case during a specific Test Run.
-- The 'final_status' determines if the test ultimately passed, failed, or was flaky.
CREATE TABLE test_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES test_runs(run_id) ON DELETE CASCADE,
    case_id UUID REFERENCES test_cases(case_id) ON DELETE CASCADE,
    final_status VARCHAR(50) NOT NULL,         -- 'PASSED', 'FAILED', 'BROKEN', 'SKIPPED', 'FLAKY'
    duration_ms BIGINT,
    error_message TEXT,                        -- Only populated if final_status != 'PASSED'
    stack_trace TEXT,
    
    -- A test case only runs once per pipeline run
    CONSTRAINT uq_run_case UNIQUE (run_id, case_id)
);

-- Index for filtering failures quickly
CREATE INDEX idx_test_results_status ON test_results(final_status);

-- 4. RETRY HISTORY TABLE
-- Specifically designed for your 2-Pass Execution Strategy (UiRunnerTest vs FailedUiRunnerTest).
-- Tracks every attempt made for a single result.
CREATE TABLE retry_history (
    retry_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    result_id UUID REFERENCES test_results(result_id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,           -- 1 (Main Runner), 2 (Retry Runner)
    status VARCHAR(50) NOT NULL,               -- 'PASSED', 'FAILED', 'BROKEN'
    duration_ms BIGINT,
    error_message TEXT,
    
    CONSTRAINT uq_result_attempt UNIQUE (result_id, attempt_number)
);

-- =================================================================================
-- ENPL QA Intelligence Platform - Deterministic Views for the MCP Server
-- =================================================================================

-- View: Tag Intelligence
-- The MCP Server will query this view to instantly answer: "How stable is @tag?"
CREATE OR REPLACE VIEW vw_tag_intelligence AS
SELECT 
    t.tag,
    COUNT(tr.result_id) AS total_executions,
    SUM(CASE WHEN tr.final_status = 'PASSED' THEN 1 ELSE 0 END) AS passed_count,
    SUM(CASE WHEN tr.final_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_count,
    SUM(CASE WHEN tr.final_status = 'FLAKY' THEN 1 ELSE 0 END) AS flaky_count,
    ROUND(
        (SUM(CASE WHEN tr.final_status = 'PASSED' THEN 1 ELSE 0 END)::NUMERIC / COUNT(tr.result_id)) * 100, 
        2
    ) AS pass_rate_percentage
FROM 
    test_cases tc
JOIN 
    test_results tr ON tc.case_id = tr.case_id
CROSS JOIN 
    UNNEST(tc.tags) AS t(tag)
GROUP BY 
    t.tag;