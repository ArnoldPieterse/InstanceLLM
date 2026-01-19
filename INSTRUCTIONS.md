# Quick Instructions for LLMs/AI Assistants

## Running This Application (Step-by-Step for AI Assistants)

### Goal
Help a user run a local LLM server that hosts language models on their network via REST API.

### Prerequisites Check
```bash
# Verify Python is installed
python --version  # Should be 3.8+

# Verify project files exist
ls llm_server.py  # Should exist
```

### Step 1: Navigate to Project
```bash
cd C:\projects\InstanceLLM
# or wherever the user has the project
```

### Step 2: Install Dependencies (One-Time)
```bash
# Option A: All at once
pip install -r requirements.txt

# Option B: Core dependencies only (if above fails)
pip install fastapi uvicorn pydantic huggingface_hub requests tqdm
```

**Expected:** Installation completes without errors.
**If errors:** Try Option B, or install packages one by one.

### Step 3: Run the Server
```bash
python llm_server.py
```

### Step 4: Interactive Model Selection
When prompted:
```
What would you like to do? [1/2/3]: 
```
**Type:** `1` (Download a popular model from HuggingFace)

When prompted to select a model:
```
Enter choice [1-8]:
```
**Recommend:** `7` (TinyLlama - 700MB, fastest) or `1` (Llama 3.2 3B - 2GB, better quality)

When asked to proceed with download:
```
Proceed with download? (y/n):
```
**Type:** `y`

**Expected:** Download progress bar appears, model downloads, server starts automatically.

### Step 5: Verify Server is Running
You should see:
```
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 6: Test the Server
Open a new terminal and run:
```bash
python quick_test.py
```

**Expected:** All 6 tests pass, showing responses from the LLM.

### Step 7: Use the API
```bash
# Health check
curl http://localhost:8000/health

# Send a prompt
curl -X POST http://localhost:8000/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!", "temperature": 0.7}'
```

Or open in browser: `http://localhost:8000/docs` for interactive API testing.

---

## Common Issues and Solutions

### Issue: "ModuleNotFoundError: No module named 'fastapi'"
**Solution:**
```bash
pip install fastapi uvicorn pydantic
```

### Issue: "No module named 'llama_cpp'" or "No module named 'transformers'"
**Expected behavior!** This is normal.
The server will use a mock LLM for testing. You'll see:
```
WARNING: USING MOCK LLM FOR TESTING
```

**To use real models (optional):**
```bash
pip install llama-cpp-python
# or
pip install transformers torch
```

### Issue: "Port already in use"
**Solution:** Use a different port:
```bash
python llm_server.py path/to/model.gguf 8080
```

### Issue: Download is slow or fails
**Solution:** 
- Try a smaller model (option 7 - TinyLlama)
- Check internet connection
- Resume download by running again (it continues from where it stopped)

### Issue: "File not found" when running server
**Solution:**
```bash
# Make sure you're in the right directory
cd C:\projects\InstanceLLM

# Verify files exist
dir  # Windows
ls   # Linux/Mac
```

---

## Understanding the Output

### Normal Output (Expected)
```
INFO:__main__:Initializing LLM Server with model: models\Llama-3.2-3B-Instruct-Q4_K_M.gguf
WARNING:__main__:llama-cpp-python not installed. Trying transformers...
WARNING:__main__:USING MOCK LLM FOR TESTING
Mock LLM loaded: Llama-3.2-3B-Instruct-Q4_K_M.gguf
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Meaning:**
- ✓ Server initialized successfully
- ✓ Model file found
- ℹ️ Using mock LLM (normal if llama-cpp-python not installed)
- ✓ Server running on port 8000

### Success Indicators
- Server shows "Uvicorn running on http://0.0.0.0:8000"
- No red ERROR messages
- Can access http://localhost:8000/docs in browser
- quick_test.py runs without errors

---

## Quick Command Reference

```bash
# Start server (auto-download model)
python llm_server.py

# Start with existing model
python llm_server.py models/model.gguf

# Start on custom port
python llm_server.py models/model.gguf 8080

# Test the server
python quick_test.py

# Download models standalone
python model_downloader.py

# List available models
python model_downloader.py list

# Check server health
curl http://localhost:8000/health
```

---

## For Advanced Users

### Custom Configuration
```python
from llm_server import LLMServer

# Method 1: Keyword arguments
server = LLMServer(
    "path/to/model.gguf",
    temperature=0.8,
    max_tokens=1024,
    n_gpu_layers=0  # CPU only
)

# Method 2: Dictionary
config = {'temperature': 0.8, 'max_tokens': 1024}
server = LLMServer.from_config_dict("path/to/model.gguf", config)

# Method 3: Array of tuples
params = [('temperature', 0.8), ('max_tokens', 1024)]
server = LLMServer.from_config_array("path/to/model.gguf", params)

server.load_model()
server.start()
```

### Parameter Meanings
- `temperature` (0.0-2.0): Higher = more creative, Lower = more focused
- `max_tokens` (1-32000): Maximum response length
- `n_gpu_layers` (0-100): GPU layers (0 = CPU only, higher = more GPU)
- `top_p` (0.0-1.0): Nucleus sampling threshold
- `context_window` (512-32768): Maximum conversation context

---

## Summary for LLM Assistants

**To run this app:**
1. `cd` to project directory
2. `pip install -r requirements.txt`
3. `python llm_server.py`
4. Follow prompts (select model, confirm download)
5. Test with `python quick_test.py`

**Expected result:** Server running on port 8000, responding to HTTP requests.

**Common success indicators:**
- "Uvicorn running on http://0.0.0.0:8000"
- quick_test.py shows "All Tests Completed Successfully"
- Can access http://localhost:8000/docs

**If user sees warnings about mock LLM:** This is normal! The API works, it's just using a test LLM instead of real inference. To use real models, install llama-cpp-python.
