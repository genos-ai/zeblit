"""
OrbStack client wrapper for container management.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-12-17): Initial OrbStack client implementation.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import docker
from docker.models.containers import Container as DockerContainer
from docker.errors import DockerException, NotFound, APIError

from src.backend.core.config import settings

logger = logging.getLogger(__name__)


class OrbStackClient:
    """
    Client wrapper for OrbStack container management.
    
    OrbStack provides a Docker-compatible API, so we use the Docker SDK
    but with OrbStack-specific optimizations and features.
    """
    
    def __init__(self):
        """Initialize OrbStack client."""
        self._client: Optional[docker.DockerClient] = None
        self._async_client = None
        self._base_image = settings.CONTAINER_BASE_IMAGE
        self._network_name = "ai-platform-network"
    
    async def connect(self) -> None:
        """Connect to OrbStack daemon."""
        try:
            # OrbStack uses standard Docker socket
            self._client = docker.from_env()
            
            # Test connection
            self._client.ping()
            
            # Ensure network exists
            await self._ensure_network()
            
            logger.info("Connected to OrbStack daemon")
            
        except Exception as e:
            logger.error(f"Failed to connect to OrbStack: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close OrbStack connection."""
        if self._client:
            self._client.close()
            self._client = None
        logger.info("Disconnected from OrbStack")
    
    @property
    def client(self) -> docker.DockerClient:
        """Get Docker client instance."""
        if not self._client:
            raise RuntimeError("OrbStack client not connected")
        return self._client
    
    async def _ensure_network(self) -> None:
        """Ensure the platform network exists."""
        try:
            self.client.networks.get(self._network_name)
        except NotFound:
            self.client.networks.create(
                name=self._network_name,
                driver="bridge",
                labels={"platform": "ai-development"}
            )
            logger.info(f"Created network: {self._network_name}")
    
    async def create_container(
        self,
        project_id: str,
        user_id: str,
        cpu_limit: float = 2.0,
        memory_limit: int = 4096,
        disk_limit: int = 10240,
        environment_vars: Optional[Dict[str, str]] = None,
        volumes: Optional[List[Dict[str, Any]]] = None,
        ports: Optional[Dict[str, int]] = None
    ) -> Tuple[str, str]:
        """
        Create a new development container.
        
        Args:
            project_id: Project ID
            user_id: User ID
            cpu_limit: CPU cores limit
            memory_limit: Memory limit in MB
            disk_limit: Disk limit in MB
            environment_vars: Environment variables
            volumes: Volume mounts
            ports: Port mappings
            
        Returns:
            Tuple of (container_id, container_name)
        """
        try:
            # Generate container name
            container_name = f"ai-dev-{project_id[:8]}-{user_id[:8]}"
            
            # Prepare environment
            env = {
                "PROJECT_ID": project_id,
                "USER_ID": user_id,
                "WORKSPACE": "/workspace",
                "NODE_ENV": "development",
                "PYTHONPATH": "/workspace",
                **(environment_vars or {})
            }
            
            # Prepare volumes
            volume_binds = {}
            if volumes:
                for vol in volumes:
                    volume_binds[vol['host_path']] = {
                        'bind': vol['container_path'],
                        'mode': 'ro' if vol.get('read_only') else 'rw'
                    }
            
            # Add default workspace volume
            workspace_volume = f"ai-workspace-{project_id}"
            volume_binds[workspace_volume] = {
                'bind': '/workspace',
                'mode': 'rw'
            }
            
            # Port mappings
            port_bindings = ports or {'3000/tcp': None}  # Dynamic port allocation
            
            # Create container
            container = self.client.containers.create(
                image=self._base_image,
                name=container_name,
                environment=env,
                volumes=volume_binds,
                ports=port_bindings,
                network=self._network_name,
                mem_limit=f"{memory_limit}m",
                nano_cpus=int(cpu_limit * 1_000_000_000),  # Convert to nanocpus
                working_dir="/workspace",
                command="/bin/bash",
                stdin_open=True,
                tty=True,
                detach=True,
                labels={
                    "platform": "ai-development",
                    "project_id": project_id,
                    "user_id": user_id,
                    "created_at": datetime.utcnow().isoformat()
                },
                # OrbStack optimizations
                platform="linux/amd64",  # Ensure compatibility
                extra_hosts={"host.docker.internal": "host-gateway"}  # Host access
            )
            
            logger.info(f"Created container: {container_name} (ID: {container.id[:12]})")
            return container.id, container_name
            
        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            raise
    
    async def start_container(self, container_id: str) -> Optional[int]:
        """
        Start a container.
        
        Args:
            container_id: Container ID
            
        Returns:
            External port mapping if applicable
        """
        try:
            container = self.client.containers.get(container_id)
            
            # Start container
            container.start()
            
            # Wait for container to be running
            container.reload()
            
            # Get port mapping
            external_port = None
            if container.ports:
                for internal, mappings in container.ports.items():
                    if mappings:
                        external_port = int(mappings[0]['HostPort'])
                        break
            
            logger.info(f"Started container: {container_id[:12]}")
            return external_port
            
        except NotFound:
            logger.error(f"Container not found: {container_id}")
            raise
        except Exception as e:
            logger.error(f"Failed to start container: {e}")
            raise
    
    async def stop_container(self, container_id: str, timeout: int = 10) -> None:
        """Stop a container gracefully."""
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)
            logger.info(f"Stopped container: {container_id[:12]}")
        except NotFound:
            logger.warning(f"Container not found: {container_id}")
        except Exception as e:
            logger.error(f"Failed to stop container: {e}")
            raise
    
    async def pause_container(self, container_id: str) -> None:
        """Pause a container (sleep mode)."""
        try:
            container = self.client.containers.get(container_id)
            container.pause()
            logger.info(f"Paused container: {container_id[:12]}")
        except Exception as e:
            logger.error(f"Failed to pause container: {e}")
            raise
    
    async def unpause_container(self, container_id: str) -> None:
        """Unpause a container (wake from sleep)."""
        try:
            container = self.client.containers.get(container_id)
            container.unpause()
            logger.info(f"Unpaused container: {container_id[:12]}")
        except Exception as e:
            logger.error(f"Failed to unpause container: {e}")
            raise
    
    async def restart_container(self, container_id: str, timeout: int = 10) -> None:
        """Restart a container."""
        try:
            container = self.client.containers.get(container_id)
            container.restart(timeout=timeout)
            logger.info(f"Restarted container: {container_id[:12]}")
        except Exception as e:
            logger.error(f"Failed to restart container: {e}")
            raise
    
    async def remove_container(self, container_id: str, force: bool = False) -> None:
        """Remove a container."""
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            logger.info(f"Removed container: {container_id[:12]}")
        except NotFound:
            logger.warning(f"Container already removed: {container_id}")
        except Exception as e:
            logger.error(f"Failed to remove container: {e}")
            raise
    
    async def get_container_stats(self, container_id: str) -> Dict[str, Any]:
        """Get container resource usage statistics."""
        try:
            container = self.client.containers.get(container_id)
            
            # Get stats (non-streaming)
            stats = container.stats(stream=False)
            
            # Calculate usage
            cpu_percent = self._calculate_cpu_percent(stats)
            memory_usage_mb = stats['memory_stats'].get('usage', 0) / (1024 * 1024)
            memory_limit_mb = stats['memory_stats'].get('limit', 0) / (1024 * 1024)
            
            # Network stats
            networks = stats.get('networks', {})
            network_in_mb = sum(net.get('rx_bytes', 0) for net in networks.values()) / (1024 * 1024)
            network_out_mb = sum(net.get('tx_bytes', 0) for net in networks.values()) / (1024 * 1024)
            
            return {
                'cpu_percent': cpu_percent,
                'memory_usage_mb': int(memory_usage_mb),
                'memory_limit_mb': int(memory_limit_mb),
                'network_in_mb': round(network_in_mb, 2),
                'network_out_mb': round(network_out_mb, 2),
                'block_read_mb': stats.get('blkio_stats', {}).get('io_service_bytes_recursive', []),
                'pids': stats.get('pids_stats', {}).get('current', 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get container stats: {e}")
            return {}
    
    async def get_container_logs(
        self,
        container_id: str,
        tail: int = 100,
        since: Optional[datetime] = None
    ) -> str:
        """Get container logs."""
        try:
            container = self.client.containers.get(container_id)
            
            kwargs = {
                'tail': tail,
                'timestamps': True,
                'stderr': True,
                'stdout': True
            }
            
            if since:
                kwargs['since'] = since
            
            logs = container.logs(**kwargs)
            return logs.decode('utf-8') if isinstance(logs, bytes) else logs
            
        except Exception as e:
            logger.error(f"Failed to get container logs: {e}")
            return ""
    
    async def execute_command(
        self,
        container_id: str,
        command: List[str],
        workdir: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None
    ) -> Tuple[int, str]:
        """
        Execute a command inside the container.
        
        Returns:
            Tuple of (exit_code, output)
        """
        try:
            container = self.client.containers.get(container_id)
            
            exec_kwargs = {
                'cmd': command,
                'stdout': True,
                'stderr': True,
                'stdin': False,
                'tty': False,
                'demux': True
            }
            
            if workdir:
                exec_kwargs['workdir'] = workdir
            if environment:
                exec_kwargs['environment'] = environment
            
            exit_code, output = container.exec_run(**exec_kwargs)
            
            # Combine stdout and stderr
            if isinstance(output, tuple):
                stdout, stderr = output
                output_str = (stdout or b'').decode('utf-8') + (stderr or b'').decode('utf-8')
            else:
                output_str = output.decode('utf-8') if output else ''
            
            return exit_code, output_str
            
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            raise
    
    async def health_check(self, container_id: str) -> bool:
        """Perform container health check."""
        try:
            # Simple check: run echo command
            exit_code, _ = await self.execute_command(
                container_id,
                ["echo", "health check"]
            )
            return exit_code == 0
        except:
            return False
    
    async def list_project_containers(self, project_id: str) -> List[Dict[str, Any]]:
        """List all containers for a project."""
        try:
            containers = self.client.containers.list(
                all=True,
                filters={"label": f"project_id={project_id}"}
            )
            
            return [
                {
                    'id': c.id,
                    'name': c.name,
                    'status': c.status,
                    'created': c.attrs['Created'],
                    'labels': c.labels
                }
                for c in containers
            ]
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            return []
    
    def _calculate_cpu_percent(self, stats: Dict[str, Any]) -> float:
        """Calculate CPU usage percentage from stats."""
        try:
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})
            
            # Calculate CPU usage
            cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
            system_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
            
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * 100.0 * cpu_stats['online_cpus']
                return round(cpu_percent, 2)
            
            return 0.0
        except:
            return 0.0
    
    async def cleanup_old_containers(self, days: int = 7) -> int:
        """Clean up containers older than specified days."""
        try:
            containers = self.client.containers.list(
                all=True,
                filters={"label": "platform=ai-development"}
            )
            
            removed_count = 0
            cutoff_date = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
            
            for container in containers:
                created_at = container.attrs['Created']
                # Parse Docker timestamp
                if isinstance(created_at, str):
                    created_timestamp = datetime.fromisoformat(
                        created_at.replace('Z', '+00:00')
                    ).timestamp()
                else:
                    created_timestamp = created_at
                
                if created_timestamp < cutoff_date and container.status == 'exited':
                    await self.remove_container(container.id, force=True)
                    removed_count += 1
            
            logger.info(f"Cleaned up {removed_count} old containers")
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup containers: {e}")
            return 0


# Global OrbStack client instance
orbstack_client = OrbStackClient() 