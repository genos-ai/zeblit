"""
File security scanning and validation.

Handles security scanning, secret detection, and file safety validation.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2025-01-11): Extracted from file.py for better organization.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from modules.backend.core.exceptions import ValidationError, ForbiddenError
from modules.backend.models import ProjectFile, User

logger = logging.getLogger(__name__)


class FileSecurityScanner:
    """Security scanning and validation for files."""
    
    # Secret patterns for security scanning
    SECRET_PATTERNS = {
        'api_key': r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9\-_]{20,})["\']?',
        'aws_key': r'(?i)(aws[_-]?access[_-]?key[_-]?id|aws[_-]?secret[_-]?access[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9+/]{20,})["\']?',
        'private_key': r'-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
        'password': r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^"\'\\s]{8,})["\']?',
        'token': r'(?i)(auth[_-]?token|access[_-]?token|bearer)\s*[:=]\s*["\']?([a-zA-Z0-9\-_.]{20,})["\']?',
        'database_url': r'(?i)(database[_-]?url|db[_-]?url)\s*[:=]\s*["\']?([^"\'\\s]+://[^"\'\\s]+)["\']?',
        'connection_string': r'(?i)(connection[_-]?string|conn[_-]?str)\s*[:=]\s*["\']?([^"\'\\s]+)["\']?',
        'secret_key': r'(?i)(secret[_-]?key|secretkey)\s*[:=]\s*["\']?([a-zA-Z0-9\-_]{20,})["\']?',
        'jwt_secret': r'(?i)(jwt[_-]?secret|jwt[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9\-_]{20,})["\']?',
        'encryption_key': r'(?i)(encryption[_-]?key|encrypt[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9\-_+/]{20,})["\']?',
    }
    
    # Dangerous file extensions
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js', '.jar',
        '.sh', '.bash', '.zsh', '.fish', '.ps1', '.psm1', '.psd1',
        '.app', '.dmg', '.pkg', '.deb', '.rpm',
        '.msi', '.msix', '.appx'
    }
    
    # Maximum allowed secrets before blocking
    MAX_SECRETS_THRESHOLD = 5
    
    def __init__(self, db: AsyncSession):
        """Initialize security scanner."""
        self.db = db
    
    async def scan_file_for_secrets(self, file: ProjectFile) -> Dict[str, Any]:
        """
        Scan file content for secrets and security issues.
        
        Args:
            file: File to scan
            
        Returns:
            Dictionary with scan results
        """
        if not file.content:
            return {
                'has_secrets': False,
                'secrets_found': [],
                'risk_level': 'low',
                'recommendations': []
            }
        
        secrets_found = []
        content = file.content
        
        # Scan for each pattern
        for secret_type, pattern in self.SECRET_PATTERNS.items():
            matches = re.finditer(pattern, content)
            for match in matches:
                secrets_found.append({
                    'type': secret_type,
                    'line': content[:match.start()].count('\n') + 1,
                    'column': match.start() - content.rfind('\n', 0, match.start()),
                    'length': len(match.group(0)),
                    'context': self._get_context(content, match.start(), match.end())
                })
        
        # Determine risk level
        risk_level = self._calculate_risk_level(secrets_found, file)
        
        # Generate recommendations
        recommendations = self._generate_security_recommendations(secrets_found, file)
        
        # Log security findings
        if secrets_found:
            logger.warning(
                f"Security scan found {len(secrets_found)} potential secrets in file {file.file_path} "
                f"(project: {file.project_id})"
            )
        
        return {
            'has_secrets': len(secrets_found) > 0,
            'secrets_found': secrets_found,
            'risk_level': risk_level,
            'recommendations': recommendations,
            'scan_timestamp': file.updated_at.isoformat() if file.updated_at else None
        }
    
    def validate_file_upload_security(self, filename: str, content: str, file_size: int) -> None:
        """
        Validate file upload for security concerns.
        
        Args:
            filename: Name of the file
            content: File content
            file_size: Size in bytes
            
        Raises:
            ValidationError: If file fails security validation
            ForbiddenError: If file is blocked for security reasons
        """
        # Check dangerous extensions
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if f'.{file_ext}' in self.DANGEROUS_EXTENSIONS:
            raise ForbiddenError(f"File type not allowed: .{file_ext}")
        
        # Check for executable signatures
        if self._has_executable_signature(content):
            raise ForbiddenError("Executable files are not allowed")
        
        # Quick secret scan for uploads
        secret_count = self._quick_secret_scan(content)
        if secret_count > self.MAX_SECRETS_THRESHOLD:
            raise ValidationError(
                f"File contains too many potential secrets ({secret_count}). "
                "Please review and remove sensitive information before uploading."
            )
        
        # Check for suspicious patterns
        if self._has_suspicious_patterns(content):
            raise ValidationError("File contains suspicious patterns that may pose security risks")
    
    async def validate_user_file_access(self, file: ProjectFile, user: User, write_access: bool = False) -> None:
        """
        Validate user access to a file.
        
        Args:
            file: File to access
            user: User requesting access
            write_access: Whether write access is needed
            
        Raises:
            ForbiddenError: If access is denied
        """
        # Check if user has project access (this would integrate with project permissions)
        # For now, basic check - in real implementation, integrate with proper permission system
        
        # System files should be read-only for non-admin users
        if write_access and self._is_system_file(file.file_path):
            if not self._is_admin_user(user):
                raise ForbiddenError("System files can only be modified by administrators")
        
        # Check file-specific permissions
        if file.file_metadata and file.file_metadata.get('restricted', False):
            if not self._user_has_file_permission(user, file):
                raise ForbiddenError("Access denied to restricted file")
    
    def _get_context(self, content: str, start: int, end: int, context_size: int = 50) -> str:
        """Get context around a match."""
        context_start = max(0, start - context_size)
        context_end = min(len(content), end + context_size)
        context = content[context_start:context_end]
        
        # Mask the actual secret
        secret_length = end - start
        relative_start = start - context_start
        relative_end = end - context_start
        
        masked_context = (
            context[:relative_start] +
            '*' * secret_length +
            context[relative_end:]
        )
        
        return masked_context.strip()
    
    def _calculate_risk_level(self, secrets_found: List[Dict], file: ProjectFile) -> str:
        """Calculate overall risk level."""
        if not secrets_found:
            return 'low'
        
        # Count high-risk secret types
        high_risk_types = {'private_key', 'aws_key', 'database_url', 'connection_string'}
        high_risk_count = sum(1 for secret in secrets_found if secret['type'] in high_risk_types)
        
        # Determine risk level
        if high_risk_count > 0:
            return 'critical'
        elif len(secrets_found) > 3:
            return 'high'
        elif len(secrets_found) > 1:
            return 'medium'
        else:
            return 'low'
    
    def _generate_security_recommendations(self, secrets_found: List[Dict], file: ProjectFile) -> List[str]:
        """Generate security recommendations based on findings."""
        recommendations = []
        
        if not secrets_found:
            recommendations.append("File appears secure - no sensitive data detected")
            return recommendations
        
        secret_types = {secret['type'] for secret in secrets_found}
        
        if 'private_key' in secret_types:
            recommendations.append(
                "Remove private keys from source code. Use secure key management services instead."
            )
        
        if 'api_key' in secret_types or 'token' in secret_types:
            recommendations.append(
                "Remove API keys and tokens from source code. Use environment variables or secure vaults."
            )
        
        if 'password' in secret_types:
            recommendations.append(
                "Remove hardcoded passwords. Use secure authentication methods instead."
            )
        
        if 'database_url' in secret_types or 'connection_string' in secret_types:
            recommendations.append(
                "Remove database connection strings. Use environment configuration instead."
            )
        
        recommendations.append(
            "Consider using a secrets scanner in your CI/CD pipeline to prevent future issues."
        )
        
        return recommendations
    
    def _has_executable_signature(self, content: str) -> bool:
        """Check if content has executable file signatures."""
        if not content:
            return False
        
        # Check for common executable signatures (binary content would be base64 encoded)
        executable_signatures = [
            b'MZ',  # PE/DOS executable
            b'\x7fELF',  # ELF executable
            b'\xfe\xed\xfa',  # Mach-O executable
            b'\xca\xfe\xba\xbe',  # Java class file
        ]
        
        content_bytes = content.encode('utf-8', errors='ignore')[:4]
        return any(sig in content_bytes for sig in executable_signatures)
    
    def _quick_secret_scan(self, content: str) -> int:
        """Quick scan to count potential secrets."""
        if not content:
            return 0
        
        total_matches = 0
        for pattern in self.SECRET_PATTERNS.values():
            matches = re.findall(pattern, content)
            total_matches += len(matches)
        
        return total_matches
    
    def _has_suspicious_patterns(self, content: str) -> bool:
        """Check for suspicious patterns that may indicate malicious content."""
        if not content:
            return False
        
        suspicious_patterns = [
            r'eval\s*\(',  # Code evaluation
            r'exec\s*\(',  # Code execution
            r'subprocess\s*\.',  # Process execution
            r'os\.system\s*\(',  # System command execution
            r'__import__\s*\(',  # Dynamic imports
            r'base64\.decode',  # Base64 decoding (potential obfuscation)
            r'chr\s*\(\s*\d+\s*\)',  # Character encoding (potential obfuscation)
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    def _is_system_file(self, file_path: str) -> bool:
        """Check if file is a system file that requires special permissions."""
        system_paths = [
            'config/',
            'secrets/',
            '.env',
            'private/',
            'keys/',
            'certs/',
            'ssl/',
        ]
        
        return any(file_path.lower().startswith(path) for path in system_paths)
    
    def _is_admin_user(self, user: User) -> bool:
        """Check if user has admin privileges."""
        # Integrate with actual role system
        return hasattr(user, 'role') and user.role == 'admin'
    
    def _user_has_file_permission(self, user: User, file: ProjectFile) -> bool:
        """Check if user has specific file permissions."""
        # Integrate with actual permission system
        # For now, basic check
        return True  # Placeholder - implement actual permission logic
    
    async def generate_security_report(self, project_id: UUID) -> Dict[str, Any]:
        """
        Generate security report for all files in a project.
        
        Args:
            project_id: Project to analyze
            
        Returns:
            Comprehensive security report
        """
        # This would scan all files in the project and generate a summary report
        # Implementation would depend on the specific requirements
        return {
            'project_id': str(project_id),
            'scan_date': None,  # Implement when needed
            'total_files_scanned': 0,
            'files_with_secrets': 0,
            'risk_summary': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            },
            'recommendations': [
                "Implement automated security scanning in CI/CD pipeline",
                "Use environment variables for configuration",
                "Regular security audits and reviews"
            ]
        }
