import os
import json
import glob
from db import get_connection

def parse_allure_results(results_dir):
    """Scans the allure-results directory and parses all *-result.json files."""
    results = {}
    json_files = glob.glob(os.path.join(results_dir, "*-result.json"))
    
    print(f"🔍 Found {len(json_files)} Allure JSON files in {results_dir}")
    
    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            scenario_name = data.get('name', 'Unknown Scenario')
            status = data.get('status', 'unknown').upper()
            
            # Extract Feature and Tags from Allure Labels
            feature_name = "Unknown Feature"
            tags = []
            for label in data.get('labels', []):
                if label.get('name') == 'feature':
                    feature_name = label.get('value')
                elif label.get('name') == 'tag':
                    tags.append(label.get('value'))
                    
            # Extract error details if failed
            error_msg = None
            stack_trace = None
            if status != 'PASSED' and 'statusDetails' in data:
                error_msg = data['statusDetails'].get('message')
                stack_trace = data['statusDetails'].get('trace')
                
            # Group by scenario to handle retries (Two-Pass Execution)
            # If a scenario runs twice, we will append it to a list for that scenario
            unique_key = f"{feature_name}::{scenario_name}"
            if unique_key not in results:
                results[unique_key] = {
                    'feature': feature_name,
                    'scenario': scenario_name,
                    'tags': tags,
                    'attempts': []
                }
                
            results[unique_key]['attempts'].append({
                'status': status,
                'duration': data.get('stop', 0) - data.get('start', 0),
                'error': error_msg,
                'trace': stack_trace
            })
            
    return results

def determine_final_status(attempts):
    """
    Calculates ENPL retry logic:
    If any attempt PASSED, and there was a FAILURE -> FLAKY
    If all attempts FAILED -> FAILED
    If all attempts PASSED -> PASSED
    """
    statuses = [a['status'] for a in attempts]
    if 'PASSED' in statuses and ('FAILED' in statuses or 'BROKEN' in statuses):
        return 'FLAKY'
    elif 'PASSED' in statuses:
        return 'PASSED'
    else:
        return 'FAILED' # Fallback for consistent failures

def ingest_data():
    results_dir = os.getenv("ALLURE_RESULTS_DIR")
    if not results_dir or not os.path.exists(results_dir):
        print("❌ ALLURE_RESULTS_DIR is invalid. Please check your .env file.")
        return

    scenarios = parse_allure_results(results_dir)
    if not scenarios:
        print("⚠️ No test data found to ingest.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Create a new Test Run (Mocking the env-info.txt for local MVP)
        cursor.execute("""
            INSERT INTO test_runs (github_run_id, environment, test_suite, is_dry_run)
            VALUES (%s, %s, %s, %s) RETURNING run_id;
        """, ("local-dev-run-001", "SIT", "Regression Testing", True))
        run_id = cursor.fetchone()[0]
        
        total_tests = len(scenarios)
        passed_count = failed_count = flaky_count = 0

        # 2. Iterate through scenarios and insert data
        for key, data in scenarios.items():
            final_status = determine_final_status(data['attempts'])
            
            # Update counts for the run table
            if final_status == 'PASSED': passed_count += 1
            elif final_status == 'FLAKY': flaky_count += 1
            else: failed_count += 1

            # Insert or fetch Test Case (Static Dictionary)
            cursor.execute("""
                INSERT INTO test_cases (module, feature_file, scenario_name, tags)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (feature_file, scenario_name) 
                DO UPDATE SET tags = EXCLUDED.tags
                RETURNING case_id;
            """, ("UI", data['feature'], data['scenario'], data['tags']))
            case_id = cursor.fetchone()[0]

            # Insert Test Result (The outcome for this specific run)
            last_attempt = data['attempts'][-1]
            cursor.execute("""
                INSERT INTO test_results (run_id, case_id, final_status, duration_ms, error_message, stack_trace)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING result_id;
            """, (run_id, case_id, final_status, last_attempt['duration'], last_attempt['error'], last_attempt['trace']))
            result_id = cursor.fetchone()[0]

            # Insert Retry History (Pass 1 vs Pass 2 details)
            for i, attempt in enumerate(data['attempts']):
                cursor.execute("""
                    INSERT INTO retry_history (result_id, attempt_number, status, duration_ms, error_message)
                    VALUES (%s, %s, %s, %s, %s);
                """, (result_id, i + 1, attempt['status'], attempt['duration'], attempt['error']))

        # Update the test run totals
        cursor.execute("""
            UPDATE test_runs SET total_tests=%s, passed_tests=%s, failed_tests=%s, flaky_tests=%s
            WHERE run_id=%s;
        """, (total_tests, passed_count, failed_count, flaky_count, run_id))

        conn.commit()
        print(f"✅ Successfully ingested {total_tests} scenarios into the database (Run ID: {run_id}).")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during ingestion: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("🚀 Starting Allure JSON Database Ingestion...")
    ingest_data()
