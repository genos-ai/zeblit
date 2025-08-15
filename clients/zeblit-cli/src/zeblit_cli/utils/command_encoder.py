"""
Command encoding utilities for safe transport and execution.

*Version: 1.0.0*
*Author: Zeblit CLI Team*

## Changelog
- 1.0.0 (2025-01-15): Initial command encoder for robust special character handling.
"""

import base64
import json
import shlex
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict


@dataclass
class CommandSpec:
    """Complete command specification."""
    command: List[str]
    workdir: Optional[str] = None
    environment: Optional[Dict[str, str]] = None
    encoding: str = "utf-8"
    shell: bool = False
    interactive: bool = False
    timeout: Optional[int] = None


class CommandEncoder:
    """Encode commands for safe transport and execution."""
    
    @staticmethod
    def encode_command(
        command: Union[str, List[str]],
        workdir: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        shell: bool = False
    ) -> str:
        """
        Encode command for safe transport.
        
        Args:
            command: Command string or list
            workdir: Working directory
            environment: Environment variables
            shell: Execute via shell (for pipes, redirects, etc.)
        
        Returns:
            Base64 encoded command specification
        """
        # Handle both string and list inputs
        if isinstance(command, str):
            if shell or CommandEncoder._needs_shell(command):
                # For shell commands, pass as single string
                cmd_list = ["/bin/bash", "-c", command]
                shell = True
            else:
                # Parse string into arguments safely
                try:
                    cmd_list = shlex.split(command)
                except ValueError:
                    # If shlex fails, use shell mode
                    cmd_list = ["/bin/bash", "-c", command]
                    shell = True
        else:
            cmd_list = command
        
        # Create command specification
        spec = CommandSpec(
            command=cmd_list,
            workdir=workdir,
            environment=environment or {},
            shell=shell
        )
        
        # Serialize to JSON then base64
        spec_json = json.dumps(asdict(spec))
        encoded = base64.b64encode(spec_json.encode('utf-8')).decode('ascii')
        
        return encoded
    
    @staticmethod
    def decode_command(encoded: str) -> CommandSpec:
        """Decode command specification."""
        try:
            spec_json = base64.b64decode(encoded.encode('ascii')).decode('utf-8')
            spec_dict = json.loads(spec_json)
            return CommandSpec(**spec_dict)
        except Exception as e:
            raise ValueError(f"Invalid encoded command format: {e}")
    
    @staticmethod
    def _needs_shell(command: str) -> bool:
        """Determine if command needs shell execution."""
        shell_operators = ['|', '&&', '||', '>', '>>', '<', ';', '&', '$', '`']
        return any(op in command for op in shell_operators) or '\n' in command


class CommandParser:
    """Parse various command input formats."""
    
    @staticmethod
    def smart_parse(input_text: str) -> CommandSpec:
        """
        Intelligently parse command input.
        
        Handles:
        - Simple commands: "ls -la"
        - Shell operations: "ps aux | grep python"
        - Multi-line scripts: "#!/bin/bash\necho hello\necho world"
        """
        # Detect if it's a shell command (contains shell operators)
        needs_shell = CommandEncoder._needs_shell(input_text)
        
        # Detect multi-line scripts
        is_multiline = '\n' in input_text.strip()
        
        if is_multiline or needs_shell:
            # Handle as shell command
            return CommandSpec(
                command=["/bin/bash", "-c", input_text],
                shell=True
            )
        else:
            # Handle as simple command
            try:
                return CommandSpec(
                    command=shlex.split(input_text),
                    shell=False
                )
            except ValueError:
                # Fallback to shell if parsing fails
                return CommandSpec(
                    command=["/bin/bash", "-c", input_text],
                    shell=True
                )
