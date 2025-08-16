"""
Container service for managing development environments.

*Version: 1.1.0*
*Author: AI Development Platform Team*

## Changelog
- 1.1.0 (2025-01-11): Added project-specific container methods for backend-first API.
- 1.0.0 (2024-12-17): Initial container service implementation.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update
from sqlalchemy.orm import selectinload

from modules.backend.models import Container, Project, User
from modules.backend.models.enums import ContainerStatus
from modules.backend.repositories.container import ContainerRepository
from modules.backend.core.orbstack_client import orbstack_client
from modules.backend.core.config import settings
from modules.backend.core.exceptions import (
    ValidationError,
    NotFoundError,
    ForbiddenError,
    ServiceError
)
from modules.backend.core.cache import project_cache

logger = logging.getLogger(__name__)


class ContainerService:
    """Service for managing development containers."""
    
    def __init__(self):
        """Initialize container service."""
        self._cleanup_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
    
    async def start_background_tasks(self) -> None:
        """Start background tasks for container management."""
        if settings.ENABLE_CONTAINERS:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            logger.info("Container background tasks started")
    
    async def stop_background_tasks(self) -> None:
        """Stop background tasks."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Container background tasks stopped")
    
    async def create_container(
        self,
        db: AsyncSession,
        project_id: UUID,
        user: User,
        cpu_limit: Optional[float] = None,
        memory_limit: Optional[int] = None,
        disk_limit: Optional[int] = None,
        environment_vars: Optional[Dict[str, str]] = None
    ) -> Container:
        """
        Create a new container for a project.
        
        Args:
            db: Database session
            project_id: Project ID
            user: Current user
            cpu_limit: CPU limit in cores
            memory_limit: Memory limit in MB
            disk_limit: Disk limit in MB
            environment_vars: Environment variables
            
        Returns:
            Created container
        """
        try:
            # Check if containers are enabled
            if not settings.ENABLE_CONTAINERS:
                raise ServiceError("Container support is disabled")
            
            # Get project and verify access
            project = await db.get(Project, project_id)
            if not project or project.owner_id != user.id:
                raise NotFoundError("Project not found")
            
            # Check if project already has a container
            existing = await db.execute(
                select(Container).where(
                    and_(
                        Container.project_id == project_id,
                        Container.status.notin_([
                            ContainerStatus.DELETED,
                            ContainerStatus.ERROR
                        ])
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise ValidationError("Project already has an active container")
            
            # Check user's container limit
            user_containers = await db.execute(
                select(Container).where(
                    and_(
                        Container.project_id.in_(
                            select(Project.id).where(Project.owner_id == user.id)
                        ),
                        Container.status != ContainerStatus.DELETED
                    )
                )
            )
            if len(user_containers.scalars().all()) >= settings.CONTAINER_MAX_PER_USER:
                raise ValidationError(
                    f"Container limit reached (max {settings.CONTAINER_MAX_PER_USER})"
                )
            
            # Validate resource limits
            cpu = self._validate_cpu_limit(cpu_limit)
            memory = self._validate_memory_limit(memory_limit)
            disk = self._validate_disk_limit(disk_limit)
            
            # Create container in OrbStack
            container_id, container_name = await orbstack_client.create_container(
                project_id=str(project_id),
                user_id=str(user.id),
                cpu_limit=cpu,
                memory_limit=memory,
                disk_limit=disk,
                environment_vars=environment_vars,
                project_name=project.name
            )
            
            # Create database record
            container_repo = ContainerRepository(db)
            container = await container_repo.create(
                project_id=project_id,
                container_id=container_id,
                container_name=container_name,
                status=ContainerStatus.CREATING,
                cpu_limit=cpu,
                memory_limit=memory,
                disk_limit=disk,
                environment_vars=environment_vars or {},
                auto_sleep_minutes=settings.CONTAINER_AUTO_SLEEP_MINUTES,
                auto_stop_hours=settings.CONTAINER_AUTO_STOP_HOURS,
                auto_delete_days=settings.CONTAINER_AUTO_DELETE_DAYS
            )
            
            # Start the container
            external_port = await orbstack_client.start_container(container_id)
            
            # Update container with port and status
            container.external_port = external_port
            container.start()
            await db.commit()
            
            # Clear project cache
            await project_cache.delete(str(project_id))
            
            logger.info(f"Created container {container.id} for project {project_id}")
            return container
            
        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            raise
    
    async def start_container(
        self,
        db: AsyncSession,
        container_id: UUID,
        user: User
    ) -> Container:
        """Start a stopped or sleeping container."""
        try:
            # Get container and verify access
            container = await self._get_container_with_access(db, container_id, user)
            
            if container.is_running:
                return container
            
            # Start in OrbStack
            if container.is_sleeping:
                await orbstack_client.unpause_container(container.container_id)
                container.wake_up()
            else:
                external_port = await orbstack_client.start_container(container.container_id)
                container.external_port = external_port
                container.start()
            
            await db.commit()
            
            # Clear cache
            await self._clear_container_cache(container)
            
            logger.info(f"Started container {container.id}")
            return container
            
        except Exception as e:
            logger.error(f"Failed to start container: {e}")
            raise
    
    async def stop_container(
        self,
        db: AsyncSession,
        container_id: UUID,
        user: User
    ) -> Container:
        """Stop a running container."""
        try:
            # Get container and verify access
            container = await self._get_container_with_access(db, container_id, user)
            
            if container.is_stopped:
                return container
            
            # Stop in OrbStack
            await orbstack_client.stop_container(container.container_id)
            container.stop()
            
            await db.commit()
            
            # Clear cache
            await self._clear_container_cache(container)
            
            logger.info(f"Stopped container {container.id}")
            return container
            
        except Exception as e:
            logger.error(f"Failed to stop container: {e}")
            raise
    
    async def restart_container(
        self,
        db: AsyncSession,
        container_id: UUID,
        user: User
    ) -> Container:
        """Restart a container."""
        try:
            # Get container and verify access
            container = await self._get_container_with_access(db, container_id, user)
            
            # Restart in OrbStack
            await orbstack_client.restart_container(container.container_id)
            container.restart()
            
            await db.commit()
            
            # Clear cache
            await self._clear_container_cache(container)
            
            logger.info(f"Restarted container {container.id}")
            return container
            
        except Exception as e:
            logger.error(f"Failed to restart container: {e}")
            raise
    
    async def delete_container(
        self,
        db: AsyncSession,
        container_id: UUID,
        user: User,
        force: bool = False
    ) -> bool:
        """Delete a container."""
        try:
            # Get container and verify access
            container = await self._get_container_with_access(db, container_id, user)
            
            # Remove from OrbStack
            await orbstack_client.remove_container(container.container_id, force=force)
            
            # Update status
            container.status = ContainerStatus.DELETED
            await db.commit()
            
            # Clear cache
            await self._clear_container_cache(container)
            
            logger.info(f"Deleted container {container.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete container: {e}")
            raise
    
    async def get_container_stats(
        self,
        db: AsyncSession,
        container_id: UUID,
        user: User
    ) -> Dict[str, Any]:
        """Get container resource usage statistics."""
        try:
            # Get container and verify access
            container = await self._get_container_with_access(db, container_id, user)
            
            if not container.is_running:
                return {
                    'status': container.status,
                    'cpu_percent': 0,
                    'memory_usage_mb': 0,
                    'disk_usage_mb': 0,
                    'network_in_mb': 0,
                    'network_out_mb': 0
                }
            
            # Get stats from OrbStack
            stats = await orbstack_client.get_container_stats(container.container_id)
            
            # Update container metrics
            if stats:
                container.update_resource_usage(
                    cpu_percent=stats['cpu_percent'],
                    memory_mb=stats['memory_usage_mb'],
                    disk_mb=0  # TODO: Get actual disk usage
                )
                container.update_network_usage(
                    network_in_mb=stats['network_in_mb'],
                    network_out_mb=stats['network_out_mb']
                )
                await db.commit()
            
            return {
                'status': container.status,
                'uptime_minutes': container.uptime_minutes,
                'resource_usage': container.resource_usage_percentage,
                **stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get container stats: {e}")
            raise
    
    async def get_container_logs(
        self,
        db: AsyncSession,
        container_id: UUID,
        user: User,
        tail: int = 100
    ) -> str:
        """Get container logs."""
        try:
            # Get container and verify access
            container = await self._get_container_with_access(db, container_id, user)
            
            # Get logs from OrbStack
            logs = await orbstack_client.get_container_logs(
                container.container_id,
                tail=tail
            )
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get container logs: {e}")
            raise
    
    async def execute_command(
        self,
        db: AsyncSession,
        container_id: UUID,
        user: User,
        command: List[str],
        workdir: Optional[str] = None
    ) -> Tuple[int, str]:
        """Execute a command in the container."""
        try:
            # Get container and verify access
            container = await self._get_container_with_access(db, container_id, user)
            
            if not container.is_running:
                raise ValidationError("Container is not running")
            
            # Update activity
            container.update_activity()
            await db.commit()
            
            # Execute command
            return await orbstack_client.execute_command(
                container.container_id,
                command,
                workdir=workdir
            )
            
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            raise
    
    async def get_project_container(
        self,
        db: AsyncSession,
        project_id: UUID,
        user: User
    ) -> Optional[Container]:
        """Get container for a project."""
        try:
            # Verify project access
            project = await db.get(Project, project_id)
            if not project or project.owner_id != user.id:
                raise NotFoundError("Project", project_id)
            
            # Get active container
            result = await db.execute(
                select(Container).where(
                    and_(
                        Container.project_id == project_id,
                        Container.status != ContainerStatus.DELETED
                    )
                )
            )
            
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get project container: {e}")
            raise
    
    async def start_project_container(
        self,
        db: AsyncSession,
        project_id: UUID,
        user: User
    ) -> Container:
        """Start or create container for a project."""
        try:
            # Check if container exists
            container = await self.get_project_container(db, project_id, user)
            
            if container:
                # Start existing container
                if not container.is_running:
                    return await self.start_container(db, container.id, user)
                return container
            else:
                # Create new container
                return await self.create_container(db, project_id, user)
                
        except Exception as e:
            logger.error(f"Failed to start project container: {e}")
            raise
    
    async def stop_project_container(
        self,
        db: AsyncSession,
        project_id: UUID,
        user: User
    ) -> bool:
        """Stop container for a project."""
        try:
            container = await self.get_project_container(db, project_id, user)
            
            if container and container.is_running:
                await self.stop_container(db, container.id, user)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to stop project container: {e}")
            raise
    
    async def get_project_container_status(
        self,
        db: AsyncSession,
        project_id: UUID,
        user: User
    ) -> Dict[str, Any]:
        """Get container status for a project."""
        try:
            container = await self.get_project_container(db, project_id, user)
            
            if not container:
                return {
                    "has_container": False,
                    "status": "none",
                    "container_id": None
                }
            
            # Get detailed info if running
            container_info = {}
            if container.is_running:
                container_info = await orbstack_client.get_container_info(container.container_id)
            
            return {
                "has_container": True,
                "status": container.status,
                "container_id": str(container.id),
                "created_at": container.created_at.isoformat(),
                "last_activity": container.last_activity_at.isoformat() if container.last_activity_at else None,
                "uptime_minutes": container.uptime_minutes if container.is_running else 0,
                "external_port": container.external_port,
                "resource_usage": container.resource_usage_percentage,
                "container_info": container_info or {}
            }
            
        except Exception as e:
            logger.error(f"Failed to get project container status: {e}")
            raise
    
    async def execute_project_command(
        self,
        db: AsyncSession,
        project_id: UUID,
        user: User,
        command: List[str],
        workdir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a command in project container."""
        try:
            container = await self.get_project_container(db, project_id, user)
            
            if not container:
                # Auto-create container if it doesn't exist
                container = await self.start_project_container(db, project_id, user)
            
            # Ensure container is running
            if not container.is_running:
                container = await self.start_container(db, container.id, user)
            
            # Execute command
            exit_code, output = await self.execute_command(
                db, container.id, user, command, workdir
            )
            
            return {
                "exit_code": exit_code,
                "output": output,
                "command": command,
                "workdir": workdir,
                "executed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to execute project command: {e}")
            raise
    
    async def execute_encoded_project_command(
        self,
        db: AsyncSession,
        project_id: UUID,
        user: User,
        encoded_command: str
    ) -> Dict[str, Any]:
        """Execute an encoded command in project container."""
        try:
            from modules.backend.utils.command_decoder import CommandDecoder, CommandSanitizer
            
            # Decode the command specification
            spec = CommandDecoder.decode_command(encoded_command)
            
            # Sanitize the command spec
            safe_workdir = CommandSanitizer.get_safe_workdir(spec.workdir)
            safe_environment = CommandSanitizer.sanitize_environment(spec.environment)
            
            container = await self.get_project_container(db, project_id, user)
            
            if not container:
                # Auto-create container if it doesn't exist
                container = await self.start_project_container(db, project_id, user)
            
            # Ensure container is running
            if not container.is_running:
                container = await self.start_container(db, container.id, user)
            
            # Execute command using the decoded specification
            exit_code, output = await self.execute_command(
                db, container.id, user, spec.command, safe_workdir
            )
            
            return {
                "exit_code": exit_code,
                "output": output,
                "command": spec.command,
                "workdir": safe_workdir,
                "environment": safe_environment,
                "executed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to execute encoded project command: {e}")
            raise
    
    async def get_project_container_logs(
        self,
        db: AsyncSession,
        project_id: UUID,
        user: User,
        tail: int = 100
    ) -> str:
        """Get logs from project container."""
        try:
            container = await self.get_project_container(db, project_id, user)
            
            if not container:
                return "No container found for this project"
            
            return await self.get_container_logs(db, container.id, user, tail)
            
        except Exception as e:
            logger.error(f"Failed to get project container logs: {e}")
            raise
    
    async def _get_container_with_access(
        self,
        db: AsyncSession,
        container_id: UUID,
        user: User
    ) -> Container:
        """Get container and verify user access."""
        # Get container with project
        result = await db.execute(
            select(Container)
            .options(selectinload(Container.project))
            .where(Container.id == container_id)
        )
        container = result.scalar_one_or_none()
        
        if not container:
            raise NotFoundError("Container not found")
        
        # Verify access
        if container.project.owner_id != user.id:
            raise ForbiddenError("Access denied")
        
        return container
    
    def _validate_cpu_limit(self, cpu_limit: Optional[float]) -> float:
        """Validate CPU limit."""
        cpu = cpu_limit or settings.CONTAINER_CPU_LIMIT
        if cpu < settings.CONTAINER_MIN_CPU or cpu > settings.CONTAINER_MAX_CPU:
            raise ValidationError(
                f"CPU limit must be between {settings.CONTAINER_MIN_CPU} "
                f"and {settings.CONTAINER_MAX_CPU} cores"
            )
        return cpu
    
    def _validate_memory_limit(self, memory_limit: Optional[int]) -> int:
        """Validate memory limit."""
        memory = memory_limit or settings.CONTAINER_MEMORY_LIMIT
        if memory < settings.CONTAINER_MIN_MEMORY or memory > settings.CONTAINER_MAX_MEMORY:
            raise ValidationError(
                f"Memory limit must be between {settings.CONTAINER_MIN_MEMORY} "
                f"and {settings.CONTAINER_MAX_MEMORY} MB"
            )
        return memory
    
    def _validate_disk_limit(self, disk_limit: Optional[int]) -> int:
        """Validate disk limit."""
        disk = disk_limit or settings.CONTAINER_DISK_LIMIT
        if disk < settings.CONTAINER_MIN_DISK or disk > settings.CONTAINER_MAX_DISK:
            raise ValidationError(
                f"Disk limit must be between {settings.CONTAINER_MIN_DISK} "
                f"and {settings.CONTAINER_MAX_DISK} MB"
            )
        return disk
    
    async def _clear_container_cache(self, container: Container) -> None:
        """Clear container-related cache."""
        await project_cache.delete(str(container.project_id))
    
    async def _cleanup_loop(self) -> None:
        """Background task to cleanup old containers."""
        while True:
            try:
                await asyncio.sleep(settings.CONTAINER_CLEANUP_INTERVAL)
                
                # Cleanup old containers in OrbStack
                removed = await orbstack_client.cleanup_old_containers(
                    days=settings.CONTAINER_AUTO_DELETE_DAYS
                )
                
                if removed > 0:
                    logger.info(f"Cleaned up {removed} old containers")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Container cleanup error: {e}")
    
    async def _health_check_loop(self) -> None:
        """Background task to check container health."""
        while True:
            try:
                await asyncio.sleep(settings.CONTAINER_HEALTH_CHECK_INTERVAL)
                
                # TODO: Implement health checks for running containers
                # - Check each running container
                # - Update health status
                # - Auto-restart unhealthy containers
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")


# Global container service instance
container_service = ContainerService() 