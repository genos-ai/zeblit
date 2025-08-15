"""
Models endpoint for OpenAI-compatible API.

Provides information about available AI models.
"""

from typing import List
from fastapi import APIRouter

router = APIRouter()


@router.get("/models", summary="List available AI models")
async def list_models():
    """
    List available AI models (OpenAI-compatible endpoint).
    
    This endpoint provides compatibility with OpenAI API clients
    that expect a /v1/models endpoint.
    
    Returns:
        List of available models
    """
    return {
        "object": "list",
        "data": [
            {
                "id": "claude-3-5-sonnet-20241022",
                "object": "model",
                "created": 1640995200,
                "owned_by": "anthropic",
                "permission": [],
                "root": "claude-3-5-sonnet-20241022",
                "parent": None
            },
            {
                "id": "gpt-4o-mini",
                "object": "model", 
                "created": 1640995200,
                "owned_by": "openai",
                "permission": [],
                "root": "gpt-4o-mini",
                "parent": None
            }
        ]
    }


@router.get("/models/{model_id}", summary="Get model details")
async def get_model(model_id: str):
    """
    Get details about a specific model.
    
    Args:
        model_id: The model identifier
        
    Returns:
        Model details
    """
    # This is a placeholder - in a real implementation,
    # you would look up the actual model details
    return {
        "id": model_id,
        "object": "model",
        "created": 1640995200,
        "owned_by": "zeblit",
        "permission": [],
        "root": model_id,
        "parent": None
    }
