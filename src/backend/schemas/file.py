"""
File schemas for API requests and responses.

Defines Pydantic models for file operations including CRUD,
versioning, and analysis.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator


class FileCreate(BaseModel):
    """Schema for creating a new file."""
    file_path: str = Field(..., description="Relative file path from project root")
    content: str = Field(..., description="File content")
    encoding: str = Field("utf-8", description="File encoding")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('file_path')
    def validate_file_path(cls, v):
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        if v.startswith('/'):
            v = v[1:]  # Remove leading slash
        return v


class FileUpdate(BaseModel):
    """Schema for updating a file."""
    content: str = Field(..., description="New file content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")


class FileMoveRequest(BaseModel):
    """Schema for moving/renaming a file."""
    old_path: str = Field(..., description="Current file path")
    new_path: str = Field(..., description="New file path")
    
    @field_validator('old_path', 'new_path')
    def validate_paths(cls, v):
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        return v


class FileCopyRequest(BaseModel):
    """Schema for copying a file."""
    source_path: str = Field(..., description="Source file path")
    target_path: str = Field(..., description="Target file path")
    
    @field_validator('source_path', 'target_path')
    def validate_paths(cls, v):
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        return v


class FileResponse(BaseModel):
    """Schema for file response."""
    id: UUID
    project_id: UUID
    file_path: str
    file_name: str
    file_extension: Optional[str]
    file_type: str
    content: Optional[str]
    content_hash: Optional[str]
    file_size: int
    is_binary: bool
    encoding: str
    version: int
    is_latest: bool
    parent_version_id: Optional[UUID]
    
    # Status flags
    is_deleted: bool
    is_ignored: bool
    is_generated: bool
    is_readonly: bool
    is_hidden: bool
    
    # Git information
    git_status: Optional[str]
    git_hash: Optional[str]
    branch_name: Optional[str]
    
    # AI analysis
    ai_analyzed: bool
    language_detected: Optional[str]
    complexity_score: int
    
    # Statistics
    line_count: int
    blank_line_count: int
    comment_line_count: int
    code_line_count: int
    
    # Security
    contains_secrets: bool
    security_issues: List[Dict[str, Any]]
    syntax_errors: List[Dict[str, Any]]
    
    # Metadata
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime]
    last_modified_at: datetime
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    
    # Computed properties
    is_code_file: bool = Field(False)
    is_config_file: bool = Field(False)
    is_documentation: bool = Field(False)
    complexity_level: str = Field("Low")
    has_security_issues: bool = Field(False)
    has_syntax_errors: bool = Field(False)
    needs_attention: bool = Field(False)
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def model_validate(cls, obj: Any):
        """Custom validation to handle computed properties."""
        if hasattr(obj, 'is_code_file'):
            setattr(obj, '_is_code_file', obj.is_code_file)
        if hasattr(obj, 'is_config_file'):
            setattr(obj, '_is_config_file', obj.is_config_file)
        if hasattr(obj, 'is_documentation'):
            setattr(obj, '_is_documentation', obj.is_documentation)
        if hasattr(obj, 'complexity_level'):
            setattr(obj, '_complexity_level', obj.complexity_level)
        if hasattr(obj, 'has_security_issues'):
            setattr(obj, '_has_security_issues', obj.has_security_issues)
        if hasattr(obj, 'has_syntax_errors'):
            setattr(obj, '_has_syntax_errors', obj.has_syntax_errors)
        if hasattr(obj, 'needs_attention'):
            setattr(obj, '_needs_attention', obj.needs_attention)
        
        instance = super().model_validate(obj)
        
        # Set computed properties
        if hasattr(obj, '_is_code_file'):
            instance.is_code_file = obj._is_code_file
        if hasattr(obj, '_is_config_file'):
            instance.is_config_file = obj._is_config_file
        if hasattr(obj, '_is_documentation'):
            instance.is_documentation = obj._is_documentation
        if hasattr(obj, '_complexity_level'):
            instance.complexity_level = obj._complexity_level
        if hasattr(obj, '_has_security_issues'):
            instance.has_security_issues = obj._has_security_issues
        if hasattr(obj, '_has_syntax_errors'):
            instance.has_syntax_errors = obj._has_syntax_errors
        if hasattr(obj, '_needs_attention'):
            instance.needs_attention = obj._needs_attention
        
        return instance


class FileVersionResponse(BaseModel):
    """Schema for file version information."""
    id: UUID
    file_path: str
    version: int
    content_hash: Optional[str]
    file_size: int
    created_at: datetime
    created_by: Optional[UUID]
    parent_version_id: Optional[UUID]
    is_latest: bool
    
    model_config = ConfigDict(from_attributes=True)


class FileTreeNode(BaseModel):
    """Schema for a node in the file tree."""
    type: str = Field(..., description="'file' or 'directory'")
    name: str = Field(..., description="File or directory name")
    size: Optional[int] = Field(None, description="File size in bytes")
    file_type: Optional[str] = Field(None, description="File type")
    id: Optional[UUID] = Field(None, description="File ID (if metadata included)")
    modified: Optional[datetime] = Field(None, description="Last modified time")
    version: Optional[int] = Field(None, description="File version")
    has_errors: Optional[bool] = Field(None, description="Has syntax errors")
    complexity: Optional[int] = Field(None, description="Complexity score")
    children: Optional[Dict[str, 'FileTreeNode']] = Field(None, description="Child nodes for directories")


class FileTreeResponse(BaseModel):
    """Schema for file tree response."""
    tree: Dict[str, Any] = Field(..., description="Hierarchical file tree")


class FileAnalysisResponse(BaseModel):
    """Schema for file analysis response."""
    language: Optional[str] = Field(None, description="Detected programming language")
    complexity: int = Field(0, description="Complexity score (0-100)")
    line_stats: Dict[str, int] = Field(
        default_factory=dict,
        description="Line statistics (total, code, comment, blank)"
    )
    security_issues: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of security issues found"
    )
    syntax_errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of syntax errors found"
    )
    imports: List[str] = Field(default_factory=list, description="List of imports")
    functions: List[str] = Field(default_factory=list, description="List of functions")
    classes: List[str] = Field(default_factory=list, description="List of classes")


class FileSyncResponse(BaseModel):
    """Schema for file sync response."""
    synced: int = Field(..., description="Number of files synced")
    total: int = Field(..., description="Total number of files")
    errors: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of sync errors"
    )


# Update forward references
FileTreeNode.model_rebuild() 