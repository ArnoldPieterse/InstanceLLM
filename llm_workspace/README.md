# LLM Workspace Directory

This directory is the **safe sandbox** for LLM-generated file system commands.

## 🔒 Security

All file/folder operations requested by the LLM are:
- **Restricted to this directory only** - Path traversal attacks are prevented
- **Creation only** - No deletion or modification of existing files
- **Pure Python** - No shell command execution (prevents injection attacks)

## 📋 How It Works

1. **Enable the filesystem subroutine** on your instance
2. **Ask the LLM** to create folders or files (e.g., "Create a project structure for a React app")
3. **Commands are detected** automatically from the LLM's response
4. **Commands execute** safely within this workspace
5. **Results display** in the chat with success/failure status

## 🎯 Supported Commands

The system detects and executes:

### PowerShell
```powershell
New-Item -Path "folder/subfolder" -ItemType Directory
New-Item -ItemType Directory -Path "folder"
New-Item -Path "file.txt" -ItemType File
mkdir folder
```

### Bash/Linux
```bash
mkdir -p folder/subfolder
mkdir folder
touch file.txt
```

### CMD
```cmd
md folder
```

## 📁 View Contents

Click **"📁 View Workspace Files"** in the Settings tab to see the directory tree.

## 🧹 Manual Cleanup

You can safely delete anything in this directory - it will be recreated as needed.

## 💡 Example Prompts

With the filesystem subroutine enabled, try:

- "Create a Python project structure with src, tests, and docs folders"
- "Set up a basic web app with folders for html, css, js, and images"
- "Create a data processing pipeline directory structure"
- "Make a folder structure for organizing my photos by year and month"

The LLM will not only describe the structure but actually create it!
