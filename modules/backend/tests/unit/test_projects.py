"""
Unit tests for project management functionality.

Tests project CRUD operations, permissions, and related services.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from modules.backend.models.project import Project
from modules.backend.models.user import User
from modules.backend.services.project import ProjectService
from modules.backend.repositories.project import ProjectRepository
from modules.backend.schemas.project import ProjectCreate, ProjectUpdate
from modules.backend.core.exceptions import NotFoundError, PermissionError


@pytest.mark.unit
@pytest.mark.asyncio
class TestProjectRepository:
    """Test project repository operations."""
    
    async def test_create_project(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test creating a project."""
        repo = ProjectRepository(db_session)
        
        project = await repo.create(
            name="Test Project",
            description="Test description",
            user_id=test_user.id,
            template="blank",
            settings={"language": "python"}
        )
        
        assert project.id is not None
        assert project.name == "Test Project"
        assert project.description == "Test description"
        assert project.user_id == test_user.id
        assert project.template == "blank"
        assert project.settings == {"language": "python"}
        assert project.is_public is False
        assert project.status == "active"
    
    async def test_get_project_by_id(
        self,
        db_session: AsyncSession,
        test_project: Project
    ):
        """Test getting project by ID."""
        repo = ProjectRepository(db_session)
        
        project = await repo.get_by_id(test_project.id)
        
        assert project is not None
        assert project.id == test_project.id
        assert project.name == test_project.name
    
    async def test_get_nonexistent_project(
        self,
        db_session: AsyncSession
    ):
        """Test getting non-existent project."""
        repo = ProjectRepository(db_session)
        
        project = await repo.get_by_id(uuid4())
        
        assert project is None
    
    async def test_get_user_projects(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project
    ):
        """Test getting user's projects."""
        repo = ProjectRepository(db_session)
        
        # Create another project
        await repo.create(
            name="Another Project",
            user_id=test_user.id,
            template="react"
        )
        
        projects = await repo.get_by_user(test_user.id)
        
        assert len(projects) == 2
        assert all(p.user_id == test_user.id for p in projects)
    
    async def test_update_project(
        self,
        db_session: AsyncSession,
        test_project: Project
    ):
        """Test updating a project."""
        repo = ProjectRepository(db_session)
        
        updated = await repo.update(
            test_project.id,
            name="Updated Name",
            description="Updated description"
        )
        
        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
        assert updated.updated_at > test_project.created_at
    
    async def test_delete_project(
        self,
        db_session: AsyncSession,
        test_project: Project
    ):
        """Test deleting a project."""
        repo = ProjectRepository(db_session)
        
        success = await repo.delete(test_project.id)
        assert success is True
        
        # Verify it's gone
        project = await repo.get_by_id(test_project.id)
        assert project is None
    
    async def test_archive_project(
        self,
        db_session: AsyncSession,
        test_project: Project
    ):
        """Test archiving a project."""
        repo = ProjectRepository(db_session)
        
        archived = await repo.archive(test_project.id)
        
        assert archived.status == "archived"
        assert archived.id == test_project.id
    
    async def test_search_projects(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test searching projects."""
        repo = ProjectRepository(db_session)
        
        # Create projects with different names
        await repo.create(name="Python Project", user_id=test_user.id)
        await repo.create(name="JavaScript App", user_id=test_user.id)
        await repo.create(name="Python Script", user_id=test_user.id)
        
        # Search for Python projects
        results = await repo.search(query="Python", user_id=test_user.id)
        
        assert len(results) == 2
        assert all("Python" in p.name for p in results)


@pytest.mark.unit
@pytest.mark.asyncio
class TestProjectService:
    """Test project service operations."""
    
    async def test_create_project_service(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_factory
    ):
        """Test creating project through service."""
        service = ProjectService(db_session)
        project_data = test_factory.create_project_data()
        
        project = await service.create_project(
            ProjectCreate(**project_data),
            test_user.id
        )
        
        assert project.name == project_data["name"]
        assert project.user_id == test_user.id
        assert project.container_id is not None  # Should assign container
    
    async def test_get_project_with_permissions(
        self,
        db_session: AsyncSession,
        test_project: Project,
        test_user: User
    ):
        """Test getting project with permission check."""
        service = ProjectService(db_session)
        
        project = await service.get_project(
            test_project.id,
            test_user.id
        )
        
        assert project.id == test_project.id
    
    async def test_get_project_without_permissions(
        self,
        db_session: AsyncSession,
        test_project: Project,
        admin_user: User
    ):
        """Test getting project without permissions."""
        service = ProjectService(db_session)
        
        # Admin trying to access user's private project
        test_project.is_public = False
        await db_session.commit()
        
        with pytest.raises(PermissionError):
            await service.get_project(
                test_project.id,
                admin_user.id
            )
    
    async def test_get_public_project(
        self,
        db_session: AsyncSession,
        test_project: Project,
        admin_user: User
    ):
        """Test getting public project."""
        service = ProjectService(db_session)
        
        # Make project public
        test_project.is_public = True
        await db_session.commit()
        
        # Anyone can access public project
        project = await service.get_project(
            test_project.id,
            admin_user.id
        )
        
        assert project.id == test_project.id
    
    async def test_update_project_service(
        self,
        db_session: AsyncSession,
        test_project: Project,
        test_user: User
    ):
        """Test updating project through service."""
        service = ProjectService(db_session)
        
        updated = await service.update_project(
            test_project.id,
            ProjectUpdate(
                name="New Name",
                description="New description",
                is_public=True
            ),
            test_user.id
        )
        
        assert updated.name == "New Name"
        assert updated.description == "New description"
        assert updated.is_public is True
    
    async def test_delete_project_service(
        self,
        db_session: AsyncSession,
        test_project: Project,
        test_user: User
    ):
        """Test deleting project through service."""
        service = ProjectService(db_session)
        
        await service.delete_project(
            test_project.id,
            test_user.id
        )
        
        # Verify it's gone
        repo = ProjectRepository(db_session)
        project = await repo.get_by_id(test_project.id)
        assert project is None
    
    async def test_get_project_stats(
        self,
        db_session: AsyncSession,
        test_project: Project,
        test_user: User
    ):
        """Test getting project statistics."""
        service = ProjectService(db_session)
        
        stats = await service.get_project_stats(
            test_project.id,
            test_user.id
        )
        
        assert stats["project_id"] == str(test_project.id)
        assert "file_count" in stats
        assert "total_size" in stats
        assert "last_activity" in stats
        assert "agent_activity" in stats


@pytest.mark.integration
@pytest.mark.asyncio
class TestProjectEndpoints:
    """Test project API endpoints."""
    
    async def test_create_project_endpoint(
        self,
        auth_client: AsyncClient,
        test_factory
    ):
        """Test create project endpoint."""
        project_data = test_factory.create_project_data()
        
        response = await auth_client.post(
            "/api/v1/projects",
            json=project_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == project_data["name"]
        assert "id" in data
        assert "container_id" in data
    
    async def test_list_projects_endpoint(
        self,
        auth_client: AsyncClient,
        test_project: Project
    ):
        """Test list projects endpoint."""
        response = await auth_client.get("/api/v1/projects")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(p["id"] == str(test_project.id) for p in data)
    
    async def test_get_project_endpoint(
        self,
        auth_client: AsyncClient,
        test_project: Project
    ):
        """Test get project endpoint."""
        response = await auth_client.get(
            f"/api/v1/projects/{test_project.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_project.id)
        assert data["name"] == test_project.name
    
    async def test_update_project_endpoint(
        self,
        auth_client: AsyncClient,
        test_project: Project
    ):
        """Test update project endpoint."""
        update_data = {
            "name": "Updated via API",
            "description": "Updated description"
        }
        
        response = await auth_client.put(
            f"/api/v1/projects/{test_project.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
    
    async def test_delete_project_endpoint(
        self,
        auth_client: AsyncClient,
        test_project: Project
    ):
        """Test delete project endpoint."""
        response = await auth_client.delete(
            f"/api/v1/projects/{test_project.id}"
        )
        
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = await auth_client.get(
            f"/api/v1/projects/{test_project.id}"
        )
        assert get_response.status_code == 404
    
    async def test_archive_project_endpoint(
        self,
        auth_client: AsyncClient,
        test_project: Project
    ):
        """Test archive project endpoint."""
        response = await auth_client.post(
            f"/api/v1/projects/{test_project.id}/archive"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "archived"
    
    async def test_project_unauthorized(
        self,
        client: AsyncClient,
        test_project: Project
    ):
        """Test accessing project without authentication."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}"
        )
        
        assert response.status_code == 401
    
    async def test_project_forbidden(
        self,
        admin_client: AsyncClient,
        test_project: Project
    ):
        """Test accessing another user's private project."""
        # Make sure project is private
        test_project.is_public = False
        
        response = await admin_client.get(
            f"/api/v1/projects/{test_project.id}"
        )
        
        assert response.status_code == 403 