"""
API Key management endpoints.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2025-01-11): Initial API key management endpoints.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from modules.backend.core.database import get_db
from modules.backend.core.dependencies import get_current_user
from modules.backend.models.user import User
from modules.backend.services.api_key import get_api_key_service
from modules.backend.core.exceptions import (
    NotFoundError,
    ValidationError,
    ForbiddenError
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth/keys",
    tags=["api-keys"],
)


@router.post("", response_model=Dict[str, Any])
async def create_api_key(
    name: str = Body(..., description="Descriptive name for the API key"),
    expires_in_days: Optional[int] = Body(None, description="Optional expiration in days"),
    client_type: Optional[str] = Body(None, description="Type of client (cli, telegram, web)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new API key for the authenticated user.
    
    Returns the API key string which should be stored securely by the client.
    The key will only be shown once and cannot be retrieved later.
    """
    try:
        api_key_service = get_api_key_service(db)
        
        # Prepare metadata
        metadata = {}
        if client_type:
            metadata["client_type"] = client_type
        
        # Create API key
        api_key_obj, api_key_string = await api_key_service.create_api_key(
            user_id=current_user.id,
            name=name,
            expires_in_days=expires_in_days,
            metadata=metadata
        )
        
        return {
            "success": True,
            "api_key": api_key_string,  # Only shown once!
            "key_info": {
                "id": str(api_key_obj.id),
                "name": api_key_obj.name,
                "prefix": api_key_obj.prefix,
                "expires_at": api_key_obj.expires_at.isoformat() if api_key_obj.expires_at else None,
                "created_at": api_key_obj.created_at.isoformat(),
                "metadata": api_key_obj.metadata
            },
            "warning": "Store this API key securely. It cannot be retrieved again."
        }
        
    except (ValidationError, ForbiddenError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


@router.get("", response_model=List[Dict[str, Any]])
async def list_api_keys(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all API keys for the authenticated user.
    
    Returns key information without the actual key strings.
    """
    try:
        api_key_service = get_api_key_service(db)
        
        keys = await api_key_service.list_user_api_keys(
            user_id=current_user.id,
            include_inactive=include_inactive
        )
        
        return keys
        
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Revoke (delete) an API key.
    
    Once revoked, the API key will no longer work for authentication.
    """
    try:
        api_key_service = get_api_key_service(db)
        
        success = await api_key_service.revoke_api_key(
            user_id=current_user.id,
            api_key_id=key_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        return {"success": True, "message": "API key revoked successfully"}
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    except Exception as e:
        logger.error(f"Failed to revoke API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )


@router.get("/stats")
async def get_api_key_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get API key usage statistics for the authenticated user.
    """
    try:
        api_key_service = get_api_key_service(db)
        
        stats = await api_key_service.get_api_key_stats(current_user.id)
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get API key stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get API key statistics"
        )


# For testing API key authentication

@router.get("/validate")
async def validate_current_api_key(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate the current API key and return user information.
    
    This endpoint can be used by clients to test their API key.
    """
    return {
        "valid": True,
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "username": current_user.username,
            "is_active": current_user.is_active
        },
        "message": "API key is valid"
    }
