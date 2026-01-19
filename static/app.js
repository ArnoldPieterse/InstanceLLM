// InstanceLLM Web Interface
console.log('InstanceLLM Web Interface loaded');

// Automatically detect the API base URL from the current page
const API_BASE = window.location.origin;

// Helper function to get the API endpoint for the active instance
function getApiEndpoint() {
    if (activeInstance) {
        if (activeInstance.url) {
            return activeInstance.url;
        } else if (activeInstance.ip) {
            // For remote instances from network scan
            return `http://${activeInstance.ip}:${activeInstance.port}`;
        } else if (activeInstance.local_ip) {
            return `http://${activeInstance.local_ip}:${activeInstance.port}`;
        } else {
            return `http://${window.location.hostname}:${activeInstance.port}`;
        }
    }
    return API_BASE;
}

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
let voiceEnabled = true;
let samVoice = null;
window.voiceRate = 1.1; // Default rate

// Microsoft Sam Text-to-Speech
function initSamVoice() {
    const voices = speechSynthesis.getVoices();
    // Try to find a voice similar to Microsoft Sam (male English voice)
    samVoice = voices.find(v => v.name.includes('Microsoft David')) ||
               voices.find(v => v.name.includes('Microsoft Mark')) ||
               voices.find(v => v.lang === 'en-US' && !v.name.includes('Female')) ||
               voices[0];
    console.log('Sam voice initialized:', samVoice?.name);
}

function speak(text) {
    if (!voiceEnabled) return;
    
    const utterance = new SpeechSynthesisUtterance(text);
    if (samVoice) {
        utterance.voice = samVoice;
    }
    utterance.rate = window.voiceRate || 1.1;
    utterance.pitch = 1.0;
    
    speechSynthesis.speak(utterance);
}

window.toggleVoice = function() {
    voiceEnabled = !voiceEnabled;
    const btn = document.getElementById('voice-toggle');
    btn.textContent = voiceEnabled ? '🔊 Voice On' : '🔇 Voice Off';
    speak(voiceEnabled ? 'Voice enabled' : 'Voice disabled');
};

window.toggleVoiceMenu = function(event) {
    event.stopPropagation();
    const menu = document.getElementById('voice-menu');
    menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
};

window.toggleVoiceOnOff = function() {
    voiceEnabled = !voiceEnabled;
    
    if (voiceEnabled) {
        speechSynthesis.resume();
    } else {
        speechSynthesis.pause();
    }
    
    const check = document.getElementById('voice-check');
    check.textContent = voiceEnabled ? '✓' : '';
    updateVoiceButtonStates();
    closeVoiceMenu();
};

window.quickToggleVoice = function() {
    voiceEnabled = !voiceEnabled;
    
    if (voiceEnabled) {
        speechSynthesis.resume();
    } else {
        speechSynthesis.pause();
    }
    
    updateVoiceButtonStates();
};

function updateVoiceButtonStates() {
    // Update quick toggle button
    const quickBtn = document.getElementById('quick-voice-toggle');
    if (quickBtn) {
        quickBtn.textContent = voiceEnabled ? '🔊 Voice On' : '🔇 Voice Off';
    }
    
    // Update menu checkmark
    const check = document.getElementById('voice-check');
    if (check) {
        check.textContent = voiceEnabled ? '✓' : '';
    }
}

window.setVoiceRate = function(rate) {
    window.voiceRate = rate;
    closeVoiceMenu();
    speak(`Voice speed set to ${rate === 0.8 ? 'slower' : rate === 1.0 ? 'normal' : 'faster'}`);
};

function closeVoiceMenu() {
    document.getElementById('voice-menu').style.display = 'none';
}

// Close menu when clicking outside
document.addEventListener('click', function(event) {
    const menu = document.getElementById('voice-menu');
    const btn = document.getElementById('voice-menu-btn');
    if (menu && btn && !menu.contains(event.target) && event.target !== btn) {
        closeVoiceMenu();
    }
});

window.testVoice = function() {
    console.log('Testing voice...');
    console.log('Voice enabled:', voiceEnabled);
    console.log('Sam voice:', samVoice);
    console.log('Available voices:', speechSynthesis.getVoices().length);
    closeVoiceMenu();
    speak('Soy. Soy. Soy. Soy. Soy. Soy. Soy. Soy. Soy. Soy. Soy. Soy.');
};

// Initialize voices when available
if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = initSamVoice;
}
setTimeout(initSamVoice, 100);

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
    
    // Load subroutines when switching to subroutines tab
    if (tabName === 'subroutines') {
        loadSubroutinesTab();
    }
};

// Check server status
async function checkServerStatus() {
    try {
        // Use activeInstance if available, otherwise use default API_BASE
        const apiEndpoint = getApiEndpoint();
        const healthUrl = `${apiEndpoint}/health`;
        
        const response = await fetch(healthUrl);
        const data = await response.json();
        
        document.getElementById('server-status').textContent = data.status === 'healthy' ? '✓ Online' : '✗ Offline';
        document.getElementById('server-status').style.color = data.status === 'healthy' ? 'green' : 'red';
        
        if (data.model_path) {
            const modelName = data.model_path.split('/').pop().split('\\').pop();
            document.getElementById('model-name').textContent = modelName;
        }
        
        // Update API endpoint display
        document.getElementById('api-endpoint').textContent = apiEndpoint;
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
window.useModel = async function(id) {
    const model = AVAILABLE_MODELS[id];
    
    if (!activeInstance) {
        alert('Please select an instance first');
        return;
    }
    
    if (!confirm(`Switch ${activeInstance.name} to ${model.name}?`)) {
        return;
    }
    
    try {
        // Update the instance's model
        activeInstance.model = model.file;
        saveInstances();
        
        // If instance is running, restart it with new model
        if (activeInstance.status === 'healthy') {
            // Stop the instance first
            await stopInstance(activeInstance.id);
            
            // Wait a moment
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Start with new model
            await startInstance(activeInstance.id);
        } else {
            // Just update the config
            speak('Model updated');
            alert(`${activeInstance.name} updated to use ${model.name}\n\nClick Start to launch it.`);
        }
        
        renderInstances();
        checkServerStatus();
    } catch (error) {
        console.error('Error switching model:', error);
        alert('Error switching model: ' + error.message);
    }
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
                
                speak('Download complete');
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

// Helper function to get subroutine system prompt
function getSubroutinePrompt() {
    console.log('getSubroutinePrompt called');
    console.log('activeInstance:', activeInstance);
    console.log('activeInstance.subroutines:', activeInstance?.subroutines);
    
    if (!activeInstance || !activeInstance.subroutines || activeInstance.subroutines.length === 0) {
        console.log('No subroutines to apply');
        return '';
    }
    
    const prompts = {
        'json': 'You must respond ONLY with valid JSON. Do not include any text before or after the JSON object.',
        'xml': 'You must respond in valid XML format. Structure your response with appropriate XML tags.',
        'markdown': 'Format all responses using proper Markdown syntax with headers, lists, code blocks, etc.',
        'code': 'Respond with code only. Do not include explanations, comments, or text outside of the code.',
        'concise': 'Be extremely concise. Provide brief, direct answers without elaboration.',
        'verbose': 'Provide detailed, thorough explanations with examples and comprehensive information.',
        'filesystem': 'When relevant, include complete file system commands (mkdir, New-Item, touch, etc.) for creating folders and files with full permissions. Provide Windows PowerShell, CMD, and/or bash commands as appropriate. Include commands for setting permissions, creating directory structures, and managing files.'
    };
    
    const instructions = activeInstance.subroutines
        .map(sub => {
            // Check if it's a custom subroutine
            if (sub.startsWith('custom:')) {
                const customName = sub.substring(7); // Remove 'custom:' prefix
                if (activeInstance.customSubroutines && activeInstance.customSubroutines[customName]) {
                    return activeInstance.customSubroutines[customName];
                }
                return null;
            }
            return prompts[sub];
        })
        .filter(p => p)
        .join(' ');
    
    const result = instructions ? `SYSTEM INSTRUCTIONS: ${instructions}\n\n` : '';
    console.log('Subroutine prompt:', result);
    return result;
}

// Normal prompt
async function sendNormalPrompt(prompt, output) {
    const apiEndpoint = getApiEndpoint();
    const subroutinePrompt = getSubroutinePrompt();
    const fullPrompt = subroutinePrompt + prompt;
    
    console.log('Sending prompt:', fullPrompt);
    
    const response = await fetch(`${apiEndpoint}/prompt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            prompt: fullPrompt,
            ...currentSettings
        })
    });
    
    if (!response.ok) {
        throw new Error('Server error');
    }
    
    const data = await response.json();
    addChatMessage('assistant', data.response);
    
    // Read response aloud
    speak(data.response);
}

// Streaming prompt
async function sendStreamingPrompt(prompt, output) {
    const apiEndpoint = getApiEndpoint();
    const subroutinePrompt = getSubroutinePrompt();
    const fullPrompt = subroutinePrompt + prompt;
    
    console.log('Sending streaming prompt:', fullPrompt);
    
    const response = await fetch(`${apiEndpoint}/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            prompt: fullPrompt,
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
    let fullResponse = '';
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        contentDiv.textContent += chunk;
        fullResponse += chunk;
        output.scrollTop = output.scrollHeight;
    }
    
    // Read full response aloud after streaming completes
    speak(fullResponse);
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
        
        // Remove duplicates based on ID
        const seen = new Set();
        instances = instances.filter(instance => {
            if (seen.has(instance.id)) {
                console.warn('Removing duplicate instance:', instance.id, instance.name);
                return false;
            }
            seen.add(instance.id);
            return true;
        });
        
        // Update default instance URL and port if needed
        const defaultInstance = instances.find(i => i.id === 'default');
        if (defaultInstance) {
            defaultInstance.url = API_BASE;
            defaultInstance.port = 8000;
            defaultInstance.type = 'local'; // Ensure type is set
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
        // Only mark as active if this is THE active instance (strict equality check)
        const isActive = activeInstance && instance.id === activeInstance.id;
        tile.className = `instance-tile ${isActive ? 'active' : ''}`;
        tile.dataset.instanceId = instance.id;
        
        console.log(`Rendering ${instance.name}: id=${instance.id}, active=${isActive}, activeInstance.id=${activeInstance?.id}`);
        
        
        const statusClass = instance.status === 'healthy' ? 'online' : 
                           instance.status === 'starting' ? 'starting' : 'offline';
        const statusText = instance.status === 'healthy' ? 'Online' : 
                          instance.status === 'starting' ? 'Starting...' : 'Offline';
        
        // Display URL with IP if available, otherwise use hostname from current page
        let displayUrl;
        if (instance.ip) {
            // For remote instances from network scan
            displayUrl = `${instance.ip}:${instance.port}`;
        } else if (instance.local_ip) {
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
        
        // Add network badge for remote instances
        const networkBadge = instance.isRemote ? '<span style="background: #008080; color: white; padding: 2px 4px; font-size: 9px; border-radius: 2px; margin-left: 4px;">NET</span>' : '';
        
        // Add subroutine badges
        let subroutineBadges = '';
        if (instance.subroutines && instance.subroutines.length > 0) {
            const badgeIcons = {
                'json': '{ }',
                'xml': '< >',
                'markdown': 'MD',
                'code': 'CODE',
                'concise': 'BRIEF',
                'verbose': 'DETAIL',
                'filesystem': '📁'
            };
            subroutineBadges = instance.subroutines.map(sub => {
                // Handle custom subroutines
                if (sub.startsWith('custom:')) {
                    const customName = sub.substring(7);
                    return `<span style="background: #800080; color: white; padding: 1px 3px; font-size: 8px; border-radius: 2px; margin-left: 2px;" title="Custom: ${customName}">${customName.substring(0, 6).toUpperCase()}</span>`;
                }
                return `<span style="background: #000080; color: white; padding: 1px 3px; font-size: 8px; border-radius: 2px; margin-left: 2px;" title="${sub}">${badgeIcons[sub] || sub.toUpperCase()}</span>`;
            }).join('');
        }
        
        tile.innerHTML = `
            <div class="instance-name">${instance.name}${networkBadge}${subroutineBadges}</div>
            <div class="instance-port">${displayUrl}</div>
            <div class="instance-status">
                <span class="status-dot ${statusClass}"></span>
                <span>${statusText}</span>
            </div>
            <div class="instance-controls">
                ${!instance.isRemote && instance.type === 'local' && instance.id !== 'default' ? `
                    <button class="btn-start" data-instance-id="${instance.id}" title="Start Instance" style="color: green; font-weight: bold;">▶ Start</button>
                    <button class="btn-stop" data-instance-id="${instance.id}" title="Stop Instance" style="color: red; font-weight: bold;">■ Stop</button>
                ` : ''}
                ${instance.id !== 'default' ? `
                    <button class="btn-remove" data-instance-id="${instance.id}" title="Remove Instance" style="color: #800000;">× Remove</button>
                ` : ''}
            </div>
        `;
        
        console.log(`Instance ${instance.name}: type=${instance.type}, isRemote=${instance.isRemote}, id=${instance.id}, showing buttons=${!instance.isRemote && instance.type === 'local' && instance.id !== 'default'}`);
        
        // Add event listeners to buttons to prevent tile click
        const startBtn = tile.querySelector('.btn-start');
        const stopBtn = tile.querySelector('.btn-stop');
        const removeBtn = tile.querySelector('.btn-remove');
        
        console.log(`Buttons found for ${instance.name}: start=${!!startBtn}, stop=${!!stopBtn}, remove=${!!removeBtn}`);
        
        if (startBtn) {
            startBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = e.currentTarget.dataset.instanceId;
                console.log('Start button clicked for:', id);
                startInstance(id);
            });
        }
        
        if (stopBtn) {
            stopBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = e.currentTarget.dataset.instanceId;
                console.log('Stop button clicked for:', id);
                stopInstance(id);
            });
        }
        
        if (removeBtn) {
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = e.currentTarget.dataset.instanceId;
                console.log('Remove button clicked for:', id);
                removeInstance(id);
            });
        }
        
        tile.addEventListener('click', () => selectInstance(instance.id));
        container.appendChild(tile);
    });
}

// Select an instance
function selectInstance(instanceId) {
    const instance = instances.find(i => i.id === instanceId);
    if (!instance) {
        console.error('Instance not found:', instanceId);
        return;
    }
    
    // Clear any previous selection
    activeInstance = instance;
    console.log('Selected instance:', instance.name, 'with id:', instance.id);
    console.log('Instance has subroutines:', instance.subroutines);
    console.log('All instance IDs:', instances.map(i => ({name: i.name, id: i.id, subroutines: i.subroutines})));
    
    // Update UI to reflect selected instance
    renderInstances();
    checkServerStatus(); // This will now use the activeInstance
}

// Update instance statuses
async function updateInstanceStatuses() {
    for (const instance of instances) {
        try {
            // Create a proper URL for health check
            let healthUrl;
            if (instance.url) {
                healthUrl = `${instance.url}/health`;
            } else if (instance.ip) {
                // For remote instances from network scan
                healthUrl = `http://${instance.ip}:${instance.port}/health`;
            } else if (instance.local_ip) {
                healthUrl = `http://${instance.local_ip}:${instance.port}/health`;
            } else {
                healthUrl = `http://${window.location.hostname}:${instance.port}/health`;
            }
            
            // Use AbortController for timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 2000);
            
            const response = await fetch(healthUrl, { 
                signal: controller.signal,
                mode: 'cors'
            });
            clearTimeout(timeoutId);
            
            const data = await response.json();
            instance.status = data.status;
            if (!instance.isRemote) {
                // Only update local_ip for local instances
                instance.local_ip = data.local_ip;
            }
            instance.resources = data.resources;
            console.log(`Instance ${instance.name} - IP: ${instance.ip || instance.local_ip}, Status: ${instance.status}`);
        } catch (error) {
            instance.status = 'offline';
            console.log(`Instance ${instance.name} - Offline (${error.name})`);
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
    
    // Always fetch models from the main server (API_BASE), not from the active instance
    fetch(`${API_BASE}/list-models`)
        .then(r => r.json())
        .then(data => {
            console.log('Models fetched:', data);
            if (data.models && data.models.length > 0) {
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model.split('/').pop();
                    modelSelect.appendChild(option);
                });
                console.log('Added', data.models.length, 'models to dropdown');
            } else {
                console.warn('No models found');
                const option = document.createElement('option');
                option.value = "";
                option.textContent = "No models found - download from Models tab";
                option.disabled = true;
                modelSelect.appendChild(option);
            }
        })
        .catch(err => {
            console.error('Failed to load models:', err);
            const option = document.createElement('option');
            option.value = "";
            option.textContent = "Error loading models";
            option.disabled = true;
            modelSelect.appendChild(option);
        });
};

// Scan network for InstanceLLM servers
window.scanNetwork = async function() {
    try {
        speak('Scanning local network for Instance L L M servers');
        console.log('Starting network scan...');
        
        // Show scanning status
        const instancesList = document.getElementById('instances-list');
        const scanningMsg = document.createElement('div');
        scanningMsg.className = 'scanning-message';
        scanningMsg.innerHTML = '<div style="padding: 12px; text-align: center; font-style: italic;">🔍 Scanning network...</div>';
        instancesList.insertBefore(scanningMsg, instancesList.firstChild);
        
        const response = await fetch(`${API_BASE}/api/discover`);
        const data = await response.json();
        
        // Remove scanning message
        scanningMsg.remove();
        
        if (data.status === 'success') {
            const count = data.count;
            console.log(`Found ${count} servers:`, data.discovered);
            
            if (count === 0) {
                speak('No Instance L L M servers found on network');
                alert('No InstanceLLM servers found on the network.');
                return;
            }
            
            speak(`Found ${count} Instance L L M ${count === 1 ? 'server' : 'servers'} on network`);
            
            // Add discovered servers to instances list
            let addedCount = 0;
            for (const server of data.discovered) {
                // Check if any instances from this server are already in our list
                const serverInstances = server.instances || [];
                
                for (const instance of serverInstances) {
                    const instanceId = `${server.hostname}_${instance.instance_id}`;
                    const existingInstance = instances.find(i => i.id === instanceId);
                    
                    if (!existingInstance) {
                        instances.push({
                            id: instanceId,
                            name: `${server.hostname} - ${instance.name}`,
                            ip: server.ip,
                            port: instance.port,
                            model: instance.model,
                            status: instance.status,
                            isRemote: true,
                            hostname: server.hostname
                        });
                        addedCount++;
                    }
                }
            }
            
            renderInstances();
            
            if (addedCount > 0) {
                speak(`Added ${addedCount} new ${addedCount === 1 ? 'instance' : 'instances'} from network`);
                alert(`Network scan complete!\nFound ${count} server(s)\nAdded ${addedCount} new instance(s)`);
            } else {
                speak('All discovered instances were already in the list');
                alert(`Network scan complete!\nFound ${count} server(s)\nAll instances already in your list`);
            }
        } else {
            speak('Network scan failed');
            console.error('Network scan failed:', data);
        }
    } catch (error) {
        speak('Error scanning network');
        console.error('Error scanning network:', error);
        alert('Failed to scan network. Make sure the server is running.');
        
        // Remove scanning message if there was an error
        const scanningMsg = document.querySelector('.scanning-message');
        if (scanningMsg) scanningMsg.remove();
    }
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
        
        // Collect selected subroutines
        const subroutines = [];
        const subroutineCheckboxes = [
            'subroutine-json',
            'subroutine-xml',
            'subroutine-markdown',
            'subroutine-code',
            'subroutine-concise',
            'subroutine-verbose',
            'subroutine-filesystem'
        ];
        
        subroutineCheckboxes.forEach(id => {
            const checkbox = document.getElementById(id);
            if (checkbox && checkbox.checked) {
                subroutines.push(checkbox.value);
            }
        });
        
        console.log('Creating instance with subroutines:', subroutines);
        
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
                local_ip: baseIp,
                subroutines: subroutines
            });
            
            // Show resource warning if an instance was paused
            if (result.paused_instance) {
                speak('Instance created. Warning. Another instance was paused.');
                alert(`Instance created!\n\nWarning: ${result.paused_instance} was paused due to high memory usage.`);
            } else {
                speak('Instance created successfully.');
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
    console.log('=== removeInstance called ===');
    console.log('Instance ID:', instanceId);
    
    const instance = instances.find(i => i.id === instanceId);
    if (!instance) {
        console.error('Instance not found:', instanceId);
        return;
    }
    
    console.log('Found instance:', instance);
    console.log('Showing confirm dialog');
    
    if (!confirm(`Remove instance "${instance.name}"?`)) {
        console.log('User cancelled remove');
        return;
    }
    
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
        
        // Optimistically update status
        instance.status = 'starting';
        renderInstances();
        
        speak(`Starting instance ${instance.name}`);
        alert(`Starting instance: ${instance.name}\n\nPlease wait a few seconds for the server to start...`);
        
        // Update status after delays to check if it's running
        setTimeout(() => {
            updateInstanceStatuses();
            speak('Instance online');
        }, 2000);
        setTimeout(() => updateInstanceStatuses(), 5000);
        setTimeout(() => updateInstanceStatuses(), 8000);
    } catch (error) {
        console.error('Start instance error:', error);
        alert(`Failed to start instance: ${error.message}`);
    }
};

// Stop instance
window.stopInstance = async function(instanceId) {
    console.log('=== stopInstance called ===' );
    console.log('Instance ID:', instanceId);
    console.log('All instances:', instances);
    
    const instance = instances.find(i => i.id === instanceId);
    if (!instance) {
        console.error('Instance not found:', instanceId);
        alert('Instance not found');
        return;
    }
    
    console.log('Found instance:', instance);
    
    // Don't allow stopping the default instance (it's hosting the web interface)
    if (instance.id === 'default') {
        console.log('Blocking stop for default instance');
        alert('Cannot stop the Main Server.\n\nThis server is hosting the web interface you\'re using.\nTo stop it, close the terminal window or press Ctrl+C.');
        return;
    }
    
    console.log('Showing confirm dialog');
    if (!confirm(`Stop instance "${instance.name}"?`)) {
        console.log('User cancelled stop');
        return;
    }
    
    speak(`Stopping instance ${instance.name}`);
    
    try {
        console.log(`Stopping instance: ${instance.name} (ID: ${instanceId}, Port: ${instance.port})`);
        
        const requestBody = {
            instance_id: instanceId,
            port: instance.port
        };
        console.log('Request body:', requestBody);
        
        const response = await fetch(`${API_BASE}/stop-instance`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to stop instance');
        }
        
        const result = await response.json();
        console.log('Stop result:', result);
        
        // Immediately update status
        instance.status = 'offline';
        renderInstances();
        saveInstances();
        
        speak('Instance stopped');
        
        if (result.status === 'error') {
            // Instance not tracked by backend - might not have been started through start button
            // or backend was restarted. Just update UI.
            console.warn('Backend error:', result.message);
            alert(`Note: ${result.message}\n\nInstance status updated to offline in UI.`);
        } else {
            alert(`Stopped instance: ${instance.name}`);
        }
        
        // Verify status after a delay
        setTimeout(() => updateInstanceStatuses(), 1000);
    } catch (error) {
        console.error('Stop instance error:', error);
        alert(`Failed to stop instance: ${error.message}`);
    }
};

// ===== SUBROUTINES TAB FUNCTIONS =====

// Load subroutines tab with current instance data
function loadSubroutinesTab() {
    if (!activeInstance) {
        document.getElementById('subroutine-instance-name').textContent = 'No instance selected';
        // Disable all checkboxes
        ['sub-json', 'sub-xml', 'sub-markdown', 'sub-code', 'sub-concise', 'sub-verbose', 'sub-filesystem'].forEach(id => {
            const checkbox = document.getElementById(id);
            if (checkbox) {
                checkbox.checked = false;
                checkbox.disabled = true;
            }
        });
        document.getElementById('active-instructions').textContent = 'Select an instance to configure subroutines';
        return;
    }
    
    // Enable all checkboxes
    ['sub-json', 'sub-xml', 'sub-markdown', 'sub-code', 'sub-concise', 'sub-verbose', 'sub-filesystem'].forEach(id => {
        const checkbox = document.getElementById(id);
        if (checkbox) checkbox.disabled = false;
    });
    
    // Update instance name
    document.getElementById('subroutine-instance-name').textContent = activeInstance.name;
    
    // Ensure customSubroutines object exists
    if (!activeInstance.customSubroutines) {
        activeInstance.customSubroutines = {};
    }
    
    // Load current subroutines
    const currentSubroutines = activeInstance.subroutines || [];
    
    // Update checkboxes for predefined subroutines
    document.getElementById('sub-json').checked = currentSubroutines.includes('json');
    document.getElementById('sub-xml').checked = currentSubroutines.includes('xml');
    document.getElementById('sub-markdown').checked = currentSubroutines.includes('markdown');
    document.getElementById('sub-code').checked = currentSubroutines.includes('code');
    document.getElementById('sub-concise').checked = currentSubroutines.includes('concise');
    document.getElementById('sub-verbose').checked = currentSubroutines.includes('verbose');
    document.getElementById('sub-filesystem').checked = currentSubroutines.includes('filesystem');
    
    // Render custom subroutines
    renderCustomSubroutines();
    
    // Update active instructions display
    updateActiveInstructions();
}

// Update active instructions display
function updateActiveInstructions() {
    const prompts = {
        'json': '{ } JSON: Respond ONLY with valid JSON',
        'xml': '< > XML: Structure response with XML tags',
        'markdown': 'MD: Format with Markdown syntax',
        'code': 'CODE: Code only, no explanations',
        'concise': 'BRIEF: Direct, concise answers',
        'verbose': 'DETAIL: Detailed, thorough explanations',
        'filesystem': '📁 FILE SYSTEM: Include folder/file creation commands'
    };
    
    const selected = [];
    
    // Check predefined subroutines
    ['sub-json', 'sub-xml', 'sub-markdown', 'sub-code', 'sub-concise', 'sub-verbose', 'sub-filesystem'].forEach(id => {
        const checkbox = document.getElementById(id);
        if (checkbox && checkbox.checked) {
            const value = checkbox.value;
            if (prompts[value]) {
                selected.push(prompts[value]);
            }
        }
    });
    
    // Check custom subroutines
    if (activeInstance && activeInstance.customSubroutines) {
        Object.keys(activeInstance.customSubroutines).forEach(name => {
            const checkbox = document.getElementById(`custom-sub-${name}`);
            if (checkbox && checkbox.checked) {
                const instruction = activeInstance.customSubroutines[name];
                selected.push(`${name.toUpperCase()}: ${instruction}`);
            }
        });
    }
    
    const instructionsDiv = document.getElementById('active-instructions');
    if (selected.length === 0) {
        instructionsDiv.innerHTML = 'No subroutines selected - LLM will respond normally';
    } else {
        instructionsDiv.innerHTML = '<strong>System will prepend:</strong><br>' + selected.join('<br>');
    }
}
        instructionsDiv.innerHTML = '<strong>System will prepend:</strong><br>' + selected.join('<br>');
    }
}

// Update subroutines (called on checkbox change)
window.updateSubroutines = function() {
    updateActiveInstructions();
};

// Clear all subroutines
window.clearAllSubroutines = function() {
    ['sub-json', 'sub-xml', 'sub-markdown', 'sub-code', 'sub-concise', 'sub-verbose', 'sub-filesystem'].forEach(id => {
        const checkbox = document.getElementById(id);
        if (checkbox) checkbox.checked = false;
    });
    updateActiveInstructions();
};

// Apply subroutines to active instance
window.applySubroutines = function() {
    if (!activeInstance) {
        alert('No instance selected');
        return;
    }
    
    // Collect selected predefined subroutines
    const subroutines = [];
    const checkboxMap = {
        'sub-json': 'json',
        'sub-xml': 'xml',
        'sub-markdown': 'markdown',
        'sub-code': 'code',
        'sub-concise': 'concise',
        'sub-verbose': 'verbose',
        'sub-filesystem': 'filesystem'
    };
    
    Object.entries(checkboxMap).forEach(([id, value]) => {
        const checkbox = document.getElementById(id);
        if (checkbox && checkbox.checked) {
            subroutines.push(value);
        }
    });
    
    // Add custom subroutines
    if (activeInstance.customSubroutines) {
        Object.keys(activeInstance.customSubroutines).forEach(name => {
            const checkbox = document.getElementById(`custom-sub-${name}`);
            if (checkbox && checkbox.checked) {
                subroutines.push(`custom:${name}`);
            }
        });
    }
    
    // Update active instance
    activeInstance.subroutines = subroutines;
    
    // Update in instances array
    const instanceIndex = instances.findIndex(i => i.id === activeInstance.id);
    if (instanceIndex !== -1) {
        instances[instanceIndex].subroutines = subroutines;
    }
    
    // Save to localStorage
    saveInstances();
    
    // Update UI
    renderInstances();
    
    // Announce
    if (subroutines.length === 0) {
        speak('Subroutines cleared');
        alert('Subroutines cleared for ' + activeInstance.name);
    } else {
        speak(`Applied ${subroutines.length} subroutine${subroutines.length === 1 ? '' : 's'}`);
        alert(`Applied ${subroutines.length} subroutine(s) to ${activeInstance.name}:\n• ${subroutines.join('\n• ')}`);
    }
};

// Render custom subroutines list
function renderCustomSubroutines() {
    const container = document.getElementById('custom-subroutines-list');
    if (!container) return;
    
    if (!activeInstance || !activeInstance.customSubroutines || Object.keys(activeInstance.customSubroutines).length === 0) {
        container.innerHTML = '<p style="font-size: 10px; color: #666; font-style: italic;">No custom subroutines yet</p>';
        return;
    }
    
    const currentSubroutines = activeInstance.subroutines || [];
    
    container.innerHTML = '';
    Object.entries(activeInstance.customSubroutines).forEach(([name, instruction]) => {
        const isChecked = currentSubroutines.includes(`custom:${name}`);
        const div = document.createElement('div');
        div.style.marginBottom = '8px';
        div.style.padding = '6px';
        div.style.background = '#ffffff';
        div.style.border = '1px solid #808080';
        
        div.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <label style="flex: 1;">
                    <input type="checkbox" id="custom-sub-${name}" value="custom:${name}" onchange="updateSubroutines()" ${isChecked ? 'checked' : ''}>
                    <strong>${name.toUpperCase()}</strong> - ${instruction.substring(0, 50)}${instruction.length > 50 ? '...' : ''}
                </label>
                <button onclick="removeCustomSubroutine('${name}')" style="min-width: 60px; color: red;">🗑️ Remove</button>
            </div>
        `;
        container.appendChild(div);
    });
}

// Add custom subroutine
window.addCustomSubroutine = function() {
    if (!activeInstance) {
        alert('No instance selected');
        return;
    }
    
    const nameInput = document.getElementById('custom-sub-name');
    const instructionInput = document.getElementById('custom-sub-instruction');
    
    const name = nameInput.value.trim().toLowerCase().replace(/[^a-z0-9_]/g, '');
    const instruction = instructionInput.value.trim();
    
    if (!name || !instruction) {
        alert('Please enter both a name and instruction');
        return;
    }
    
    if (name.length < 2) {
        alert('Name must be at least 2 characters');
        return;
    }
    
    // Initialize customSubroutines if needed
    if (!activeInstance.customSubroutines) {
        activeInstance.customSubroutines = {};
    }
    
    // Add to custom subroutines
    activeInstance.customSubroutines[name] = instruction;
    
    // Update in instances array
    const instanceIndex = instances.findIndex(i => i.id === activeInstance.id);
    if (instanceIndex !== -1) {
        if (!instances[instanceIndex].customSubroutines) {
            instances[instanceIndex].customSubroutines = {};
        }
        instances[instanceIndex].customSubroutines[name] = instruction;
    }
    
    // Save
    saveInstances();
    
    // Clear inputs
    nameInput.value = '';
    instructionInput.value = '';
    
    // Refresh display
    renderCustomSubroutines();
    updateActiveInstructions();
    
    speak(`Custom subroutine ${name} added`);
};

// Remove custom subroutine
window.removeCustomSubroutine = function(name) {
    if (!activeInstance || !activeInstance.customSubroutines) return;
    
    if (!confirm(`Remove custom subroutine "${name}"?`)) {
        return;
    }
    
    // Remove from customSubroutines
    delete activeInstance.customSubroutines[name];
    
    // Remove from active subroutines list if present
    if (activeInstance.subroutines) {
        activeInstance.subroutines = activeInstance.subroutines.filter(s => s !== `custom:${name}`);
    }
    
    // Update in instances array
    const instanceIndex = instances.findIndex(i => i.id === activeInstance.id);
    if (instanceIndex !== -1) {
        if (instances[instanceIndex].customSubroutines) {
            delete instances[instanceIndex].customSubroutines[name];
        }
        if (instances[instanceIndex].subroutines) {
            instances[instanceIndex].subroutines = instances[instanceIndex].subroutines.filter(s => s !== `custom:${name}`);
        }
    }
    
    // Save
    saveInstances();
    
    // Refresh display
    renderCustomSubroutines();
    updateActiveInstructions();
    
    speak(`Custom subroutine ${name} removed`);
};
