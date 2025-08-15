"""
Command decoder utilities for safe command execution.

*Version: 1.0.0*
*Author: Zeblit Backend Team*

## Changelog
- 1.0.0 (2025-01-15): Initial command decoder for robust special character handling.
"""

import base64
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


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


class CommandDecoder:
    """Decode and validate commands for safe execution."""
    
    @staticmethod
    def decode_command(encoded: str) -> CommandSpec:
        """
        Decode base64 encoded command specification.
        
        Args:
            encoded: Base64 encoded command specification
            
        Returns:
            CommandSpec object
            
        Raises:
            ValueError: If encoded command is invalid
        """
        try:
            # Decode base64
            spec_json = base64.b64decode(encoded.encode('ascii')).decode('utf-8')
            
            # Parse JSON
            spec_dict = json.loads(spec_json)
            
            # Validate required fields
            if 'command' not in spec_dict:
                raise ValueError("Command specification missing 'command' field")
            
            # Create CommandSpec with defaults
            spec = CommandSpec(
                command=spec_dict['command'],
                workdir=spec_dict.get('workdir'),
                environment=spec_dict.get('environment', {}),
                encoding=spec_dict.get('encoding', 'utf-8'),
                shell=spec_dict.get('shell', False),
                interactive=spec_dict.get('interactive', False),
                timeout=spec_dict.get('timeout')
            )
            
            # Validate command
            CommandDecoder._validate_command_spec(spec)
            
            return spec
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse command JSON: {e}")
            raise ValueError(f"Invalid JSON in encoded command: {e}")
        except Exception as e:
            logger.error(f"Failed to decode command: {e}")
            raise ValueError(f"Invalid encoded command format: {e}")
    
    @staticmethod
    def _validate_command_spec(spec: CommandSpec) -> None:
        """
        Validate command specification for security and safety.
        
        Args:
            spec: CommandSpec to validate
            
        Raises:
            ValueError: If command specification is invalid or unsafe
        """
        # Check command is not empty
        if not spec.command or not isinstance(spec.command, list):
            raise ValueError("Command must be a non-empty list")
        
        # Check for empty command elements
        if any(not isinstance(cmd, str) or not cmd.strip() for cmd in spec.command):
            raise ValueError("Command elements must be non-empty strings")
        
        # Security: Check for dangerous commands (configurable)
        dangerous_commands = ['rm', 'dd', 'mkfs', 'fdisk', 'parted']
        first_cmd = spec.command[0].split('/')[-1]  # Get basename
        
        if first_cmd in dangerous_commands:
            logger.warning(f"Potentially dangerous command detected: {first_cmd}")
            # Could raise an error here for strict security
        
        # Validate working directory
        if spec.workdir:
            if not isinstance(spec.workdir, str):
                raise ValueError("Working directory must be a string")
            
            # Security: Ensure workdir is safe (no path traversal)
            if '..' in spec.workdir or spec.workdir.startswith('/'):
                if not spec.workdir.startswith('/workspace'):
                    raise ValueError("Working directory must be within /workspace")
        
        # Validate environment variables
        if spec.environment:
            if not isinstance(spec.environment, dict):
                raise ValueError("Environment must be a dictionary")
            
            for key, value in spec.environment.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise ValueError("Environment variables must be strings")
        
        # Validate timeout
        if spec.timeout is not None:
            if not isinstance(spec.timeout, int) or spec.timeout <= 0:
                raise ValueError("Timeout must be a positive integer")
            
            # Reasonable timeout limits
            if spec.timeout > 3600:  # 1 hour max
                raise ValueError("Timeout cannot exceed 3600 seconds")
        
        logger.debug(f"Command specification validated: {spec.command[:2]}...")


class CommandSanitizer:
    """Sanitize commands for safe execution."""
    
    @staticmethod
    def sanitize_environment(env: Dict[str, str]) -> Dict[str, str]:
        """
        Sanitize environment variables.
        
        Args:
            env: Environment variables dictionary
            
        Returns:
            Sanitized environment variables
        """
        sanitized = {}
        
        # Allow list of safe environment variables
        safe_vars = {
            'PATH', 'HOME', 'USER', 'SHELL', 'TERM', 'LANG', 'LC_ALL',
            'NODE_ENV', 'NODE_PATH', 'NPM_CONFIG_PREFIX',
            'PYTHON_PATH', 'PYTHONPATH', 'PIP_CONFIG_FILE',
            'PORT', 'HOST', 'DEBUG', 'LOG_LEVEL'
        }
        
        for key, value in env.items():
            # Check if variable name is safe
            if key in safe_vars or key.startswith('APP_') or key.startswith('CUSTOM_'):
                # Sanitize value (remove potentially dangerous characters)
                sanitized_value = value.replace(';', '').replace('&', '').replace('|', '')
                sanitized[key] = sanitized_value
            else:
                logger.warning(f"Skipping potentially unsafe environment variable: {key}")
        
        return sanitized
    
    @staticmethod
    def get_safe_workdir(workdir: Optional[str]) -> str:
        """
        Get safe working directory.
        
        Args:
            workdir: Requested working directory
            
        Returns:
            Safe working directory path
        """
        if not workdir:
            return '/workspace'
        
        # Ensure it's within workspace
        if workdir.startswith('/workspace'):
            return workdir
        else:
            # Treat as relative to workspace
            return f'/workspace/{workdir.lstrip("/")}'
