"""
Pydantic schemas for Git operations.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class GitStatusResponse(BaseModel):
    """Git status information."""
    current_branch: str = Field(..., description="Current branch name")
    modified_files: List[str] = Field(default_factory=list, description="Modified files")
    staged_files: List[str] = Field(default_factory=list, description="Staged files")
    untracked_files: List[str] = Field(default_factory=list, description="Untracked files")
    clean: bool = Field(..., description="Whether working directory is clean")
    ahead: int = Field(0, description="Commits ahead of remote")
    behind: int = Field(0, description="Commits behind remote")


class GitBranchResponse(BaseModel):
    """Git branch information."""
    name: str = Field(..., description="Branch name")
    commit: str = Field(..., description="Latest commit hash")
    commit_message: str = Field(..., description="Latest commit message")
    commit_date: str = Field(..., description="Latest commit date")
    is_current: bool = Field(False, description="Whether this is the current branch")
    agent_type: Optional[str] = Field(None, description="Agent type if agent branch")
    task_id: Optional[str] = Field(None, description="Task ID if agent branch")


class GitBranchCreate(BaseModel):
    """Request to create a Git branch."""
    agent_type: str = Field(..., description="Type of agent creating the branch")
    task_id: UUID = Field(..., description="Task ID the agent is working on")
    base_branch: str = Field("main", description="Branch to create from")


class GitCommitRequest(BaseModel):
    """Request to commit changes."""
    message: str = Field(..., description="Commit message", min_length=3)
    files: Optional[List[str]] = Field(None, description="Specific files to commit")
    agent_type: Optional[str] = Field(None, description="Agent making the commit")


class GitCommitResponse(BaseModel):
    """Response after committing changes."""
    commit_hash: str = Field(..., description="Commit hash")
    message: str = Field(..., description="Commit message")


class GitMergeRequest(BaseModel):
    """Request to merge branches."""
    source_branch: str = Field(..., description="Branch to merge from")
    target_branch: str = Field("main", description="Branch to merge into")
    strategy: str = Field("recursive", description="Merge strategy")


class GitMergeResponse(BaseModel):
    """Response after merge attempt."""
    success: bool = Field(..., description="Whether merge succeeded")
    merge_commit: Optional[str] = Field(None, description="Merge commit hash if successful")
    conflict_message: Optional[str] = Field(None, description="Conflict details if failed")


class GitDiffResponse(BaseModel):
    """Git diff information."""
    from_ref: str = Field(..., description="Starting reference")
    to_ref: str = Field(..., description="Ending reference")
    diff: str = Field(..., description="Diff output")


class GitLogResponse(BaseModel):
    """Git commit log entry."""
    hash: str = Field(..., description="Commit hash")
    message: str = Field(..., description="Commit message (without agent prefix)")
    full_message: str = Field(..., description="Full commit message")
    author: str = Field(..., description="Commit author")
    email: str = Field(..., description="Author email")
    date: str = Field(..., description="Commit date")
    agent_type: Optional[str] = Field(None, description="Agent type if agent commit")
    files_changed: int = Field(..., description="Number of files changed")


class GitRollbackRequest(BaseModel):
    """Request to rollback to a commit."""
    commit_hash: str = Field(..., description="Commit to rollback to")
    create_backup: bool = Field(True, description="Create backup branch before rollback")


class GitRollbackResponse(BaseModel):
    """Response after rollback."""
    success: bool = Field(..., description="Whether rollback succeeded")
    backup_branch: Optional[str] = Field(None, description="Backup branch name if created")
    rolled_back_to: str = Field(..., description="Commit rolled back to") 