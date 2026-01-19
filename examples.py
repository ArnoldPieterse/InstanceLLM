"""
Example usage scripts for the Local LLM Server
"""

# Example 1: Basic usage with default parameters
def example_basic():
    from llm_server import LLMServer
    
    server = LLMServer("./models/llama-2-7b.gguf")
    server.load_model()
    server.start()


# Example 2: Custom parameters via kwargs
def example_custom_params():
    from llm_server import LLMServer
    
    server = LLMServer(
        "./models/mistral-7b.gguf",
        temperature=0.8,
        max_tokens=1024,
        top_p=0.9,
        top_k=50,
        repeat_penalty=1.2,
        n_gpu_layers=35,  # GPU acceleration
        context_window=4096,
        stop_sequences=["###", "User:", "Assistant:"],
        verbose=True
    )
    
    server.load_model()
    server.start(host="0.0.0.0", port=8080)


# Example 3: Using configuration dictionary
def example_config_dict():
    from llm_server import LLMServer
    
    config = {
        'temperature': 0.7,
        'max_tokens': 512,
        'top_p': 0.95,
        'n_gpu_layers': 20,
        'context_window': 2048,
        'n_threads': 8
    }
    
    server = LLMServer.from_config_dict("./models/phi-2.gguf", config)
    server.load_model()
    server.start()


# Example 4: Using configuration array
def example_config_array():
    from llm_server import LLMServer
    
    params = [
        ('temperature', 0.9),
        ('max_tokens', 2048),
        ('top_p', 0.92),
        ('top_k', 60),
        ('n_gpu_layers', 40),
        ('context_window', 8192),
        ('repeat_penalty', 1.15)
    ]
    
    server = LLMServer.from_config_array("./models/llama-3-8b.gguf", params)
    server.load_model()
    server.start(port=9000)


# Example 5: Direct generation (without starting server)
def example_direct_generation():
    from llm_server import LLMServer
    
    server = LLMServer(
        "./models/model.gguf",
        temperature=0.7,
        max_tokens=200
    )
    server.load_model()
    
    # Generate response directly
    prompt = "Explain quantum computing in simple terms:"
    response = server.generate(prompt)
    print(response)
    
    # Generate with override parameters
    response2 = server.generate(
        "Write a haiku about programming",
        temperature=0.95,
        max_tokens=50
    )
    print(response2)


# Example 6: Streaming generation
def example_streaming():
    from llm_server import LLMServer
    
    server = LLMServer("./models/model.gguf")
    server.load_model()
    
    prompt = "Tell me a story about a space explorer:"
    for chunk in server.generate_stream(prompt):
        print(chunk, end='', flush=True)


# Example 7: Multiple servers on different ports
def example_multiple_servers():
    from llm_server import LLMServer
    import threading
    
    # Server 1: Fast, creative model
    def run_server1():
        server1 = LLMServer(
            "./models/small-model.gguf",
            temperature=0.9,
            max_tokens=500
        )
        server1.load_model()
        server1.start(port=8000)
    
    # Server 2: Slower, more accurate model
    def run_server2():
        server2 = LLMServer(
            "./models/large-model.gguf",
            temperature=0.5,
            max_tokens=1024,
            n_gpu_layers=40
        )
        server2.load_model()
        server2.start(port=8001)
    
    # Run both servers
    thread1 = threading.Thread(target=run_server1)
    thread2 = threading.Thread(target=run_server2)
    
    thread1.start()
    thread2.start()
    
    thread1.join()
    thread2.join()


# Example 8: Production-ready configuration
def example_production():
    from llm_server import LLMServer
    
    server = LLMServer(
        "./models/production-model.gguf",
        temperature=0.7,
        max_tokens=1024,
        top_p=0.95,
        top_k=40,
        repeat_penalty=1.1,
        n_gpu_layers=35,  # Adjust based on your GPU
        context_window=4096,
        n_threads=8,
        stop_sequences=["<|endoftext|>", "###END###"],
        verbose=False
    )
    
    server.load_model()
    
    # Start on all interfaces, production port
    server.start(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    import sys
    
    examples = {
        "1": ("Basic usage", example_basic),
        "2": ("Custom parameters", example_custom_params),
        "3": ("Config dictionary", example_config_dict),
        "4": ("Config array", example_config_array),
        "5": ("Direct generation", example_direct_generation),
        "6": ("Streaming", example_streaming),
        "7": ("Multiple servers", example_multiple_servers),
        "8": ("Production config", example_production),
    }
    
    print("Available examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}: {name}")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
        if choice in examples:
            print(f"\nRunning example: {examples[choice][0]}")
            examples[choice][1]()
        else:
            print(f"Invalid choice: {choice}")
    else:
        print("\nUsage: python examples.py <example_number>")
        print("Example: python examples.py 2")
