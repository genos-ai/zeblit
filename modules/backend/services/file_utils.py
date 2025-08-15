"""
File utility functions and helpers.

Shared utilities for file operations, validation, and type detection.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2025-01-11): Extracted from file.py for better organization.
"""

import os
import re
import hashlib
import mimetypes
from typing import Dict, Any
from pathlib import Path

from modules.backend.core.exceptions import ValidationError


class FileUtils:
    """Utility functions for file operations."""
    
    # File size limits
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_TEXT_FILE_SIZE = 10 * 1024 * 1024  # 10MB for text files
    
    # Dangerous file patterns
    DANGEROUS_PATTERNS = [
        r'\.\./', r'\.\.\\',  # Directory traversal
        r'^/etc/', r'^/root/', r'^/home/',  # System directories
        r'^\~/',  # Home directory
    ]
    
    @staticmethod
    def validate_file_path(file_path: str) -> None:
        """
        Validate file path for security.
        
        Args:
            file_path: Path to validate
            
        Raises:
            ValidationError: If path is invalid or dangerous
        """
        if not file_path or file_path.strip() == '':
            raise ValidationError("File path cannot be empty")
        
        # Check for dangerous patterns
        for pattern in FileUtils.DANGEROUS_PATTERNS:
            if re.search(pattern, file_path):
                raise ValidationError(f"Invalid file path: {file_path}")
        
        # Normalize and check path
        normalized = os.path.normpath(file_path)
        if normalized.startswith('/') or normalized.startswith('\\'):
            raise ValidationError("Absolute paths not allowed")
        
        if '..' in normalized:
            raise ValidationError("Directory traversal not allowed")
    
    @staticmethod
    def detect_file_type(file_name: str, content: str = "") -> str:
        """
        Detect file type from name and content.
        
        Args:
            file_name: Name of the file
            content: File content (optional)
            
        Returns:
            Detected file type
        """
        # Get extension
        _, ext = os.path.splitext(file_name)
        ext = ext.lower()
        
        # Map extensions to types
        type_map = {
            # Web
            '.html': 'html',
            '.htm': 'html', 
            '.css': 'css',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.vue': 'vue',
            '.svelte': 'svelte',
            
            # Python
            '.py': 'python',
            '.pyx': 'python',
            '.pyi': 'python',
            
            # Data
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.xml': 'xml',
            '.csv': 'csv',
            '.sql': 'sql',
            
            # Config
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'config',
            '.conf': 'config',
            '.env': 'env',
            
            # Documentation
            '.md': 'markdown',
            '.rst': 'restructuredtext',
            '.txt': 'text',
            '.log': 'log',
            
            # Languages
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.h': 'c_header',
            '.hpp': 'cpp_header',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'zsh',
            '.fish': 'fish',
            
            # Images
            '.png': 'image',
            '.jpg': 'image',
            '.jpeg': 'image', 
            '.gif': 'image',
            '.svg': 'image',
            '.webp': 'image',
            
            # Archives
            '.zip': 'archive',
            '.tar': 'archive',
            '.gz': 'archive',
            '.bz2': 'archive',
            '.xz': 'archive',
            
            # Documents
            '.pdf': 'document',
            '.doc': 'document',
            '.docx': 'document',
            '.odt': 'document',
        }
        
        file_type = type_map.get(ext, 'text')
        
        # Content-based detection for ambiguous cases
        if file_type == 'text' and content:
            if content.strip().startswith('<?xml'):
                return 'xml'
            elif content.strip().startswith('<!DOCTYPE html'):
                return 'html'
            elif 'import ' in content and 'def ' in content:
                return 'python'
            elif 'function ' in content or 'const ' in content:
                return 'javascript'
        
        return file_type
    
    @staticmethod
    def calculate_file_hash(content: str, encoding: str = 'utf-8') -> str:
        """
        Calculate SHA256 hash of file content.
        
        Args:
            content: File content
            encoding: Content encoding
            
        Returns:
            Hex hash string
        """
        return hashlib.sha256(content.encode(encoding)).hexdigest()
    
    @staticmethod
    def get_file_info(file_path: str, content: str = "", encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Get comprehensive file information.
        
        Args:
            file_path: Path to the file
            content: File content
            encoding: Content encoding
            
        Returns:
            Dictionary with file information
        """
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1].lower()
        file_type = FileUtils.detect_file_type(file_name, content)
        file_size = len(content.encode(encoding))
        content_hash = FileUtils.calculate_file_hash(content, encoding)
        
        return {
            'file_name': file_name,
            'file_extension': file_extension,
            'file_type': file_type,
            'file_size': file_size,
            'content_hash': content_hash,
            'encoding': encoding,
            'is_binary': FileUtils.is_binary_content(content),
            'mime_type': mimetypes.guess_type(file_name)[0] or 'text/plain'
        }
    
    @staticmethod
    def is_binary_content(content: str) -> bool:
        """
        Check if content appears to be binary.
        
        Args:
            content: Content to check
            
        Returns:
            True if content appears binary
        """
        if not content:
            return False
        
        # Check for null bytes (common in binary files)
        if '\0' in content:
            return True
        
        # Check for high ratio of non-printable characters
        printable_chars = sum(1 for c in content if c.isprintable() or c.isspace())
        if len(content) > 0:
            printable_ratio = printable_chars / len(content)
            return printable_ratio < 0.7
        
        return False
    
    @staticmethod
    def validate_file_size(file_size: int, is_binary: bool = False) -> None:
        """
        Validate file size against limits.
        
        Args:
            file_size: Size in bytes
            is_binary: Whether file is binary
            
        Raises:
            ValidationError: If file is too large
        """
        max_size = FileUtils.MAX_FILE_SIZE if is_binary else FileUtils.MAX_TEXT_FILE_SIZE
        
        if file_size > max_size:
            raise ValidationError(
                f"File too large: {file_size} bytes "
                f"(max: {max_size} bytes for {'binary' if is_binary else 'text'} files)"
            )
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for safe storage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip('. ')
        
        # Ensure not empty
        if not sanitized:
            sanitized = 'untitled'
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255-len(ext)] + ext
        
        return sanitized
    
    @staticmethod
    def get_directory_tree(files: list, base_path: str = "") -> Dict[str, Any]:
        """
        Build directory tree structure from file list.
        
        Args:
            files: List of file objects with file_path attribute
            base_path: Base path to filter by
            
        Returns:
            Nested dictionary representing directory tree
        """
        tree = {}
        
        for file_obj in files:
            if hasattr(file_obj, 'file_path'):
                path = file_obj.file_path
            else:
                path = str(file_obj)
            
            # Skip if not under base path
            if base_path and not path.startswith(base_path):
                continue
            
            # Remove base path
            if base_path:
                relative_path = path[len(base_path):].lstrip('/')
            else:
                relative_path = path
            
            # Split path into components
            parts = relative_path.split('/')
            current = tree
            
            # Build tree structure
            for i, part in enumerate(parts):
                if not part:  # Skip empty parts
                    continue
                
                if part not in current:
                    is_file = i == len(parts) - 1
                    current[part] = {
                        'type': 'file' if is_file else 'directory',
                        'children': {} if not is_file else None,
                        'file': file_obj if is_file else None
                    }
                
                if not current[part]['type'] == 'file':
                    current = current[part]['children']
        
        return tree
