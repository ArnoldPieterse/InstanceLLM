# LLM Workspace Directory

This directory is the **safe sandbox** for LLM-generated commands and scripts.

## 🔒 Security

All commands and scripts executed by the LLM are:
- **Restricted to this directory only** - Commands run with cwd set to workspace
- **30-second timeout** - Prevents infinite loops or long-running processes
- **Output captured** - Stdout/stderr shown in chat, not executed directly
- **No system access** - Can't escape the workspace boundary

## 📋 How It Works

1. **Enable the terminal access subroutine** (💻 checkbox) on your instance
2. **Ask the LLM** to create scripts, run commands, install packages, etc.
3. **LLM responds** with commands in code blocks:
   - \```powershell for Windows PowerShell commands
   - \```bash for Linux/Mac bash commands
   - \```python for Python scripts
4. **Commands execute automatically** in this workspace
5. **Results display** in chat with stdout, stderr, and exit codes

## 🎯 Supported Commands

The system detects and executes:

### PowerShell Code Blocks
\```powershell
Get-Date
Get-ChildItem
New-Item -Path "folder" -ItemType Directory
\```

### Bash/Shell Code Blocks
\```bash
ls -la
mkdir -p project/src
echo "Hello World" > greeting.txt
\```

### Python Scripts
\```python
import datetime
print(f"Current time: {datetime.datetime.now()}")

# Write to file
with open('output.txt', 'w') as f:
    f.write('Hello from Python!')
\```

### Inline Commands
Single line commands with $ or > prefix also work

### File System Commands (Still Supported)
Direct commands like `mkdir folder` or `touch file.txt` still work

## 📁 View Contents

Click **"📁 View Workspace Files"** in the Settings tab to see the directory tree.

## 🧹 Manual Cleanup

You can safely delete anything in this directory - it will be recreated as needed.

## 💡 Example Prompts

With the terminal access subroutine enabled, try:

**Project Setup:**
- "Create a Python Flask app structure with folders and a basic app.py file, then list the contents"
- "Set up a React project structure and create a package.json with common dependencies"

**Data Processing:**
- "Create a Python script that generates 100 random numbers and saves them to data.csv, then run it and show the file"
- "Write a bash script to organize files by extension into folders, then execute it"

**Package Management:**
- "Install the requests library using pip and create a script that fetches data from an API"
- "Check the Python version and list all installed packages"

**Automation:**
- "Create a Python script that backs up all .txt files to a backup/ folder and run it"
- "Write a PowerShell script to find all files larger than 1KB"

The LLM will not only write the code but **actually execute it** and show you the results!
