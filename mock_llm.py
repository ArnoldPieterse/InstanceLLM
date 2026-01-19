"""
Mock LLM for testing - simulates model loading without actual inference
"""

import os
import time
import random
from pathlib import Path


class MockLlama:
    """Mock LLM that simulates responses without actual model loading."""
    
    def __init__(self, model_path, n_ctx=2048, n_threads=4, n_gpu_layers=0, verbose=False):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.n_gpu_layers = n_gpu_layers
        self.verbose = verbose
        print(f"Mock LLM loaded: {Path(model_path).name}")
        print(f"Context size: {n_ctx}, Threads: {n_threads}, GPU layers: {n_gpu_layers}")
    
    def __call__(self, prompt, temperature=0.7, max_tokens=512, top_p=0.95, 
                 top_k=40, repeat_penalty=1.1, stop=None, stream=False, echo=False):
        """Simulate model inference."""
        
        if stream:
            # Streaming mode
            return self._generate_stream(prompt, max_tokens)
        else:
            # Normal mode
            response_text = self._generate_response(prompt, max_tokens)
            return {
                'choices': [{
                    'text': response_text,
                    'finish_reason': 'stop'
                }]
            }
    
    def _generate_response(self, prompt, max_tokens):
        """Generate a mock response based on the prompt."""
        
        # Simulate thinking time
        time.sleep(0.5)
        
        # Simple pattern matching for demo responses
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ['hello', 'hi', 'hey']):
            responses = [
                "Hello! I'm a mock LLM running on your local network. How can I help you today?",
                "Hi there! I'm here to assist you. What would you like to know?",
                "Hey! I'm a local language model ready to answer your questions."
            ]
        elif any(word in prompt_lower for word in ['what', 'who', 'where', 'when', 'why', 'how']):
            responses = [
                f"That's an interesting question about '{prompt[:50]}...'. In a real scenario, I would provide a detailed answer based on my training data. This is a mock response for testing purposes.",
                f"Based on your question, I can tell you that this is a demonstration of the local LLM server. The actual model would provide real answers once llama-cpp-python is properly installed.",
                f"Great question! In production, this would be answered by the actual LLM model. For now, I'm demonstrating the server functionality."
            ]
        elif 'code' in prompt_lower or 'program' in prompt_lower or 'python' in prompt_lower:
            responses = [
                "Here's a simple example:\n\n```python\ndef hello_world():\n    print('Hello from the local LLM server!')\n    return True\n```\n\nThis demonstrates code generation capabilities.",
                "I can help with coding! This is a mock response, but a real model would provide actual code solutions.",
            ]
        elif any(word in prompt_lower for word in ['thank', 'thanks']):
            responses = [
                "You're welcome! Feel free to ask more questions.",
                "Happy to help! This local LLM server is working great!",
                "My pleasure! The server is ready for more requests."
            ]
        else:
            responses = [
                f"I received your prompt: '{prompt[:50]}...'\n\nThis is a mock response demonstrating the local LLM server functionality. Once you install llama-cpp-python or transformers, you'll get real AI-generated responses!",
                f"Thank you for testing the local LLM server! Your prompt was processed successfully. In production mode with a real model, this would be an intelligent, contextual response.",
                f"The local LLM server is working correctly! This mock response confirms that:\n- Model loading works\n- API endpoints are functional\n- Network access is enabled\n- Parameters are configurable\n\nInstall a real inference library to get actual AI responses!"
            ]
        
        response = random.choice(responses)
        
        # Truncate to max_tokens (rough approximation: 4 chars per token)
        max_chars = max_tokens * 4
        if len(response) > max_chars:
            response = response[:max_chars] + "..."
        
        return response
    
    def _generate_stream(self, prompt, max_tokens):
        """Generate streaming responses."""
        response = self._generate_response(prompt, max_tokens)
        
        # Stream word by word
        words = response.split()
        for word in words:
            time.sleep(0.05)  # Simulate streaming delay
            yield {
                'choices': [{
                    'text': word + ' ',
                    'finish_reason': None
                }]
            }
        
        # Final chunk
        yield {
            'choices': [{
                'text': '',
                'finish_reason': 'stop'
            }]
        }
