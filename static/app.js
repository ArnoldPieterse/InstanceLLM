// InstanceLLM Web Interface

const API_BASE = 'http://localhost:8001';

// State
let currentSettings = {
    temperature: 0.8,
    max_tokens: 512,
    top_p: 0.9,
    top_k: 40
};

let selectedModel = null;

// Available models (matching model_downloader.py)
const AVAILABLE_MODELS = {
    "1": {
        "name": "Llama 3.2 3B Instruct (Q4_K_M)",
        "repo": "bartowski/Llama-3.2-3B-Instruct-GGUF",
        "file": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "size": "~2.0 GB",
        "description": "Fast, efficient model good for general tasks"
    },
    "2": {
        "name": "Llama 3.1 8B Instruct (Q4_K_M)",
        "repo": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
        "file": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "size": "~4.9 GB",
        "description": "Powerful 8B model, great for most tasks"
    },
    "3": {
        "name": "Mistral 7B Instruct v0.3 (Q4_K_M)",
        "repo": "bartowski/Mistral-7B-Instruct-v0.3-GGUF",
        "file": "Mistral-7B-Instruct-v0.3-Q4_K_M.gguf",
        "size": "~4.4 GB",
        "description": "Excellent instruction-following model"
    },
    "4": {
        "name": "Phi-3 Mini 4K Instruct (Q4_K_M)",
        "repo": "bartowski/Phi-3-mini-4k-instruct-GGUF",
        "file": "Phi-3-mini-4k-instruct-Q4_K_M.gguf",
        "size": "~2.3 GB",
        "description": "Small, fast model from Microsoft"
    },
    "5": {
        "name": "Qwen 2.5 7B Instruct (Q4_K_M)",
        "repo": "bartowski/Qwen2.5-7B-Instruct-GGUF",
        "file": "Qwen2.5-7B-Instruct-Q4_K_M.gguf",
        "size": "~4.7 GB",
        "description": "Strong multilingual model from Alibaba"
    },
    "6": {
        "name": "Gemma 2 9B Instruct (Q4_K_M)",
        "repo": "bartowski/gemma-2-9b-it-GGUF",
        "file": "gemma-2-9b-it-Q4_K_M.gguf",
        "size": "~5.4 GB",
        "description": "Google's powerful 9B model"
    },
    "7": {
        "name": "TinyLlama 1.1B Chat (Q4_K_M)",
        "repo": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
        "file": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "size": "~0.7 GB",
        "description": "Tiny model, perfect for testing and low-resource devices"
    }
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkServerStatus();
    loadModelsList();
    setupSettingsListeners();
    
    // Auto-refresh status every 5 seconds
    setInterval(checkServerStatus, 5000);
});

// Tab switching
function switchTab(tabName) {
    // Update buttons
    const buttons = document.querySelectorAll('menu[role="tablist"] button');
    buttons.forEach(btn => btn.setAttribute('aria-selected', 'false'));
    event.target.setAttribute('aria-selected', 'true');
    
    // Update panels
    const panels = document.querySelectorAll('article[role="tabpanel"]');
    panels.forEach(panel => panel.style.display = 'none');
    document.getElementById(`tab-${tabName}`).style.display = 'block';
    
    // Load models when switching to models tab
    if (tabName === 'models') {
        loadModelsList();
    }
}

// Check server status
async function checkServerStatus() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        
        document.getElementById('server-status').textContent = data.status === 'healthy' ? '✓ Online' : '✗ Offline';
        document.getElementById('server-status').style.color = data.status === 'healthy' ? 'green' : 'red';
        
        if (data.model_path) {
            const modelName = data.model_path.split('/').pop().split('\\').pop();
            document.getElementById('model-name').textContent = modelName;
        }
    } catch (error) {
        document.getElementById('server-status').textContent = '✗ Offline';
        document.getElementById('server-status').style.color = 'red';
        document.getElementById('model-name').textContent = 'None';
    }
}

// Load models list
function loadModelsList() {
    const container = document.getElementById('models-list');
    container.innerHTML = '';
    
    Object.entries(AVAILABLE_MODELS).forEach(([id, model]) => {
        const tile = document.createElement('div');
        tile.className = 'model-tile';
        tile.dataset.modelId = id;
        
        tile.innerHTML = `
            <div class="model-tile-header">
                <div class="model-name">${model.name}</div>
                <div class="model-size">${model.size}</div>
            </div>
            <div class="model-description">${model.description}</div>
            <div class="model-actions">
                <button onclick="downloadModel('${id}')">Download</button>
                <button onclick="selectModel('${id}')">Details</button>
            </div>
        `;
        
        tile.addEventListener('click', (e) => {
            if (!e.target.matches('button')) {
                selectModelTile(tile);
            }
        });
        
        container.appendChild(tile);
    });
}

// Select model tile
function selectModelTile(tile) {
    document.querySelectorAll('.model-tile').forEach(t => t.classList.remove('selected'));
    tile.classList.add('selected');
}

// Select model (show details)
function selectModel(id) {
    const model = AVAILABLE_MODELS[id];
    alert(`Model: ${model.name}\n\nSize: ${model.size}\nRepository: ${model.repo}\nFile: ${model.file}\n\nDescription:\n${model.description}`);
}

// Download model
async function downloadModel(id) {
    const model = AVAILABLE_MODELS[id];
    
    if (!confirm(`Download ${model.name} (${model.size})?\n\nThis will take several minutes.`)) {
        return;
    }
    
    const statusDiv = document.getElementById('download-status');
    statusDiv.innerHTML = `Downloading ${model.name}...<br>Size: ${model.size}<br>Please wait...`;
    
    // Note: Actual download would need to be implemented on the server side
    // This is a placeholder showing the UI interaction
    alert(`Download feature requires server-side implementation.\n\nTo download manually:\n1. Use model_downloader.py\n2. Run: python model_downloader.py\n3. Select option ${id}`);
    
    statusDiv.innerHTML = 'Download requires model_downloader.py - see instructions';
}

// Send prompt
async function sendPrompt() {
    const input = document.getElementById('prompt-input');
    const output = document.getElementById('chat-output');
    const streaming = document.getElementById('streaming-mode').checked;
    
    const prompt = input.value.trim();
    if (!prompt) return;
    
    // Add user message
    addChatMessage('user', prompt);
    input.value = '';
    
    try {
        if (streaming) {
            await sendStreamingPrompt(prompt, output);
        } else {
            await sendNormalPrompt(prompt, output);
        }
    } catch (error) {
        addChatMessage('error', `Error: ${error.message}`);
    }
}

// Normal prompt
async function sendNormalPrompt(prompt, output) {
    const response = await fetch(`${API_BASE}/prompt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            prompt: prompt,
            ...currentSettings
        })
    });
    
    if (!response.ok) {
        throw new Error('Server error');
    }
    
    const data = await response.json();
    addChatMessage('assistant', data.response);
}

// Streaming prompt
async function sendStreamingPrompt(prompt, output) {
    const response = await fetch(`${API_BASE}/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            prompt: prompt,
            ...currentSettings
        })
    });
    
    if (!response.ok) {
        throw new Error('Server error');
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message assistant';
    messageDiv.innerHTML = '<div class="label">Assistant:</div><div class="content"></div>';
    output.appendChild(messageDiv);
    
    const contentDiv = messageDiv.querySelector('.content');
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        contentDiv.textContent += chunk;
        output.scrollTop = output.scrollHeight;
    }
}

// Add chat message
function addChatMessage(type, text) {
    const output = document.getElementById('chat-output');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;
    
    const label = type === 'user' ? 'You' : type === 'error' ? 'Error' : 'Assistant';
    messageDiv.innerHTML = `<div class="label">${label}:</div><div class="content">${text}</div>`;
    
    output.appendChild(messageDiv);
    output.scrollTop = output.scrollHeight;
}

// Enter key to send
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('prompt-input');
    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendPrompt();
            }
        });
    }
});

// Settings listeners
function setupSettingsListeners() {
    const tempSlider = document.getElementById('temperature');
    const tempValue = document.getElementById('temp-value');
    tempSlider.addEventListener('input', (e) => {
        tempValue.textContent = e.target.value;
        currentSettings.temperature = parseFloat(e.target.value);
    });
    
    const topPSlider = document.getElementById('top-p');
    const topPValue = document.getElementById('top-p-value');
    topPSlider.addEventListener('input', (e) => {
        topPValue.textContent = e.target.value;
        currentSettings.top_p = parseFloat(e.target.value);
    });
    
    const maxTokens = document.getElementById('max-tokens');
    maxTokens.addEventListener('change', (e) => {
        currentSettings.max_tokens = parseInt(e.target.value);
    });
    
    const topK = document.getElementById('top-k');
    topK.addEventListener('change', (e) => {
        currentSettings.top_k = parseInt(e.target.value);
    });
}

// Reset settings
function resetSettings() {
    document.getElementById('temperature').value = 0.8;
    document.getElementById('temp-value').textContent = '0.8';
    document.getElementById('max-tokens').value = 512;
    document.getElementById('top-p').value = 0.9;
    document.getElementById('top-p-value').textContent = '0.9';
    document.getElementById('top-k').value = 40;
    
    currentSettings = {
        temperature: 0.8,
        max_tokens: 512,
        top_p: 0.9,
        top_k: 40
    };
    
    alert('Settings reset to defaults');
}

// Save settings
function saveSettings() {
    localStorage.setItem('llm_settings', JSON.stringify(currentSettings));
    alert('Settings saved!');
}

// Load saved settings
document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('llm_settings');
    if (saved) {
        currentSettings = JSON.parse(saved);
        document.getElementById('temperature').value = currentSettings.temperature;
        document.getElementById('temp-value').textContent = currentSettings.temperature;
        document.getElementById('max-tokens').value = currentSettings.max_tokens;
        document.getElementById('top-p').value = currentSettings.top_p;
        document.getElementById('top-p-value').textContent = currentSettings.top_p;
        document.getElementById('top-k').value = currentSettings.top_k;
    }
});
