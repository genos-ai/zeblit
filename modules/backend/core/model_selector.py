"""
Intelligent model selection for different types of AI tasks.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-16): Initial model selection utility for tiered approach.
"""

import re
from enum import Enum
from typing import Optional, Dict, Any

from modules.backend.core.config import settings


class ModelTier(Enum):
    """Model complexity tiers."""
    QUICK = "quick"        # Fast responses, simple tasks (Haiku)
    PRIMARY = "primary"    # Default fast responses (Haiku) 
    STANDARD = "standard"  # Development tasks (Sonnet)
    COMPLEX = "complex"    # Deep thinking, complex analysis (Opus)


class ModelSelector:
    """Intelligent model selection based on task complexity."""
    
    # Keywords that indicate complex tasks requiring deep thinking
    COMPLEX_INDICATORS = {
        # Architecture and design
        "architecture", "design pattern", "system design", "technical design",
        "scalability", "performance", "optimization", "refactor", "migrate",
        
        # Analysis and planning
        "analyze", "analysis", "deep dive", "comprehensive", "detailed plan",
        "strategy", "roadmap", "requirements analysis", "research",
        
        # Complex development tasks
        "algorithm", "data structure", "complex logic", "security audit",
        "performance tuning", "debugging complex", "troubleshoot",
        
        # Multi-step workflows
        "workflow", "orchestration", "coordination", "delegation",
        "multi-agent", "collaboration", "pipeline",
        
        # Documentation and specifications
        "specification", "documentation", "technical document", "API design",
        "protocol design", "standard", "best practices"
    }
    
    # Keywords that indicate quick/simple tasks
    QUICK_INDICATORS = {
        # Simple responses
        "hello", "hi", "thanks", "thank you", "ok", "yes", "no",
        "status", "check", "list", "show", "display",
        
        # Quick questions
        "what", "how", "when", "where", "who", "which",
        "quick question", "simple", "basic",
        
        # Status and info requests
        "current", "latest", "recent", "summary", "brief",
        "overview", "info", "information"
    }
    
    # Keywords that definitely need primary model (standard development)
    PRIMARY_INDICATORS = {
        # Code development
        "implement", "code", "function", "class", "method", "feature",
        "bug fix", "enhancement", "development", "programming",
        
        # File operations
        "create file", "edit file", "modify", "update", "change",
        "write", "generate code", "build",
        
        # Testing and validation
        "test", "testing", "unit test", "integration", "validation",
        "review", "check code", "verify"
    }
    
    @classmethod
    def select_model(
        cls, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        force_tier: Optional[ModelTier] = None
    ) -> str:
        """
        Select the appropriate model based on message content and context.
        
        Args:
            message: User message or task description
            context: Additional context that might influence model selection
            force_tier: Force a specific tier (overrides automatic selection)
            
        Returns:
            Model name to use
        """
        if force_tier:
            return cls._get_model_for_tier(force_tier)
        
        # Normalize message for analysis
        message_lower = message.lower()
        
        # Check message length - very long messages often need complex thinking
        if len(message) > 500:
            return cls._get_model_for_tier(ModelTier.COMPLEX)
        
        # Count complexity indicators
        complex_score = sum(1 for keyword in cls.COMPLEX_INDICATORS 
                          if keyword in message_lower)
        
        quick_score = sum(1 for keyword in cls.QUICK_INDICATORS 
                         if keyword in message_lower)
        
        primary_score = sum(1 for keyword in cls.PRIMARY_INDICATORS 
                           if keyword in message_lower)
        
        # Check for @mentions of multiple agents (indicates coordination task)
        agent_mentions = len(re.findall(r'@\w+', message))
        if agent_mentions > 1:
            complex_score += 2
        
        # Check context for complexity indicators
        if context:
            # Multiple files or large context suggests complex task
            if context.get('file_count', 0) > 5:
                complex_score += 1
            
            # Large project context
            if context.get('project_size', 0) > 1000000:  # 1MB+
                complex_score += 1
            
            # Previous conversation was complex
            if context.get('previous_model_tier') == ModelTier.COMPLEX.value:
                complex_score += 1
        
        # Decision logic
        if complex_score >= 2:
            return cls._get_model_for_tier(ModelTier.COMPLEX)
        elif primary_score >= 1:
            # Development tasks get standard model (Sonnet)
            return cls._get_model_for_tier(ModelTier.STANDARD)
        elif quick_score >= 1 and primary_score == 0 and complex_score == 0:
            # Explicitly simple tasks stay on quick
            return cls._get_model_for_tier(ModelTier.QUICK)
        else:
            # Default to primary (fast Haiku) for most interactions
            return cls._get_model_for_tier(ModelTier.PRIMARY)
    
    @classmethod
    def _get_model_for_tier(cls, tier: ModelTier) -> str:
        """Get the model name for a specific tier."""
        if tier == ModelTier.QUICK:
            return settings.QUICK_MODEL
        elif tier == ModelTier.STANDARD:
            return settings.STANDARD_MODEL
        elif tier == ModelTier.COMPLEX:
            return settings.COMPLEX_MODEL
        else:  # PRIMARY (default)
            return settings.PRIMARY_MODEL
    
    @classmethod
    def get_tier_info(cls, model_name: str) -> Dict[str, Any]:
        """Get information about a model tier."""
        if model_name == settings.QUICK_MODEL:
            return {
                "tier": ModelTier.QUICK.value,
                "description": "Fast responses for simple chats",
                "use_case": "Quick questions, status checks, simple interactions"
            }
        elif model_name == settings.STANDARD_MODEL:
            return {
                "tier": ModelTier.STANDARD.value,
                "description": "Standard development tasks",
                "use_case": "Code implementation, file operations, testing"
            }
        elif model_name == settings.COMPLEX_MODEL:
            return {
                "tier": ModelTier.COMPLEX.value,
                "description": "Deep thinking for complex analysis",
                "use_case": "Architecture design, complex planning, multi-agent coordination"
            }
        else:
            return {
                "tier": ModelTier.PRIMARY.value,
                "description": "Default fast responses",
                "use_case": "General chat, quick responses, most interactions"
            }
