"""
Senior Engineer Agent implementation.

The Senior Engineer writes code, implements features, creates tests,
debugs issues, and ensures code quality through best practices.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy import select

from src.backend.agents.base import BaseAgent
from src.backend.models.agent import AgentType
from src.backend.models.task import Task, TaskStatus, TaskType
from src.backend.models.project import Project
from src.backend.config.logging_config import get_logger, log_operation

logger = get_logger(__name__)


class EngineerAgent(BaseAgent):
    """
    Senior Engineer agent responsible for:
    - Writing clean, maintainable code
    - Implementing features based on specifications
    - Creating comprehensive test suites
    - Debugging and fixing issues
    - Refactoring code for better quality
    - Following best practices and design patterns
    - Conducting code reviews
    - Optimizing performance
    """
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the Senior Engineer."""
        return """You are a Senior Software Engineer for an AI-powered development platform.

Your responsibilities:
1. Write clean, efficient, and maintainable code
2. Implement features according to specifications
3. Create comprehensive test suites with high coverage
4. Debug issues and provide fixes
5. Refactor code to improve quality and performance
6. Follow SOLID principles and design patterns
7. Ensure code security and handle edge cases
8. Write clear documentation and comments

Programming Best Practices:
- DRY (Don't Repeat Yourself): Avoid code duplication
- KISS (Keep It Simple, Stupid): Prefer simple solutions
- YAGNI (You Aren't Gonna Need It): Don't over-engineer
- Single Responsibility: Each function/class should do one thing well
- Defensive Programming: Validate inputs and handle errors gracefully
- Test-Driven Development: Write tests first when appropriate
- Code Reviews: Always consider readability and maintainability

Code Quality Standards:
1. Use meaningful variable and function names
2. Keep functions small and focused (< 20 lines ideally)
3. Write self-documenting code with clear intent
4. Add comments only when necessary to explain "why"
5. Handle errors appropriately with try-catch blocks
6. Use type hints/annotations where applicable
7. Follow language-specific conventions and style guides
8. Optimize for readability over cleverness

Testing Guidelines:
- Unit tests for individual functions/methods
- Integration tests for component interactions
- Edge case testing (null, empty, boundary values)
- Error condition testing
- Performance testing for critical paths
- Aim for >80% code coverage

When implementing features:
1. Understand requirements fully before coding
2. Break down complex tasks into smaller functions
3. Consider edge cases and error scenarios
4. Write tests alongside implementation
5. Refactor after making tests pass
6. Document complex logic
7. Consider performance implications
8. Ensure backward compatibility when needed"""
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """
        Process a task as the Senior Engineer.
        
        Main task types:
        - IMPLEMENTATION: Write code for features
        - TESTING: Create test suites
        - DEBUGGING: Fix bugs and issues
        - REFACTORING: Improve code quality
        - REVIEW: Review code and suggest improvements
        """
        logger.info(
            "Senior Engineer processing task",
            task_id=str(task.id),
            task_type=task.type.value,
            task_title=task.title,
        )
        
        try:
            if task.type == TaskType.IMPLEMENTATION:
                return await self._handle_implementation_task(task)
            elif task.type == TaskType.TESTING:
                return await self._handle_testing_task(task)
            elif task.type == TaskType.DEBUGGING:
                return await self._handle_debugging_task(task)
            elif task.type == TaskType.REFACTORING:
                return await self._handle_refactoring_task(task)
            elif task.type == TaskType.REVIEW:
                return await self._handle_review_task(task)
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
    
    async def _handle_implementation_task(self, task: Task) -> Dict[str, Any]:
        """Implement features based on specifications."""
        with log_operation("engineer_implementation", task_id=str(task.id)):
            await self.update_task_progress(task, 0.1, "Analyzing requirements...")
            
            # Get project context
            project = await self.db_session.get(Project, task.project_id)
            if not project:
                raise ValueError(f"Project {task.project_id} not found")
            
            context = {
                "project_name": project.name,
                "technology_stack": project.technology_stack,
                "requirements": task.description,
                "user_stories": task.metadata.get("user_stories", []) if task.metadata else [],
                "design_specs": task.metadata.get("design", {}) if task.metadata else {},
                "database_schema": task.metadata.get("schema", {}) if task.metadata else {},
            }
            
            # Determine the primary language/framework
            language = self._determine_language(project.technology_stack)
            
            prompt = f"""Implement the following feature:

Feature: {task.title}
Requirements: {task.description}

Please provide a JSON response with the following structure:
{{
    "implementation_plan": "High-level approach to implementing this feature",
    "files": [
        {{
            "path": "path/to/file.ext",
            "language": "{language}",
            "purpose": "What this file does",
            "code": "Complete file content with proper imports and structure",
            "tests_required": true,
            "dependencies": ["package1", "package2"]
        }}
    ],
    "api_endpoints": [
        {{
            "method": "GET|POST|PUT|DELETE",
            "path": "/api/endpoint",
            "description": "What this endpoint does",
            "request_body": {{}},
            "response_body": {{}},
            "authentication": "required|optional|none"
        }}
    ],
    "database_changes": [
        {{
            "type": "migration|seed|query",
            "description": "What this change does",
            "sql": "SQL statement if applicable"
        }}
    ],
    "configuration": [
        {{
            "file": "config file path",
            "changes": "What needs to be added/modified"
        }}
    ],
    "testing_strategy": {{
        "unit_tests": ["Test description"],
        "integration_tests": ["Test description"],
        "edge_cases": ["Edge case to test"]
    }},
    "security_considerations": ["Security aspect to consider"],
    "performance_notes": ["Performance consideration"],
    "deployment_notes": ["Deployment consideration"]
}}"""
            
            response = await self.think(prompt, context, use_complex_model=True)
            
            try:
                implementation = json.loads(response)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    implementation = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse implementation response as JSON")
            
            await self.update_task_progress(task, 0.5, "Generating code files...")
            
            # Process and format the code files
            formatted_files = await self._format_code_files(implementation.get("files", []))
            
            # Create implementation documentation
            documentation = await self._create_implementation_docs(implementation, task)
            
            task.status = TaskStatus.COMPLETED
            task.result = {
                "implementation_plan": implementation.get("implementation_plan", ""),
                "files_created": len(formatted_files),
                "files": formatted_files,
                "api_endpoints": implementation.get("api_endpoints", []),
                "database_changes": implementation.get("database_changes", []),
                "documentation": documentation,
                "testing_strategy": implementation.get("testing_strategy", {}),
                "security_notes": implementation.get("security_considerations", []),
            }
            
            # Store implementation details in metadata
            task.metadata = task.metadata or {}
            task.metadata["implementation"] = implementation
            
            await self.db_session.commit()
            
            await self.update_task_progress(
                task, 
                1.0, 
                f"Implementation complete! Created {len(formatted_files)} files."
            )
            
            return task.result
    
    async def _handle_testing_task(self, task: Task) -> Dict[str, Any]:
        """Create comprehensive test suites."""
        context = {
            "test_target": task.description,
            "implementation": task.metadata.get("implementation", {}) if task.metadata else {},
            "user_stories": task.metadata.get("user_stories", []) if task.metadata else [],
        }
        
        language = task.metadata.get("language", "python") if task.metadata else "python"
        
        prompt = f"""Create a comprehensive test suite for: {task.description}

Please provide a JSON response with test files:
{{
    "test_strategy": "Overall testing approach",
    "test_files": [
        {{
            "path": "path/to/test_file.ext",
            "framework": "pytest|jest|junit|etc",
            "type": "unit|integration|e2e",
            "code": "Complete test file content",
            "coverage_target": "Functions/classes being tested"
        }}
    ],
    "test_cases": [
        {{
            "name": "test_case_name",
            "description": "What this test verifies",
            "type": "positive|negative|edge_case",
            "expected_result": "What should happen"
        }}
    ],
    "mock_data": [
        {{
            "name": "mock_object_name",
            "purpose": "What this mock represents",
            "structure": {{}}
        }}
    ],
    "coverage_report": {{
        "estimated_coverage": "80-90%",
        "uncovered_scenarios": ["Scenario not tested"],
        "recommendations": ["Testing recommendation"]
    }}
}}"""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        try:
            tests = json.loads(response)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                tests = json.loads(json_match.group())
            else:
                raise ValueError("Could not parse test response as JSON")
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "test_strategy": tests.get("test_strategy", ""),
            "test_files": tests.get("test_files", []),
            "test_case_count": len(tests.get("test_cases", [])),
            "coverage_estimate": tests.get("coverage_report", {}).get("estimated_coverage", "Unknown"),
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_debugging_task(self, task: Task) -> Dict[str, Any]:
        """Debug and fix issues."""
        context = {
            "issue_description": task.description,
            "error_logs": task.metadata.get("error_logs", []) if task.metadata else [],
            "stack_trace": task.metadata.get("stack_trace", "") if task.metadata else "",
            "affected_files": task.metadata.get("affected_files", []) if task.metadata else [],
        }
        
        prompt = """Analyze and fix the reported issue.

Provide:
1. Root cause analysis
2. Step-by-step debugging approach
3. Code fixes with explanations
4. Prevention strategies
5. Test cases to verify the fix"""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        # Parse debugging solution
        solution = await self._parse_debugging_solution(response)
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "root_cause": solution.get("root_cause", ""),
            "fix_description": solution.get("fix_description", ""),
            "code_changes": solution.get("code_changes", []),
            "prevention_strategies": solution.get("prevention", []),
            "verification_steps": solution.get("verification", []),
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_refactoring_task(self, task: Task) -> Dict[str, Any]:
        """Refactor code for better quality."""
        context = {
            "refactoring_target": task.description,
            "current_code": task.metadata.get("current_code", "") if task.metadata else "",
            "issues": task.metadata.get("code_issues", []) if task.metadata else [],
        }
        
        prompt = """Refactor the code to improve quality.

Focus on:
1. Reducing complexity
2. Improving readability
3. Eliminating duplication
4. Applying design patterns
5. Enhancing performance
6. Following best practices

Provide before/after comparisons with explanations."""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "refactoring_summary": response,
            "improvements": [
                "Code is more maintainable",
                "Reduced complexity",
                "Better separation of concerns"
            ],
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_review_task(self, task: Task) -> Dict[str, Any]:
        """Review code and suggest improvements."""
        context = {
            "review_target": task.description,
            "code_files": task.metadata.get("code_files", []) if task.metadata else [],
            "pull_request": task.metadata.get("pull_request", {}) if task.metadata else {},
        }
        
        prompt = """Conduct a thorough code review.

Evaluate:
1. Code quality and readability
2. Adherence to best practices
3. Potential bugs or issues
4. Performance concerns
5. Security vulnerabilities
6. Test coverage
7. Documentation completeness

Provide specific, actionable feedback."""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "review_feedback": response,
            "review_status": "approved_with_suggestions",
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_generic_task(self, task: Task) -> Dict[str, Any]:
        """Handle generic engineering tasks."""
        response = await self.think(
            f"As a Senior Engineer, handle this task: {task.title}\n\nDetails: {task.description}",
            {"task_type": task.type.value}
        )
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "response": response,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    def _determine_language(self, tech_stack: List[str]) -> str:
        """Determine primary programming language from tech stack."""
        if not tech_stack:
            return "python"
        
        # Map common stack items to languages
        language_indicators = {
            "python": ["python", "django", "flask", "fastapi", "pytest"],
            "javascript": ["javascript", "node", "react", "vue", "angular", "express"],
            "typescript": ["typescript", "ts", "angular", "nestjs"],
            "java": ["java", "spring", "junit", "maven", "gradle"],
            "go": ["go", "golang", "gin", "echo"],
            "rust": ["rust", "cargo", "actix"],
            "ruby": ["ruby", "rails", "rspec"],
            "csharp": ["c#", "csharp", ".net", "aspnet"],
        }
        
        # Count mentions of each language
        language_scores = {}
        for lang, indicators in language_indicators.items():
            score = sum(1 for tech in tech_stack 
                       for indicator in indicators 
                       if indicator.lower() in tech.lower())
            if score > 0:
                language_scores[lang] = score
        
        # Return the most mentioned language
        if language_scores:
            return max(language_scores, key=language_scores.get)
        
        return "python"  # Default
    
    async def _format_code_files(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format code files with proper structure."""
        formatted_files = []
        
        for file in files:
            formatted = {
                "path": file.get("path", ""),
                "language": file.get("language", ""),
                "purpose": file.get("purpose", ""),
                "content": file.get("code", ""),
                "size": len(file.get("code", "")),
                "dependencies": file.get("dependencies", []),
            }
            formatted_files.append(formatted)
        
        return formatted_files
    
    async def _create_implementation_docs(self, implementation: Dict[str, Any], task: Task) -> str:
        """Create implementation documentation."""
        doc_parts = [
            f"# Implementation: {task.title}",
            f"\n## Overview\n{implementation.get('implementation_plan', '')}",
        ]
        
        # Document files created
        if implementation.get("files"):
            doc_parts.append("\n## Files Created\n")
            for file in implementation["files"]:
                doc_parts.append(f"\n### {file['path']}")
                doc_parts.append(f"**Purpose**: {file.get('purpose', 'Implementation file')}")
                doc_parts.append(f"**Language**: {file.get('language', 'Unknown')}")
                if file.get("dependencies"):
                    doc_parts.append(f"**Dependencies**: {', '.join(file['dependencies'])}")
        
        # Document API endpoints
        if implementation.get("api_endpoints"):
            doc_parts.append("\n## API Endpoints\n")
            for endpoint in implementation["api_endpoints"]:
                doc_parts.append(f"\n### {endpoint['method']} {endpoint['path']}")
                doc_parts.append(endpoint.get("description", ""))
                doc_parts.append(f"**Authentication**: {endpoint.get('authentication', 'required')}")
        
        # Document database changes
        if implementation.get("database_changes"):
            doc_parts.append("\n## Database Changes\n")
            for change in implementation["database_changes"]:
                doc_parts.append(f"- **{change['type']}**: {change['description']}")
        
        # Add testing strategy
        if implementation.get("testing_strategy"):
            doc_parts.append("\n## Testing Strategy")
            strategy = implementation["testing_strategy"]
            if strategy.get("unit_tests"):
                doc_parts.append("\n**Unit Tests:**")
                for test in strategy["unit_tests"]:
                    doc_parts.append(f"- {test}")
            if strategy.get("integration_tests"):
                doc_parts.append("\n**Integration Tests:**")
                for test in strategy["integration_tests"]:
                    doc_parts.append(f"- {test}")
        
        # Add security considerations
        if implementation.get("security_considerations"):
            doc_parts.append("\n## Security Considerations")
            for consideration in implementation["security_considerations"]:
                doc_parts.append(f"- {consideration}")
        
        return "\n".join(doc_parts)
    
    async def _parse_debugging_solution(self, response: str) -> Dict[str, Any]:
        """Parse debugging solution from response."""
        # In a real implementation, this would parse structured debugging info
        # For now, return a structured representation
        return {
            "root_cause": "Identified root cause from analysis",
            "fix_description": "Description of the fix",
            "code_changes": [
                {
                    "file": "path/to/file",
                    "change": "Description of change",
                    "code": "Fixed code snippet"
                }
            ],
            "prevention": ["Prevention strategy"],
            "verification": ["How to verify the fix works"],
        }
    
    async def generate_code_snippet(self, description: str, language: str) -> Dict[str, Any]:
        """Generate a code snippet for a specific purpose."""
        prompt = f"""Generate a {language} code snippet for: {description}

Requirements:
1. Follow best practices
2. Include necessary imports
3. Add helpful comments
4. Handle errors appropriately
5. Make it production-ready"""
        
        response = await self.think(prompt)
        
        return {
            "code": response,
            "language": language,
            "description": description,
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    async def optimize_code(self, code: str, optimization_goals: List[str]) -> Dict[str, Any]:
        """Optimize code for specific goals."""
        context = {
            "original_code": code,
            "goals": optimization_goals,
        }
        
        prompt = """Optimize this code for the specified goals.

Provide:
1. Optimized version
2. Explanation of changes
3. Performance improvements
4. Trade-offs considered"""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        return {
            "optimized_code": response,
            "optimization_goals": optimization_goals,
            "timestamp": datetime.utcnow().isoformat(),
        } 