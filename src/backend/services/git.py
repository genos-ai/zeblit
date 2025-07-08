"""
Git service for version control operations.

This service provides Git functionality for projects, allowing
AI agents to create branches, commit code, and manage version control.
"""

import os
import shutil
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime
from pathlib import Path

import git
from git import Repo, GitCommandError, InvalidGitRepositoryError
from git.exc import NoSuchPathError

from src.backend.models.project import Project
from src.backend.models.agent import AgentType
from src.backend.models.git_branch import GitBranch
from src.backend.repositories.project import ProjectRepository
from src.backend.repositories.git_branch import GitBranchRepository
from src.backend.services.container import ContainerService
from src.backend.config.logging_config import get_logger, log_operation

logger = get_logger(__name__)


class GitService:
    """Service for Git operations on projects."""
    
    def __init__(self, db):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.branch_repo = GitBranchRepository(db)
        self.container_service = ContainerService(db)
    
    def _get_project_path(self, project: Project) -> Path:
        """Get the filesystem path for a project's Git repository."""
        # Projects are stored in containers at /workspace
        container_path = f"/workspace/projects/{project.id}"
        return Path(container_path)
    
    async def initialize_repository(
        self,
        project_id: UUID,
        initial_branch: str = "main"
    ) -> Repo:
        """
        Initialize a Git repository for a project.
        
        Args:
            project_id: Project to initialize Git for
            initial_branch: Name of the initial branch (default: main)
            
        Returns:
            Git repository object
        """
        with log_operation("initialize_git_repository", project_id=str(project_id)):
            try:
                # Get project
                project = await self.project_repo.get(project_id)
                if not project:
                    raise ValueError(f"Project {project_id} not found")
                
                # Get project path
                project_path = self._get_project_path(project)
                
                # Create directory if it doesn't exist
                project_path.mkdir(parents=True, exist_ok=True)
                
                # Initialize Git repository
                repo = Repo.init(project_path)
                
                # Configure Git
                with repo.config_writer() as config:
                    config.set_value("user", "name", "AI Development Platform")
                    config.set_value("user", "email", "ai@dev-platform.com")
                    config.set_value("init", "defaultBranch", initial_branch)
                
                # Create initial commit
                readme_path = project_path / "README.md"
                readme_path.write_text(f"# {project.name}\n\n{project.description or 'AI-powered project'}")
                
                repo.index.add([str(readme_path)])
                repo.index.commit("Initial commit")
                
                # Create main branch in database
                await self.branch_repo.create(
                    project_id=project_id,
                    name=initial_branch,
                    is_default=True,
                    created_by=project.owner_id
                )
                
                logger.info(
                    "Initialized Git repository",
                    project_id=str(project_id),
                    path=str(project_path)
                )
                
                return repo
                
            except Exception as e:
                logger.error(
                    "Failed to initialize Git repository",
                    project_id=str(project_id),
                    error=str(e),
                    exc_info=True
                )
                raise
    
    async def get_repository(self, project_id: UUID) -> Repo:
        """
        Get Git repository for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Git repository object
        """
        try:
            project = await self.project_repo.get(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            project_path = self._get_project_path(project)
            
            try:
                return Repo(project_path)
            except (InvalidGitRepositoryError, NoSuchPathError):
                # Repository doesn't exist, initialize it
                return await self.initialize_repository(project_id)
                
        except Exception as e:
            logger.error(
                "Failed to get repository",
                project_id=str(project_id),
                error=str(e),
                exc_info=True
            )
            raise
    
    async def create_agent_branch(
        self,
        project_id: UUID,
        agent_type: AgentType,
        task_id: UUID,
        base_branch: str = "main"
    ) -> str:
        """
        Create a branch for an agent to work on.
        
        Args:
            project_id: Project ID
            agent_type: Type of agent creating the branch
            task_id: Task ID the agent is working on
            base_branch: Branch to create from
            
        Returns:
            Name of the created branch
        """
        with log_operation("create_agent_branch", project_id=str(project_id), agent_type=agent_type.value):
            try:
                repo = await self.get_repository(project_id)
                
                # Generate branch name
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                branch_name = f"agent/{agent_type.value}/{task_id}/{timestamp}"
                
                # Create branch
                base = repo.heads[base_branch]
                new_branch = repo.create_head(branch_name, base)
                new_branch.checkout()
                
                # Record in database
                project = await self.project_repo.get(project_id)
                await self.branch_repo.create(
                    project_id=project_id,
                    name=branch_name,
                    is_default=False,
                    created_by=project.owner_id,
                    metadata={
                        "agent_type": agent_type.value,
                        "task_id": str(task_id),
                        "base_branch": base_branch
                    }
                )
                
                logger.info(
                    "Created agent branch",
                    project_id=str(project_id),
                    branch_name=branch_name,
                    agent_type=agent_type.value
                )
                
                return branch_name
                
            except Exception as e:
                logger.error(
                    "Failed to create agent branch",
                    project_id=str(project_id),
                    error=str(e),
                    exc_info=True
                )
                raise
    
    async def commit_changes(
        self,
        project_id: UUID,
        message: str,
        files: Optional[List[str]] = None,
        agent_type: Optional[AgentType] = None
    ) -> str:
        """
        Commit changes to the repository.
        
        Args:
            project_id: Project ID
            message: Commit message
            files: Specific files to commit (None = all changes)
            agent_type: Agent making the commit
            
        Returns:
            Commit hash
        """
        with log_operation("commit_changes", project_id=str(project_id)):
            try:
                repo = await self.get_repository(project_id)
                
                # Add agent info to commit message if provided
                if agent_type:
                    message = f"[{agent_type.value}] {message}"
                
                # Stage files
                if files:
                    repo.index.add(files)
                else:
                    # Stage all changes
                    repo.git.add(A=True)
                
                # Check if there are changes to commit
                if not repo.index.diff("HEAD") and not repo.untracked_files:
                    logger.info("No changes to commit", project_id=str(project_id))
                    return repo.head.commit.hexsha
                
                # Commit
                commit = repo.index.commit(message)
                
                logger.info(
                    "Committed changes",
                    project_id=str(project_id),
                    commit_hash=commit.hexsha,
                    message=message
                )
                
                return commit.hexsha
                
            except Exception as e:
                logger.error(
                    "Failed to commit changes",
                    project_id=str(project_id),
                    error=str(e),
                    exc_info=True
                )
                raise
    
    async def get_status(self, project_id: UUID) -> Dict[str, Any]:
        """
        Get Git status for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Git status information
        """
        try:
            repo = await self.get_repository(project_id)
            
            # Get modified files
            modified = [item.a_path for item in repo.index.diff(None)]
            
            # Get staged files
            staged = [item.a_path for item in repo.index.diff("HEAD")]
            
            # Get untracked files
            untracked = repo.untracked_files
            
            status = {
                "current_branch": repo.active_branch.name,
                "modified_files": modified,
                "staged_files": staged,
                "untracked_files": untracked,
                "clean": len(modified) == 0 and len(staged) == 0 and len(untracked) == 0,
                "ahead": 0,  # Will be calculated if remote exists
                "behind": 0
            }
            
            # Check if we're ahead/behind remote
            if repo.remotes:
                try:
                    remote = repo.remotes.origin
                    remote.fetch()
                    
                    # Count commits ahead/behind
                    ahead = list(repo.iter_commits(f"origin/{repo.active_branch.name}..HEAD"))
                    behind = list(repo.iter_commits(f"HEAD..origin/{repo.active_branch.name}"))
                    
                    status["ahead"] = len(ahead)
                    status["behind"] = len(behind)
                except Exception as e:
                    logger.warning(f"Could not fetch remote status: {e}")
            
            return status
            
        except Exception as e:
            logger.error(
                "Failed to get Git status",
                project_id=str(project_id),
                error=str(e),
                exc_info=True
            )
            raise
    
    async def get_branches(self, project_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all branches for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of branch information
        """
        try:
            repo = await self.get_repository(project_id)
            
            branches = []
            for branch in repo.heads:
                branch_info = {
                    "name": branch.name,
                    "commit": branch.commit.hexsha,
                    "commit_message": branch.commit.message.strip(),
                    "commit_date": branch.commit.committed_datetime.isoformat(),
                    "is_current": branch == repo.active_branch
                }
                
                # Check if this is an agent branch
                if branch.name.startswith("agent/"):
                    parts = branch.name.split("/")
                    if len(parts) >= 4:
                        branch_info["agent_type"] = parts[1]
                        branch_info["task_id"] = parts[2]
                
                branches.append(branch_info)
            
            return branches
            
        except Exception as e:
            logger.error(
                "Failed to get branches",
                project_id=str(project_id),
                error=str(e),
                exc_info=True
            )
            raise
    
    async def merge_branch(
        self,
        project_id: UUID,
        source_branch: str,
        target_branch: str = "main",
        strategy: str = "recursive"
    ) -> Tuple[bool, Optional[str]]:
        """
        Merge a branch into another branch.
        
        Args:
            project_id: Project ID
            source_branch: Branch to merge from
            target_branch: Branch to merge into
            strategy: Merge strategy (recursive, ours, theirs)
            
        Returns:
            Tuple of (success, merge_commit_hash or error_message)
        """
        with log_operation("merge_branch", project_id=str(project_id), source=source_branch, target=target_branch):
            try:
                repo = await self.get_repository(project_id)
                
                # Checkout target branch
                repo.heads[target_branch].checkout()
                
                # Try to merge
                try:
                    merge_commit = repo.git.merge(source_branch, strategy=strategy)
                    
                    logger.info(
                        "Successfully merged branch",
                        project_id=str(project_id),
                        source=source_branch,
                        target=target_branch
                    )
                    
                    return True, repo.head.commit.hexsha
                    
                except GitCommandError as e:
                    if "CONFLICT" in str(e):
                        # Merge conflict
                        conflicts = self._get_merge_conflicts(repo)
                        
                        logger.warning(
                            "Merge conflict detected",
                            project_id=str(project_id),
                            conflicts=conflicts
                        )
                        
                        # Abort merge
                        repo.git.merge("--abort")
                        
                        return False, f"Merge conflict in files: {', '.join(conflicts)}"
                    else:
                        raise
                        
            except Exception as e:
                logger.error(
                    "Failed to merge branch",
                    project_id=str(project_id),
                    error=str(e),
                    exc_info=True
                )
                return False, str(e)
    
    def _get_merge_conflicts(self, repo: Repo) -> List[str]:
        """Get list of files with merge conflicts."""
        conflicts = []
        for item in repo.index.entries:
            if item[1] != 0:  # Stage != 0 means conflict
                conflicts.append(item[0])
        return conflicts
    
    async def create_diff(
        self,
        project_id: UUID,
        from_ref: str = "HEAD",
        to_ref: Optional[str] = None
    ) -> str:
        """
        Create a diff between two references.
        
        Args:
            project_id: Project ID
            from_ref: Starting reference (commit, branch, tag)
            to_ref: Ending reference (None = working directory)
            
        Returns:
            Diff as string
        """
        try:
            repo = await self.get_repository(project_id)
            
            if to_ref:
                diff = repo.git.diff(from_ref, to_ref)
            else:
                diff = repo.git.diff(from_ref)
            
            return diff
            
        except Exception as e:
            logger.error(
                "Failed to create diff",
                project_id=str(project_id),
                error=str(e),
                exc_info=True
            )
            raise
    
    async def get_commit_log(
        self,
        project_id: UUID,
        branch: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get commit log for a project.
        
        Args:
            project_id: Project ID
            branch: Specific branch (None = current branch)
            limit: Maximum number of commits to return
            
        Returns:
            List of commit information
        """
        try:
            repo = await self.get_repository(project_id)
            
            # Get commits
            if branch:
                commits = list(repo.iter_commits(branch, max_count=limit))
            else:
                commits = list(repo.iter_commits(max_count=limit))
            
            commit_log = []
            for commit in commits:
                # Extract agent type if present in message
                agent_type = None
                message = commit.message.strip()
                if message.startswith("[") and "]" in message:
                    agent_part = message[1:message.index("]")]
                    if agent_part in [at.value for at in AgentType]:
                        agent_type = agent_part
                        message = message[message.index("]")+1:].strip()
                
                commit_log.append({
                    "hash": commit.hexsha,
                    "message": message,
                    "full_message": commit.message.strip(),
                    "author": commit.author.name,
                    "email": commit.author.email,
                    "date": commit.committed_datetime.isoformat(),
                    "agent_type": agent_type,
                    "files_changed": len(commit.stats.files)
                })
            
            return commit_log
            
        except Exception as e:
            logger.error(
                "Failed to get commit log",
                project_id=str(project_id),
                error=str(e),
                exc_info=True
            )
            raise
    
    async def rollback_to_commit(
        self,
        project_id: UUID,
        commit_hash: str,
        create_backup_branch: bool = True
    ) -> str:
        """
        Rollback to a specific commit.
        
        Args:
            project_id: Project ID
            commit_hash: Commit to rollback to
            create_backup_branch: Whether to create a backup branch
            
        Returns:
            Name of backup branch if created
        """
        with log_operation("rollback_to_commit", project_id=str(project_id), commit=commit_hash):
            try:
                repo = await self.get_repository(project_id)
                
                backup_branch = None
                if create_backup_branch:
                    # Create backup branch
                    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                    backup_branch = f"backup/{repo.active_branch.name}/{timestamp}"
                    repo.create_head(backup_branch)
                    
                    logger.info(
                        "Created backup branch",
                        project_id=str(project_id),
                        branch=backup_branch
                    )
                
                # Reset to commit
                repo.head.reset(commit_hash, index=True, working_tree=True)
                
                logger.info(
                    "Rolled back to commit",
                    project_id=str(project_id),
                    commit=commit_hash
                )
                
                return backup_branch
                
            except Exception as e:
                logger.error(
                    "Failed to rollback",
                    project_id=str(project_id),
                    error=str(e),
                    exc_info=True
                )
                raise
    
    async def delete_branch(
        self,
        project_id: UUID,
        branch_name: str,
        force: bool = False
    ) -> bool:
        """
        Delete a branch.
        
        Args:
            project_id: Project ID
            branch_name: Branch to delete
            force: Force delete even if not merged
            
        Returns:
            Success status
        """
        with log_operation("delete_branch", project_id=str(project_id), branch=branch_name):
            try:
                repo = await self.get_repository(project_id)
                
                # Can't delete current branch
                if repo.active_branch.name == branch_name:
                    raise ValueError("Cannot delete current branch")
                
                # Delete branch
                repo.delete_head(branch_name, force=force)
                
                # Delete from database
                await self.branch_repo.delete_by_name(project_id, branch_name)
                
                logger.info(
                    "Deleted branch",
                    project_id=str(project_id),
                    branch=branch_name
                )
                
                return True
                
            except Exception as e:
                logger.error(
                    "Failed to delete branch",
                    project_id=str(project_id),
                    branch=branch_name,
                    error=str(e),
                    exc_info=True
                )
                raise 