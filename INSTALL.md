# InstanceLLM - Installation Guide

## Quick Install (Windows)

### Option 1: Automated Installer (Recommended)
1. Download or clone this repository
2. Double-click `install.bat`
3. Wait for installation to complete
4. Double-click `start-instancellm.bat` to start the server
5. Open http://localhost:8000 in your browser

### Option 2: Manual Installation
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

- **OS**: Windows 10/11
- **Python**: 3.10 or higher
- **RAM**: 4GB minimum (8GB+ recommended for larger models)
- **Disk**: 5GB+ for models
- **CPU**: Modern multi-core processor (GPU support optional)

## Recommended Models

| Model | Size | Use Case | Speed |
|-------|------|----------|-------|
| TinyLlama 1.1B | ~0.7 GB | Testing, low-end systems | ⚡⚡⚡ Very Fast |
| Llama 3.2 3B | ~2.0 GB | General tasks, balanced | ⚡⚡ Fast |
| Phi-3 Mini 4K | ~2.3 GB | Code, reasoning | ⚡⚡ Fast |
| Llama 3.1 8B | ~4.7 GB | Complex tasks, quality | ⚡ Medium |
| Qwen 2.5 7B | ~4.7 GB | Multilingual, versatile | ⚡ Medium |

## Troubleshooting

### Port Already in Use
```bash
# Edit start-instancellm.bat and change the port number
# Or stop the conflicting application
```

### Model Not Loading
- Check that .gguf files exist in the `models\` folder
- Verify the model file isn't corrupted (re-download if needed)
- Check available RAM (close other applications)

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

Run `uninstall.bat` to remove:
- Virtual environment
- Start scripts
- Installation files

Models and configurations are preserved by default.

To completely remove InstanceLLM:
1. Run `uninstall.bat`
2. Delete the `models\` folder (if you want to remove downloaded models)
3. Delete the entire InstanceLLM directory

## Advanced Usage

### Custom Model Path
```bash
python llm_server.py path\to\your\model.gguf 8000
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
