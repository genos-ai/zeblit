"""
Data Analyst Agent implementation.

The Data Analyst designs database schemas, creates data models,
optimizes queries, and provides analytics insights.
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


class DataAnalystAgent(BaseAgent):
    """
    Data Analyst agent responsible for:
    - Designing database schemas and data models
    - Creating efficient queries and indexes
    - Implementing data validation rules
    - Designing ETL pipelines
    - Providing analytics and reporting solutions
    - Optimizing database performance
    - Ensuring data security and privacy
    """
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the Data Analyst."""
        return """You are a Data Analyst for an AI-powered development platform.

Your responsibilities:
1. Design efficient database schemas based on requirements
2. Create normalized data models following best practices
3. Write optimized SQL queries and suggest indexes
4. Design data validation and integrity rules
5. Create ETL pipeline specifications
6. Provide analytics and reporting solutions
7. Optimize database performance
8. Ensure data security and privacy compliance

Key Principles:
- Normalization: Follow database normalization principles (up to 3NF typically)
- Performance: Design for query performance from the start
- Scalability: Consider future growth in your designs
- Integrity: Enforce data integrity through constraints
- Security: Implement proper access controls and data protection
- Documentation: Clearly document all schemas and relationships

Database Design Guidelines:
1. Use appropriate data types for each field
2. Define primary keys and foreign key relationships
3. Create indexes for frequently queried columns
4. Consider denormalization only when justified by performance needs
5. Plan for data archival and retention policies
6. Include audit fields (created_at, updated_at, created_by, etc.)

When designing schemas, provide:
1. Table definitions with columns and data types
2. Primary and foreign key constraints
3. Indexes for performance
4. Sample queries for common operations
5. Data validation rules
6. Security considerations"""
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """
        Process a task as the Data Analyst.
        
        Main task types:
        - DESIGN: Create database schemas and data models
        - ANALYSIS: Analyze data requirements and patterns
        - OPTIMIZATION: Optimize queries and performance
        - IMPLEMENTATION: Create SQL scripts and migrations
        """
        logger.info(
            "Data Analyst processing task",
            task_id=str(task.id),
            task_type=task.type.value,
            task_title=task.title,
        )
        
        try:
            if task.type == TaskType.DESIGN:
                return await self._handle_design_task(task)
            elif task.type == TaskType.ANALYSIS:
                return await self._handle_analysis_task(task)
            elif task.type == TaskType.OPTIMIZATION:
                return await self._handle_optimization_task(task)
            elif task.type == TaskType.IMPLEMENTATION:
                return await self._handle_implementation_task(task)
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
        """Design database schemas and data models."""
        with log_operation("data_analyst_design", task_id=str(task.id)):
            await self.update_task_progress(task, 0.1, "Analyzing data requirements...")
            
            # Get project context
            project = await self.db_session.get(Project, task.project_id)
            if not project:
                raise ValueError(f"Project {task.project_id} not found")
            
            context = {
                "project_name": project.name,
                "project_description": project.description,
                "requirements": task.description,
                "user_stories": task.metadata.get("user_stories", []) if task.metadata else [],
            }
            
            prompt = f"""Design a database schema for the following requirements:

Requirements: {task.description}

Please provide a JSON response with the following structure:
{{
    "schema_overview": "High-level description of the database design",
    "tables": [
        {{
            "name": "table_name",
            "description": "What this table stores",
            "columns": [
                {{
                    "name": "column_name",
                    "type": "VARCHAR(255)|INTEGER|TIMESTAMP|etc",
                    "nullable": false,
                    "primary_key": false,
                    "foreign_key": null,
                    "unique": false,
                    "default": null,
                    "description": "What this column represents"
                }}
            ],
            "indexes": [
                {{
                    "name": "index_name",
                    "columns": ["column1", "column2"],
                    "unique": false,
                    "description": "Why this index is needed"
                }}
            ],
            "constraints": [
                {{
                    "type": "CHECK|UNIQUE|etc",
                    "name": "constraint_name",
                    "definition": "constraint definition",
                    "description": "What this constraint enforces"
                }}
            ]
        }}
    ],
    "relationships": [
        {{
            "from_table": "table1",
            "from_column": "column1",
            "to_table": "table2",
            "to_column": "column2",
            "type": "one-to-many|many-to-many|one-to-one",
            "description": "Nature of the relationship"
        }}
    ],
    "views": [
        {{
            "name": "view_name",
            "description": "Purpose of this view",
            "query": "SELECT statement for the view"
        }}
    ],
    "sample_queries": [
        {{
            "description": "What this query does",
            "query": "SQL query",
            "expected_performance": "Performance considerations"
        }}
    ],
    "data_validation_rules": [
        "Validation rule description"
    ],
    "security_considerations": [
        "Security measure or consideration"
    ],
    "migration_notes": "Notes for database migration"
}}"""
            
            response = await self.think(prompt, context, use_complex_model=True)
            
            try:
                schema = json.loads(response)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    schema = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse schema response as JSON")
            
            await self.update_task_progress(task, 0.5, "Generating SQL scripts...")
            
            # Generate SQL scripts
            sql_scripts = await self._generate_sql_scripts(schema)
            
            # Create documentation
            documentation = await self._create_schema_documentation(schema, task)
            
            task.status = TaskStatus.COMPLETED
            task.result = {
                "schema_overview": schema.get("schema_overview", ""),
                "table_count": len(schema.get("tables", [])),
                "relationship_count": len(schema.get("relationships", [])),
                "sql_scripts": sql_scripts,
                "documentation": documentation,
                "validation_rules": schema.get("data_validation_rules", []),
                "security_measures": schema.get("security_considerations", []),
            }
            
            # Store schema in metadata
            task.metadata = task.metadata or {}
            task.metadata["schema"] = schema
            
            await self.db_session.commit()
            
            await self.update_task_progress(
                task, 
                1.0, 
                f"Created schema with {len(schema.get('tables', []))} tables."
            )
            
            return task.result
    
    async def _handle_analysis_task(self, task: Task) -> Dict[str, Any]:
        """Analyze data requirements and patterns."""
        context = {
            "analysis_request": task.description,
            "project_context": task.metadata.get("project_context", {}) if task.metadata else {},
        }
        
        prompt = """Analyze the data requirements and provide insights on:
1. Data sources and types
2. Volume and velocity expectations
3. Data quality requirements
4. Analytics and reporting needs
5. Performance requirements
6. Compliance and regulatory considerations

Provide specific recommendations for the data architecture."""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "analysis": response,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_optimization_task(self, task: Task) -> Dict[str, Any]:
        """Optimize queries and database performance."""
        context = {
            "optimization_target": task.description,
            "current_schema": task.metadata.get("schema", {}) if task.metadata else {},
            "performance_issues": task.metadata.get("performance_issues", []) if task.metadata else [],
        }
        
        prompt = """Analyze and optimize the database performance:
1. Identify slow queries and bottlenecks
2. Suggest index improvements
3. Recommend query rewrites
4. Propose caching strategies
5. Consider partitioning or sharding needs
6. Suggest monitoring and alerting setup

Provide specific, actionable optimization steps."""
        
        response = await self.think(prompt, context, use_complex_model=True)
        
        # Parse optimization suggestions
        optimizations = await self._parse_optimizations(response)
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "optimization_plan": response,
            "optimizations": optimizations,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_implementation_task(self, task: Task) -> Dict[str, Any]:
        """Create SQL scripts and migrations."""
        context = {
            "implementation_request": task.description,
            "schema": task.metadata.get("schema", {}) if task.metadata else {},
            "database_type": task.metadata.get("database_type", "postgresql") if task.metadata else "postgresql",
        }
        
        prompt = f"""Create SQL implementation scripts for: {task.description}

Include:
1. CREATE TABLE statements
2. ALTER TABLE for constraints
3. CREATE INDEX statements
4. INSERT statements for seed data
5. Migration rollback scripts
6. Comments explaining each section

Target database: {context['database_type']}"""
        
        response = await self.think(prompt, context)
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "sql_script": response,
            "script_type": "implementation",
            "database_type": context["database_type"],
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_generic_task(self, task: Task) -> Dict[str, Any]:
        """Handle generic data analysis tasks."""
        response = await self.think(
            f"As a Data Analyst, handle this task: {task.title}\n\nDetails: {task.description}",
            {"task_type": task.type.value}
        )
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "response": response,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _generate_sql_scripts(self, schema: Dict[str, Any]) -> Dict[str, str]:
        """Generate SQL scripts from schema definition."""
        scripts = {
            "create_tables": "",
            "create_indexes": "",
            "create_constraints": "",
            "create_views": "",
            "rollback": "",
        }
        
        # Generate CREATE TABLE statements
        create_tables = []
        drop_tables = []
        
        for table in schema.get("tables", []):
            # Build column definitions
            columns = []
            for col in table["columns"]:
                col_def = f"{col['name']} {col['type']}"
                if col.get("primary_key"):
                    col_def += " PRIMARY KEY"
                if not col.get("nullable", True):
                    col_def += " NOT NULL"
                if col.get("unique"):
                    col_def += " UNIQUE"
                if col.get("default") is not None:
                    col_def += f" DEFAULT {col['default']}"
                columns.append(col_def)
            
            create_stmt = f"CREATE TABLE {table['name']} (\n  " + ",\n  ".join(columns) + "\n);"
            create_tables.append(create_stmt)
            drop_tables.append(f"DROP TABLE IF EXISTS {table['name']} CASCADE;")
        
        scripts["create_tables"] = "\n\n".join(create_tables)
        scripts["rollback"] = "\n".join(reversed(drop_tables))
        
        # Generate CREATE INDEX statements
        create_indexes = []
        for table in schema.get("tables", []):
            for idx in table.get("indexes", []):
                unique = "UNIQUE " if idx.get("unique") else ""
                cols = ", ".join(idx["columns"])
                create_indexes.append(
                    f"CREATE {unique}INDEX {idx['name']} ON {table['name']} ({cols});"
                )
        
        scripts["create_indexes"] = "\n".join(create_indexes)
        
        # Generate foreign key constraints
        constraints = []
        for rel in schema.get("relationships", []):
            constraint_name = f"fk_{rel['from_table']}_{rel['to_table']}"
            constraints.append(
                f"ALTER TABLE {rel['from_table']} "
                f"ADD CONSTRAINT {constraint_name} "
                f"FOREIGN KEY ({rel['from_column']}) "
                f"REFERENCES {rel['to_table']}({rel['to_column']});"
            )
        
        scripts["create_constraints"] = "\n".join(constraints)
        
        # Generate CREATE VIEW statements
        views = []
        for view in schema.get("views", []):
            views.append(f"CREATE VIEW {view['name']} AS\n{view['query']};")
        
        scripts["create_views"] = "\n\n".join(views)
        
        return scripts
    
    async def _create_schema_documentation(self, schema: Dict[str, Any], task: Task) -> str:
        """Create comprehensive schema documentation."""
        doc_parts = [
            f"# Database Schema: {task.title}",
            f"\n## Overview\n{schema.get('schema_overview', '')}",
            "\n## Tables\n"
        ]
        
        # Document each table
        for table in schema.get("tables", []):
            doc_parts.append(f"\n### {table['name']}")
            doc_parts.append(f"{table['description']}")
            doc_parts.append("\n**Columns:**")
            
            for col in table["columns"]:
                nullable = "NULL" if col.get("nullable", True) else "NOT NULL"
                pk = " (PK)" if col.get("primary_key") else ""
                fk = f" (FK -> {col['foreign_key']})" if col.get("foreign_key") else ""
                doc_parts.append(
                    f"- `{col['name']}` {col['type']} {nullable}{pk}{fk} - {col['description']}"
                )
            
            if table.get("indexes"):
                doc_parts.append("\n**Indexes:**")
                for idx in table["indexes"]:
                    unique = "(UNIQUE) " if idx.get("unique") else ""
                    doc_parts.append(
                        f"- `{idx['name']}` {unique}on ({', '.join(idx['columns'])}) - {idx['description']}"
                    )
        
        # Document relationships
        if schema.get("relationships"):
            doc_parts.append("\n## Relationships\n")
            for rel in schema["relationships"]:
                doc_parts.append(
                    f"- **{rel['from_table']}.{rel['from_column']}** → "
                    f"**{rel['to_table']}.{rel['to_column']}** "
                    f"({rel['type']}) - {rel['description']}"
                )
        
        # Document sample queries
        if schema.get("sample_queries"):
            doc_parts.append("\n## Sample Queries\n")
            for query in schema["sample_queries"]:
                doc_parts.append(f"\n**{query['description']}**")
                doc_parts.append(f"```sql\n{query['query']}\n```")
                if query.get("expected_performance"):
                    doc_parts.append(f"*Performance: {query['expected_performance']}*")
        
        # Add validation rules
        if schema.get("data_validation_rules"):
            doc_parts.append("\n## Data Validation Rules")
            for rule in schema["data_validation_rules"]:
                doc_parts.append(f"- {rule}")
        
        # Add security considerations
        if schema.get("security_considerations"):
            doc_parts.append("\n## Security Considerations")
            for consideration in schema["security_considerations"]:
                doc_parts.append(f"- {consideration}")
        
        return "\n".join(doc_parts)
    
    async def _parse_optimizations(self, optimization_response: str) -> List[Dict[str, Any]]:
        """Parse optimization suggestions into structured format."""
        # In a real implementation, this would parse the response
        # For now, return a simple structure
        return [
            {
                "type": "index",
                "description": "Optimization suggestion from response",
                "impact": "high",
                "effort": "low",
            }
        ]
    
    async def analyze_data_requirements(self, requirements: str) -> Dict[str, Any]:
        """Analyze data requirements and provide recommendations."""
        prompt = f"""Analyze these data requirements and provide:
1. Recommended database type (SQL vs NoSQL)
2. Data volume estimates
3. Performance requirements
4. Scalability considerations
5. Security and compliance needs

Requirements: {requirements}"""
        
        response = await self.think(prompt, use_complex_model=True)
        
        return {
            "analysis": response,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def design_analytics_solution(self, analytics_needs: str) -> Dict[str, Any]:
        """Design analytics and reporting solution."""
        prompt = f"""Design an analytics solution for: {analytics_needs}

Include:
1. Data warehouse/mart design
2. ETL pipeline architecture
3. Reporting schema (facts and dimensions)
4. Real-time vs batch processing decisions
5. Visualization recommendations
6. Performance optimization strategies"""
        
        response = await self.think(prompt, use_complex_model=True)
        
        return {
            "solution": response,
            "timestamp": datetime.utcnow().isoformat(),
        } 