from mcp.server.fastmcp import FastMCP
import psycopg2
import os
from dotenv import load_dotenv

# Load database credentials from the .env file you created earlier
load_dotenv()

# Initialize the MCP Server
mcp = FastMCP("ENPL QA Intelligence")

def get_db_connection():
    """Helper method to establish database connection."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "qa_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres")
    )

@mcp.tool()
def get_execution_summary() -> str:
    """
    Gets the high-level summary of the latest test run (total, passed, failed, flaky).
    Always use this tool when a user asks about the overall pass rate or run status.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT run_id, environment, test_suite, total_tests, passed_tests, failed_tests, flaky_tests
            FROM test_runs ORDER BY execution_date DESC LIMIT 1;
        """)
        row = cursor.fetchone()
        if not row:
            return "No test runs found in the database."
        
        return (f"Latest Run ID: {row[0]}\n"
                f"Environment: {row[1]} | Suite: {row[2]}\n"
                f"Total Tests: {row[3]}\n"
                f"Passed: {row[4]} | Failed: {row[5]} | Flaky: {row[6]}")
    except Exception as e:
        return f"Error querying database: {str(e)}"
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

@mcp.tool()
def get_tag_intelligence(tag_name: str) -> str:
    """
    Gets the historical stability and pass rate for a specific Cucumber tag (e.g., @CreateDemand1).
    Use this when a user asks how stable a specific tag, feature, or module is.
    """
    try:
        # Ensure tag starts with @
        if not tag_name.startswith('@'):
            tag_name = f"@{tag_name}"
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT total_executions, passed_count, failed_count, flaky_count, pass_rate_percentage
            FROM vw_tag_intelligence WHERE tag = %s;
        """, (tag_name,))
        row = cursor.fetchone()
        if not row:
            return f"No historical data found for tag: {tag_name}"
        
        return (f"Tag Intelligence for {tag_name}:\n"
                f"Overall Pass Rate: {row[4]}%\n"
                f"Total Executions: {row[0]}\n"
                f"Stable Passes: {row[1]} | Hard Fails: {row[2]} | Flaky Passes (Required Retry): {row[3]}")
    except Exception as e:
        return f"Error querying database: {str(e)}"
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    print("Starting ENPL QA Intelligence MCP Server...")
    # The server runs over standard input/output so Claude can communicate with it
    mcp.run(transport='stdio')
