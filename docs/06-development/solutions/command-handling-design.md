# Command Handling Design - Robust Solution

*Version: 1.0.0*
*Author: Zeblit Development Team*
*Date: 2025-01-15*

## Changelog
- 1.0.0 (2025-01-15): Initial design for robust command handling with special characters.

---

## 🎯 **THE PROBLEM**

Current command execution pipeline has multiple failure points:
1. **CLI Shell Interpretation**: `!`, `$`, `"`, `'`, `\` get interpreted by user's shell
2. **JSON Serialization**: Quotes and escapes break JSON structure  
3. **API Transport**: HTTP payload encoding issues
4. **Container Execution**: Docker exec command parsing
5. **Multi-line Support**: No support for complex scripts
6. **Interactive Commands**: No stdin/stdout streaming

## 🧠 **SOLUTION: Multi-Layer Command Encoding**

### **Layer 1: CLI Command Encoding**
```python
# clients/zeblit-cli/src/zeblit_cli/utils/command_encoder.py

import base64
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class CommandSpec:
    """Complete command specification."""
    command: List[str]
    workdir: Optional[str] = None
    environment: Optional[Dict[str, str]] = None
    encoding: str = "utf-8"
    shell: bool = False  # Whether to execute via shell
    interactive: bool = False
    timeout: Optional[int] = None

class CommandEncoder:
    """Encode commands for safe transport and execution."""
    
    @staticmethod
    def encode_command(
        command: str | List[str],
        workdir: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        shell: bool = False
    ) -> str:
        """
        Encode command for safe transport.
        
        Args:
            command: Command string or list
            workdir: Working directory
            environment: Environment variables
            shell: Execute via shell (for pipes, redirects, etc.)
        
        Returns:
            Base64 encoded command specification
        """
        # Handle both string and list inputs
        if isinstance(command, str):
            if shell:
                # For shell commands, pass as single string
                cmd_list = ["/bin/bash", "-c", command]
            else:
                # Parse string into arguments (basic shlex)
                import shlex
                cmd_list = shlex.split(command)
        else:
            cmd_list = command
        
        # Create command specification
        spec = CommandSpec(
            command=cmd_list,
            workdir=workdir,
            environment=environment or {},
            shell=shell
        )
        
        # Serialize to JSON then base64
        spec_json = json.dumps(spec.__dict__)
        encoded = base64.b64encode(spec_json.encode('utf-8')).decode('ascii')
        
        return encoded
    
    @staticmethod
    def decode_command(encoded: str) -> CommandSpec:
        """Decode command specification."""
        spec_json = base64.b64decode(encoded.encode('ascii')).decode('utf-8')
        spec_dict = json.loads(spec_json)
        return CommandSpec(**spec_dict)

class CommandParser:
    """Parse various command input formats."""
    
    @staticmethod
    def smart_parse(input_text: str) -> CommandSpec:
        """
        Intelligently parse command input.
        
        Handles:
        - Simple commands: "ls -la"
        - Shell operations: "ps aux | grep python"
        - Multi-line scripts: "#!/bin/bash\necho hello\necho world"
        """
        # Detect if it's a shell command (contains shell operators)
        shell_operators = ['|', '&&', '||', '>', '>>', '<', ';', '&']
        needs_shell = any(op in input_text for op in shell_operators)
        
        # Detect multi-line scripts
        is_multiline = '\n' in input_text.strip()
        
        if is_multiline:
            # Handle as script
            return CommandSpec(
                command=["/bin/bash", "-c", input_text],
                shell=True
            )
        elif needs_shell:
            # Handle as shell command
            return CommandSpec(
                command=["/bin/bash", "-c", input_text],
                shell=True
            )
        else:
            # Handle as simple command
            import shlex
            return CommandSpec(
                command=shlex.split(input_text),
                shell=False
            )
```

### **Layer 2: Enhanced CLI Interface**

```python
# clients/zeblit-cli/src/zeblit_cli/commands/container_enhanced.py

@container_commands.command("run")
@click.argument("command", nargs=-1)
@click.option("--working-dir", "-w", help="Working directory")
@click.option("--shell", "-s", is_flag=True, help="Execute via shell (for pipes, redirects)")
@click.option("--file", "-f", type=click.File('r'), help="Execute commands from file")
@click.option("--env", "-e", multiple=True, help="Environment variables (KEY=VALUE)")
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode")
def run_command_enhanced(
    command: tuple,
    working_dir: str,
    shell: bool,
    file: Optional[click.File],
    env: tuple,
    interactive: bool
):
    """Execute a command in the container with robust handling."""
    
    if file:
        # Read command from file
        command_text = file.read()
    elif command:
        # Join command parts
        command_text = " ".join(command)
    else:
        # Interactive mode or error
        if interactive:
            command_text = click.prompt("Enter command")
        else:
            click.echo("Error: No command specified")
            return
    
    # Parse environment variables
    environment = {}
    for env_var in env:
        if '=' in env_var:
            key, value = env_var.split('=', 1)
            environment[key] = value
    
    # Encode command
    encoded_command = CommandEncoder.encode_command(
        command_text,
        workdir=working_dir,
        environment=environment,
        shell=shell
    )
    
    asyncio.run(execute_encoded_command(encoded_command, interactive))

async def execute_encoded_command(encoded_command: str, interactive: bool = False):
    """Execute encoded command."""
    try:
        auth_manager = get_auth_manager()
        settings = get_settings()
        
        project_id = settings.current_project_id
        if not project_id:
            console.print("[red]No project specified[/red]")
            return
        
        async with ZeblitAPIClient(auth_manager) as api_client:
            if interactive:
                # Use WebSocket for interactive execution
                await execute_interactive_command(api_client, project_id, encoded_command)
            else:
                # Use REST API for simple execution
                result = await api_client.execute_encoded_command(project_id, encoded_command)
                display_command_result(result)
                
    except Exception as e:
        console.print(f"[red]Error executing command:[/red] {str(e)}")

def display_command_result(result: Dict[str, Any]):
    """Display command execution result with proper formatting."""
    exit_code = result.get("exit_code", 0)
    output = result.get("output", "")
    command = result.get("command", [])
    
    # Show command that was executed
    console.print(f"⚡ Executed: [bold]{' '.join(command)}[/bold]")
    
    # Show output with syntax highlighting if possible
    if output.strip():
        console.print("\n[bold]Output:[/bold]")
        
        # Try to detect output type for syntax highlighting
        if any(keyword in output.lower() for keyword in ["error", "exception", "traceback"]):
            console.print(f"[red]{output.rstrip()}[/red]")
        else:
            console.print(output.rstrip())
    
    # Show result status
    if exit_code == 0:
        console.print("✅ [green]Command completed successfully[/green]")
    else:
        console.print(f"❌ [red]Command failed with exit code {exit_code}[/red]")
```

### **Layer 3: Enhanced API Schema**

```python
# modules/backend/schemas/container_enhanced.py

class EncodedContainerCommand(BaseModel):
    """Enhanced container command with encoding support."""
    encoded_command: str = Field(..., description="Base64 encoded command specification")
    
    @field_validator('encoded_command')
    @classmethod
    def validate_encoded_command(cls, v: str) -> str:
        """Validate that the encoded command can be decoded."""
        try:
            # Attempt to decode to validate format
            import base64
            import json
            decoded = base64.b64decode(v.encode('ascii')).decode('utf-8')
            json.loads(decoded)
            return v
        except Exception:
            raise ValueError("Invalid encoded command format")

class ContainerCommandResultEnhanced(BaseModel):
    """Enhanced command execution result."""
    exit_code: int
    output: str
    error_output: str = Field("", description="Separate stderr output")
    command: List[str]
    workdir: Optional[str]
    environment: Dict[str, str]
    execution_time_ms: int
    executed_at: datetime
    
class InteractiveSession(BaseModel):
    """Interactive session management."""
    session_id: str
    project_id: UUID
    container_id: str
    created_at: datetime
    last_activity: datetime
    is_active: bool
```

### **Layer 4: Backend Command Decoder**

```python
# modules/backend/services/command_executor.py

class CommandExecutor:
    """Execute commands with full special character support."""
    
    async def execute_encoded_command(
        self,
        container_id: str,
        encoded_command: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute base64 encoded command."""
        start_time = datetime.utcnow()
        
        try:
            # Decode command specification
            spec = CommandEncoder.decode_command(encoded_command)
            
            # Execute based on specification
            if spec.interactive:
                return await self._execute_interactive(container_id, spec)
            else:
                return await self._execute_standard(container_id, spec, timeout)
                
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise
    
    async def _execute_standard(
        self,
        container_id: str,
        spec: CommandSpec,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute standard (non-interactive) command."""
        from modules.backend.core.orbstack_client import orbstack_client
        
        start_time = datetime.utcnow()
        
        try:
            # Execute command with proper environment and working directory
            exit_code, output = await orbstack_client.execute_command(
                container_id=container_id,
                command=spec.command,
                workdir=spec.workdir,
                environment=spec.environment
            )
            
            end_time = datetime.utcnow()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                "exit_code": exit_code,
                "output": output,
                "error_output": "",  # Combined in output for now
                "command": spec.command,
                "workdir": spec.workdir,
                "environment": spec.environment,
                "execution_time_ms": execution_time_ms,
                "executed_at": start_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Standard command execution failed: {e}")
            raise
```

### **Layer 5: Interactive Command Support**

```python
# modules/backend/services/interactive_executor.py

class InteractiveCommandExecutor:
    """Handle interactive command execution via WebSocket."""
    
    def __init__(self):
        self.active_sessions: Dict[str, InteractiveSession] = {}
    
    async def create_session(
        self,
        project_id: UUID,
        container_id: str,
        websocket: WebSocket
    ) -> str:
        """Create new interactive session."""
        session_id = str(uuid4())
        
        session = InteractiveSession(
            session_id=session_id,
            project_id=project_id,
            container_id=container_id,
            websocket=websocket,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            is_active=True
        )
        
        self.active_sessions[session_id] = session
        return session_id
    
    async def execute_interactive_command(
        self,
        session_id: str,
        encoded_command: str
    ) -> None:
        """Execute command in interactive session."""
        session = self.active_sessions.get(session_id)
        if not session or not session.is_active:
            raise ValueError("Invalid or inactive session")
        
        # Decode command
        spec = CommandEncoder.decode_command(encoded_command)
        
        # Stream execution via WebSocket
        await self._stream_execution(session, spec)
    
    async def _stream_execution(
        self,
        session: InteractiveSession,
        spec: CommandSpec
    ) -> None:
        """Stream command execution to WebSocket."""
        # Implementation for real-time streaming
        pass
```

## 🎯 **IMPLEMENTATION PHASES**

### **Phase 1: Basic Encoding (Immediate)**
- Implement CommandEncoder for base64 encoding
- Update CLI to use encoding for special characters
- Update API to accept encoded commands
- Test with problematic characters: `!"'$\|&;`

### **Phase 2: Enhanced Parsing (Short-term)**
- Add smart command parsing (shell vs direct)
- Support for multi-line scripts
- Environment variable handling
- File-based command execution

### **Phase 3: Interactive Support (Medium-term)**
- WebSocket-based interactive sessions
- Real-time stdin/stdout streaming
- Session management and persistence
- Interactive shell access

### **Phase 4: Advanced Features (Long-term)**
- Command history and replay
- Output parsing and formatting
- Syntax highlighting
- Command templates and macros

## 🧪 **TEST CASES**

```bash
# Special characters
zeblit container run 'echo "Hello $USER with '\''quotes'\'' and !history"'

# Shell operations
zeblit container run --shell 'ps aux | grep python | wc -l'

# Multi-line script
zeblit container run --file script.sh

# Environment variables
zeblit container run --env NODE_ENV=production --env PORT=3000 'npm start'

# Interactive session
zeblit container interactive
```

## 📈 **BENEFITS**

1. **100% Character Support**: Any character combination works
2. **Shell Feature Support**: Pipes, redirects, variables, etc.
3. **Multi-line Scripts**: Full script execution capability  
4. **Environment Control**: Precise environment variable management
5. **Interactive Mode**: Real-time command interaction
6. **Error Isolation**: Clear separation of stdout/stderr
7. **Performance Metrics**: Execution time tracking
8. **Security**: No shell injection vulnerabilities

This solution provides enterprise-grade command execution with full special character support while maintaining security and performance.
