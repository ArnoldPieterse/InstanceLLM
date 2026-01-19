#!/bin/bash

# InstanceLLM Installer for macOS/Linux
# This script sets up the InstanceLLM environment

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "================================================================================"
echo "  InstanceLLM Installer"
echo "  Windows 95 Style LLM Instance Manager"
echo "================================================================================"
echo ""

# Check for Python
echo "[1/6] Checking for Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is not installed!${NC}"
    echo ""
    echo "Please install Python 3.10 or higher:"
    echo "  macOS: brew install python@3.10"
    echo "  Linux: sudo apt install python3 python3-venv python3-pip"
    echo ""
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}Found Python ${PYTHON_VERSION}${NC}"

# Check Python version
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}[ERROR] Python 3.10 or higher is required!${NC}"
    echo "Found: Python $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment
echo ""
echo "[2/6] Creating virtual environment..."
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists, skipping...${NC}"
else
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to create virtual environment!${NC}"
        exit 1
    fi
    echo -e "${GREEN}Virtual environment created successfully!${NC}"
fi

# Activate virtual environment and install dependencies
echo ""
echo "[3/6] Installing dependencies..."
source .venv/bin/activate
python -m pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to install dependencies!${NC}"
        exit 1
    fi
else
    echo "Installing core dependencies..."
    pip install fastapi uvicorn llama-cpp-python python-multipart huggingface_hub
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to install dependencies!${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}Dependencies installed successfully!${NC}"

# Create models directory
echo ""
echo "[4/6] Setting up directories..."
mkdir -p models
echo -e "${GREEN}models/ directory ready${NC}"

# Create start script
echo ""
echo "[5/6] Creating launcher script..."
cat > start-instancellm.sh << 'EOF'
#!/bin/bash

# InstanceLLM Launcher

cd "$(dirname "$0")"

echo "Starting InstanceLLM Server..."
echo ""

# Activate virtual environment
source .venv/bin/activate

# Check for models
if ! ls models/*.gguf 1> /dev/null 2>&1; then
    echo "[WARNING] No models found in models/ directory"
    echo ""
    echo "You can download models from the web interface:"
    echo "1. Click on the Models tab"
    echo "2. Choose a model and click 'Download'"
    echo ""
    echo "Starting with default configuration..."
    echo ""
    python llm_server.py 8000
else
    # Use first available model
    MODEL=$(ls models/*.gguf | head -n 1)
    echo "Using model: $MODEL"
    echo ""
    echo "Access the interface at: http://localhost:8000"
    echo ""
    python llm_server.py "$MODEL" 8000
fi
EOF

chmod +x start-instancellm.sh
echo -e "${GREEN}Start script created: start-instancellm.sh${NC}"

# Create documentation
echo ""
echo "[6/6] Creating documentation..."
if [ ! -f "INSTALLATION.txt" ]; then
    cat > INSTALLATION.txt << 'EOF'
InstanceLLM - Installation Complete!

TO START THE SERVER:
  Run: ./start-instancellm.sh
  Or: bash start-instancellm.sh

FIRST TIME SETUP:
  1. Run ./start-instancellm.sh
  2. Open http://localhost:8000 in your browser
  3. Go to the Models tab
  4. Download a model (TinyLlama recommended for testing)
  5. Restart the server

CREATING INSTANCES:
  1. Click the + button in the Instances panel
  2. Enter a name, select a model, and choose a port
  3. Click Start to launch the instance

FEATURES:
  - Windows 95 retro interface
  - Multiple LLM instances on different ports
  - Model downloading from Hugging Face
  - Microsoft Sam text-to-speech
  - Streaming and non-streaming chat modes

TROUBLESHOOTING:
  - Port already in use: Change the port number in start script
  - Model not loading: Check models/ folder for .gguf files
  - Voice not working: Check browser audio permissions
  - Permission denied: Run chmod +x start-instancellm.sh

macOS SPECIFIC:
  - If you get security warnings, go to System Preferences > 
    Security & Privacy and allow the app to run
  - For M1/M2 Macs, llama-cpp-python should automatically use Metal

For more info: https://github.com/yourusername/InstanceLLM
EOF
fi

echo ""
echo "================================================================================"
echo -e "  ${GREEN}Installation Complete!${NC}"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "  1. Run ./start-instancellm.sh to start the server"
echo "  2. Open http://localhost:8000 in your web browser"
echo "  3. Download a model from the Models tab"
echo ""
echo "Read INSTALLATION.txt for detailed instructions"
echo ""
