# InstanceLLM - Installation Guide

## Quick Install

### Windows

#### Option 1: Automated Installer (Recommended)
1. Download or clone this repository
2. Double-click `install.bat`
3. Wait for installation to complete
4. Double-click `start-instancellm.bat` to start the server
5. Open http://localhost:8000 in your browser

#### Option 2: Manual Installation
```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate virtual environment
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server (without model for first-time setup)
python llm_server.py 8000

# Or with a specific model
python llm_server.py models\your-model.gguf 8000
```

### macOS / Linux

#### Option 1: Automated Installer (Recommended)
```bash
# 1. Download or clone this repository
git clone https://github.com/yourusername/InstanceLLM.git
cd InstanceLLM

# 2. Make installer executable
chmod +x install.sh

# 3. Run installer
./install.sh

# 4. Start the server
./start-instancellm.sh
```

#### Option 2: Manual Installation
```bash
# 1. Create virtual environment
python3 -m venv .venv

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server (without model for first-time setup)
python llm_server.py 8000

# Or with a specific model
python llm_server.py models/your-model.gguf 8000
```

#### macOS Notes
- **M1/M2 Macs**: `llama-cpp-python` automatically uses Metal acceleration for better performance
- **Security**: If you get security warnings, go to System Preferences > Security & Privacy and allow the app
- **Homebrew**: Install Python via `brew install python@3.10` if needed

## First-Time Setup

1. **Start the Server**
   - Run `start-instancellm.bat`
   - The server will start on http://localhost:8000

2. **Download a Model**
   - Open http://localhost:8000 in your browser
   - Go to the **Models** tab
   - Click **🌐 Scan Online Models**
   - Choose a model (TinyLlama recommended for first test - only 0.7 GB)
   - Click **Download**
   - Wait for download to complete

3. **Restart the Server**
   - Close the server window (or press Ctrl+C)
   - Run `start-instancellm.bat` again
   - The server will automatically use the downloaded model

## Creating Multiple Instances

1. Click the **+** button in the Instances panel
2. Enter:
   - **Name**: Give your instance a name (e.g., "Fast Model", "Large Model")
   - **Model**: Select from downloaded models
   - **Port**: Choose a port (8001, 8002, etc.)
3. Click **Create**
4. Click **▶ Start** button on the instance tile
5. Each instance runs independently and can use different models!

## Features

### 🎨 Retro Interface
- Authentic Windows 95 styling
- Nostalgic UI elements
- Classic system tray and windows

### 🤖 Multiple Instances
- Run multiple LLM instances simultaneously
- Each instance can use a different model
- Independent ports for each instance
- Resource monitoring and management

### 📦 Model Management
- Download models directly from Hugging Face
- Scan local models in the models\ folder
- Easy model switching
- Progress tracking for downloads

### 🎙️ Microsoft Sam Voice
- Text-to-speech for LLM responses
- Classic "Soy" test phrase
- Adjustable speed (slower/normal/faster)
- Pause/resume functionality
- Quick mute toggle

### 💬 Chat Interface
- Streaming and non-streaming modes
- Conversation history
- Adjustable generation parameters
- System prompt support

## System Requirements

### All Platforms
- **Python**: 3.10 or higher
- **RAM**: 4GB minimum (8GB+ recommended for larger models)
- **Disk**: 5GB+ for models
- **CPU**: Modern multi-core processor (GPU support optional)

### Platform-Specific
- **Windows**: Windows 10/11
- **macOS**: macOS 11 (Big Sur) or higher
  - M1/M2 Macs: Native Metal acceleration supported
  - Intel Macs: CPU-only (still fast with smaller models)
- **Linux**: Most modern distributions with Python 3.10+

## Recommended Models

| Model | Size | Use Case | Speed |
|-------|------|----------|-------|
| TinyLlama 1.1B | ~0.7 GB | Testing, low-end systems | ⚡⚡⚡ Very Fast |
| Llama 3.2 3B | ~2.0 GB | General tasks, balanced | ⚡⚡ Fast |
| Phi-3 Mini 4K | ~2.3 GB | Code, reasoning | ⚡⚡ Fast |
| Llama 3.1 8B | ~4.7 GB | Complex tasks, quality | ⚡ Medium |
| Qwen 2.5 7B | ~4.7 GB | Multilingual, versatile | ⚡ Medium |

## Troubleshooting

### Windows

#### Port Already in Use
```bash
# Edit start-instancellm.bat and change the port number
# Or stop the conflicting application
```

#### Model Not Loading
- Check that .gguf files exist in the `models\` folder
- Verify the model file isn't corrupted (re-download if needed)
- Check available RAM (close other applications)

### macOS / Linux

#### Permission Denied
```bash
chmod +x install.sh
chmod +x start-instancellm.sh
./start-instancellm.sh
```

#### Port Already in Use
```bash
# Edit start-instancellm.sh and change the port number
# Or find and kill the process: lsof -ti:8000 | xargs kill
```

#### Model Not Loading
- Check that .gguf files exist in the `models/` folder
- Verify the model file isn't corrupted (re-download if needed)
- Check available RAM (close other applications)

#### macOS Security Warning
- Go to System Preferences > Security & Privacy
- Click "Open Anyway" for the blocked script

#### M1/M2 Metal Acceleration Not Working
```bash
# Reinstall llama-cpp-python with Metal support
pip uninstall llama-cpp-python
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python
```

### All Platforms

### Voice Not Working
- Check browser audio permissions
- Click the **🎤 Test** button in Settings
- Ensure volume isn't muted

### Download Failing
- Check internet connection
- Verify `huggingface_hub` is installed: `pip install huggingface_hub`
- Try a smaller model first

### Out of Memory
- Close other applications
- Use a smaller model
- Reduce context window in Settings

## Uninstallation

### Windows
Run `uninstall.bat` to remove:
- Virtual environment
- Start scripts
- Installation files

### macOS / Linux
```bash
chmod +x uninstall.sh
./uninstall.sh
```

Models and configurations are preserved by default.

**Complete Removal:**
1. Run the appropriate uninstaller
2. Delete the `models/` folder (if you want to remove downloaded models)
3. Delete the entire InstanceLLM directory

## Advanced Usage

### Custom Model Path

**Windows:**
```bash
python llm_server.py path\to\your\model.gguf 8000
```

**macOS / Linux:**
```bash
python llm_server.py path/to/your/model.gguf 8000
```

### Running as Background Service

**macOS (launchd):**
```bash
# Create ~/Library/LaunchAgents/com.instancellm.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.instancellm</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/InstanceLLM/start-instancellm.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>

# Load service
launchctl load ~/Library/LaunchAgents/com.instancellm.plist
```

**Linux (systemd):**
```bash
# Create /etc/systemd/system/instancellm.service
[Unit]
Description=InstanceLLM Server
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/InstanceLLM
ExecStart=/path/to/InstanceLLM/start-instancellm.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable instancellm
sudo systemctl start instancellm
```

### API Endpoints
- `GET /health` - Server health check
- `POST /prompt` - Send prompt (non-streaming)
- `POST /stream` - Send prompt (streaming)
- `GET /list-models` - List available models
- `POST /start-instance` - Start an instance
- `POST /stop-instance` - Stop an instance

### Configuration
Edit generation parameters in the Settings tab:
- **Temperature**: Randomness (0.0-2.0)
- **Max Tokens**: Response length
- **Top P**: Nucleus sampling
- **Top K**: Token selection pool

## Support

For issues, questions, or contributions:
- GitHub Issues: [Your Repository URL]
- Documentation: Check INSTALLATION.txt

## License

[Your License Here]

---

**Made with 💾 in the spirit of Windows 95**
