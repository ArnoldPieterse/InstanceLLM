"""
Model Downloader for Local LLM Server
Provides functionality to discover and download popular LLM models.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import requests
from tqdm import tqdm


class ModelDownloader:
    """Download and manage LLM models from popular sources."""
    
    # Popular GGUF models from HuggingFace
    POPULAR_MODELS = {
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
        },
        "8": {
            "name": "Custom URL",
            "repo": None,
            "file": None,
            "size": "Variable",
            "description": "Download from a custom URL"
        }
    }
    
    def __init__(self, models_dir: str = "./models"):
        """
        Initialize the model downloader.
        
        Args:
            models_dir: Directory to store downloaded models
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
    
    def list_popular_models(self) -> None:
        """Display a list of popular models available for download."""
        print("\n" + "=" * 70)
        print("Popular LLM Models Available for Download")
        print("=" * 70)
        
        for key, model in self.POPULAR_MODELS.items():
            print(f"\n[{key}] {model['name']}")
            print(f"    Size: {model['size']}")
            print(f"    {model['description']}")
            if model['repo']:
                print(f"    Source: {model['repo']}")
        
        print("\n" + "=" * 70)
    
    def download_from_huggingface(self, repo: str, filename: str, 
                                  output_path: Optional[Path] = None) -> Path:
        """
        Download a model file from HuggingFace Hub.
        
        Args:
            repo: Repository name (e.g., "TheBloke/Llama-2-7B-GGUF")
            filename: File name to download
            output_path: Optional custom output path
        
        Returns:
            Path to the downloaded file
        """
        try:
            from huggingface_hub import hf_hub_download
            
            print(f"\nDownloading {filename} from {repo}...")
            print("This may take a while depending on your internet connection...\n")
            
            # Download with progress bar
            file_path = hf_hub_download(
                repo_id=repo,
                filename=filename,
                local_dir=str(self.models_dir),
                local_dir_use_symlinks=False
            )
            
            downloaded_path = Path(file_path)
            print(f"\n✓ Download complete: {downloaded_path}")
            return downloaded_path
            
        except ImportError:
            print("Error: huggingface_hub is not installed.")
            print("Install it with: pip install huggingface_hub")
            raise
        except Exception as e:
            print(f"Error downloading from HuggingFace: {e}")
            raise
    
    def download_from_url(self, url: str, filename: Optional[str] = None) -> Path:
        """
        Download a model from a direct URL.
        
        Args:
            url: Direct download URL
            filename: Optional filename (extracted from URL if not provided)
        
        Returns:
            Path to the downloaded file
        """
        if filename is None:
            filename = url.split('/')[-1]
            if '?' in filename:
                filename = filename.split('?')[0]
        
        output_path = self.models_dir / filename
        
        print(f"\nDownloading from {url}...")
        print(f"Saving to: {output_path}\n")
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f, tqdm(
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    pbar.update(size)
            
            print(f"\n✓ Download complete: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error downloading from URL: {e}")
            if output_path.exists():
                output_path.unlink()  # Remove partial download
            raise
    
    def interactive_download(self) -> Optional[Path]:
        """
        Interactive prompt to select and download a model.
        
        Returns:
            Path to the downloaded model, or None if cancelled
        """
        self.list_popular_models()
        
        print("\nSelect a model to download (or 'q' to quit):")
        choice = input("Enter choice [1-8]: ").strip()
        
        if choice.lower() in ['q', 'quit', 'exit']:
            return None
        
        if choice not in self.POPULAR_MODELS:
            print(f"Invalid choice: {choice}")
            return None
        
        model_info = self.POPULAR_MODELS[choice]
        
        # Handle custom URL
        if choice == "8":
            url = input("\nEnter the direct download URL: ").strip()
            if not url:
                print("No URL provided. Cancelled.")
                return None
            
            filename = input("Enter filename (or press Enter to auto-detect): ").strip()
            filename = filename if filename else None
            
            return self.download_from_url(url, filename)
        
        # Download from HuggingFace
        print(f"\nYou selected: {model_info['name']}")
        print(f"Size: {model_info['size']}")
        
        confirm = input("\nProceed with download? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Download cancelled.")
            return None
        
        return self.download_from_huggingface(
            model_info['repo'],
            model_info['file']
        )
    
    def list_local_models(self) -> List[Path]:
        """
        List all GGUF models in the models directory.
        
        Returns:
            List of paths to local GGUF files
        """
        if not self.models_dir.exists():
            return []
        
        gguf_files = list(self.models_dir.glob("**/*.gguf"))
        return sorted(gguf_files)
    
    def check_and_prompt_download(self, model_path: Optional[str] = None) -> Optional[Path]:
        """
        Check if a model exists, and prompt for download if not.
        
        Args:
            model_path: Path to check (if None, checks models directory)
        
        Returns:
            Path to a valid model, or None
        """
        # If specific path provided and exists, return it
        if model_path and Path(model_path).exists():
            return Path(model_path)
        
        # Check for any local models
        local_models = self.list_local_models()
        
        if local_models:
            print("\nFound local models:")
            for i, model in enumerate(local_models, 1):
                size_mb = model.stat().st_size / (1024 * 1024)
                print(f"  [{i}] {model.name} ({size_mb:.1f} MB)")
            
            print(f"\n  [0] Download a new model")
            choice = input(f"\nSelect a model [0-{len(local_models)}]: ").strip()
            
            if choice == "0":
                return self.interactive_download()
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(local_models):
                    return local_models[idx]
            except ValueError:
                pass
            
            print("Invalid selection.")
            return None
        
        # No models found
        print("\n" + "!" * 70)
        print("No LLM models found!")
        print("!" * 70)
        print("\nYou can:")
        print("  1. Download a popular model from HuggingFace")
        print("  2. Download from a custom URL")
        print("  3. Exit and manually add a model to the './models' directory")
        
        choice = input("\nWhat would you like to do? [1/2/3]: ").strip()
        
        if choice == "1" or choice == "2":
            return self.interactive_download()
        
        return None


def main():
    """Standalone model downloader utility."""
    print("=" * 70)
    print("LLM Model Downloader")
    print("=" * 70)
    
    downloader = ModelDownloader()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "list":
            downloader.list_popular_models()
        
        elif command == "download":
            if len(sys.argv) < 3:
                print("Usage: python model_downloader.py download <model_number>")
                downloader.list_popular_models()
            else:
                choice = sys.argv[2]
                if choice in downloader.POPULAR_MODELS:
                    model_info = downloader.POPULAR_MODELS[choice]
                    if model_info['repo']:
                        downloader.download_from_huggingface(
                            model_info['repo'],
                            model_info['file']
                        )
                else:
                    print(f"Invalid model number: {choice}")
        
        elif command == "url":
            if len(sys.argv) < 3:
                print("Usage: python model_downloader.py url <download_url> [filename]")
            else:
                url = sys.argv[2]
                filename = sys.argv[3] if len(sys.argv) > 3 else None
                downloader.download_from_url(url, filename)
        
        elif command == "local":
            local_models = downloader.list_local_models()
            if local_models:
                print("\nLocal models found:")
                for model in local_models:
                    size_mb = model.stat().st_size / (1024 * 1024)
                    print(f"  • {model.name} ({size_mb:.1f} MB)")
                    print(f"    Path: {model}")
            else:
                print("\nNo local models found in ./models directory")
        
        else:
            print(f"Unknown command: {command}")
            print("\nAvailable commands:")
            print("  list     - List popular models")
            print("  download - Download a model by number")
            print("  url      - Download from custom URL")
            print("  local    - List local models")
    
    else:
        # Interactive mode
        downloader.interactive_download()


if __name__ == "__main__":
    main()
