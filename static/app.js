// InstanceLLM Web Interface
console.log('InstanceLLM Web Interface loaded');

// Automatically detect the API base URL from the current page
const API_BASE = window.location.origin;

// State
let currentSettings = {
    temperature: 0.8,
    max_tokens: 512,
    top_p: 0.9,
    top_k: 40
};

let selectedModel = null;
let instances = [];
let activeInstance = null;

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
    console.log('DOM Content Loaded - initializing...');
    loadInstances();
    updateInstanceStatuses(); // Fetch IPs immediately
    checkServerStatus();
    loadModelsList();
    setupSettingsListeners();
    setupEnterKeyListener();
    
    // Auto-refresh status every 5 seconds
    setInterval(checkServerStatus, 5000);
    setInterval(updateInstanceStatuses, 5000);
    
    console.log('Initialization complete');
});

// Tab switching - GLOBAL FUNCTION
window.switchTab = function(tabName) {
    console.log('switchTab called:', tabName);
    // Update buttons
    const buttons = document.querySelectorAll('menu[role="tablist"] button');
    buttons.forEach(btn => {
        btn.setAttribute('aria-selected', 'false');
        btn.classList.remove('active');
    });
    
    const activeButton = document.querySelector(`button[onclick*="${tabName}"]`);
    if (activeButton) {
        activeButton.setAttribute('aria-selected', 'true');
        activeButton.classList.add('active');
    }
    
    // Update panels
    const panels = document.querySelectorAll('article[role="tabpanel"]');
    panels.forEach(panel => {
        panel.style.display = 'none';
        panel.classList.remove('active');
    });
    
    const activePanel = document.getElementById(`tab-${tabName}`);
    if (activePanel) {
        activePanel.style.display = 'block';
        activePanel.classList.add('active');
    }
    
    // Load models when switching to models tab
    if (tabName === 'models') {
        loadModelsList();
    }
};

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
    
    // Fetch list of downloaded models first
    fetch(`${API_BASE}/list-models`)
        .then(r => r.json())
        .then(data => {
            const downloadedModels = data.models || [];
            
            Object.entries(AVAILABLE_MODELS).forEach(([id, model]) => {
                const tile = document.createElement('div');
                const isDownloaded = downloadedModels.some(m => m.includes(model.file));
                tile.className = `model-tile ${isDownloaded ? 'downloaded' : ''}`;
                tile.dataset.modelId = id;
                
                tile.innerHTML = `
                    ${isDownloaded ? '<div class="downloaded-badge">✓ DOWNLOADED</div>' : ''}
                    <div class="model-tile-header">
                        <div class="model-name">${model.name}</div>
                        <div class="model-size">${model.size}</div>
                    </div>
                    <div class="model-description">${model.description}</div>
                    <div class="model-actions">
                        ${isDownloaded ? 
                            '<button onclick="useModel(\''+id+'\')">Use This Model</button>' :
                            '<button onclick="downloadModel(\''+id+'\')">Download</button>'}
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
        })
        .catch(err => {
            console.error('Failed to load models:', err);
            // Fallback to showing all models without download status
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
        });
}

// Select model tile
function selectModelTile(tile) {
    document.querySelectorAll('.model-tile').forEach(t => t.classList.remove('selected'));
    tile.classList.add('selected');
}

// Scan for downloaded models - GLOBAL FUNCTION
window.scanForModels = async function() {
    console.log('Scanning for downloaded models...');
    try {
        const response = await fetch(`${API_BASE}/list-models`);
        if (!response.ok) throw new Error('Failed to scan models');
        
        const data = await response.json();
        const count = data.models?.length || 0;
        
        // Reload the models list to show updated download status
        loadModelsList();
        
        alert(`Scan complete!\n\nFound ${count} downloaded model(s) in the models directory.`);
    } catch (error) {
        console.error('Scan error:', error);
        alert(`Failed to scan models: ${error.message}`);
    }
};

// Scan for online models - GLOBAL FUNCTION
window.scanOnlineModels = async function() {
    console.log('Refreshing online model catalog...');
    try {
        // Show loading message
        const modelsContainer = document.getElementById('models-list');
        modelsContainer.innerHTML = '<div style="padding: 20px; text-align: center;">🌐 Refreshing online model catalog...</div>';
        
        // Add a small delay to show the loading message
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // Reload the models list
        loadModelsList();
        
        alert('Online model catalog refreshed!\n\nShowing latest available models from the curated list.');
    } catch (error) {
        console.error('Online scan error:', error);
        alert('Error refreshing online models');
    }
};

// Use model - GLOBAL FUNCTION
window.useModel = function(id) {
    const model = AVAILABLE_MODELS[id];
    alert(`To use ${model.name}:\n\n1. Stop the current server\n2. Restart with: python llm_server.py models\\${model.file} 8001`);
};

// Select model (show details) - GLOBAL FUNCTION
window.selectModel = function(id) {
    console.log('selectModel called:', id);
    const model = AVAILABLE_MODELS[id];
    alert(`Model: ${model.name}\n\nSize: ${model.size}\nRepository: ${model.repo}\nFile: ${model.file}\n\nDescription:\n${model.description}`);
};

// Download model - GLOBAL FUNCTION
window.downloadModel = async function(id) {
    console.log('downloadModel called:', id);
    const model = AVAILABLE_MODELS[id];
    
    if (!confirm(`Download ${model.name} (${model.size})?\n\nThis will take several minutes depending on your internet connection.`)) {
        return;
    }
    
    const statusDiv = document.getElementById('download-status');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar-inner');
    const progressText = document.getElementById('progress-text');
    const downloadButton = event.target;
    
    // Disable button during download
    downloadButton.disabled = true;
    downloadButton.textContent = 'Downloading...';
    
    // Show progress bar
    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    progressText.textContent = '0%';
    
    statusDiv.innerHTML = `<strong>Downloading ${model.name}...</strong><br>Size: ${model.size}<br><em>Please wait, this may take several minutes...</em>`;
    
    try {
        // Start listening to progress updates via EventSource FIRST
        const eventSource = new EventSource(`${API_BASE}/download-progress/${id}`);
        console.log('EventSource created for model:', id);
        
        eventSource.onopen = function() {
            console.log('EventSource connection opened');
        };
        
        eventSource.onmessage = function(event) {
            console.log('Progress update received:', event.data);
            const data = JSON.parse(event.data);
            
            if (data.status === 'progress') {
                const percent = Math.round(data.percent);
                progressBar.style.width = percent + '%';
                progressText.textContent = `${percent}% - ${data.downloaded} / ${data.total}`;
                console.log(`Progress: ${percent}%`);
            } else if (data.status === 'complete') {
                console.log('Download complete');
                eventSource.close();
                progressBar.style.width = '100%';
                progressText.textContent = '100% - Complete';
                
                statusDiv.innerHTML = `<strong style="color: green;">✓ Download Complete!</strong><br>Model: ${data.model_name}<br>Path: ${data.model_path}<br><em>You can now restart the server with this model.</em>`;
                
                downloadButton.disabled = false;
                downloadButton.textContent = 'Downloaded ✓';
                downloadButton.style.backgroundColor = '#90EE90';
                
                setTimeout(() => {
                    progressContainer.style.display = 'none';
                }, 3000);
                
                alert(`Download complete!\n\n${data.model_name}\n\nRestart the server to use this model.`);
            } else if (data.status === 'error') {
                console.error('Download error:', data.message);
                eventSource.close();
                throw new Error(data.message);
            }
        };
        
        eventSource.onerror = function(error) {
            console.error('EventSource error:', error);
            eventSource.close();
            
            statusDiv.innerHTML = `<strong style="color: red;">✗ Download Failed</strong><br>Error: Connection lost<br><br>Check server console for details.`;
            
            progressContainer.style.display = 'none';
            downloadButton.disabled = false;
            downloadButton.textContent = 'Download';
        };
        
        // Wait a moment for EventSource to connect, then trigger the download
        await new Promise(resolve => setTimeout(resolve, 500));
        
        console.log('Triggering download via POST request');
        const response = await fetch(`${API_BASE}/download-model?model_id=${id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            const error = await response.json();
            eventSource.close();
            throw new Error(error.detail || 'Failed to start download');
        }
        
        const result = await response.json();
        console.log('Download started:', result);
        
    } catch (error) {
        console.error('Download error:', error);
        statusDiv.innerHTML = `<strong style="color: red;">✗ Download Failed</strong><br>Error: ${error.message}<br><br>If huggingface_hub is not installed, run:<br><code>pip install huggingface_hub</code>`;
        
        progressContainer.style.display = 'none';
        downloadButton.disabled = false;
        downloadButton.textContent = 'Download';
        
        alert(`Download failed: ${error.message}\n\nCheck the download status panel for details.`);
    }
};

// Send prompt - GLOBAL FUNCTION
window.sendPrompt = async function() {
    console.log('sendPrompt called');
    const input = document.getElementById('prompt-input');
    const output = document.getElementById('chat-output');
    const streaming = document.getElementById('streaming-mode').checked;
    
    const prompt = input.value.trim();
    if (!prompt) {
        console.log('Empty prompt, returning');
        return;
    }
    
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
};

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
function setupEnterKeyListener() {
    const input = document.getElementById('prompt-input');
    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                window.sendPrompt();
            }
        });
        console.log('Enter key listener attached');
    }
}

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

// Reset settings - GLOBAL FUNCTION
window.resetSettings = function() {
    console.log('resetSettings called');
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
};

// Save settings - GLOBAL FUNCTION
window.saveSettings = function() {
    console.log('saveSettings called');
    localStorage.setItem('llm_settings', JSON.stringify(currentSettings));
    alert('Settings saved!');
};

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

// ========================================
// INSTANCE MANAGEMENT
// ========================================

// Load instances from localStorage
function loadInstances() {
    const saved = localStorage.getItem('llm_instances');
    if (saved) {
        instances = JSON.parse(saved);
        
        // Update default instance URL and port if needed
        const defaultInstance = instances.find(i => i.id === 'default');
        if (defaultInstance) {
            defaultInstance.url = API_BASE;
            defaultInstance.port = 8000;
            // Update local_ip to current hostname if not already set
            if (!defaultInstance.local_ip) {
                defaultInstance.local_ip = window.location.hostname;
            }
            // Ensure default instance has a model
            if (!defaultInstance.model) {
                defaultInstance.model = 'Llama-3.2-3B-Instruct-Q4_K_M.gguf';
            }
        }
    } else {
        // Add default instance (current server)
        instances = [{
            id: 'default',
            name: 'Main Server',
            url: API_BASE,
            port: 8000,
            type: 'local',
            status: 'unknown',
            model: 'Llama-3.2-3B-Instruct-Q4_K_M.gguf'  // Default model
        }];
        saveInstances();
    }
    
    renderInstances();
    if (instances.length > 0) {
        selectInstance(instances[0].id);
    }
}

// Save instances to localStorage
function saveInstances() {
    localStorage.setItem('llm_instances', JSON.stringify(instances));
}

// Render instance tiles
function renderInstances() {
    const container = document.getElementById('instances-list');
    container.innerHTML = '';
    
    instances.forEach(instance => {
        const tile = document.createElement('div');
        tile.className = `instance-tile ${instance.id === (activeInstance?.id) ? 'active' : ''}`;
        tile.dataset.instanceId = instance.id;
        
        const statusClass = instance.status === 'healthy' ? 'online' : 'offline';
        const statusText = instance.status === 'healthy' ? 'Online' : 'Offline';
        
        // Display URL with IP if available, otherwise use hostname from current page
        let displayUrl;
        if (instance.local_ip) {
            displayUrl = `${instance.local_ip}:${instance.port}`;
        } else if (instance.url) {
            // Extract hostname from URL
            try {
                const urlObj = new URL(instance.url);
                displayUrl = `${urlObj.hostname}:${instance.port}`;
            } catch {
                displayUrl = `${window.location.hostname}:${instance.port}`;
            }
        } else {
            displayUrl = `${window.location.hostname}:${instance.port}`;
        }
        
        tile.innerHTML = `
            <div class="instance-name">${instance.name}</div>
            <div class="instance-port">${displayUrl}</div>
            <div class="instance-status">
                <span class="status-dot ${statusClass}"></span>
                <span>${statusText}</span>
            </div>
            <div class="instance-controls">
                ${instance.type === 'local' && instance.id !== 'default' ? `
                    <button onclick="event.stopPropagation(); startInstance('${instance.id}')" title="Start">▶</button>
                    <button onclick="event.stopPropagation(); stopInstance('${instance.id}')" title="Stop">■</button>
                ` : ''}
                ${instance.id !== 'default' ? `
                    <button onclick="event.stopPropagation(); removeInstance('${instance.id}')" title="Remove">×</button>
                ` : ''}
            </div>
        `;
        
        tile.addEventListener('click', () => selectInstance(instance.id));
        container.appendChild(tile);
    });
}

// Select an instance
function selectInstance(instanceId) {
    const instance = instances.find(i => i.id === instanceId);
    if (!instance) return;
    
    activeInstance = instance;
    
    // Update API_BASE for the active instance
    // Note: This would need more work to properly switch contexts
    
    // Update UI
    renderInstances();
    checkServerStatus();
}

// Update instance statuses
async function updateInstanceStatuses() {
    for (const instance of instances) {
        try {
            const response = await fetch(`${instance.url}/health`, { timeout: 2000 });
            const data = await response.json();
            instance.status = data.status;
            instance.local_ip = data.local_ip;
            instance.resources = data.resources;
            console.log(`Instance ${instance.name} - IP: ${instance.local_ip}, Status: ${instance.status}`);
        } catch (error) {
            instance.status = 'offline';
            console.log(`Instance ${instance.name} - Offline`);
        }
    }
    renderInstances();
    updateResourceDisplay();
    saveInstances(); // Save the updated IP addresses
}

// Update resource display
function updateResourceDisplay() {
    // Find the main server instance and show its resources
    const mainInstance = instances.find(i => i.id === 'default') || instances[0];
    if (mainInstance && mainInstance.resources && mainInstance.resources.available) {
        const r = mainInstance.resources;
        const resourceInfo = `CPU: ${r.cpu_percent.toFixed(1)}% | Memory: ${r.memory_percent.toFixed(1)}% (${r.memory_available_gb.toFixed(1)}GB available)`;
        
        // Update or create resource display in settings tab
        let resourceDiv = document.getElementById('resource-display');
        if (!resourceDiv) {
            resourceDiv = document.createElement('div');
            resourceDiv.id = 'resource-display';
            resourceDiv.style.cssText = 'margin-top: 12px; padding: 8px; background: #c0c0c0; border: 2px inset; font-size: 11px;';
            const settingsPanel = document.querySelector('.settings-panel');
            if (settingsPanel) {
                settingsPanel.appendChild(resourceDiv);
            }
        }
        resourceDiv.innerHTML = `<strong>System Resources:</strong> ${resourceInfo}`;
    }
}

// Show add instance dialog
window.showAddInstanceDialog = function() {
    document.getElementById('add-instance-dialog').style.display = 'flex';
    
    // Populate model dropdown
    const modelSelect = document.getElementById('instance-model');
    modelSelect.innerHTML = '<option value="">Select model...</option>';
    
    fetch(`${API_BASE}/list-models`)
        .then(r => r.json())
        .then(data => {
            if (data.models) {
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model.split('/').pop();
                    modelSelect.appendChild(option);
                });
            }
        })
        .catch(err => console.error('Failed to load models:', err));
};

// Close add instance dialog
window.closeAddInstanceDialog = function() {
    document.getElementById('add-instance-dialog').style.display = 'none';
};

// Toggle instance type fields
window.toggleInstanceType = function() {
    const type = document.querySelector('input[name="instance-type"]:checked').value;
    document.getElementById('new-instance-fields').style.display = type === 'new' ? 'block' : 'none';
    document.getElementById('custom-instance-fields').style.display = type === 'custom' ? 'block' : 'none';
};

// Add instance
window.addInstance = async function() {
    const type = document.querySelector('input[name="instance-type"]:checked').value;
    
    if (type === 'new') {
        const name = document.getElementById('instance-name').value.trim();
        const port = parseInt(document.getElementById('instance-port').value);
        const model = document.getElementById('instance-model').value;
        
        if (!name || !port || !model) {
            alert('Please fill in all fields');
            return;
        }
        
        // Create new instance via API
        try {
            const response = await fetch(`${API_BASE}/create-instance`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, port, model })
            });
            
            if (!response.ok) {
                throw new Error('Failed to create instance');
            }
            
            const result = await response.json();
            
            // Get the IP from the main instance or use API_BASE
            const mainInstance = instances.find(i => i.id === 'default');
            const baseIp = mainInstance?.local_ip || window.location.hostname;
            
            instances.push({
                id: result.instance_id || `instance-${Date.now()}`,
                name: name,
                url: `http://${baseIp}:${port}`,
                port: port,
                type: 'local',
                model: model,
                status: 'offline',
                local_ip: baseIp
            });
            
            // Show resource warning if an instance was paused
            if (result.paused_instance) {
                alert(`Instance created!\n\nWarning: ${result.paused_instance} was paused due to high memory usage.`);
            }
            
        } catch (error) {
            alert(`Failed to create instance: ${error.message}`);
            return;
        }
        
    } else {
        const name = document.getElementById('custom-name').value.trim();
        const url = document.getElementById('custom-url').value.trim();
        
        if (!name || !url) {
            alert('Please fill in all fields');
            return;
        }
        
        // Extract port from URL
        const portMatch = url.match(/:(\d+)/);
        const port = portMatch ? parseInt(portMatch[1]) : 80;
        
        instances.push({
            id: `custom-${Date.now()}`,
            name: name,
            url: url,
            port: port,
            type: 'custom',
            status: 'unknown'
        });
    }
    
    saveInstances();
    renderInstances();
    closeAddInstanceDialog();
    
    // Check status of new instance
    updateInstanceStatuses();
};

// Remove instance
window.removeInstance = async function(instanceId) {
    const instance = instances.find(i => i.id === instanceId);
    if (!instance) return;
    
    if (!confirm(`Remove instance "${instance.name}"?`)) return;
    
    // If local instance, stop it first
    if (instance.type === 'local') {
        try {
            await fetch(`${API_BASE}/stop-instance/${instanceId}`, { method: 'POST' });
        } catch (error) {
            console.error('Failed to stop instance:', error);
        }
    }
    
    instances = instances.filter(i => i.id !== instanceId);
    
    // If active instance was removed, select first remaining
    if (activeInstance?.id === instanceId && instances.length > 0) {
        selectInstance(instances[0].id);
    }
    
    saveInstances();
    renderInstances();
};

// Start instance
window.startInstance = async function(instanceId) {
    const instance = instances.find(i => i.id === instanceId);
    if (!instance) {
        alert('Instance not found');
        return;
    }
    
    // Don't allow starting the default instance (it's already running)
    if (instance.id === 'default') {
        alert('The Main Server is already running.\n\nThis is the server hosting this web interface.');
        return;
    }
    
    if (instance.status === 'healthy') {
        alert('Instance is already running');
        return;
    }
    
    // Check if instance has a model
    if (!instance.model) {
        alert(`Cannot start instance: No model assigned.\n\nPlease recreate this instance with a model selected.`);
        return;
    }
    
    try {
        console.log(`Starting instance: ${instance.name} with model: ${instance.model}`);
        
        const response = await fetch(`${API_BASE}/start-instance`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                instance_id: instanceId,
                port: instance.port,
                model: instance.model
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to start instance');
        }
        
        const result = await response.json();
        console.log('Start result:', result);
        alert(`Starting instance: ${instance.name}\n\nPlease wait a few seconds for the server to start...`);
        
        // Update status after a delay
        setTimeout(updateInstanceStatuses, 3000);
    } catch (error) {
        console.error('Start instance error:', error);
        alert(`Failed to start instance: ${error.message}`);
    }
};

// Stop instance
window.stopInstance = async function(instanceId) {
    const instance = instances.find(i => i.id === instanceId);
    if (!instance) {
        alert('Instance not found');
        return;
    }
    
    // Don't allow stopping the default instance (it's hosting the web interface)
    if (instance.id === 'default') {
        alert('Cannot stop the Main Server.\n\nThis server is hosting the web interface you\'re using.\nTo stop it, close the terminal window or press Ctrl+C.');
        return;
    }
    
    if (!confirm(`Stop instance "${instance.name}"?`)) return;
    
    try {
        console.log(`Stopping instance: ${instance.name}`);
        
        const response = await fetch(`${API_BASE}/stop-instance`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                instance_id: instanceId,
                port: instance.port
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to stop instance');
        }
        
        const result = await response.json();
        console.log('Stop result:', result);
        
        instance.status = 'offline';
        renderInstances();
        
        if (result.status === 'error') {
            alert(result.message);
        } else {
            alert(`Stopped instance: ${instance.name}`);
        }
        
        // Update status after a delay
        setTimeout(updateInstanceStatuses, 1000);
    } catch (error) {
        console.error('Stop instance error:', error);
        alert(`Failed to stop instance: ${error.message}`);
    }
};
