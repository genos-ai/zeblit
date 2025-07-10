"""
OrbStack integration for container management.

Version: 1.0.0
Author: Zeblit Team

## Changelog
- 1.0.0 (2024-01-08): Initial OrbStack client implementation
"""

import asyncio
import json
import logging
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from uuid import uuid4

from src.backend.core.config import settings

logger = logging.getLogger(__name__)


class OrbStackClient:
    """Client for interacting with OrbStack container runtime."""
    
    def __init__(self):
        """Initialize OrbStack client."""
        self.base_image = settings.CONTAINER_BASE_IMAGE
        self.network_name = settings.CONTAINER_NETWORK_NAME
        self._ensure_network()
    
    def _ensure_network(self) -> None:
        """Ensure the container network exists."""
        try:
            # Check if network exists
            result = subprocess.run(
                ["docker", "network", "ls", "--format", "{{.Name}}"],
                capture_output=True,
                text=True
            )
            
            if self.network_name not in result.stdout:
                # Create network
                subprocess.run(
                    ["docker", "network", "create", self.network_name],
                    check=True
                )
                logger.info(f"Created Docker network: {self.network_name}")
        except Exception as e:
            logger.error(f"Failed to ensure network: {e}")
    
    async def create_container(
        self,
        project_id: str,
        user_id: str,
        cpu_limit: float,
        memory_limit: int,
        disk_limit: int,
        environment_vars: Optional[Dict[str, str]] = None
    ) -> Tuple[str, str]:
        """
        Create a new container.
        
        Returns:
            Tuple of (container_id, container_name)
        """
        try:
            # Generate container name
            container_name = f"aidev-{user_id[:8]}-{project_id[:8]}-{uuid4().hex[:8]}"
            
            # Build docker run command
            cmd = [
                "docker", "create",
                "--name", container_name,
                "--network", self.network_name,
                "--cpus", str(cpu_limit),
                "--memory", f"{memory_limit}m",
                "--restart", "unless-stopped",
                "--label", f"aidev.project_id={project_id}",
                "--label", f"aidev.user_id={user_id}",
                "--label", "aidev.managed=true"
            ]
            
            # Add environment variables
            if environment_vars:
                for key, value in environment_vars.items():
                    cmd.extend(["-e", f"{key}={value}"])
            
            # Add default environment
            cmd.extend([
                "-e", f"PROJECT_ID={project_id}",
                "-e", f"USER_ID={user_id}",
                "-e", "PYTHONUNBUFFERED=1"
            ])
            
            # Add volume for project files
            cmd.extend([
                "-v", f"aidev-{project_id}:/workspace",
                "-w", "/workspace"
            ])
            
            # Add image
            cmd.append(self.base_image)
            
            # Default command
            cmd.extend(["sleep", "infinity"])
            
            # Create container
            result = await self._run_command(cmd)
            container_id = result.strip()
            
            logger.info(f"Created container {container_name} ({container_id})")
            return container_id, container_name
            
        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            raise
    
    async def start_container(self, container_id: str) -> int:
        """
        Start a container.
        
        Returns:
            External port number
        """
        try:
            # Start container
            await self._run_command(["docker", "start", container_id])
            
            # Get container port (if exposed)
            # For now, return a dummy port - in production, this would
            # get the actual mapped port
            port = 8000 + hash(container_id) % 1000
            
            logger.info(f"Started container {container_id}")
            return port
            
        except Exception as e:
            logger.error(f"Failed to start container: {e}")
            raise
    
    async def stop_container(self, container_id: str) -> None:
        """Stop a container."""
        try:
            await self._run_command(["docker", "stop", container_id])
            logger.info(f"Stopped container {container_id}")
        except Exception as e:
            logger.error(f"Failed to stop container: {e}")
            raise
    
    async def restart_container(self, container_id: str) -> None:
        """Restart a container."""
        try:
            await self._run_command(["docker", "restart", container_id])
            logger.info(f"Restarted container {container_id}")
        except Exception as e:
            logger.error(f"Failed to restart container: {e}")
            raise
    
    async def pause_container(self, container_id: str) -> None:
        """Pause a container (sleep mode)."""
        try:
            await self._run_command(["docker", "pause", container_id])
            logger.info(f"Paused container {container_id}")
        except Exception as e:
            logger.error(f"Failed to pause container: {e}")
            raise
    
    async def unpause_container(self, container_id: str) -> None:
        """Unpause a container (wake from sleep)."""
        try:
            await self._run_command(["docker", "unpause", container_id])
            logger.info(f"Unpaused container {container_id}")
        except Exception as e:
            logger.error(f"Failed to unpause container: {e}")
            raise
    
    async def remove_container(self, container_id: str, force: bool = False) -> None:
        """Remove a container."""
        try:
            cmd = ["docker", "rm"]
            if force:
                cmd.append("-f")
            cmd.append(container_id)
            
            await self._run_command(cmd)
            logger.info(f"Removed container {container_id}")
        except Exception as e:
            logger.error(f"Failed to remove container: {e}")
            raise
    
    async def get_container_stats(self, container_id: str) -> Dict[str, Any]:
        """Get container resource usage statistics."""
        try:
            # Get stats
            cmd = [
                "docker", "stats", container_id,
                "--no-stream", "--format", "json"
            ]
            result = await self._run_command(cmd)
            
            if not result:
                return {}
            
            stats = json.loads(result)
            
            # Parse stats
            cpu_percent = float(stats.get("CPUPerc", "0%").rstrip("%"))
            
            # Parse memory usage
            mem_usage = stats.get("MemUsage", "0MiB / 0MiB")
            mem_current = self._parse_size(mem_usage.split("/")[0].strip())
            
            # Parse network I/O
            net_io = stats.get("NetIO", "0B / 0B")
            net_parts = net_io.split("/")
            net_in = self._parse_size(net_parts[0].strip())
            net_out = self._parse_size(net_parts[1].strip()) if len(net_parts) > 1 else 0
            
            return {
                "cpu_percent": cpu_percent,
                "memory_usage_mb": mem_current / (1024 * 1024),
                "network_in_mb": net_in / (1024 * 1024),
                "network_out_mb": net_out / (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"Failed to get container stats: {e}")
            return {}
    
    async def get_container_logs(
        self,
        container_id: str,
        tail: int = 100
    ) -> str:
        """Get container logs."""
        try:
            cmd = ["docker", "logs", container_id, "--tail", str(tail)]
            result = await self._run_command(cmd)
            return result
        except Exception as e:
            logger.error(f"Failed to get container logs: {e}")
            return ""
    
    async def execute_command(
        self,
        container_id: str,
        command: List[str],
        workdir: Optional[str] = None
    ) -> Tuple[int, str]:
        """
        Execute a command in the container.
        
        Returns:
            Tuple of (exit_code, output)
        """
        try:
            cmd = ["docker", "exec"]
            
            if workdir:
                cmd.extend(["-w", workdir])
            
            cmd.append(container_id)
            cmd.extend(command)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            stdout, _ = await process.communicate()
            output = stdout.decode() if stdout else ""
            
            return process.returncode or 0, output
            
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            return 1, str(e)
    
    async def cleanup_old_containers(self, days: int) -> int:
        """
        Clean up containers older than specified days.
        
        Returns:
            Number of containers removed
        """
        try:
            # Find old containers
            cmd = [
                "docker", "ps", "-a",
                "--filter", "label=aidev.managed=true",
                "--format", "{{.ID}} {{.CreatedAt}}"
            ]
            result = await self._run_command(cmd)
            
            if not result:
                return 0
            
            removed = 0
            for line in result.strip().split("\n"):
                parts = line.split(maxsplit=1)
                if len(parts) < 2:
                    continue
                
                container_id = parts[0]
                # TODO: Parse date and check if older than days
                # For now, skip actual cleanup
                
            return removed
            
        except Exception as e:
            logger.error(f"Failed to cleanup containers: {e}")
            return 0
    
    async def _run_command(self, cmd: List[str]) -> str:
        """Run a command and return output."""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"Command failed: {error_msg}")
        
        return stdout.decode() if stdout else ""
    
    def _parse_size(self, size_str: str) -> float:
        """Parse size string (e.g., '1.5GiB') to bytes."""
        size_str = size_str.strip()
        if not size_str or size_str == "0":
            return 0
        
        units = {
            "B": 1,
            "KB": 1024,
            "KiB": 1024,
            "MB": 1024 * 1024,
            "MiB": 1024 * 1024,
            "GB": 1024 * 1024 * 1024,
            "GiB": 1024 * 1024 * 1024
        }
        
        for unit, multiplier in units.items():
            if size_str.endswith(unit):
                try:
                    value = float(size_str[:-len(unit)])
                    return value * multiplier
                except ValueError:
                    pass
        
        # Try to parse as plain number
        try:
            return float(size_str)
        except ValueError:
            return 0


# Create singleton instance
orbstack_client = OrbStackClient() 