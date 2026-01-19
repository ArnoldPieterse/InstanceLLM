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
        Detect file system and terminal commands in LLM output.
        
        Args:
            text: The text to search for commands
            
        Returns:
            List of detected commands with type and parameters
        """
        commands = []
        
        # Terminal command patterns (detect code blocks and command markers)
        # Look for commands in code blocks or after $ or >
        terminal_patterns = [
            # PowerShell/CMD commands in code blocks
            (r'```(?:powershell|ps1|cmd|bash|sh|shell)\n(.*?)\n```', 'terminal_block'),
            # Single line commands with $ or > prefix
            (r'^\$\s+(.+?)$', 'terminal_line'),
            (r'^>\s+(.+?)$', 'terminal_line'),
            # Python scripts
            (r'```python\n(.*?)\n```', 'python_script'),
        ]
        
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
        
        # Detect terminal commands first (higher priority)
        for pattern, cmd_type in terminal_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            for match in matches:
                command_text = match.group(1).strip()
                commands.append({
                    'type': cmd_type,
                    'command': command_text,
                    'original': match.group(0)
                })
        
        # Then detect file system commands
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
    
    def execute_terminal_command(self, command: str, cmd_type: str = 'terminal_block') -> Dict[str, any]:
        """
        Execute a terminal command safely within the workspace.
        
        Args:
            command: Command string to execute
            cmd_type: Type of command (terminal_block, terminal_line, python_script)
            
        Returns:
            Result dictionary with status, output, and error
        """
        try:
            # Determine the shell
            if self.is_windows:
                shell_cmd = ['powershell', '-Command', command]
            else:
                shell_cmd = ['bash', '-c', command]
            
            # For Python scripts, use python directly
            if cmd_type == 'python_script':
                # Write to temp file and execute
                temp_file = self.workspace_dir / '_temp_script.py'
                temp_file.write_text(command)
                shell_cmd = ['python', str(temp_file)]
            
            logger.info(f"Executing terminal command in workspace: {command[:100]}")
            
            # Execute with timeout
            result = subprocess.run(
                shell_cmd,
                cwd=str(self.workspace_dir),
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                shell=False
            )
            
            # Clean up temp file if it exists
            if cmd_type == 'python_script':
                temp_file = self.workspace_dir / '_temp_script.py'
                if temp_file.exists():
                    temp_file.unlink()
            
            success = result.returncode == 0
            
            return {
                'success': success,
                'command': command[:200],  # Truncate for display
                'return_code': result.returncode,
                'stdout': result.stdout.strip() if result.stdout else '',
                'stderr': result.stderr.strip() if result.stderr else '',
                'message': 'Command executed successfully' if success else 'Command failed',
                'type': cmd_type
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout: {command[:100]}")
            return {
                'success': False,
                'command': command[:200],
                'error': 'Command timed out after 30 seconds',
                'type': cmd_type
            }
        except Exception as e:
            logger.error(f"Terminal command error: {e}")
            return {
                'success': False,
                'command': command[:200],
                'error': str(e),
                'type': cmd_type
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
            
            # Handle terminal commands
            if cmd_type in ['terminal_block', 'terminal_line', 'python_script']:
                result = self.execute_terminal_command(cmd['command'], cmd_type)
            # Handle file system commands
            elif cmd_type == 'mkdir':
                result = self.execute_mkdir(cmd['path'])
            elif cmd_type == 'touch':
                result = self.execute_touch(cmd['path'])
            else:
                result = {
                    'success': False,
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
