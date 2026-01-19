"""
Local LLM Network Server
========================

PURPOSE:
    Host a local Large Language Model (LLM) on your network with a RESTful API.
    Supports automatic model downloads, custom configurations, and streaming responses.

QUICK START:
    1. Install dependencies: pip install -r requirements.txt
    2. Run: python llm_server.py
    3. Follow prompts to download a model
    4. Access API at http://localhost:8000

USAGE EXAMPLES:
    # Simple initialization
    server = LLMServer("path/to/model.gguf")
    server.load_model()
    server.start()

    # With custom parameters (overloaded constructor)
    server = LLMServer(
        "path/to/model.gguf",
        temperature=0.8,
        max_tokens=1024,
        n_gpu_layers=0  # Set to 0 for CPU-only
    )
    
    # From configuration dictionary
    config = {'temperature': 0.8, 'max_tokens': 1024}
    server = LLMServer.from_config_dict("path/to/model.gguf", config)
    
    # From configuration array (tuples)
    params = [('temperature', 0.8), ('max_tokens', 1024)]
    server = LLMServer.from_config_array("path/to/model.gguf", params)

API ENDPOINTS:
    GET  /health     - Server status and configuration
    POST /prompt     - Generate response (standard or streaming)
    POST /stream     - Generate streaming response
    GET  /docs       - Interactive API documentation

FEATURES:
    - Automatic model detection and download
    - Overloaded initialization (kwargs, dict, array)
    - GPU acceleration support (n_gpu_layers parameter)
    - Streaming and non-streaming responses
    - Mock LLM fallback for testing without inference libraries
    - Network accessible (0.0.0.0:8000)

DEPENDENCIES:
    Required: fastapi, uvicorn, pydantic, huggingface_hub, requests, tqdm
    Optional: llama-cpp-python (for GGUF models) or transformers (for HF models)
    Fallback: mock_llm.py (for testing without inference libraries)

AUTHOR: InstanceLLM Project
LICENSE: MIT
VERSION: 1.0.0
"""

import os
import sys
import logging
import socket
from typing import Optional, Dict, Any, List, Generator
from pathlib import Path
from dataclasses import dataclass, field
import asyncio
import json
import threading
import subprocess
from queue import Queue

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

try:
    from model_downloader import ModelDownloader
    MODEL_DOWNLOADER_AVAILABLE = True
except ImportError:
    MODEL_DOWNLOADER_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global progress tracking
download_progress = {}
progress_queues = {}

# Instance management
running_instances = {}  # {instance_id: {"process": subprocess.Popen, "port": int, "model": str, "name": str}}


def get_local_ip():
    """Get the local IP address of this machine."""
    try:
        # Create a socket to find the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_resource_usage():
    """Get current system resource usage."""
    if not PSUTIL_AVAILABLE:
        return {
            "cpu_percent": 0,
            "memory_percent": 0,
            "memory_available_gb": 0,
            "available": False
        }
    
    try:
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "available": True
        }
    except Exception as e:
        logger.error(f"Error getting resource usage: {e}")
        return {
            "cpu_percent": 0,
            "memory_percent": 0,
            "memory_available_gb": 0,
            "available": False
        }


@dataclass
class LLMConfig:
    """Configuration class for LLM parameters."""
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float = 0.95
    top_k: int = 40
    repeat_penalty: float = 1.1
    context_window: int = 2048
    stop_sequences: List[str] = field(default_factory=list)
    n_gpu_layers: int = 0  # Number of layers to offload to GPU
    n_threads: int = 4
    verbose: bool = False


class PromptRequest(BaseModel):
    """Request model for prompt endpoint."""
    prompt: str = Field(..., description="The input prompt for the LLM")
    temperature: Optional[float] = Field(None, description="Override temperature")
    max_tokens: Optional[int] = Field(None, description="Override max tokens")
    top_p: Optional[float] = Field(None, description="Override top_p")
    stream: bool = Field(False, description="Enable streaming response")


class PromptResponse(BaseModel):
    """Response model for prompt endpoint."""
    response: str
    model_path: str
    config_used: Dict[str, Any]


class StartInstanceRequest(BaseModel):
    """Request model for starting an instance."""
    instance_id: str
    port: int
    model: str


class StopInstanceRequest(BaseModel):
    """Request model for stopping an instance."""
    instance_id: str
    port: Optional[int] = None


class CreateInstanceRequest(BaseModel):
    """Request model for creating a new instance."""
    name: str
    port: int
    model: str


class LLMServer:
    """
    Main LLM Server class with overloaded initialization.
    Supports both simple path-based initialization and custom configuration.
    """
    
    def __init__(self, model_path: str, **kwargs):
        """
        Initialize LLM Server.
        
        Args:
            model_path: Path to the local LLM model file
            **kwargs: Custom configuration parameters for LLM
                - temperature (float): Sampling temperature (default: 0.7)
                - max_tokens (int): Maximum tokens to generate (default: 512)
                - top_p (float): Nucleus sampling parameter (default: 0.95)
                - top_k (int): Top-k sampling parameter (default: 40)
                - repeat_penalty (float): Repetition penalty (default: 1.1)
                - context_window (int): Context window size (default: 2048)
                - stop_sequences (list): Stop sequences for generation
                - n_gpu_layers (int): GPU layers to offload (default: 0)
                - n_threads (int): CPU threads to use (default: 4)
                - verbose (bool): Enable verbose logging (default: False)
        
        Example:
            # Simple initialization
            server = LLMServer("path/to/model.gguf")
            
            # Advanced initialization with custom parameters
            server = LLMServer(
                "path/to/model.gguf",
                temperature=0.8,
                max_tokens=1024,
                top_p=0.9,
                n_gpu_layers=0  # CPU-only, set to 35 for GPU
            )
        """
        self.model_path = Path(model_path)
        self.model = None
        self.app = FastAPI(title="Local LLM Server", version="1.0.0")
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Mount static files
        static_path = Path(__file__).parent / "static"
        if static_path.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        
        # Initialize configuration with custom parameters
        self.config = self._initialize_config(**kwargs)
        
        # Validate model path - offer to download if not found
        if not self.model_path.exists():
            logger.warning(f"Model file not found: {self.model_path}")
            
            if MODEL_DOWNLOADER_AVAILABLE:
                logger.info("Checking for available models...")
                downloader = ModelDownloader()
                downloaded_model = downloader.check_and_prompt_download(str(self.model_path))
                
                if downloaded_model:
                    self.model_path = downloaded_model
                    logger.info(f"Using model: {self.model_path}")
                else:
                    raise FileNotFoundError(f"No model available. Please provide a valid model path.")
            else:
                raise FileNotFoundError(
                    f"Model file not found: {self.model_path}\n"
                    f"Install model_downloader dependencies to download models automatically:\n"
                    f"  pip install huggingface_hub requests tqdm"
                )
        
        logger.info(f"Initializing LLM Server with model: {self.model_path}")
        logger.info(f"Configuration: {self.config}")
        
        # Setup API routes
        self._setup_routes()
    
    @classmethod
    def from_config_dict(cls, model_path: str, config_dict: Dict[str, Any]):
        """
        Alternative constructor using a configuration dictionary.
        
        Args:
            model_path: Path to the local LLM model file
            config_dict: Dictionary containing LLM configuration parameters
        
        Example:
            config = {
                'temperature': 0.8,
                'max_tokens': 1024,
                'top_p': 0.9,
                'n_gpu_layers': 0  # CPU-only
            }
            server = LLMServer.from_config_dict("path/to/model.gguf", config)
        """
        return cls(model_path, **config_dict)
    
    @classmethod
    def from_config_array(cls, model_path: str, config_params: List[tuple]):
        """
        Alternative constructor using an array of parameter tuples.
        
        Args:
            model_path: Path to the local LLM model file
            config_params: List of (key, value) tuples for configuration
        
        Example:
            params = [
                ('temperature', 0.8),
                ('max_tokens', 1024),
                ('top_p', 0.9),
                ('n_gpu_layers', 0)  # CPU-only
            ]
            server = LLMServer.from_config_array("path/to/model.gguf", params)
        """
        config_dict = dict(config_params)
        return cls(model_path, **config_dict)
    
    def _initialize_config(self, **kwargs) -> LLMConfig:
        """Initialize configuration with provided parameters or defaults."""
        config_dict = {}
        
        # Extract known parameters
        for key in LLMConfig.__dataclass_fields__.keys():
            if key in kwargs:
                config_dict[key] = kwargs[key]
        
        return LLMConfig(**config_dict)
    
    def load_model(self):
        """
        Load the LLM model. Supports GGUF format via llama-cpp-python.
        """
        try:
            from llama_cpp import Llama
            
            logger.info("Loading model with llama-cpp-python...")
            self.model = Llama(
                model_path=str(self.model_path),
                n_ctx=self.config.context_window,
                n_threads=self.config.n_threads,
                n_gpu_layers=self.config.n_gpu_layers,
                verbose=self.config.verbose
            )
            logger.info("Model loaded successfully!")
            return True
            
        except ImportError:
            logger.warning("llama-cpp-python not installed. Trying transformers...")
            return self._load_model_transformers()
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def _load_model_transformers(self):
        """
        Alternative loader using HuggingFace transformers.
        """
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            logger.info("Loading model with transformers...")
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
            self.model = AutoModelForCausalLM.from_pretrained(
                str(self.model_path),
                device_map="auto"
            )
            logger.info("Model loaded successfully with transformers!")
            return True
            
        except ImportError:
            logger.warning("transformers not installed. Using mock LLM for testing...")
            return self._load_mock_model()
        except Exception as e:
            logger.warning(f"Error loading model with transformers: {e}")
            logger.info("Falling back to mock LLM for testing...")
            return self._load_mock_model()
    
    def _load_mock_model(self):
        """
        Load mock LLM for testing when real libraries aren't available.
        """
        try:
            from mock_llm import MockLlama
            
            logger.warning("=" * 70)
            logger.warning("USING MOCK LLM FOR TESTING")
            logger.warning("Install llama-cpp-python or transformers for real inference")
            logger.warning("=" * 70)
            
            self.model = MockLlama(
                model_path=str(self.model_path),
                n_ctx=self.config.context_window,
                n_threads=self.config.n_threads,
                n_gpu_layers=self.config.n_gpu_layers,
                verbose=self.config.verbose
            )
            logger.info("Mock model loaded successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error loading mock model: {e}")
            raise ImportError("No model loading library available")
    
    def generate(self, prompt: str, **override_params) -> str:
        """
        Generate response from the model.
        
        Args:
            prompt: Input prompt string
            **override_params: Parameters to override the default config
        
        Returns:
            Generated text response
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Merge override parameters with config
        gen_params = {
            'temperature': override_params.get('temperature', self.config.temperature),
            'max_tokens': override_params.get('max_tokens', self.config.max_tokens),
            'top_p': override_params.get('top_p', self.config.top_p),
            'top_k': override_params.get('top_k', self.config.top_k),
            'repeat_penalty': override_params.get('repeat_penalty', self.config.repeat_penalty),
        }
        
        if self.config.stop_sequences:
            gen_params['stop'] = self.config.stop_sequences
        
        try:
            # Check if using llama-cpp-python
            if hasattr(self.model, '__call__'):
                response = self.model(
                    prompt,
                    **gen_params,
                    echo=False
                )
                return response['choices'][0]['text']
            
            # Otherwise, using transformers
            else:
                from transformers import GenerationConfig
                inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
                
                generation_config = GenerationConfig(
                    temperature=gen_params['temperature'],
                    top_p=gen_params['top_p'],
                    top_k=gen_params['top_k'],
                    max_new_tokens=gen_params['max_tokens'],
                    repetition_penalty=gen_params['repeat_penalty'],
                    do_sample=True
                )
                
                outputs = self.model.generate(
                    **inputs,
                    generation_config=generation_config
                )
                return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def generate_stream(self, prompt: str, **override_params) -> Generator[str, None, None]:
        """
        Generate streaming response from the model.
        
        Args:
            prompt: Input prompt string
            **override_params: Parameters to override the default config
        
        Yields:
            Generated text chunks
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        gen_params = {
            'temperature': override_params.get('temperature', self.config.temperature),
            'max_tokens': override_params.get('max_tokens', self.config.max_tokens),
            'top_p': override_params.get('top_p', self.config.top_p),
            'top_k': override_params.get('top_k', self.config.top_k),
            'repeat_penalty': override_params.get('repeat_penalty', self.config.repeat_penalty),
        }
        
        if self.config.stop_sequences:
            gen_params['stop'] = self.config.stop_sequences
        
        try:
            if hasattr(self.model, '__call__'):
                # llama-cpp-python streaming
                for output in self.model(prompt, **gen_params, stream=True, echo=False):
                    chunk = output['choices'][0]['text']
                    yield chunk
            else:
                # Transformers - generate full response then chunk it
                response = self.generate(prompt, **override_params)
                # Simulate streaming by chunking the response
                for i in range(0, len(response), 10):
                    yield response[i:i+10]
                    
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            raise
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def root():
            # Serve the web interface
            static_path = Path(__file__).parent / "static" / "index.html"
            if static_path.exists():
                return FileResponse(str(static_path))
            return {
                "message": "Local LLM Server",
                "model": str(self.model_path),
                "status": "ready" if self.model else "not loaded"
            }
        
        @self.app.get("/health")
        async def health():
            local_ip = get_local_ip()
            resources = get_resource_usage()
            
            return {
                "status": "healthy",
                "model_loaded": self.model is not None,
                "model_path": str(self.model_path),
                "local_ip": local_ip,
                "resources": resources,
                "config": {
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                    "context_window": self.config.context_window
                }
            }
        
        @self.app.post("/prompt", response_model=PromptResponse)
        async def generate_response(request: PromptRequest):
            if self.model is None:
                raise HTTPException(status_code=503, detail="Model not loaded")
            
            try:
                override_params = {}
                if request.temperature is not None:
                    override_params['temperature'] = request.temperature
                if request.max_tokens is not None:
                    override_params['max_tokens'] = request.max_tokens
                if request.top_p is not None:
                    override_params['top_p'] = request.top_p
                
                if request.stream:
                    # Return streaming response
                    async def stream_generator():
                        for chunk in self.generate_stream(request.prompt, **override_params):
                            yield chunk
                    
                    return StreamingResponse(stream_generator(), media_type="text/plain")
                else:
                    # Return standard response
                    response_text = self.generate(request.prompt, **override_params)
                    return PromptResponse(
                        response=response_text,
                        model_path=str(self.model_path),
                        config_used={**self.config.__dict__, **override_params}
                    )
            
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/stream")
        async def stream_response(request: PromptRequest):
            if self.model is None:
                raise HTTPException(status_code=503, detail="Model not loaded")
            
            try:
                override_params = {}
                if request.temperature is not None:
                    override_params['temperature'] = request.temperature
                if request.max_tokens is not None:
                    override_params['max_tokens'] = request.max_tokens
                if request.top_p is not None:
                    override_params['top_p'] = request.top_p
                
                def stream_generator():
                    for chunk in self.generate_stream(request.prompt, **override_params):
                        yield chunk
                
                return StreamingResponse(stream_generator(), media_type="text/plain")
            
            except Exception as e:
                logger.error(f"Error processing stream request: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/download-progress/{model_id}")
        async def download_progress_stream(model_id: str):
            """Stream download progress updates via Server-Sent Events."""
            async def event_generator():
                # Get or create queue for this model
                if model_id not in progress_queues:
                    progress_queues[model_id] = Queue()
                
                queue = progress_queues[model_id]
                logger.info(f"Client connected to progress stream for model {model_id}")
                
                try:
                    while True:
                        # Check for progress updates
                        if not queue.empty():
                            data = queue.get()
                            logger.info(f"Sending progress: {data}")
                            yield f"data: {json.dumps(data)}\n\n"
                            
                            # Stop if download is complete or errored
                            if data.get('status') in ['complete', 'error']:
                                logger.info(f"Download {data.get('status')} for model {model_id}")
                                break
                        
                        await asyncio.sleep(0.1)  # Check more frequently
                except asyncio.CancelledError:
                    # Client disconnected
                    logger.info(f"Client disconnected from progress stream for model {model_id}")
                    raise
                finally:
                    # Clean up queue after some time
                    await asyncio.sleep(5)
                    if model_id in progress_queues:
                        del progress_queues[model_id]
            
            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        @self.app.post("/download-model")
        async def download_model(model_id: str):
            """Download a model from HuggingFace with progress tracking."""
            try:
                import requests
                from model_downloader import ModelDownloader
                
                downloader = ModelDownloader(models_dir="./models")
                
                # Validate model ID
                if model_id not in downloader.POPULAR_MODELS:
                    raise HTTPException(status_code=400, detail=f"Invalid model ID: {model_id}")
                
                model_info = downloader.POPULAR_MODELS[model_id]
                
                # Don't allow custom URL downloads via API (security)
                if model_id == "8":
                    raise HTTPException(status_code=400, detail="Custom URL downloads not supported via API")
                
                # Initialize progress queue if not exists
                if model_id not in progress_queues:
                    progress_queues[model_id] = Queue()
                
                # Start download in background thread
                def download_with_progress():
                    try:
                        logger.info(f"Starting download of {model_info['name']}")
                        
                        # Get download URL from HuggingFace
                        url = f"https://huggingface.co/{model_info['repo']}/resolve/main/{model_info['file']}"
                        output_path = Path("./models") / model_info['file']
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        logger.info(f"Downloading from: {url}")
                        
                        # Download with progress tracking
                        response = requests.get(url, stream=True, timeout=30)
                        response.raise_for_status()
                        
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        
                        logger.info(f"Total size: {total_size / 1024 / 1024:.1f} MB")
                        
                        # Send initial progress
                        if model_id in progress_queues:
                            progress_queues[model_id].put({
                                'status': 'progress',
                                'percent': 0,
                                'downloaded': '0.0 MB',
                                'total': f"{total_size / 1024 / 1024:.1f} MB"
                            })
                        
                        with open(output_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    
                                    # Update progress every 1MB or so
                                    if total_size > 0 and downloaded % (1024 * 1024) < 8192:
                                        percent = (downloaded / total_size) * 100
                                        progress_data = {
                                            'status': 'progress',
                                            'percent': percent,
                                            'downloaded': f"{downloaded / 1024 / 1024:.1f} MB",
                                            'total': f"{total_size / 1024 / 1024:.1f} MB"
                                        }
                                        
                                        logger.info(f"Progress: {percent:.1f}%")
                                        
                                        if model_id in progress_queues:
                                            progress_queues[model_id].put(progress_data)
                        
                        # Download complete
                        logger.info(f"Download complete: {output_path}")
                        
                        complete_data = {
                            'status': 'complete',
                            'model_name': model_info['name'],
                            'model_path': str(output_path)
                        }
                        
                        if model_id in progress_queues:
                            progress_queues[model_id].put(complete_data)
                        
                    except Exception as e:
                        logger.error(f"Download error: {e}")
                        error_data = {
                            'status': 'error',
                            'message': str(e)
                        }
                        
                        if model_id in progress_queues:
                            progress_queues[model_id].put(error_data)
                
                # Wait a bit for EventSource to connect
                await asyncio.sleep(0.5)
                
                # Start download in background
                thread = threading.Thread(target=download_with_progress, daemon=True)
                thread.start()
                
                return {"status": "started", "message": "Download started"}
                
            except ImportError as e:
                raise HTTPException(
                    status_code=500, 
                    detail="Required libraries not installed. Run: pip install requests"
                )
            except Exception as e:
                logger.error(f"Download error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/list-models")
        async def list_models():
            """List all available model files."""
            try:
                models_dir = Path("./models")
                if not models_dir.exists():
                    return {"models": []}
                
                model_files = list(models_dir.glob("**/*.gguf"))
                return {"models": [str(m.relative_to(models_dir)) for m in model_files]}
            except Exception as e:
                logger.error(f"Error listing models: {e}")
                return {"models": []}
        
        @self.app.get("/resources")
        async def get_resources():
            """Get system resource usage."""
            resources = get_resource_usage()
            resources["local_ip"] = get_local_ip()
            resources["running_instances"] = len(running_instances)
            return resources
        
        @self.app.post("/create-instance")
        async def create_instance(request: CreateInstanceRequest):
            """Create a new LLM instance on a different port."""
            try:
                name = request.name
                port = request.port
                model = request.model
                
                instance_id = f"instance-{port}"
                
                # Check if already running
                if instance_id in running_instances:
                    return {"status": "error", "message": "Instance already running on this port"}
                
                # Check resource availability
                resources = get_resource_usage()
                paused_instance = None
                
                if resources["available"] and resources["memory_percent"] > 85:
                    # Memory usage is high, pause the oldest instance
                    if running_instances:
                        # Get the first instance (oldest)
                        oldest_id = list(running_instances.keys())[0]
                        oldest = running_instances[oldest_id]
                        logger.warning(f"Memory usage high ({resources['memory_percent']:.1f}%), pausing instance {oldest_id}")
                        
                        try:
                            oldest["process"].terminate()
                            oldest["process"].wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            oldest["process"].kill()
                        
                        # Keep the instance in the dict but mark as paused
                        oldest["paused"] = True
                        paused_instance = oldest_id
                
                # Validate model exists
                model_path = Path("./models") / model
                if not model_path.exists():
                    raise HTTPException(status_code=404, detail=f"Model not found: {model}")
                
                # Start the instance
                cmd = [
                    sys.executable,
                    "llm_server.py",
                    str(model_path),
                    str(port)
                ]
                
                logger.info(f"Starting instance {instance_id}: {' '.join(cmd)}")
                process = subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
                )
                
                # Track the instance
                running_instances[instance_id] = {
                    "process": process,
                    "port": port,
                    "model": model,
                    "pid": process.pid,
                    "name": name,
                    "paused": False
                }
                
                response = {
                    "status": "success",
                    "instance_id": instance_id,
                    "message": f"Instance {name} starting on port {port}",
                    "pid": process.pid,
                    "local_ip": get_local_ip(),
                    "resources": resources
                }
                
                if paused_instance:
                    response["paused_instance"] = paused_instance
                    response["message"] += f" (paused {paused_instance} due to high memory usage)"
                
                return response
                
            except Exception as e:
                    "pid": process.pid
                }
                
            except Exception as e:
                logger.error(f"Error creating instance: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/start-instance")
        async def start_instance_endpoint(request: StartInstanceRequest):
            """Start an existing instance."""
            try:
                instance_id = request.instance_id
                port = request.port
                model = request.model
                
                if instance_id in running_instances:
                    return {"status": "error", "message": "Instance already running"}
                
                model_path = Path("./models") / model
                if not model_path.exists():
                    raise HTTPException(status_code=404, detail=f"Model not found: {model}")
                
                # Start the instance
                cmd = [
                    sys.executable,
                    "llm_server.py",
                    str(model_path),
                    str(port)
                ]
                
                logger.info(f"Starting instance {instance_id} on port {port}: {' '.join(cmd)}")
                process = subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
                )
                
                running_instances[instance_id] = {
                    "process": process,
                    "port": port,
                    "model": model,
                    "pid": process.pid
                }
                
                return {
                    "status": "success",
                    "message": f"Instance {instance_id} started on port {port}",
                    "pid": process.pid
                }
                
            except Exception as e:
                logger.error(f"Error starting instance: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/stop-instance")
        async def stop_instance_endpoint(request: StopInstanceRequest):
            """Stop a running instance."""
            try:
                instance_id = request.instance_id
                
                if instance_id not in running_instances:
                    return {"status": "error", "message": "Instance not running or not found"}
                
                instance = running_instances[instance_id]
                process = instance["process"]
                
                # Terminate the process
                process.terminate()
                try:
                    process.wait(timeout=5)  # Wait up to 5 seconds
                except subprocess.TimeoutExpired:
                    process.kill()  # Force kill if it doesn't terminate
                
                del running_instances[instance_id]
                
                return {
                    "status": "success",
                    "message": f"Instance {instance_id} stopped"
                }
                
            except Exception as e:
                logger.error(f"Error stopping instance: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/list-instances")
        async def list_instances():
            """List all running instances."""
            try:
                instances = []
                for instance_id, data in running_instances.items():
                    # Check if process is still running
                    if data["process"].poll() is None:
                        instances.append({
                            "instance_id": instance_id,
                            "port": data["port"],
                            "model": data["model"],
                            "pid": data["pid"],
                            "status": "running"
                        })
                    else:
                        # Process died, remove from tracking
                        instances.append({
                            "instance_id": instance_id,
                            "port": data["port"],
                            "model": data["model"],
                            "pid": data["pid"],
                            "status": "stopped"
                        })
                
                return {"status": "success", "instances": instances}
                
            except Exception as e:
                logger.error(f"Error listing instances: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def start(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Start the FastAPI server on the local network.
        
        Args:
            host: Host address to bind (default: "0.0.0.0" for all interfaces)
            port: Port number to listen on (default: 8000)
        """
        if self.model is None:
            logger.warning("Model not loaded. Loading now...")
            self.load_model()
        
        logger.info(f"Starting server on {host}:{port}")
        logger.info(f"Access the server at http://{host}:{port}")
        logger.info(f"API documentation available at http://{host}:{port}/docs")
        
        uvicorn.run(self.app, host=host, port=port)


def main():
    """
    Main entry point for the LLM Server.
    
    Usage:
        python llm_server.py                          # Auto-download model
        python llm_server.py path/to/model.gguf       # Use existing model
        python llm_server.py path/to/model.gguf 8080  # Custom port
    
    Process:
        1. Check for command-line arguments (model path, port)
        2. If no model provided, check for local models
        3. If no local models, offer interactive download
        4. Initialize server with custom configuration
        5. Load model (tries llama-cpp-python → transformers → mock)
        6. Start FastAPI server on specified host:port
    
    Configuration:
        The example configuration uses:
        - temperature=0.8    (balanced creativity)
        - max_tokens=1024    (medium response length)
        - top_p=0.9          (nucleus sampling)
        - n_gpu_layers=0     (CPU-only - set to 35 for GPU acceleration)
        - context_window=4096 (large context)
        - stop_sequences     (tokens that end generation)
    
    Notes:
        - Server binds to 0.0.0.0:8000 for network access
        - API docs available at http://localhost:8000/docs
        - If llama-cpp-python/transformers not installed, uses mock LLM
    """
    import sys
    
    # If no arguments provided, try to find or download a model
    if len(sys.argv) < 2:
        print("No model path provided.")
        
        if MODEL_DOWNLOADER_AVAILABLE:
            print("Checking for available models...\n")
            downloader = ModelDownloader()
            model_path_obj = downloader.check_and_prompt_download()
            
            if model_path_obj:
                model_path = str(model_path_obj)
                port = 8000
            else:
                print("\nNo model selected. Exiting.")
                print("\nUsage: python llm_server.py <path_to_model> [port]")
                print("\nExample:")
                print("  python llm_server.py ./models/llama-2-7b.gguf")
                print("  python llm_server.py ./models/llama-2-7b.gguf 8080")
                sys.exit(1)
        else:
            print("\nUsage: python llm_server.py <path_to_model> [port]")
            print("\nExample:")
            print("  python llm_server.py ./models/llama-2-7b.gguf")
            print("  python llm_server.py ./models/llama-2-7b.gguf 8080")
            print("\nTo enable automatic model downloads, install:")
            print("  pip install huggingface_hub requests tqdm")
            sys.exit(1)
    else:
        model_path = sys.argv[1]
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    
    # Example 1: Simple initialization
    # server = LLMServer(model_path)
    
    # Example 2: Initialization with custom parameters
    server = LLMServer(
        model_path,
        temperature=0.8,
        max_tokens=1024,
        top_p=0.9,
        n_gpu_layers=0,  # CPU-only (change to 35 for GPU acceleration)
        context_window=4096,
        stop_sequences=["User:", "Assistant:"]
    )
    
    # Example 3: Using from_config_dict
    # config = {
    #     'temperature': 0.8,
    #     'max_tokens': 1024,
    #     'top_p': 0.9,
    #     'n_gpu_layers': 0  # CPU-only
    # }
    # server = LLMServer.from_config_dict(model_path, config)
    
    # Example 4: Using from_config_array
    # params = [
    #     ('temperature', 0.8),
    #     ('max_tokens', 1024),
    #     ('top_p', 0.9),
    #     ('n_gpu_layers', 0)  # CPU-only
    # ]
    # server = LLMServer.from_config_array(model_path, params)
    
    # Load model and start server
    server.load_model()
    server.start(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
