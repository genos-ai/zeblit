"""
Git API endpoints for version control operations.

These endpoints provide Git functionality for projects,
allowing users and agents to manage version control.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query

from modules.backend.core.database import get_db
from modules.backend.core.dependencies import get_current_user
from modules.backend.models.user import User
from modules.backend.services.git import GitService
from modules.backend.schemas.git import (
    GitStatusResponse,
    GitBranchResponse,
    GitBranchCreate,
    GitCommitRequest,
    GitCommitResponse,
    GitMergeRequest,
    GitMergeResponse,
    GitDiffResponse,
    GitLogResponse,
    GitRollbackRequest,
    GitRollbackResponse
)
from modules.backend.config.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["git"])


@router.get("/projects/{project_id}/git/status", response_model=GitStatusResponse)
async def get_git_status(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get Git status for a project.
    
    Shows current branch, modified files, staged files, and untracked files.
    """
    service = GitService(db)
    
    try:
        status = await service.get_status(project_id)
        return GitStatusResponse(**status)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get Git status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Git status"
        )


@router.get("/projects/{project_id}/git/branches", response_model=List[GitBranchResponse])
async def get_branches(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get all branches for a project.
    
    Returns list of branches with commit information.
    """
    service = GitService(db)
    
    try:
        branches = await service.get_branches(project_id)
        return [GitBranchResponse(**branch) for branch in branches]
        
    except Exception as e:
        logger.error(f"Failed to get branches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get branches"
        )


@router.post("/projects/{project_id}/git/branches", response_model=GitBranchResponse)
async def create_branch(
    project_id: UUID,
    branch: GitBranchCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a new branch.
    
    This is typically used by agents to create feature branches.
    """
    service = GitService(db)
    
    try:
        from modules.backend.models.agent import AgentType
        
        # Create agent branch
        branch_name = await service.create_agent_branch(
            project_id=project_id,
            agent_type=AgentType(branch.agent_type),
            task_id=branch.task_id,
            base_branch=branch.base_branch
        )
        
        # Get branch info
        branches = await service.get_branches(project_id)
        branch_info = next((b for b in branches if b["name"] == branch_name), None)
        
        if not branch_info:
            raise ValueError("Failed to find created branch")
        
        return GitBranchResponse(**branch_info)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create branch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create branch"
        )


@router.post("/projects/{project_id}/git/commit", response_model=GitCommitResponse)
async def commit_changes(
    project_id: UUID,
    commit: GitCommitRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Commit changes to the repository.
    
    Can specify specific files or commit all changes.
    """
    service = GitService(db)
    
    try:
        from modules.backend.models.agent import AgentType
        
        agent_type = AgentType(commit.agent_type) if commit.agent_type else None
        
        commit_hash = await service.commit_changes(
            project_id=project_id,
            message=commit.message,
            files=commit.files,
            agent_type=agent_type
        )
        
        return GitCommitResponse(
            commit_hash=commit_hash,
            message=commit.message
        )
        
    except Exception as e:
        logger.error(f"Failed to commit changes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to commit changes"
        )


@router.post("/projects/{project_id}/git/merge", response_model=GitMergeResponse)
async def merge_branch(
    project_id: UUID,
    merge: GitMergeRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Merge one branch into another.
    
    Typically used to merge agent branches back to main.
    """
    service = GitService(db)
    
    try:
        success, result = await service.merge_branch(
            project_id=project_id,
            source_branch=merge.source_branch,
            target_branch=merge.target_branch,
            strategy=merge.strategy
        )
        
        return GitMergeResponse(
            success=success,
            merge_commit=result if success else None,
            conflict_message=result if not success else None
        )
        
    except Exception as e:
        logger.error(f"Failed to merge branch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to merge branch"
        )


@router.get("/projects/{project_id}/git/diff", response_model=GitDiffResponse)
async def get_diff(
    project_id: UUID,
    from_ref: str = Query("HEAD", description="Starting reference"),
    to_ref: Optional[str] = Query(None, description="Ending reference"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get diff between two references.
    
    If to_ref is not provided, shows diff with working directory.
    """
    service = GitService(db)
    
    try:
        diff = await service.create_diff(
            project_id=project_id,
            from_ref=from_ref,
            to_ref=to_ref
        )
        
        return GitDiffResponse(
            from_ref=from_ref,
            to_ref=to_ref or "working directory",
            diff=diff
        )
        
    except Exception as e:
        logger.error(f"Failed to get diff: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get diff"
        )


@router.get("/projects/{project_id}/git/log", response_model=List[GitLogResponse])
async def get_commit_log(
    project_id: UUID,
    branch: Optional[str] = Query(None, description="Specific branch"),
    limit: int = Query(50, description="Maximum commits to return"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get commit log for a project.
    
    Shows commit history with agent information if available.
    """
    service = GitService(db)
    
    try:
        commits = await service.get_commit_log(
            project_id=project_id,
            branch=branch,
            limit=limit
        )
        
        return [GitLogResponse(**commit) for commit in commits]
        
    except Exception as e:
        logger.error(f"Failed to get commit log: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get commit log"
        )


@router.post("/projects/{project_id}/git/rollback", response_model=GitRollbackResponse)
async def rollback_to_commit(
    project_id: UUID,
    rollback: GitRollbackRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Rollback to a specific commit.
    
    Optionally creates a backup branch before rollback.
    """
    service = GitService(db)
    
    try:
        backup_branch = await service.rollback_to_commit(
            project_id=project_id,
            commit_hash=rollback.commit_hash,
            create_backup_branch=rollback.create_backup
        )
        
        return GitRollbackResponse(
            success=True,
            backup_branch=backup_branch,
            rolled_back_to=rollback.commit_hash
        )
        
    except Exception as e:
        logger.error(f"Failed to rollback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rollback"
        )


@router.delete("/projects/{project_id}/git/branches/{branch_name}")
async def delete_branch(
    project_id: UUID,
    branch_name: str,
    force: bool = Query(False, description="Force delete even if not merged"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Delete a branch.
    
    Cannot delete the current branch or default branch.
    """
    service = GitService(db)
    
    try:
        success = await service.delete_branch(
            project_id=project_id,
            branch_name=branch_name,
            force=force
        )
        
        return {"success": success, "message": f"Branch {branch_name} deleted"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to delete branch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete branch"
        ) 