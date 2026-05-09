# MCP Server Configuration Guide

This guide details how to configure the Model Context Protocol (MCP) servers for the QA Intelligence Platform across various popular IDEs and AI assistants. 

The project utilizes two primary MCP servers:
1. **`qa-filesystem-core`**: Provides the AI with read access to the UI automation source code and test results.
2. **`qa-database-intel`**: Connects the AI to the local PostgreSQL database containing the parsed, normalized QA intelligence data.

---

## The Base Configuration

Regardless of the IDE you use, the underlying JSON configuration payload remains the same. You will need to paste the following JSON into the respective configuration file for your environment:

```json
{
  "mcpServers": {
    "qa-filesystem-core": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/deena/workspace/enpl-qa-automation-v2/enpl-ui-automation/src/test/java",
        "/Users/deena/workspace/enpl-qa-automation-v2/enpl-ui-automation/src/test/resources/features",
        "/Users/deena/workspace/enpl-qa-automation-v2/enpl-ui-automation/target/allure-results",
        "/Users/deena/workspace/enpl-qa-automation-v2/enpl-ui-automation/src/main/java/com/publicissapient/ui"
      ]
    },
    "qa-database-intel": {
      "command": "/Users/deena/workspace/qa-intelligence-backend/venv/bin/python",
      "args": [
        "/Users/deena/workspace/qa-intelligence-backend/src/mcp_server.py"
      ],
      "env": {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "qa_intelligence",
        "DB_USER": "postgres",
        "DB_PASSWORD": "postgres"
      }
    }
  }
}
```

---

## 1. Claude Desktop Setup

Claude Desktop reads from a global configuration file. 

1. Open Claude Desktop.
2. Go to **Settings** (or Developer > Settings depending on the version).
3. Under the **Local MCP servers** section, click **Edit Config**.
4. This will open the file located at: `~/Library/Application Support/Claude/claude_desktop_config.json`.
5. Paste the base configuration payload above into the file and save it.
6. Claude Desktop will automatically detect the changes and reload the servers. Check the settings page to verify they are connected successfully.

---

## 2. Antigravity / Claude Code Setup

Antigravity and Claude Code can read MCP configurations either globally (from the Claude Desktop config) or on a per-project basis. 

**Per-Project Setup (Recommended):**
1. Create a file named `claude.json` in the root of your project directory (`/Users/deena/workspace/qa-intelligence-backend/claude.json`).
2. Paste the base configuration payload into this file and save it.
3. Antigravity will instantly recognize the configuration whenever you are working within this workspace.

---

## 3. VS Code Setup (Using Cline / Roo Code)

For VS Code, MCP functionality is typically provided via AI extensions like **Cline** or **Roo Code**.

1. In the VS Code sidebar, open the **Cline** or **Roo Code** extension panel.
2. Click on the **MCP servers icon** (usually looks like a plug or database icon near the bottom of the panel).
3. Click on the **Edit MCP Settings** gear icon.
4. This will open `cline_mcp_settings.json` (typically located in `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`).
5. Paste the base configuration payload into the file and save it.
6. The extension will automatically restart the MCP connection.

---

## 4. IntelliJ IDEA Setup

IntelliJ natively supports MCP through the built-in JetBrains AI Assistant (versions 2025.1+).

### Option 1: One-Click Import (If Claude Desktop is configured)
If you have already configured Claude Desktop on your machine:
1. Go to **Settings** > **Tools** > **AI Assistant** > **Model Context Protocol (MCP)**.
2. Click **Import from Claude**. 
3. IntelliJ will automatically read your `claude_desktop_config.json` and instantly add both `qa-filesystem-core` and `qa-database-intel`.

### Option 2: Manual Entry
1. Go to **Settings** > **Tools** > **AI Assistant** > **Model Context Protocol (MCP)**.
2. Click the **+** (Add) button.
3. Add a configuration for the database server:
   - **Name:** `qa-database-intel`
   - **Command:** `/Users/deena/workspace/qa-intelligence-backend/venv/bin/python`
   - **Arguments:** `/Users/deena/workspace/qa-intelligence-backend/src/mcp_server.py`
   - **Environment Variables:** `DB_HOST=localhost`, `DB_PORT=5432`, `DB_NAME=qa_intelligence`, `DB_USER=postgres`, `DB_PASSWORD=postgres`
4. Click **+** again to add the filesystem server:
   - **Name:** `qa-filesystem-core`
   - **Command:** `npx`
   - **Arguments:** `-y`, `@modelcontextprotocol/server-filesystem`, and all four absolute paths shown in the base configuration above.
5. Apply and save. The tools will immediately become available in the IntelliJ AI Assistant chat window by typing `/`.

---

## 5. Cursor IDE Setup

Cursor provides native support for MCP servers. You can configure them either through the UI or via a JSON file.

### Option 1: Using the `.cursor/mcp.json` file (Recommended)
1. In the root of your project, create a new directory named `.cursor` if it doesn't already exist.
2. Inside that directory, create a file named `mcp.json` (e.g., `/Users/deena/workspace/qa-intelligence-backend/.cursor/mcp.json`).
3. Paste the **Base Configuration** JSON payload (from the top of this guide) into `mcp.json` and save it. Cursor will automatically detect and connect to the servers for this specific workspace.

### Option 2: Using the Cursor Settings UI
1. Open Cursor Settings (`Cmd/Ctrl + Shift + J` or the gear icon).
2. Navigate to **Features** > **MCP** (or **Tools & Integrations** > **MCP** depending on the Cursor version).
3. Click **+ Add New MCP Server**.
4. Select **command** as the type.
5. Enter the Name, Command, and Arguments exactly as they are defined in the base JSON configuration above. 
6. Add the Database Environment Variables (`DB_USER`, etc.) in the provided fields.
7. Click **Save**. You should see a green dot indicating the server is connected and ready to use in the Cursor chat!

---

## 6. Microsoft 365 Copilot (via Copilot Studio)

Microsoft 365 Copilot supports MCP by integrating servers through **Microsoft Copilot Studio**. However, because it is a cloud service, your MCP server must be exposed as a web endpoint (using Server-Sent Events / SSE transport) rather than running locally via standard command line processes (`stdio`).

To configure this for a Copilot agent:
1. Open **Microsoft Copilot Studio**.
2. Select your agent and ensure **Generative Orchestration** is enabled in the agent settings.
3. Navigate to the **Tools** section.
4. Click **Add a tool** and select **Model Context Protocol**.
5. Provide the server details:
   * **Server Name:** e.g., `QA_Database_Intel`
   * **Server Description:** e.g., `Provides QA test results and intelligence data.`
   * **Server URL:** The public-facing HTTP endpoint URL where your MCP server is hosted.

*Note: Since the base configurations provided above rely on local CLI processes (`stdio`), you would need to run your python server via a web framework with SSE transport and expose it to the internet (e.g. via ngrok or cloud hosting) to connect it to M365 Copilot.*

---

## Troubleshooting Checklist

* **Server Disconnected / Crash Loop**: Ensure that the provided paths exist. For example, if `@modelcontextprotocol/server-filesystem` is given a directory path that hasn't been created yet (like `target/allure-results` before the first test run), it will crash.
* **ModuleNotFoundError**: Ensure the `qa-database-intel` command points directly to the virtual environment's python binary (`venv/bin/python`) and that you have run `pip install mcp` inside that virtual environment.
* **Node.js Issues**: Ensure `npm` and `npx` are installed on your machine and accessible in your system `PATH`.

---

## How to Test the MCP Services

Once your MCP servers are configured and connected, you can verify they are working by prompting your AI assistant (Claude, Antigravity, or your IDE's AI) to interact with them. 

Simply open the chat interface and try the following prompts:

### 1. Testing the Filesystem Server
Ask the AI to read a file or list a directory:
> *"Can you use your filesystem tools to list the contents of the `/Users/deena/workspace/enpl-qa-automation-v2/enpl-ui-automation/src/test/java` directory?"*

If successful, the AI will invoke the `list_directory` tool provided by the `qa-filesystem-core` server and summarize the contents for you.

### 2. Testing the Database Server
Ask the AI to query the local PostgreSQL database:
> *"Please query the `test_results` table in the database and give me a summary of the latest automation run."*

If successful, the AI will invoke the tools provided by the `qa-database-intel` server, execute the SQL query, and present the results in the chat.
