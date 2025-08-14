"""
Architect Agent implementation.

The Architect designs system architectures, selects technologies,
applies design patterns, and ensures scalability and maintainability.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy import select

from modules.backend.agents.base import BaseAgent
from modules.backend.models.agent import AgentType
from modules.backend.models.task import Task, TaskStatus, TaskType
from modules.backend.models.project import Project
from modules.backend.config.logging_config import get_logger, log_operation

logger = get_logger(__name__)


class ArchitectAgent(BaseAgent):
    """
    Architect agent responsible for:
    - Designing system architectures
    - Selecting appropriate technologies
    - Applying design patterns and best practices
    - Ensuring scalability and performance
    - Creating architectural documentation
    - Conducting architecture reviews
    - Planning for future growth
    - Ensuring security and compliance
    """
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the Architect."""
        return """You are a Software Architect for an AI-powered development platform.

Your responsibilities:
1. Design scalable and maintainable system architectures
2. Select appropriate technologies and frameworks
3. Apply architectural patterns and best practices
4. Ensure system performance and reliability
5. Plan for future growth and extensibility
6. Create comprehensive architectural documentation
7. Conduct architecture reviews and provide guidance
8. Ensure security, compliance, and operational excellence

Architectural Principles:
- Separation of Concerns: Divide system into distinct features with minimal overlap
- Single Source of Truth: Each piece of data has one authoritative source
- Don't Repeat Yourself (DRY): Avoid duplication in logic and data
- YAGNI: Don't add functionality until it's needed
- Loose Coupling: Minimize dependencies between components
- High Cohesion: Keep related functionality together
- Design for Failure: Assume things will fail and plan accordingly
- Security by Design: Build security in from the start

Key Architectural Patterns:
1. Microservices vs Monolith (choose based on needs)
2. Event-Driven Architecture for loose coupling
3. API Gateway for unified entry points
4. Service Mesh for microservice communication
5. CQRS for read/write optimization
6. Event Sourcing for audit trails
7. Circuit Breaker for fault tolerance
8. Saga Pattern for distributed transactions

Technology Selection Criteria:
- Maturity and community support
- Performance characteristics
- Scalability potential
- Development velocity
- Operational complexity
- Cost considerations
- Team expertise
- Integration capabilities

When designing architectures:
1. Start with requirements and constraints
2. Identify key quality attributes (performance, security, etc.)
3. Choose appropriate architectural style
4. Design component interactions
5. Plan data flow and storage
6. Consider deployment and operations
7. Document decisions and rationale
8. Plan for monitoring and observability"""
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """
        Process a task as the Architect.
        
        Main task types:
        - DESIGN: Create system architectures
        - ANALYSIS: Analyze architectural requirements
        - REVIEW: Review existing architectures
        - PLANNING: Plan technical roadmaps
        - OPTIMIZATION: Optimize system design
        """
        logger.info(
            "Architect processing task",
            task_id=str(task.id),
            task_type=task.type.value,
            task_title=task.title,
        )
        
        try:
            if task.type == TaskType.DESIGN:
                return await self._handle_design_task(task)
            elif task.type == TaskType.ANALYSIS:
                return await self._handle_analysis_task(task)
            elif task.type == TaskType.REVIEW:
                return await self._handle_review_task(task)
            elif task.type == TaskType.PLANNING:
                return await self._handle_planning_task(task)
            elif task.type == TaskType.OPTIMIZATION:
                return await self._handle_optimization_task(task)
            else:
                return await self._handle_generic_task(task)
                
        except Exception as e:
            logger.error(
                "Error processing task",
                task_id=str(task.id),
                error=str(e),
                exc_info=True,
            )
            
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
    
    async def _handle_design_task(self, task: Task) -> Dict[str, Any]:
        """Design system architecture."""
        with log_operation("architect_design", task_id=str(task.id)):
            await self.update_task_progress(task, 0.1, "Analyzing requirements...")
            
            # Get project context
            project = await self.db_session.get(Project, task.project_id)
            if not project:
                raise ValueError(f"Project {task.project_id} not found")
            
            context = {
                "project_name": project.name,
                "project_description": project.description,
                "requirements": task.description,
                "user_stories": task.metadata.get("user_stories", []) if task.metadata else [],
                "expected_scale": task.metadata.get("expected_scale", "medium") if task.metadata else "medium",
                "constraints": task.metadata.get("constraints", []) if task.metadata else [],
            }
            
            prompt = f"""Design a system architecture for:

Project: {task.title}
Requirements: {task.description}

Please provide a JSON response with the following structure:
{{
    "architecture_overview": "High-level description of the architecture",
    "architectural_style": "microservices|monolith|serverless|hybrid",
    "components": [
        {{
            "name": "Component name",
            "type": "service|database|cache|queue|gateway|etc",
            "purpose": "What this component does",
            "technology": "Specific technology/framework",
            "interfaces": [
                {{
                    "type": "REST|GraphQL|gRPC|WebSocket|etc",
                    "description": "Interface description"
                }}
            ],
            "dependencies": ["Other components it depends on"],
            "scalability": "horizontal|vertical|both",
            "data_storage": "Type of data it stores if applicable"
        }}
    ],
    "data_flow": [
        {{
            "from": "Component A",
            "to": "Component B",
            "type": "sync|async|event",
            "protocol": "HTTP|AMQP|etc",
            "description": "What data flows and why"
        }}
    ],
    "technology_stack": {{
        "frontend": ["Technology choices"],
        "backend": ["Technology choices"],
        "database": ["Technology choices"],
        "infrastructure": ["Technology choices"],
        "devops": ["Technology choices"]
    }},
    "design_patterns": [
        {{
            "pattern": "Pattern name",
            "usage": "Where/how it's used",
            "rationale": "Why this pattern"
        }}
    ],
    "security_architecture": {{
        "authentication": "Method and implementation",
        "authorization": "RBAC|ABAC|etc",
        "encryption": "At rest and in transit approach",
        "api_security": "Security measures",
        "compliance": ["Relevant compliance requirements"]
    }},
    "scalability_plan": {{
        "current_capacity": "Initial capacity",
        "scaling_triggers": ["When to scale"],
        "scaling_strategy": "How to scale",
        "bottlenecks": ["Potential bottlenecks"],
        "mitigation": ["How to address bottlenecks"]
    }},
    "deployment_architecture": {{
        "environment": "cloud|on-premise|hybrid",
        "orchestration": "kubernetes|docker-compose|etc",
        "ci_cd": "Pipeline approach",
        "monitoring": "Monitoring strategy",
        "disaster_recovery": "DR approach"
    }},
    "architectural_decisions": [
        {{
            "decision": "Key decision made",
            "rationale": "Why this decision",
            "alternatives": ["Alternatives considered"],
            "trade_offs": ["Trade-offs accepted"]
        }}
    ],
    "risks": ["Architectural risks"],
    "future_considerations": ["Things to consider for future"]
}}"""
            
            response = await self.think(prompt, context, use_complex_model=True)
            
            try:
                architecture = json.loads(response)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    architecture = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse architecture response as JSON")
            
            await self.update_task_progress(task, 0.5, "Creating architectural diagrams...")
            
            # Generate architecture diagrams (as text descriptions)
            diagrams = await self._generate_architecture_diagrams(architecture)
            
            # Create comprehensive documentation
            documentation = await self._create_architecture_documentation(architecture, task)
            
            task.status = TaskStatus.COMPLETED
            task.result = {
                "architecture_overview": architecture.get("architecture_overview", ""),
                "architectural_style": architecture.get("architectural_style", ""),
                "component_count": len(architecture.get("components", [])),
                "technology_stack": architecture.get("technology_stack", {}),
                "diagrams": diagrams,
                "documentation": documentation,
                "security_measures": architecture.get("security_architecture", {}),
                "scalability_plan": architecture.get("scalability_plan", {}),
            }
            
            # Store architecture in metadata
            task.metadata = task.metadata or {}
            task.metadata["architecture"] = architecture
            
            await self.db_session.commit()
            
            await self.update_task_progress(
                task, 
                1.0, 
                f"Architecture design complete with {len(architecture.get('components', []))} components."
            )
            
            return task.result
    
    async def _handle_analysis_task(self, task: Task) -> Dict[str, Any]:
        """Analyze architectural requirements and constraints."""
        context = {
            "analysis_scope": task.description,
            "current_state": task.metadata.get("current_architecture", {}) if task.metadata else {},
            "requirements": task.metadata.get("requirements", []) if task.metadata else [],
        }
        
        prompt = """Analyze the architectural requirements and provide:
1. Key quality attributes (performance, security, etc.)
2. Architectural constraints and drivers
3. Risk assessment
4. Technology recommendations
5. Architectural style recommendation
6. Integration requirements
7. Compliance and regulatory considerations

Provide specific, actionable insights."""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "analysis": response,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_review_task(self, task: Task) -> Dict[str, Any]:
        """Review existing architecture."""
        context = {
            "review_target": task.description,
            "architecture": task.metadata.get("architecture", {}) if task.metadata else {},
            "concerns": task.metadata.get("concerns", []) if task.metadata else [],
        }
        
        prompt = """Review the architecture and evaluate:
1. Alignment with requirements
2. Scalability and performance
3. Security posture
4. Maintainability
5. Cost efficiency
6. Technical debt
7. Operational complexity
8. Future extensibility

Provide specific recommendations for improvement."""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "review_feedback": response,
            "review_status": "approved_with_recommendations",
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_planning_task(self, task: Task) -> Dict[str, Any]:
        """Create technical roadmaps and migration plans."""
        context = {
            "planning_scope": task.description,
            "current_state": task.metadata.get("current_state", {}) if task.metadata else {},
            "target_state": task.metadata.get("target_state", {}) if task.metadata else {},
            "timeline": task.metadata.get("timeline", "6 months") if task.metadata else "6 months",
        }
        
        prompt = """Create a technical roadmap including:
1. Phased migration/implementation plan
2. Key milestones and deliverables
3. Dependencies and prerequisites
4. Risk mitigation strategies
5. Resource requirements
6. Success metrics
7. Rollback procedures

Provide a realistic, actionable plan."""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "roadmap": response,
            "planning_horizon": context["timeline"],
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_optimization_task(self, task: Task) -> Dict[str, Any]:
        """Optimize system architecture."""
        context = {
            "optimization_target": task.description,
            "current_architecture": task.metadata.get("architecture", {}) if task.metadata else {},
            "performance_issues": task.metadata.get("issues", []) if task.metadata else [],
            "constraints": task.metadata.get("constraints", []) if task.metadata else [],
        }
        
        prompt = """Optimize the architecture focusing on:
1. Performance improvements
2. Cost optimization
3. Scalability enhancements
4. Security hardening
5. Operational efficiency
6. Technical debt reduction

Provide before/after comparisons and implementation steps."""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "optimization_plan": response,
            "expected_improvements": [
                "Better performance",
                "Reduced costs",
                "Improved scalability"
            ],
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_generic_task(self, task: Task) -> Dict[str, Any]:
        """Handle generic architecture tasks."""
        response = await self.think(
            f"As a Software Architect, handle this task: {task.title}\n\nDetails: {task.description}",
            {"task_type": task.type.value}
        )
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "response": response,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _generate_architecture_diagrams(self, architecture: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate architecture diagram descriptions."""
        diagrams = []
        
        # System context diagram
        context_diagram = {
            "type": "system_context",
            "title": "System Context Diagram",
            "description": "High-level view of the system and its external dependencies",
            "elements": []
        }
        
        # Add main system
        context_diagram["elements"].append({
            "type": "system",
            "name": "Main System",
            "description": architecture.get("architecture_overview", "")[:100] + "..."
        })
        
        # Add external systems
        for component in architecture.get("components", []):
            if component.get("type") in ["external_api", "third_party"]:
                context_diagram["elements"].append({
                    "type": "external_system",
                    "name": component["name"],
                    "description": component["purpose"]
                })
        
        diagrams.append(context_diagram)
        
        # Component diagram
        component_diagram = {
            "type": "component",
            "title": "Component Diagram",
            "description": "Internal components and their relationships",
            "components": []
        }
        
        for component in architecture.get("components", []):
            component_diagram["components"].append({
                "name": component["name"],
                "type": component["type"],
                "technology": component.get("technology", ""),
                "interfaces": component.get("interfaces", [])
            })
        
        diagrams.append(component_diagram)
        
        # Data flow diagram
        if architecture.get("data_flow"):
            flow_diagram = {
                "type": "data_flow",
                "title": "Data Flow Diagram",
                "description": "How data moves through the system",
                "flows": architecture["data_flow"]
            }
            diagrams.append(flow_diagram)
        
        return diagrams
    
    async def _create_architecture_documentation(self, architecture: Dict[str, Any], task: Task) -> str:
        """Create comprehensive architecture documentation."""
        doc_parts = [
            f"# System Architecture: {task.title}",
            f"\n## Overview\n{architecture.get('architecture_overview', '')}",
            f"\n**Architectural Style**: {architecture.get('architectural_style', 'Not specified')}",
        ]
        
        # Document components
        if architecture.get("components"):
            doc_parts.append("\n## System Components\n")
            for comp in architecture["components"]:
                doc_parts.append(f"\n### {comp['name']}")
                doc_parts.append(f"**Type**: {comp['type']}")
                doc_parts.append(f"**Purpose**: {comp['purpose']}")
                doc_parts.append(f"**Technology**: {comp.get('technology', 'TBD')}")
                
                if comp.get("interfaces"):
                    doc_parts.append("\n**Interfaces**:")
                    for interface in comp["interfaces"]:
                        doc_parts.append(f"- {interface['type']}: {interface['description']}")
                
                if comp.get("dependencies"):
                    doc_parts.append(f"\n**Dependencies**: {', '.join(comp['dependencies'])}")
        
        # Document technology stack
        if architecture.get("technology_stack"):
            doc_parts.append("\n## Technology Stack")
            stack = architecture["technology_stack"]
            for layer, techs in stack.items():
                if techs:
                    doc_parts.append(f"\n**{layer.title()}**: {', '.join(techs)}")
        
        # Document design patterns
        if architecture.get("design_patterns"):
            doc_parts.append("\n## Design Patterns")
            for pattern in architecture["design_patterns"]:
                doc_parts.append(f"\n**{pattern['pattern']}**")
                doc_parts.append(f"- Usage: {pattern['usage']}")
                doc_parts.append(f"- Rationale: {pattern['rationale']}")
        
        # Document security architecture
        if architecture.get("security_architecture"):
            doc_parts.append("\n## Security Architecture")
            security = architecture["security_architecture"]
            doc_parts.append(f"**Authentication**: {security.get('authentication', 'TBD')}")
            doc_parts.append(f"**Authorization**: {security.get('authorization', 'TBD')}")
            doc_parts.append(f"**Encryption**: {security.get('encryption', 'TBD')}")
            if security.get("compliance"):
                doc_parts.append(f"**Compliance**: {', '.join(security['compliance'])}")
        
        # Document scalability
        if architecture.get("scalability_plan"):
            doc_parts.append("\n## Scalability Plan")
            scale = architecture["scalability_plan"]
            doc_parts.append(f"**Current Capacity**: {scale.get('current_capacity', 'TBD')}")
            doc_parts.append(f"**Scaling Strategy**: {scale.get('scaling_strategy', 'TBD')}")
            if scale.get("bottlenecks"):
                doc_parts.append("\n**Potential Bottlenecks**:")
                for bottleneck in scale["bottlenecks"]:
                    doc_parts.append(f"- {bottleneck}")
        
        # Document architectural decisions
        if architecture.get("architectural_decisions"):
            doc_parts.append("\n## Key Architectural Decisions")
            for decision in architecture["architectural_decisions"]:
                doc_parts.append(f"\n**Decision**: {decision['decision']}")
                doc_parts.append(f"**Rationale**: {decision['rationale']}")
                if decision.get("trade_offs"):
                    doc_parts.append("**Trade-offs**:")
                    for tradeoff in decision["trade_offs"]:
                        doc_parts.append(f"- {tradeoff}")
        
        # Add risks
        if architecture.get("risks"):
            doc_parts.append("\n## Architectural Risks")
            for risk in architecture["risks"]:
                doc_parts.append(f"- {risk}")
        
        return "\n".join(doc_parts)
    
    async def evaluate_technology(self, technology: str, use_case: str) -> Dict[str, Any]:
        """Evaluate a technology for a specific use case."""
        prompt = f"""Evaluate {technology} for {use_case}.

Consider:
1. Strengths and weaknesses
2. Performance characteristics
3. Scalability
4. Learning curve
5. Community and support
6. Cost implications
7. Integration capabilities
8. Alternatives to consider"""
        
        response = await self.think(prompt, use_complex_model=True)
        
        return {
            "evaluation": response,
            "technology": technology,
            "use_case": use_case,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def design_microservice(self, service_name: str, requirements: str) -> Dict[str, Any]:
        """Design a specific microservice."""
        prompt = f"""Design a microservice: {service_name}

Requirements: {requirements}

Include:
1. Service boundaries and responsibilities
2. API design (REST/GraphQL/gRPC)
3. Data model and storage
4. Communication patterns
5. Security considerations
6. Deployment strategy
7. Monitoring and observability"""
        
        response = await self.think(prompt, use_complex_model=True)
        
        return {
            "design": response,
            "service_name": service_name,
            "timestamp": datetime.utcnow().isoformat(),
        } 