# **Phase 1 Execution Guide: Local MVP (Proof of Value)**

## **1\. Phase Objective**

The goal of Phase 1 is to quickly prove the core value proposition of the QA Intelligence Platform without writing any custom backend code or altering cloud infrastructure.

By the end of this phase, the team will demonstrate that a Large Language Model (LLM) can act as a QA Copilot by securely reading local test execution logs (Allure JSONs) and cross-referencing them with the actual automation codebase (Java/Playwright) to diagnose failures.

**Estimated Effort:** 1 \- 2 Hours

**Primary Persona:** QA Lead / SDET

## **2\. Prerequisites**

Based on a clean macOS environment, ensure you have the following:

* **Node.js** installed. (Verify by running node \-v in your terminal).  
* A local clone of your enterprise QA automation repository.  
* The ability to run your automation suite locally via Maven.

## **3\. Step-by-Step Setup Instructions (macOS)**

### **Step 1: Install the AI Client (Claude Desktop)**

To interact with the MCP server and get the "QA Chatbot" experience, you need a compatible client. Claude Desktop is the standard free client provided by Anthropic.

1. **Download:** Go to [https://claude.ai/download](https://claude.ai/download) and download the macOS version.  
2. **Install:** Open the downloaded .dmg file and drag the **Claude** application icon into your **Applications** folder.  
3. **Setup:** Open the Claude app from your Applications folder. You will need to log in or create a free account to continue. **Note:** You must use the actual App, not the website in Chrome.

### **Step 2: Generate Local Test Data**

To give the AI something to analyze, we need fresh test execution data.

1. Open your **Terminal** app and navigate to your automation project directory:  
   cd /path/to/your/automation/project

2. Execute a local test run (preferably one known to have a mix of passes and failures):  
   mvn clean test

3. Verify that raw execution data has been generated in your target directory (e.g., target/allure-results/).

### **Step 3: Configure the Filesystem MCP Server**

We will use the official @modelcontextprotocol/server-filesystem. Because you have Node.js installed, this server will download and run automatically in the background.

1. Open your **Terminal** and run these commands to create the config file (using $HOME ensures the path is correct):  
   mkdir \-p "$HOME/Library/Application Support/Claude"  
   touch "$HOME/Library/Application Support/Claude/claude\_desktop\_config.json"

2. Open that file in a text editor:  
   open -e "$HOME/Library/Application Support/Claude/claude_desktop_config.json"

3. Paste the following JSON configuration into the file.  
   **CRITICAL:** Replace /absolute/path/to/your/project with the actual path to the automation repository on your Mac.

```json
{
  "mcpServers": {
    "qa-filesystem-core": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/absolute/path/to/your/project/src/test/java",
        "/absolute/path/to/your/project/src/test/resources/features",
        "/absolute/path/to/your/project/target/allure-results"
      ]
    }
  }
}
```

4. Save the file (Cmd + S) and close TextEdit (Cmd + Q).

### **Step 4: Initialize the Connection**

1. **Fully Quit** the Claude Desktop app. (Click "Claude" in the top Mac menu bar and select **Quit Claude**, or press Cmd \+ Q).  
2. Re-open Claude from your Applications folder.  
3. Look at the chat input bar. You should now see a small **Plug Icon** (🔌) or a **Hammer Icon**.

## **4\. Troubleshooting: Why can't I see the icon?**

If you have followed the steps and still don't see the icon:

1. **Verify you are NOT in a browser:** If you see a URL bar (like google.com or claude.ai) at the top, you are in a browser. Close the tab and open the **Claude App** from your Mac's Applications folder.  
2. **Check JSON Syntax:** Run cat "$HOME/Library/Application Support/Claude/claude\_desktop\_config.json" in your terminal. Ensure there are no missing quotes or extra commas.  
3. **Absolute Paths Only:** Ensure the paths in your args start with /Users/.... The MCP server does not understand \~ or relative paths.  
4. **Hard Restart:** You must completely Quit the app (Right-click the icon in the Dock and select Quit) and relaunch it for changes to take effect.

## **5\. Validation & Demonstration Prompts**

Once the icon appears, use these prompts to test the connection:

### **Prompt 1: Triage and Error Extraction**

*"Use your filesystem tools to look at the JSON files in my target/allure-results directory. Please list the names of any tests that failed during the last run, and extract the exact error message or stack trace for each."*

### **Prompt 2: Root Cause Code Analysis**

*"Now, take the first failed test you found. Search the src/test/java directory for the corresponding Step Definition or Page Object class. Tell me exactly which Playwright locator or Verify assertion failed."*

## **6. Success Criteria for Phase 1**

Phase 1 is complete when:

* [x] The LLM can successfully read local Allure JSON files.  
* [x] The LLM can map a failed test to the correct .java or .feature file.  
* [x] The team has demonstrated a root-cause diagnosis to stakeholders.
