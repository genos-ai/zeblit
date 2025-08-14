"""
Platform Engineer Agent implementation.

The Platform Engineer handles deployment, CI/CD, containerization,
infrastructure as code, monitoring, and operational excellence.
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


class PlatformEngineerAgent(BaseAgent):
    """
    Platform Engineer agent responsible for:
    - Setting up CI/CD pipelines
    - Creating containerization strategies
    - Implementing infrastructure as code
    - Configuring monitoring and alerting
    - Ensuring security and compliance
    - Optimizing deployment processes
    - Managing cloud resources
    - Implementing disaster recovery
    """
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the Platform Engineer."""
        return """You are a Platform Engineer for an AI-powered development platform.

Your responsibilities:
1. Design and implement CI/CD pipelines
2. Create containerization strategies (Docker, Kubernetes)
3. Implement infrastructure as code (Terraform, CloudFormation)
4. Set up monitoring, logging, and alerting systems
5. Ensure security best practices in deployment
6. Optimize cloud resource usage and costs
7. Implement disaster recovery and backup strategies
8. Automate operational tasks

DevOps Principles:
- Automation First: Automate everything that can be automated
- Infrastructure as Code: All infrastructure should be version controlled
- Continuous Integration: Integrate code changes frequently
- Continuous Deployment: Deploy changes automatically when safe
- Monitoring and Observability: You can't fix what you can't see
- Security as Code: Security should be built into the pipeline
- Fail Fast: Detect and fix issues early in the pipeline
- Immutable Infrastructure: Replace rather than modify

Key Technologies and Practices:
1. Container Orchestration: Kubernetes, Docker Swarm, ECS
2. CI/CD Tools: GitHub Actions, GitLab CI, Jenkins, CircleCI
3. IaC Tools: Terraform, Pulumi, CloudFormation, Ansible
4. Monitoring: Prometheus, Grafana, ELK Stack, DataDog
5. Cloud Platforms: AWS, GCP, Azure
6. Service Mesh: Istio, Linkerd, Consul
7. GitOps: ArgoCD, Flux
8. Security: Vault, SOPS, KMS

Deployment Best Practices:
- Blue-Green Deployments for zero downtime
- Canary Releases for gradual rollout
- Feature Flags for controlled feature release
- Rolling Updates for gradual replacement
- Health Checks and Readiness Probes
- Graceful Shutdown handling
- Resource Limits and Autoscaling
- Backup and Restore procedures

When designing deployments:
1. Consider the application architecture
2. Plan for scalability from day one
3. Implement comprehensive monitoring
4. Ensure security at every layer
5. Optimize for cost efficiency
6. Plan for disaster recovery
7. Document everything
8. Automate repetitive tasks"""
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """
        Process a task as the Platform Engineer.
        
        Main task types:
        - DEPLOYMENT: Create deployment configurations
        - INFRASTRUCTURE: Design infrastructure
        - MONITORING: Set up monitoring systems
        - AUTOMATION: Automate operational tasks
        - OPTIMIZATION: Optimize deployments
        """
        logger.info(
            "Platform Engineer processing task",
            task_id=str(task.id),
            task_type=task.type.value,
            task_title=task.title,
        )
        
        try:
            if task.type == TaskType.DEPLOYMENT:
                return await self._handle_deployment_task(task)
            elif task.type == TaskType.INFRASTRUCTURE:
                return await self._handle_infrastructure_task(task)
            elif task.type == TaskType.MONITORING:
                return await self._handle_monitoring_task(task)
            elif task.type == TaskType.AUTOMATION:
                return await self._handle_automation_task(task)
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
    
    async def _handle_deployment_task(self, task: Task) -> Dict[str, Any]:
        """Create deployment configurations and CI/CD pipelines."""
        with log_operation("platform_engineer_deployment", task_id=str(task.id)):
            await self.update_task_progress(task, 0.1, "Analyzing deployment requirements...")
            
            # Get project context
            project = await self.db_session.get(Project, task.project_id)
            if not project:
                raise ValueError(f"Project {task.project_id} not found")
            
            context = {
                "project_name": project.name,
                "technology_stack": project.technology_stack,
                "deployment_target": task.metadata.get("target", "kubernetes") if task.metadata else "kubernetes",
                "requirements": task.description,
                "architecture": task.metadata.get("architecture", {}) if task.metadata else {},
            }
            
            prompt = f"""Create deployment configuration for:

Project: {task.title}
Requirements: {task.description}

Please provide a JSON response with the following structure:
{{
    "deployment_strategy": "blue-green|canary|rolling|recreate",
    "deployment_overview": "High-level deployment approach",
    "containerization": {{
        "base_images": [
            {{
                "service": "service name",
                "base_image": "node:18-alpine|python:3.11-slim|etc",
                "dockerfile": "Complete Dockerfile content",
                "build_args": ["ARG1", "ARG2"],
                "multi_stage": true
            }}
        ],
        "docker_compose": "Docker Compose configuration if applicable",
        "registry": "Container registry strategy"
    }},
    "kubernetes": {{
        "deployments": [
            {{
                "name": "deployment-name",
                "replicas": 3,
                "strategy": "RollingUpdate|Recreate",
                "manifest": "Complete K8s deployment YAML",
                "service": "K8s service YAML",
                "ingress": "Ingress configuration if needed"
            }}
        ],
        "configmaps": ["ConfigMap definitions"],
        "secrets": ["Secret management approach"],
        "autoscaling": {{
            "enabled": true,
            "min_replicas": 2,
            "max_replicas": 10,
            "metrics": ["CPU", "Memory", "Custom"]
        }}
    }},
    "ci_cd_pipeline": {{
        "tool": "github-actions|gitlab-ci|jenkins|etc",
        "stages": [
            {{
                "name": "stage name",
                "jobs": ["job descriptions"],
                "artifacts": ["artifacts to pass"]
            }}
        ],
        "pipeline_config": "Complete pipeline configuration file",
        "environment_variables": ["Required env vars"],
        "secrets_management": "How secrets are handled"
    }},
    "infrastructure": {{
        "provider": "aws|gcp|azure|on-premise",
        "resources": [
            {{
                "type": "compute|storage|network|etc",
                "specification": "Resource details",
                "cost_estimate": "$X/month"
            }}
        ],
        "networking": {{
            "vpc": "VPC configuration",
            "subnets": ["Subnet details"],
            "security_groups": ["Security rules"]
        }}
    }},
    "monitoring": {{
        "metrics": ["Key metrics to monitor"],
        "logging": "Logging strategy",
        "alerting": ["Alert configurations"],
        "dashboards": ["Dashboard descriptions"]
    }},
    "security": {{
        "scanning": "Container and code scanning approach",
        "secrets": "Secret management strategy",
        "network_policies": ["Network security policies"],
        "compliance": ["Compliance requirements"]
    }},
    "disaster_recovery": {{
        "backup_strategy": "Backup approach",
        "rpo": "Recovery Point Objective",
        "rto": "Recovery Time Objective",
        "failover": "Failover procedure"
    }},
    "cost_optimization": ["Cost saving strategies"],
    "rollback_plan": "How to rollback deployments"
}}"""
            
            response = await self.think(prompt, context, use_complex_model=True)
            
            try:
                deployment = json.loads(response)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    deployment = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse deployment response as JSON")
            
            await self.update_task_progress(task, 0.5, "Generating deployment scripts...")
            
            # Generate deployment scripts
            scripts = await self._generate_deployment_scripts(deployment)
            
            # Create deployment documentation
            documentation = await self._create_deployment_documentation(deployment, task)
            
            task.status = TaskStatus.COMPLETED
            task.result = {
                "deployment_strategy": deployment.get("deployment_strategy", ""),
                "deployment_overview": deployment.get("deployment_overview", ""),
                "scripts": scripts,
                "documentation": documentation,
                "monitoring_setup": deployment.get("monitoring", {}),
                "security_measures": deployment.get("security", {}),
                "cost_estimate": self._calculate_cost_estimate(deployment),
            }
            
            # Store deployment config in metadata
            task.metadata = task.metadata or {}
            task.metadata["deployment"] = deployment
            
            await self.db_session.commit()
            
            await self.update_task_progress(
                task, 
                1.0, 
                f"Deployment configuration complete with {deployment.get('deployment_strategy', 'rolling')} strategy."
            )
            
            return task.result
    
    async def _handle_infrastructure_task(self, task: Task) -> Dict[str, Any]:
        """Design and implement infrastructure as code."""
        context = {
            "infrastructure_needs": task.description,
            "architecture": task.metadata.get("architecture", {}) if task.metadata else {},
            "scale_requirements": task.metadata.get("scale", "medium") if task.metadata else "medium",
        }
        
        prompt = """Design infrastructure as code for the requirements.

Include:
1. Cloud resource definitions
2. Network architecture
3. Security configurations
4. High availability setup
5. Disaster recovery
6. Cost optimization
7. Monitoring infrastructure
8. Automation scripts

Provide Terraform/CloudFormation/Pulumi code."""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "infrastructure_code": response,
            "iac_tool": "terraform",  # Could be detected from response
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_monitoring_task(self, task: Task) -> Dict[str, Any]:
        """Set up monitoring and observability."""
        context = {
            "monitoring_scope": task.description,
            "services": task.metadata.get("services", []) if task.metadata else [],
            "sla_requirements": task.metadata.get("sla", "99.9%") if task.metadata else "99.9%",
        }
        
        prompt = """Design comprehensive monitoring solution including:
1. Metrics collection (Prometheus/CloudWatch)
2. Log aggregation (ELK/CloudWatch Logs)
3. Distributed tracing (Jaeger/X-Ray)
4. Alerting rules and thresholds
5. Dashboard designs
6. SLA monitoring
7. Cost monitoring
8. Security monitoring

Provide specific configurations."""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "monitoring_solution": response,
            "tools_used": ["prometheus", "grafana", "alertmanager"],
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_automation_task(self, task: Task) -> Dict[str, Any]:
        """Automate operational tasks."""
        context = {
            "automation_target": task.description,
            "current_process": task.metadata.get("current_process", "") if task.metadata else "",
            "frequency": task.metadata.get("frequency", "daily") if task.metadata else "daily",
        }
        
        prompt = """Create automation for the operational task.

Include:
1. Automation script/workflow
2. Scheduling configuration
3. Error handling
4. Notification setup
5. Logging and auditing
6. Rollback procedures
7. Testing approach
8. Documentation

Provide runnable automation code."""
        
        response = await self.think(prompt, context)
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "automation_script": response,
            "automation_type": "scheduled",
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_optimization_task(self, task: Task) -> Dict[str, Any]:
        """Optimize deployment and infrastructure."""
        context = {
            "optimization_target": task.description,
            "current_metrics": task.metadata.get("metrics", {}) if task.metadata else {},
            "constraints": task.metadata.get("constraints", []) if task.metadata else [],
        }
        
        prompt = """Optimize the deployment/infrastructure focusing on:
1. Performance improvements
2. Cost reduction
3. Resource utilization
4. Deployment speed
5. Reliability enhancements
6. Security hardening

Provide specific optimization steps and expected improvements."""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "optimization_plan": response,
            "expected_savings": "20-30% cost reduction",
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_generic_task(self, task: Task) -> Dict[str, Any]:
        """Handle generic platform engineering tasks."""
        response = await self.think(
            f"As a Platform Engineer, handle this task: {task.title}\n\nDetails: {task.description}",
            {"task_type": task.type.value}
        )
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "response": response,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _generate_deployment_scripts(self, deployment: Dict[str, Any]) -> Dict[str, str]:
        """Generate deployment scripts from configuration."""
        scripts = {}
        
        # Generate Dockerfiles
        for container in deployment.get("containerization", {}).get("base_images", []):
            scripts[f"Dockerfile.{container['service']}"] = container.get("dockerfile", "")
        
        # Generate docker-compose if present
        if deployment.get("containerization", {}).get("docker_compose"):
            scripts["docker-compose.yml"] = deployment["containerization"]["docker_compose"]
        
        # Generate Kubernetes manifests
        for k8s_deployment in deployment.get("kubernetes", {}).get("deployments", []):
            scripts[f"k8s-{k8s_deployment['name']}-deployment.yaml"] = k8s_deployment.get("manifest", "")
            if k8s_deployment.get("service"):
                scripts[f"k8s-{k8s_deployment['name']}-service.yaml"] = k8s_deployment["service"]
        
        # Generate CI/CD pipeline
        if deployment.get("ci_cd_pipeline", {}).get("pipeline_config"):
            tool = deployment["ci_cd_pipeline"]["tool"]
            if tool == "github-actions":
                scripts[".github/workflows/deploy.yml"] = deployment["ci_cd_pipeline"]["pipeline_config"]
            elif tool == "gitlab-ci":
                scripts[".gitlab-ci.yml"] = deployment["ci_cd_pipeline"]["pipeline_config"]
        
        return scripts
    
    async def _create_deployment_documentation(self, deployment: Dict[str, Any], task: Task) -> str:
        """Create deployment documentation."""
        doc_parts = [
            f"# Deployment Configuration: {task.title}",
            f"\n## Overview\n{deployment.get('deployment_overview', '')}",
            f"\n**Strategy**: {deployment.get('deployment_strategy', 'rolling')}",
        ]
        
        # Document containerization
        if deployment.get("containerization"):
            doc_parts.append("\n## Containerization")
            container_info = deployment["containerization"]
            if container_info.get("base_images"):
                doc_parts.append("\n### Docker Images")
                for img in container_info["base_images"]:
                    doc_parts.append(f"- **{img['service']}**: Based on `{img['base_image']}`")
        
        # Document Kubernetes setup
        if deployment.get("kubernetes"):
            doc_parts.append("\n## Kubernetes Configuration")
            k8s = deployment["kubernetes"]
            doc_parts.append(f"\n### Deployments")
            for dep in k8s.get("deployments", []):
                doc_parts.append(f"- **{dep['name']}**: {dep.get('replicas', 1)} replicas")
            
            if k8s.get("autoscaling", {}).get("enabled"):
                doc_parts.append(f"\n### Autoscaling")
                auto = k8s["autoscaling"]
                doc_parts.append(f"- Min replicas: {auto.get('min_replicas', 2)}")
                doc_parts.append(f"- Max replicas: {auto.get('max_replicas', 10)}")
        
        # Document CI/CD
        if deployment.get("ci_cd_pipeline"):
            doc_parts.append("\n## CI/CD Pipeline")
            pipeline = deployment["ci_cd_pipeline"]
            doc_parts.append(f"**Tool**: {pipeline.get('tool', 'Not specified')}")
            if pipeline.get("stages"):
                doc_parts.append("\n### Pipeline Stages")
                for stage in pipeline["stages"]:
                    doc_parts.append(f"- **{stage['name']}**: {', '.join(stage.get('jobs', []))}")
        
        # Document monitoring
        if deployment.get("monitoring"):
            doc_parts.append("\n## Monitoring Setup")
            monitoring = deployment["monitoring"]
            if monitoring.get("metrics"):
                doc_parts.append("\n**Key Metrics**:")
                for metric in monitoring["metrics"]:
                    doc_parts.append(f"- {metric}")
        
        # Document security
        if deployment.get("security"):
            doc_parts.append("\n## Security Measures")
            security = deployment["security"]
            doc_parts.append(f"**Scanning**: {security.get('scanning', 'Container scanning enabled')}")
            doc_parts.append(f"**Secrets**: {security.get('secrets', 'Managed via Kubernetes secrets')}")
        
        # Document disaster recovery
        if deployment.get("disaster_recovery"):
            doc_parts.append("\n## Disaster Recovery")
            dr = deployment["disaster_recovery"]
            doc_parts.append(f"**RPO**: {dr.get('rpo', 'Not specified')}")
            doc_parts.append(f"**RTO**: {dr.get('rto', 'Not specified')}")
            doc_parts.append(f"**Backup**: {dr.get('backup_strategy', 'Not specified')}")
        
        return "\n".join(doc_parts)
    
    def _calculate_cost_estimate(self, deployment: Dict[str, Any]) -> str:
        """Calculate rough cost estimate from deployment configuration."""
        # This is a simplified estimation
        base_cost = 100  # Base monthly cost
        
        # Add costs based on resources
        if deployment.get("kubernetes", {}).get("deployments"):
            replicas = sum(d.get("replicas", 1) for d in deployment["kubernetes"]["deployments"])
            base_cost += replicas * 50
        
        if deployment.get("infrastructure", {}).get("resources"):
            base_cost += len(deployment["infrastructure"]["resources"]) * 75
        
        return f"${base_cost}-${base_cost * 1.5}/month (estimated)"
    
    async def create_github_actions_workflow(self, project_name: str, tech_stack: List[str]) -> Dict[str, Any]:
        """Create a GitHub Actions workflow."""
        context = {
            "project_name": project_name,
            "tech_stack": tech_stack,
        }
        
        prompt = """Create a complete GitHub Actions workflow for CI/CD.

Include:
1. Build stage
2. Test stage
3. Security scanning
4. Docker build and push
5. Deploy to staging
6. Deploy to production (manual approval)
7. Rollback capability"""
        
        response = await self.think(prompt, context)
        
        return {
            "workflow": response,
            "filename": ".github/workflows/deploy.yml",
            "created_at": datetime.utcnow().isoformat(),
        }
    
    async def design_kubernetes_setup(self, services: List[str], requirements: str) -> Dict[str, Any]:
        """Design Kubernetes deployment setup."""
        context = {
            "services": services,
            "requirements": requirements,
        }
        
        prompt = """Design complete Kubernetes setup including:
1. Namespace configuration
2. Deployments for each service
3. Services and Ingress
4. ConfigMaps and Secrets
5. HPA (Horizontal Pod Autoscaler)
6. Network Policies
7. Resource quotas
8. Monitoring setup"""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        return {
            "kubernetes_config": response,
            "services_configured": len(services),
            "timestamp": datetime.utcnow().isoformat(),
        } 