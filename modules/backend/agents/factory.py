"""
Agent factory for creating agent instances.

Provides a centralized way to instantiate agents based on their type.
"""

from typing import Optional, Type, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from modules.backend.agents.base import BaseAgent
from modules.backend.agents.project_manager import ProjectManagerAgent
from modules.backend.agents.product_manager import ProductManagerAgent
from modules.backend.agents.data_analyst import DataAnalystAgent
from modules.backend.agents.engineer import EngineerAgent
from modules.backend.agents.architect import ArchitectAgent
from modules.backend.agents.platform_engineer import PlatformEngineerAgent
from modules.backend.agents.security_engineer import SecurityEngineerAgent

from modules.backend.core.llm import LLMProvider
from modules.backend.models.agent import Agent as AgentModel, AgentType
from modules.backend.config.logging_config import get_logger

logger = get_logger(__name__)


class AgentFactory:
    """Factory for creating agent instances."""
    
    # Agent type to class mapping
    AGENT_CLASSES: Dict[AgentType, Type[BaseAgent]] = {
        AgentType.PROJECT_MANAGER: ProjectManagerAgent,
        AgentType.PRODUCT_MANAGER: ProductManagerAgent,
        AgentType.DATA_ANALYST: DataAnalystAgent,
        AgentType.ENGINEER: EngineerAgent,
        AgentType.ARCHITECT: ArchitectAgent,
        AgentType.PLATFORM_ENGINEER: PlatformEngineerAgent,
        AgentType.SECURITY_ENGINEER: SecurityEngineerAgent,
    }
    
    @classmethod
    def create_agent(
        cls,
        agent_model: AgentModel,
        db_session: AsyncSession,
        llm_provider: Optional[LLMProvider] = None,
        project_id: Optional[UUID] = None,
    ) -> BaseAgent:
        """
        Create an agent instance based on the agent model type.
        
        Args:
            agent_model: Agent database model
            db_session: Database session
            llm_provider: Optional LLM provider instance
            project_id: Optional project context
            
        Returns:
            Agent instance
            
        Raises:
            ValueError: If agent type is not supported
        """
        agent_type = agent_model.type
        
        if agent_type not in cls.AGENT_CLASSES:
            raise ValueError(
                f"Agent type '{agent_type.value}' not supported. "
                f"Available types: {', '.join(t.value for t in cls.AGENT_CLASSES.keys())}"
            )
        
        agent_class = cls.AGENT_CLASSES[agent_type]
        
        logger.info(
            "Creating agent instance",
            agent_id=str(agent_model.id),
            agent_type=agent_type.value,
            agent_class=agent_class.__name__,
            project_id=str(project_id) if project_id else None,
        )
        
        return agent_class(
            agent_model=agent_model,
            db_session=db_session,
            llm_provider=llm_provider,
            project_id=project_id,
        )
    
    @classmethod
    def register_agent(
        cls,
        agent_type: AgentType,
        agent_class: Type[BaseAgent]
    ) -> None:
        """
        Register a new agent type.
        
        Args:
            agent_type: Type of agent
            agent_class: Agent class implementation
        """
        cls.AGENT_CLASSES[agent_type] = agent_class
        logger.info(
            "Registered agent type",
            agent_type=agent_type.value,
            agent_class=agent_class.__name__,
        )
    
    @classmethod
    def get_available_types(cls) -> list[AgentType]:
        """Get list of available agent types."""
        return list(cls.AGENT_CLASSES.keys())
    
    @classmethod
    async def create_agent_by_type(
        cls,
        agent_type: AgentType,
        db_session: AsyncSession,
        llm_provider: Optional[LLMProvider] = None,
        project_id: Optional[UUID] = None,
    ) -> BaseAgent:
        """
        Create an agent by type, loading the model from database.
        
        Args:
            agent_type: Type of agent to create
            db_session: Database session
            llm_provider: Optional LLM provider instance
            project_id: Optional project context
            
        Returns:
            Agent instance
            
        Raises:
            ValueError: If agent not found in database
        """
        from sqlalchemy import select
        
        # Find agent in database
        stmt = select(AgentModel).where(AgentModel.type == agent_type)
        result = await db_session.execute(stmt)
        agent_model = result.scalar_one_or_none()
        
        if not agent_model:
            raise ValueError(f"Agent of type '{agent_type.value}' not found in database")
        
        return cls.create_agent(
            agent_model=agent_model,
            db_session=db_session,
            llm_provider=llm_provider,
            project_id=project_id,
        ) 