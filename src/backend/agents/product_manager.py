"""
Product Manager Agent implementation.

The Product Manager translates user requirements into detailed specifications,
creates user stories, makes UI/UX decisions, and prioritizes features.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.agents.base import BaseAgent
from src.backend.models.agent import AgentType
from src.backend.models.task import Task, TaskStatus, TaskType
from src.backend.models.project import Project
from src.backend.config.logging_config import get_logger, log_operation

logger = get_logger(__name__)


class ProductManagerAgent(BaseAgent):
    """
    Product Manager agent responsible for:
    - Translating business requirements into technical specifications
    - Creating user stories with acceptance criteria
    - Making UI/UX design decisions
    - Defining feature scope and priorities
    - Ensuring user needs are met
    - Creating mockups and wireframes (descriptions)
    - Validating implementations against requirements
    """
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the Product Manager."""
        return """You are a Product Manager for an AI-powered development platform.

Your responsibilities:
1. Translate user requirements into clear, actionable specifications
2. Create detailed user stories with acceptance criteria
3. Make UI/UX design decisions that prioritize user experience
4. Define feature scope and identify MVP vs. nice-to-have features
5. Ensure accessibility and usability standards are met
6. Create wireframe descriptions and user flow diagrams
7. Validate that implementations meet user needs
8. Prioritize features based on user value and technical feasibility

Key Principles:
- User-first thinking: Always consider the end user's perspective
- Clarity: Write specifications that developers can easily understand
- Completeness: Include all necessary details to avoid ambiguity
- Testability: Define clear acceptance criteria for every feature
- Simplicity: Favor simple, intuitive solutions over complex ones
- Accessibility: Ensure features are usable by all users
- Iterative: Plan for MVP first, then enhancements

User Story Format:
"As a [user type], I want to [action] so that [benefit]"

Acceptance Criteria Format:
- Given [context]
- When [action]
- Then [expected result]

When designing UI/UX:
1. Consider the user journey and flow
2. Maintain consistency with existing patterns
3. Prioritize usability over aesthetics
4. Ensure responsive design for different screen sizes
5. Include error states and edge cases
6. Provide clear feedback for user actions"""
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """
        Process a task as the Product Manager.
        
        Main task types:
        - PLANNING: Create user stories and specifications
        - DESIGN: Make UI/UX decisions and create wireframes
        - REVIEW: Validate implementations against requirements
        - ANALYSIS: Analyze user needs and market requirements
        """
        logger.info(
            "Product Manager processing task",
            task_id=str(task.id),
            task_type=task.type.value,
            task_title=task.title,
        )
        
        try:
            if task.type == TaskType.PLANNING:
                return await self._handle_planning_task(task)
            elif task.type == TaskType.DESIGN:
                return await self._handle_design_task(task)
            elif task.type == TaskType.REVIEW:
                return await self._handle_review_task(task)
            elif task.type == TaskType.ANALYSIS:
                return await self._handle_analysis_task(task)
            else:
                # Generic task handling
                return await self._handle_generic_task(task)
                
        except Exception as e:
            logger.error(
                "Error processing task",
                task_id=str(task.id),
                error=str(e),
                exc_info=True,
            )
            
            # Update task status
            task.status = TaskStatus.FAILED
            task.metadata = task.metadata or {}
            task.metadata["error"] = str(e)
            task.metadata["failed_at"] = datetime.utcnow().isoformat()
            await self.db_session.commit()
            
            return {
                "success": False,
                "error": str(e),
                "task_id": str(task.id),
            }
    
    async def _handle_planning_task(self, task: Task) -> Dict[str, Any]:
        """Create user stories and specifications from requirements."""
        with log_operation("product_manager_planning", task_id=str(task.id)):
            # Update progress
            await self.update_task_progress(task, 0.1, "Analyzing requirements...")
            
            # Get project context
            project = await self.db_session.get(Project, task.project_id)
            if not project:
                raise ValueError(f"Project {task.project_id} not found")
            
            # Prepare context
            context = {
                "project_name": project.name,
                "project_description": project.description,
                "target_audience": project.metadata.get("target_audience", "general users") if project.metadata else "general users",
                "existing_features": await self._get_existing_features(project.id),
            }
            
            # Create prompt for user story generation
            prompt = f"""Analyze the following requirement and create detailed user stories:

Requirement: {task.description}

Please provide a JSON response with the following structure:
{{
    "requirement_analysis": "Analysis of the requirement from a user perspective",
    "user_stories": [
        {{
            "id": "US001",
            "title": "Brief story title",
            "story": "As a [user], I want to [action] so that [benefit]",
            "priority": "must-have|should-have|nice-to-have",
            "acceptance_criteria": [
                "Given [context], When [action], Then [result]"
            ],
            "ui_requirements": [
                "UI element or interaction requirement"
            ],
            "technical_notes": "Any technical considerations",
            "estimated_complexity": "simple|medium|complex"
        }}
    ],
    "ui_flow": {{
        "description": "Description of the user flow",
        "steps": [
            "Step 1: User action/screen",
            "Step 2: System response/next screen"
        ]
    }},
    "success_metrics": [
        "How to measure if this feature is successful"
    ],
    "risks_and_considerations": [
        "Potential issues or things to consider"
    ]
}}"""
            
            # Get AI response
            response = await self.think(prompt, context, use_complex_model=True)
            
            # Parse response
            try:
                specs = json.loads(response)
            except json.JSONDecodeError:
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    specs = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse planning response as JSON")
            
            # Update progress
            await self.update_task_progress(task, 0.5, "Creating detailed specifications...")
            
            # Store user stories in task metadata
            task.metadata = task.metadata or {}
            task.metadata["user_stories"] = specs["user_stories"]
            task.metadata["ui_flow"] = specs.get("ui_flow", {})
            task.metadata["success_metrics"] = specs.get("success_metrics", [])
            
            # Create detailed specification document
            specification = await self._create_specification_document(specs, task)
            
            # Update task result
            task.status = TaskStatus.COMPLETED
            task.result = {
                "requirement_analysis": specs.get("requirement_analysis", ""),
                "user_story_count": len(specs["user_stories"]),
                "priorities": {
                    "must_have": len([s for s in specs["user_stories"] if s.get("priority") == "must-have"]),
                    "should_have": len([s for s in specs["user_stories"] if s.get("priority") == "should-have"]),
                    "nice_to_have": len([s for s in specs["user_stories"] if s.get("priority") == "nice-to-have"]),
                },
                "specification": specification,
                "risks": specs.get("risks_and_considerations", []),
            }
            
            await self.db_session.commit()
            
            # Update progress
            await self.update_task_progress(
                task, 
                1.0, 
                f"Created {len(specs['user_stories'])} user stories with specifications."
            )
            
            logger.info(
                "Planning task completed",
                task_id=str(task.id),
                user_stories_created=len(specs["user_stories"]),
            )
            
            return task.result
    
    async def _handle_design_task(self, task: Task) -> Dict[str, Any]:
        """Create UI/UX designs and wireframes."""
        with log_operation("product_manager_design", task_id=str(task.id)):
            # Update progress
            await self.update_task_progress(task, 0.1, "Analyzing design requirements...")
            
            # Prepare context
            context = {
                "feature": task.title,
                "description": task.description,
                "user_stories": task.metadata.get("user_stories", []) if task.metadata else [],
                "design_system": task.metadata.get("design_system", "modern, clean") if task.metadata else "modern, clean",
            }
            
            # Create design prompt
            prompt = f"""Create a detailed UI/UX design for the following feature:

Feature: {task.title}
Description: {task.description}

Please provide a JSON response with the following structure:
{{
    "design_overview": "High-level design approach and principles",
    "wireframes": [
        {{
            "screen_name": "Name of the screen/component",
            "description": "Detailed description of the screen",
            "layout": {{
                "structure": "Description of layout structure",
                "components": [
                    {{
                        "name": "Component name",
                        "type": "button|input|list|card|etc",
                        "purpose": "What this component does",
                        "position": "Where it's located",
                        "interaction": "How users interact with it"
                    }}
                ]
            }},
            "user_actions": [
                "Possible user actions on this screen"
            ],
            "navigation": "How users get to/from this screen"
        }}
    ],
    "interaction_patterns": [
        {{
            "pattern": "Name of the pattern",
            "description": "How it works",
            "when_to_use": "When this pattern applies"
        }}
    ],
    "accessibility": [
        "Accessibility consideration or requirement"
    ],
    "responsive_design": {{
        "mobile": "Mobile-specific considerations",
        "tablet": "Tablet-specific considerations",
        "desktop": "Desktop-specific considerations"
    }},
    "visual_style": {{
        "color_scheme": "Primary and secondary colors",
        "typography": "Font choices and hierarchy",
        "spacing": "Spacing and layout principles",
        "imagery": "Use of images/icons"
    }}
}}"""
            
            # Get AI response
            response = await self.think(prompt, context, use_complex_model=True)
            
            # Parse response
            try:
                design = json.loads(response)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    design = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse design response as JSON")
            
            # Update progress
            await self.update_task_progress(task, 0.7, "Finalizing design documentation...")
            
            # Create design documentation
            design_doc = await self._create_design_document(design, task)
            
            # Update task
            task.status = TaskStatus.COMPLETED
            task.result = {
                "design_overview": design.get("design_overview", ""),
                "wireframe_count": len(design.get("wireframes", [])),
                "design_document": design_doc,
                "accessibility_considerations": design.get("accessibility", []),
                "responsive_design": design.get("responsive_design", {}),
            }
            
            # Store design details in metadata
            task.metadata = task.metadata or {}
            task.metadata["design"] = design
            
            await self.db_session.commit()
            
            # Update progress
            await self.update_task_progress(
                task, 
                1.0, 
                f"Created UI/UX design with {len(design.get('wireframes', []))} wireframes."
            )
            
            return task.result
    
    async def _handle_review_task(self, task: Task) -> Dict[str, Any]:
        """Review implementation against requirements."""
        context = {
            "implementation": task.description,
            "original_requirements": task.metadata.get("requirements", "") if task.metadata else "",
            "user_stories": task.metadata.get("user_stories", []) if task.metadata else [],
        }
        
        prompt = """Review the implementation against the original requirements and user stories.
Evaluate:
1. Does it meet all acceptance criteria?
2. Is the user experience intuitive?
3. Are there any missing features?
4. Are error cases handled properly?
5. Is the implementation accessible?

Provide specific feedback and recommendations."""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "review_feedback": response,
            "reviewed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_analysis_task(self, task: Task) -> Dict[str, Any]:
        """Analyze user needs and market requirements."""
        context = {
            "analysis_scope": task.description,
            "project_type": task.metadata.get("project_type", "web application") if task.metadata else "web application",
        }
        
        prompt = """Conduct a product analysis for the given scope.
Include:
1. User personas and their needs
2. Key features that address these needs
3. Competitive advantages
4. Potential challenges
5. Success metrics
6. MVP vs. future enhancements"""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "analysis": response,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_generic_task(self, task: Task) -> Dict[str, Any]:
        """Handle generic product management tasks."""
        response = await self.think(
            f"As a Product Manager, handle this task: {task.title}\n\nDetails: {task.description}",
            {"task_type": task.type.value}
        )
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "response": response,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _get_existing_features(self, project_id: UUID) -> List[str]:
        """Get list of existing features for context."""
        # In a real implementation, this would query completed user stories
        # For now, return empty list
        return []
    
    async def _create_specification_document(self, specs: Dict[str, Any], task: Task) -> str:
        """Create a formatted specification document."""
        doc_parts = [
            f"# Product Specification: {task.title}",
            f"\n## Requirement Analysis\n{specs.get('requirement_analysis', '')}",
            "\n## User Stories\n"
        ]
        
        # Add user stories
        for story in specs.get("user_stories", []):
            doc_parts.append(f"\n### {story['id']}: {story['title']}")
            doc_parts.append(f"**Priority**: {story.get('priority', 'medium')}")
            doc_parts.append(f"\n{story['story']}")
            
            doc_parts.append("\n**Acceptance Criteria:**")
            for criterion in story.get("acceptance_criteria", []):
                doc_parts.append(f"- {criterion}")
            
            if story.get("ui_requirements"):
                doc_parts.append("\n**UI Requirements:**")
                for req in story["ui_requirements"]:
                    doc_parts.append(f"- {req}")
            
            if story.get("technical_notes"):
                doc_parts.append(f"\n**Technical Notes**: {story['technical_notes']}")
        
        # Add UI flow
        if specs.get("ui_flow"):
            doc_parts.append("\n## User Flow")
            doc_parts.append(specs["ui_flow"].get("description", ""))
            doc_parts.append("\n**Steps:**")
            for step in specs["ui_flow"].get("steps", []):
                doc_parts.append(f"- {step}")
        
        # Add success metrics
        if specs.get("success_metrics"):
            doc_parts.append("\n## Success Metrics")
            for metric in specs["success_metrics"]:
                doc_parts.append(f"- {metric}")
        
        # Add risks
        if specs.get("risks_and_considerations"):
            doc_parts.append("\n## Risks and Considerations")
            for risk in specs["risks_and_considerations"]:
                doc_parts.append(f"- {risk}")
        
        return "\n".join(doc_parts)
    
    async def _create_design_document(self, design: Dict[str, Any], task: Task) -> str:
        """Create a formatted design document."""
        doc_parts = [
            f"# UI/UX Design: {task.title}",
            f"\n## Design Overview\n{design.get('design_overview', '')}",
        ]
        
        # Add wireframes
        if design.get("wireframes"):
            doc_parts.append("\n## Wireframes\n")
            for wireframe in design["wireframes"]:
                doc_parts.append(f"\n### {wireframe['screen_name']}")
                doc_parts.append(wireframe.get("description", ""))
                
                if wireframe.get("layout", {}).get("components"):
                    doc_parts.append("\n**Components:**")
                    for comp in wireframe["layout"]["components"]:
                        doc_parts.append(f"- **{comp['name']}** ({comp['type']}): {comp['purpose']}")
                
                if wireframe.get("user_actions"):
                    doc_parts.append("\n**User Actions:**")
                    for action in wireframe["user_actions"]:
                        doc_parts.append(f"- {action}")
        
        # Add interaction patterns
        if design.get("interaction_patterns"):
            doc_parts.append("\n## Interaction Patterns")
            for pattern in design["interaction_patterns"]:
                doc_parts.append(f"\n**{pattern['pattern']}**")
                doc_parts.append(pattern.get("description", ""))
        
        # Add accessibility
        if design.get("accessibility"):
            doc_parts.append("\n## Accessibility Requirements")
            for req in design["accessibility"]:
                doc_parts.append(f"- {req}")
        
        # Add responsive design
        if design.get("responsive_design"):
            doc_parts.append("\n## Responsive Design")
            rd = design["responsive_design"]
            if rd.get("mobile"):
                doc_parts.append(f"**Mobile**: {rd['mobile']}")
            if rd.get("tablet"):
                doc_parts.append(f"**Tablet**: {rd['tablet']}")
            if rd.get("desktop"):
                doc_parts.append(f"**Desktop**: {rd['desktop']}")
        
        return "\n".join(doc_parts)
    
    async def create_user_persona(self, project_id: UUID, persona_description: str) -> Dict[str, Any]:
        """Create a detailed user persona."""
        prompt = f"""Create a detailed user persona based on: {persona_description}

Include:
1. Demographics (age, occupation, tech-savviness)
2. Goals and motivations
3. Pain points and frustrations
4. Preferred features and functionality
5. Usage patterns and scenarios"""
        
        response = await self.think(prompt, {"project_id": str(project_id)})
        
        return {
            "persona": response,
            "created_at": datetime.utcnow().isoformat(),
        }
    
    async def prioritize_features(self, features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize a list of features using various frameworks."""
        context = {
            "features": features,
            "total_features": len(features),
        }
        
        prompt = """Prioritize these features using the MoSCoW method (Must-have, Should-have, Could-have, Won't-have).
Consider:
1. User value and impact
2. Technical complexity
3. Dependencies
4. Business goals
5. Resource constraints

Return a prioritized list with justifications."""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        # In a real implementation, this would parse and structure the response
        return {
            "prioritized_features": response,
            "method": "MoSCoW",
            "prioritized_at": datetime.utcnow().isoformat(),
        } 