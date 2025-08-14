"""
OrbStack client wrapper for container management.

*Version: 1.1.0*
*Author: AI Development Platform Team*

## Changelog
- 1.1.0 (2025-01-11): Enhanced with file operations, streaming, and complete API coverage.
- 1.0.0 (2024-12-17): Initial OrbStack client implementation.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple, AsyncIterator
from datetime import datetime
import docker
from docker.models.containers import Container as DockerContainer
from docker.errors import DockerException, NotFound, APIError

from modules.backend.core.config import settings

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
    
    async def upload_file(
        self,
        container_id: str,
        file_path: str,
        content: bytes,
        create_dirs: bool = True
    ) -> bool:
        """
        Upload a file to the container.
        
        Args:
            container_id: Container ID
            file_path: Path inside container (absolute)
            content: File content as bytes
            create_dirs: Whether to create parent directories
            
        Returns:
            True if successful
        """
        try:
            container = self.client.containers.get(container_id)
            
            # Create parent directories if needed
            if create_dirs:
                parent_dir = os.path.dirname(file_path)
                if parent_dir and parent_dir != '/':
                    await self.execute_command(
                        container_id,
                        ["mkdir", "-p", parent_dir]
                    )
            
            # Create a tar archive with the file
            import tarfile
            import io
            
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
                info = tarfile.TarInfo(name=os.path.basename(file_path))
                info.size = len(content)
                info.mode = 0o644
                tar.addfile(info, io.BytesIO(content))
            
            tar_buffer.seek(0)
            
            # Upload to container
            container.put_archive(
                path=os.path.dirname(file_path) or '/',
                data=tar_buffer.getvalue()
            )
            
            logger.debug(f"Uploaded file {file_path} to container {container_id[:12]}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            return False
    
    async def download_file(self, container_id: str, file_path: str) -> Optional[bytes]:
        """
        Download a file from the container.
        
        Args:
            container_id: Container ID
            file_path: Path inside container (absolute)
            
        Returns:
            File content as bytes, or None if failed
        """
        try:
            container = self.client.containers.get(container_id)
            
            # Download tar archive
            stream, _ = container.get_archive(file_path)
            
            # Extract content
            import tarfile
            import io
            
            tar_data = b''.join(stream)
            tar_buffer = io.BytesIO(tar_data)
            
            with tarfile.open(fileobj=tar_buffer, mode='r') as tar:
                # Get the first (and should be only) file
                for member in tar.getmembers():
                    if member.isfile():
                        f = tar.extractfile(member)
                        if f:
                            content = f.read()
                            logger.debug(f"Downloaded file {file_path} from container {container_id[:12]}")
                            return content
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {e}")
            return None
    
    async def list_files(
        self,
        container_id: str,
        directory: str = "/workspace",
        recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List files in a container directory.
        
        Args:
            container_id: Container ID
            directory: Directory path
            recursive: Whether to list recursively
            
        Returns:
            List of file info dictionaries
        """
        try:
            cmd = ["find", directory, "-maxdepth", "1" if not recursive else "999", "-type", "f", "-exec", "stat", "-c", "%n|%s|%Y", "{}", ";"]
            exit_code, output = await self.execute_command(container_id, cmd)
            
            if exit_code != 0:
                return []
            
            files = []
            for line in output.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) == 3:
                        path, size, mtime = parts
                        files.append({
                            'path': path,
                            'name': os.path.basename(path),
                            'size': int(size),
                            'modified': int(mtime),
                            'is_directory': False
                        })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files in {directory}: {e}")
            return []
    
    async def create_directory(self, container_id: str, directory_path: str) -> bool:
        """Create a directory in the container."""
        try:
            exit_code, _ = await self.execute_command(
                container_id,
                ["mkdir", "-p", directory_path]
            )
            return exit_code == 0
        except Exception as e:
            logger.error(f"Failed to create directory {directory_path}: {e}")
            return False
    
    async def get_container_info(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed container information."""
        try:
            container = self.client.containers.get(container_id)
            container.reload()
            
            # Get port mappings
            port_mappings = {}
            if container.ports:
                for internal, mappings in container.ports.items():
                    if mappings:
                        port_mappings[internal] = [
                            f"{m['HostIp']}:{m['HostPort']}" for m in mappings
                        ]
            
            return {
                'id': container.id,
                'short_id': container.short_id,
                'name': container.name,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else container.image.id,
                'created': container.attrs['Created'],
                'started': container.attrs['State'].get('StartedAt'),
                'finished': container.attrs['State'].get('FinishedAt'),
                'exit_code': container.attrs['State'].get('ExitCode'),
                'ports': port_mappings,
                'labels': container.labels,
                'network_settings': container.attrs.get('NetworkSettings', {}),
                'mounts': container.attrs.get('Mounts', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get container info: {e}")
            return None
    
    async def stream_logs(
        self,
        container_id: str,
        follow: bool = True,
        tail: str = "50"
    ) -> AsyncIterator[str]:
        """
        Stream container logs in real-time.
        
        Yields log lines as they appear.
        """
        try:
            container = self.client.containers.get(container_id)
            
            # Use the low-level API for streaming
            logs = container.logs(
                stream=True,
                follow=follow,
                tail=tail,
                timestamps=True
            )
            
            for log_line in logs:
                if isinstance(log_line, bytes):
                    yield log_line.decode('utf-8').rstrip('\n')
                else:
                    yield log_line.rstrip('\n')
                    
        except Exception as e:
            logger.error(f"Failed to stream logs: {e}")
            yield f"Error: {e}"
    
    async def execute_command_stream(
        self,
        container_id: str,
        command: List[str],
        workdir: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None
    ) -> AsyncIterator[str]:
        """
        Execute a command and stream output in real-time.
        
        Yields output lines as they appear.
        """
        try:
            container = self.client.containers.get(container_id)
            
            exec_kwargs = {
                'cmd': command,
                'stdout': True,
                'stderr': True,
                'stdin': False,
                'tty': True,
                'stream': True
            }
            
            if workdir:
                exec_kwargs['workdir'] = workdir
            if environment:
                exec_kwargs['environment'] = environment
            
            exec_result = container.exec_run(**exec_kwargs)
            
            # Stream output
            for output in exec_result:
                if isinstance(output, bytes):
                    yield output.decode('utf-8')
                else:
                    yield output
                    
        except Exception as e:
            logger.error(f"Failed to execute streaming command: {e}")
            yield f"Error: {e}"
    
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
    
    async def get_workspace_files(self, container_id: str) -> Dict[str, Any]:
        """
        Get a complete file tree of the workspace.
        
        Returns a nested dictionary representing the file structure.
        """
        try:
            # Use find command to get all files and directories
            exit_code, output = await self.execute_command(
                container_id,
                ["find", "/workspace", "-type", "f", "-o", "-type", "d"]
            )
            
            if exit_code != 0:
                return {}
            
            file_tree = {}
            for line in output.strip().split('\n'):
                if line and line != '/workspace':
                    # Remove /workspace prefix
                    relative_path = line[10:] if line.startswith('/workspace/') else line
                    if relative_path:
                        self._add_to_tree(file_tree, relative_path.split('/'))
            
            return file_tree
            
        except Exception as e:
            logger.error(f"Failed to get workspace files: {e}")
            return {}
    
    def _add_to_tree(self, tree: Dict[str, Any], path_parts: List[str]) -> None:
        """Helper method to build file tree structure."""
        if not path_parts:
            return
        
        current = path_parts[0]
        remaining = path_parts[1:]
        
        if current not in tree:
            tree[current] = {} if remaining else None
        
        if remaining and isinstance(tree[current], dict):
            self._add_to_tree(tree[current], remaining)


# Global OrbStack client instance
orbstack_client = OrbStackClient() 