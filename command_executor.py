"""
Command Executor for LLM-generated filesystem commands
Safely executes file/folder operations within a sandboxed workspace directory
"""

import os
import re
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class CommandExecutor:
    """Executes file system commands within a safe sandbox directory"""
    
    def __init__(self, workspace_dir: str = "./llm_workspace"):
        """
        Initialize the command executor with a workspace directory.
        
        Args:
            workspace_dir: Path to the sandbox directory (default: ./llm_workspace)
        """
        self.workspace_dir = Path(workspace_dir).resolve()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.is_windows = platform.system() == "Windows"
        logger.info(f"CommandExecutor initialized with workspace: {self.workspace_dir}")
    
    def is_safe_path(self, path: str) -> bool:
        """
        Verify that a path is within the workspace (prevents path traversal attacks).
        
        Args:
            path: Path to verify
            
        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Resolve to absolute path
            resolved = (self.workspace_dir / path).resolve()
            # Check if it's within workspace
            return str(resolved).startswith(str(self.workspace_dir))
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            return False
    
    def detect_commands(self, text: str) -> List[Dict[str, str]]:
        """
        Detect file system commands in LLM output.
        
        Args:
            text: The text to search for commands
            
        Returns:
            List of detected commands with type and parameters
        """
        commands = []
        
        # PowerShell patterns
        powershell_patterns = [
            (r'New-Item\s+-Path\s+["\']?([^"\'>\n]+)["\']?\s+-ItemType\s+Directory', 'mkdir'),
            (r'New-Item\s+-ItemType\s+Directory\s+-Path\s+["\']?([^"\'>\n]+)["\']?', 'mkdir'),
            (r'New-Item\s+-Path\s+["\']?([^"\'>\n]+)["\']?\s+-ItemType\s+File', 'touch'),
            (r'New-Item\s+-ItemType\s+File\s+-Path\s+["\']?([^"\'>\n]+)["\']?', 'touch'),
            (r'mkdir\s+["\']?([^"\'>\n]+)["\']?', 'mkdir'),
        ]
        
        # Bash/CMD patterns
        bash_patterns = [
            (r'mkdir\s+-p\s+["\']?([^"\'>\n]+)["\']?', 'mkdir'),
            (r'mkdir\s+["\']?([^"\'>\n]+)["\']?', 'mkdir'),
            (r'touch\s+["\']?([^"\'>\n]+)["\']?', 'touch'),
        ]
        
        # CMD patterns
        cmd_patterns = [
            (r'md\s+["\']?([^"\'>\n]+)["\']?', 'mkdir'),
        ]
        
        # Combine all patterns
        all_patterns = powershell_patterns + bash_patterns + cmd_patterns
        
        for pattern, cmd_type in all_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                path = match.group(1).strip()
                commands.append({
                    'type': cmd_type,
                    'path': path,
                    'original': match.group(0)
                })
        
        return commands
    
    def execute_mkdir(self, path: str) -> Dict[str, any]:
        """
        Create a directory safely within the workspace.
        
        Args:
            path: Relative path to create
            
        Returns:
            Result dictionary with status and message
        """
        try:
            if not self.is_safe_path(path):
                return {
                    'success': False,
                    'path': path,
                    'error': 'Path outside workspace boundary (security violation)'
                }
            
            full_path = self.workspace_dir / path
            full_path.mkdir(parents=True, exist_ok=True)
            
            return {
                'success': True,
                'path': str(full_path.relative_to(self.workspace_dir)),
                'absolute_path': str(full_path),
                'message': 'Directory created successfully'
            }
        except Exception as e:
            logger.error(f"mkdir error: {e}")
            return {
                'success': False,
                'path': path,
                'error': str(e)
            }
    
    def execute_touch(self, path: str) -> Dict[str, any]:
        """
        Create a file safely within the workspace.
        
        Args:
            path: Relative path to create
            
        Returns:
            Result dictionary with status and message
        """
        try:
            if not self.is_safe_path(path):
                return {
                    'success': False,
                    'path': path,
                    'error': 'Path outside workspace boundary (security violation)'
                }
            
            full_path = self.workspace_dir / path
            
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create or touch the file
            full_path.touch(exist_ok=True)
            
            return {
                'success': True,
                'path': str(full_path.relative_to(self.workspace_dir)),
                'absolute_path': str(full_path),
                'message': 'File created successfully'
            }
        except Exception as e:
            logger.error(f"touch error: {e}")
            return {
                'success': False,
                'path': path,
                'error': str(e)
            }
    
    def execute_commands(self, commands: List[Dict[str, str]]) -> List[Dict[str, any]]:
        """
        Execute a list of detected commands.
        
        Args:
            commands: List of command dictionaries from detect_commands()
            
        Returns:
            List of execution results
        """
        results = []
        
        for cmd in commands:
            cmd_type = cmd['type']
            path = cmd['path']
            
            if cmd_type == 'mkdir':
                result = self.execute_mkdir(path)
            elif cmd_type == 'touch':
                result = self.execute_touch(path)
            else:
                result = {
                    'success': False,
                    'path': path,
                    'error': f'Unknown command type: {cmd_type}'
                }
            
            result['original_command'] = cmd['original']
            results.append(result)
        
        return results
    
    def process_llm_output(self, text: str) -> Tuple[str, List[Dict[str, any]]]:
        """
        Detect and execute commands in LLM output.
        
        Args:
            text: LLM output text
            
        Returns:
            Tuple of (original_text, execution_results)
        """
        commands = self.detect_commands(text)
        
        if not commands:
            return text, []
        
        results = self.execute_commands(commands)
        
        # Log execution summary
        success_count = sum(1 for r in results if r['success'])
        logger.info(f"Executed {success_count}/{len(results)} commands successfully")
        
        return text, results
    
    def get_workspace_contents(self) -> Dict[str, any]:
        """
        Get a tree view of workspace contents.
        
        Returns:
            Dictionary containing workspace structure
        """
        def build_tree(path: Path, prefix: str = "") -> List[str]:
            """Recursively build directory tree"""
            items = []
            try:
                contents = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
                for i, item in enumerate(contents):
                    is_last = i == len(contents) - 1
                    current_prefix = "└── " if is_last else "├── "
                    items.append(prefix + current_prefix + item.name)
                    
                    if item.is_dir():
                        extension = "    " if is_last else "│   "
                        items.extend(build_tree(item, prefix + extension))
            except PermissionError:
                pass
            
            return items
        
        tree = [str(self.workspace_dir) + "/"]
        tree.extend(build_tree(self.workspace_dir))
        
        return {
            'workspace': str(self.workspace_dir),
            'tree': tree,
            'tree_string': '\n'.join(tree)
        }
