# **Phase 2 Execution Guide: Data Modeling & Core Engine**

## **1\. Phase Objective**

The goal of Phase 2 is to move our test execution data out of raw JSON files and into a highly structured PostgreSQL database, and then expose that database to the LLM via a Custom MCP Server. This eliminates LLM token limits and math hallucinations.

**Primary Persona:** SDET / Backend Developer

**Prerequisites:** A Mac, basic terminal knowledge, and the phase2\_init\_schema.sql file.

## **Step 1: Set Up Your Local PostgreSQL Database**

1. Run a local PostgreSQL instance (via Docker or Postgres.app).  
2. Connect using a Database GUI (DBeaver / pgAdmin).  
3. Execute the phase2\_init\_schema.sql script to create the test\_runs, test\_cases, test\_results, and retry\_history tables.

## **Step 2: Scaffold the Python Backend**

Create the project that will parse JSONs and serve the LLM.

1. Create and enter the directory:  
   mkdir enpl-qa-intelligence-backend  
   cd enpl-qa-intelligence-backend

2. Initialize a Python virtual environment and activate it:  
   python3 \-m venv venv  
   source venv/bin/activate

3. Install dependencies **(CRITICAL: Do not skip this step)**:  
   pip install psycopg2-binary python-dotenv mcp  
   pip freeze \> requirements.txt

4. Create the folder structure:  
   mkdir src  
   touch src/db.py  
   touch src/ingestion.py  
   touch src/mcp\_server.py  
   touch .env

## **Step 3: Configure Environment Variables**

Edit the .env file in the root of your new project to include your database credentials and the absolute path to your allure-results folder.

DB\_HOST=localhost  
DB\_PORT=5432  
DB\_NAME=qa\_intelligence  
DB\_USER=postgres  
DB\_PASSWORD=postgres  
ALLURE\_RESULTS\_DIR=/absolute/path/to/your/enpl-qa-automation-v2/enpl-ui-automation/target/allure-results

## **Step 4: Run the Ingestion Engine**

Add the parsing logic to src/db.py and src/ingestion.py.

Execute the script to transform the unstructured Allure JSON files into normalized PostgreSQL records:

python3 src/ingestion.py

*Verify success by checking the test\_results table in pgAdmin/DBeaver.*

## **Step 5: Start the Custom MCP Server (The AI Brain)**

Now that the data is in PostgreSQL, we expose it to Claude using the Model Context Protocol (MCP).

1. **Create and Save the File:** Open src/mcp_server.py in your text editor, paste the provided FastMCP server code into it, and **save the file**. *(If you leave this file empty, the server will instantly crash).*  
2. Update your Claude Desktop configuration file ($HOME/Library/Application Support/Claude/claude_desktop_config.json) to include the new server.  
   **CRITICAL:** You must replace the /absolute/path/to/your/... placeholders with the actual absolute paths (e.g., /Users/yourname/work/...) to your virtual environment's Python executable and your mcp_server.py script.

```json
{
  "mcpServers": {
    "qa-filesystem-core": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/absolute/path/to/your/project/src/test/java",
        "/absolute/path/to/your/project/target/allure-results"
      ]
    },
    "qa-database-intel": {
      "command": "/absolute/path/to/your/enpl-qa-intelligence-backend/venv/bin/python",
      "args": [
        "/absolute/path/to/your/enpl-qa-intelligence-backend/src/mcp_server.py"
      ]
    }
  }
}
```

3. **Fully Quit (Cmd + Q)** and restart Claude Desktop.  
4. Click the 🔌 icon to verify both qa-filesystem-core and qa-database-intel are running.

## **Troubleshooting: "Server Disconnected" Error**

If Claude shows a red failed badge and the error reads "Server disconnected" for your qa-database-intel server, it means the script crashed immediately upon execution. Check the following:

1. **Verify your Paths:** Double-check that you used your actual Mac paths (e.g., /Users/username/...) in the claude\_desktop\_config.json file. Claude will fail instantly if the paths do not exist.  
2. **File is Empty:** Ensure you actually pasted the code into src/mcp\_server.py and saved it.  
3. **Missing MCP Dependency:** Ensure you ran the pip install mcp command from **Step 2.3** while your virtual environment was active. If the mcp module is missing, the script will crash. To fix:  
   cd /path/to/enpl-qa-intelligence-backend  
   source venv/bin/activate  
   pip install mcp psycopg2-binary python-dotenv

## **6. Validation Prompts for Phase 2**

Ask Claude the following questions to verify it is using the database tools (instantly) rather than reading JSON files (slowly):

* *"Can you use your tools to give me the execution summary of our latest test run?"*  
* *"What is the historical pass rate and flakiness for one of the tags you see in the summary?"*

**Success Criteria:** Phase 2 is complete when Claude accurately quotes the database statistics in less than a second, without hitting token limits.