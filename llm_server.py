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
import logging
from typing import Optional, Dict, Any, List, Generator
from pathlib import Path
from dataclasses import dataclass, field
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
                # Transfo            # Serve the web interface
            static_path = Path(__file__).parent / "static" / "index.html"
            if static_path.exists():
                return FileResponse(str(static_path))                response = self.generate(prompt, **override_params)
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
            return {
                "message": "Local LLM Server",
                "model": str(self.model_path),
                "status": "ready" if self.model else "not loaded"
            }
        
        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "model_loaded": self.model is not None,
                "model_path": str(self.model_path),
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
