# Complete Setup Guide - Real LLM Inference

## Overview

This guide shows you how to set up the InstanceLLM server with **real LLM inference** (not mock mode).

## What You'll Achieve

✅ Server running with actual Llama 3.2 3B model  
✅ Real AI-generated responses  
✅ Full GGUF model support  
✅ Network-accessible REST API  

## Prerequisites

- Windows 10/11, macOS, or Linux
- Python 3.8 or higher
- 4GB+ RAM
- 3GB+ free disk space

---

## Quick Start (Mock Mode)

If you just want to test the API without real inference:

```bash
cd C:\projects\InstanceLLM
pip install fastapi uvicorn pydantic huggingface_hub requests tqdm
python llm_server.py
```

Server runs with mock LLM - full API functionality, simulated responses.

---

## Full Setup (Real LLM)

### Step 1: Install Core Dependencies

```bash
cd C:\projects\InstanceLLM
pip install -r requirements.txt
```

### Step 2: Install C++ Build Tools (Windows Only)

**Why needed:** `llama-cpp-python` requires C++ compiler to build from source.

**Installation:**
```bash
winget install Microsoft.VisualStudio.2022.BuildTools --override "--quiet --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

**Time:** ~5 minutes  
**Size:** ~2GB download

**Verify installation:**
```bash
& "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"
nmake /?  # Should show nmake help
```

### Step 3: Install llama-cpp-python

**Windows (with VS Build Tools):**
```powershell
# Open new PowerShell
& "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"
pip install llama-cpp-python
```

**Linux/macOS:**
```bash
pip install llama-cpp-python
```

**Expected output:**
```
Building wheels for collected packages: llama-cpp-python
  Building wheel for llama-cpp-python (pyproject.toml) ... done
Successfully installed llama-cpp-python-0.3.16
```

**Time:** 3-5 minutes (compiling C++ code)

### Step 4: Download a Model

**Option A: Automatic (Recommended)**
```bash
python llm_server.py
# Follow prompts to download Llama 3.2 3B (~2GB)
```

**Option B: Manual**
```bash
python model_downloader.py
# Select model #1 (Llama 3.2 3B) or #7 (TinyLlama - faster)
```

### Step 5: Start the Server

```bash
python llm_server.py models/Llama-3.2-3B-Instruct-Q4_K_M.gguf
```

**Success indicators:**
```
INFO:__main__:Loading model with llama-cpp-python...
INFO:__main__:Model loaded successfully!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**No "USING MOCK LLM" warning = real inference active!**

### Step 6: Test Real Inference

**PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/prompt" -Method Post -ContentType "application/json" -Body '{"prompt": "Write a haiku about Python", "max_tokens": 100}'
```

**Bash/cURL:**
```bash
curl -X POST http://localhost:8000/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a haiku about Python", "max_tokens": 100}'
```

**Browser:** http://localhost:8000/docs

---

## Comparison: Mock vs Real

| Feature | Mock LLM | Real LLM |
|---------|----------|----------|
| Installation | Easy (no compiler) | Requires VS Build Tools (Windows) |
| Response Quality | Pattern-based, generic | AI-generated, contextual |
| Speed | Instant | 2-10 seconds per response |
| Model Size | 0 MB | 700MB - 5GB |
| Use Case | API testing, development | Production, real queries |

## Verified Working Setup

**Tested on:** January 19, 2026  
**System:** Windows 11  
**Python:** 3.14  
**Model:** Llama 3.2 3B Instruct Q4_K_M (1.9GB)  

**Installation steps used:**
1. Installed Visual Studio Build Tools 2022
2. Activated VS environment in PowerShell
3. Built llama-cpp-python from source
4. Downloaded Llama 3.2 3B model
5. Server started successfully with real inference

**Sample real output:**
```
Prompt: "Write a haiku about Python programming"
Response:

lines of code
dancing in the darkness
wisdom is found here

Note: A traditional haiku consists of three lines with a syllable
count of 5-7-5. I've followed this structure as closely as possible
while capturing the essence of Python programming.
```

---

## Troubleshooting

### llama-cpp-python won't install

**Error:** `CMake Error: CMAKE_C_COMPILER not set`

**Solution:**
```bash
# Install Visual Studio Build Tools
winget install Microsoft.VisualStudio.2022.BuildTools --override "--quiet --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"

# Restart PowerShell, activate VS environment
& "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"

# Try again
pip install llama-cpp-python
```

### Server still uses mock LLM

**Check:**
```bash
python -c "import llama_cpp; print('Installed')"
```

If error, llama-cpp-python isn't installed. Reinstall per Step 3.

### Model loading fails

**Error:** `FileNotFoundError: Model file not found`

**Solution:** Download model first:
```bash
python model_downloader.py
```

### Port already in use

**Solution:** Use different port:
```bash
python llm_server.py model.gguf 8001
```

---

## Alternative: Use Transformers

If you can't install llama-cpp-python:

```bash
pip install transformers torch accelerate
```

**Note:** Transformers cannot load GGUF files. You'd need HuggingFace format models.

---

## Performance Tips

**For faster inference:**
```python
# Edit llm_server.py main() function
server = LLMServer(
    model_path,
    n_threads=8,  # Use more CPU threads
    n_gpu_layers=35,  # If you have GPU
    max_tokens=512  # Shorter responses = faster
)
```

**For lower memory:**
- Use TinyLlama (700MB) instead of Llama 3.2 3B (2GB)
- Set `context_window=2048` (default 4096)

---

## Next Steps

✅ Server running with real LLM  
→ Test all API endpoints: http://localhost:8000/docs  
→ Try different models: `python model_downloader.py`  
→ Customize parameters in `llm_server.py`  
→ Deploy on network (already accessible at 0.0.0.0:8000)  
→ Integrate with your applications  

---

## Summary

**For Mock LLM (quick testing):**
- Install: `pip install -r requirements.txt` (skip llama-cpp-python)
- Run: `python llm_server.py`
- API works, responses are simulated

**For Real LLM (production):**
- Install Visual Studio Build Tools (Windows)
- Build llama-cpp-python with VS environment
- Download model
- Run server
- Get real AI responses!

**GitHub:** https://github.com/ArnoldPieterse/InstanceLLM
