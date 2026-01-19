#!/bin/bash

# InstanceLLM Uninstaller for macOS/Linux

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "================================================================================"
echo "  InstanceLLM Uninstaller"
echo "================================================================================"
echo ""
echo "This will remove:"
echo "  - Virtual environment (.venv)"
echo "  - Start script (start-instancellm.sh)"
echo "  - Installation file (INSTALLATION.txt)"
echo ""
echo "This will NOT remove:"
echo "  - Downloaded models (models/ folder)"
echo "  - Your instance configurations (localStorage in browser)"
echo "  - Source code files"
echo ""

read -p "Do you want to continue with uninstallation? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Uninstallation cancelled."
    echo ""
    exit 0
fi

echo ""
echo "Uninstalling..."

# Remove virtual environment
if [ -d ".venv" ]; then
    echo "Removing virtual environment..."
    rm -rf .venv
    echo -e "${GREEN}Virtual environment removed${NC}"
fi

# Remove start script
if [ -f "start-instancellm.sh" ]; then
    echo "Removing start script..."
    rm start-instancellm.sh
    echo -e "${GREEN}Start script removed${NC}"
fi

# Remove installation file
if [ -f "INSTALLATION.txt" ]; then
    echo "Removing installation file..."
    rm INSTALLATION.txt
    echo -e "${GREEN}Installation file removed${NC}"
fi

echo ""
echo "================================================================================"
echo -e "  ${GREEN}Uninstallation Complete!${NC}"
echo "================================================================================"
echo ""
echo "To completely remove InstanceLLM:"
echo "  1. Delete the models/ folder (if you want to remove downloaded models)"
echo "  2. Delete this entire directory"
echo ""
