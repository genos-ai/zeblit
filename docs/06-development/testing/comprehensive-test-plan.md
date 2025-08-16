# Comprehensive Test Plan - Zeblit AI Platform

*Version: 1.0.0*  
*Author: Zeblit Development Team*  
*Date: 2025-01-15*

## Changelog
- 1.0.0 (2025-01-15): Initial comprehensive test plan created after agent chat system completion.

---

## 🎯 **Test Plan Overview**

This document provides a systematic testing approach for the Zeblit AI Platform, organized by functional areas and complexity levels. Each test phase builds upon the previous, ensuring a solid foundation before advancing to more complex features.

### **Current Status**
- ✅ **Phase 1**: Core Foundation (COMPLETED)
- ✅ **Phase 2**: Container Management (MAJOR FIXES APPLIED - READY FOR FULL TESTING)
- ⏳ **Phase 3**: Real-time Features (INFRASTRUCTURE EXISTS)
- ✅ **Phase 4**: Task Scheduling (AUTHENTICATION FIXED - READY FOR TESTING)
- 🚀 **Phase 5**: Advanced Agent Workflows (BASIC CHAT WORKING)
- 🛡️ **Phase 6**: Error Handling & Edge Cases (NEEDS SYSTEMATIC TESTING)
- ⚡ **Phase 7**: Performance & Scalability (NOT TESTED)

---

## 📋 **PHASE 1: CORE FOUNDATION** ✅

### **Status: COMPLETED**
All basic operations have been tested and are working correctly.

#### **1.1 Authentication System** ✅
- [x] API key validation and database lookup
- [x] Database-backed user authentication  
- [x] Permission checking and access control
- [x] Test user creation with API key: `zbl_3fde4dc9_b565978b892be11f6bc90db3be0e2a4e`

#### **1.2 Project Management** ✅
- [x] Create projects with metadata
- [x] List projects with pagination
- [x] Update project settings
- [x] Delete projects and cleanup
- [x] Project ownership and access control

#### **1.3 File Operations** ✅
- [x] File tree exploration (`zeblit files tree`)
- [x] File listing and filtering (`zeblit files list`)
- [x] File content reading
- [x] Workspace file management
- [x] File metadata and permissions

#### **1.4 Agent Chat System** ✅
- [x] Agent discovery and listing (`zeblit chat agents`)
- [x] Single-agent communication (`zeblit chat send`)
- [x] Response formatting with Rich library
- [x] Claude 4 model integration (Sonnet 4 + Opus 4.1)
- [x] Project-specific agent instances

---

## ✅ **PHASE 2: CONTAINER MANAGEMENT**

### **Status: MAJOR FIXES APPLIED - READY FOR FULL TESTING**
✅ **RECENT FIXES COMPLETED:**
- **Container Command Execution**: Fixed with base64 encoding system
- **Special Character Support**: Full shell operations now working
- **File Upload/Download**: Multipart form handling implemented
- **Security**: Command sanitization and validation added

OrbStack installed, robust command execution implemented, needs systematic testing of advanced scenarios.

### **Prerequisites**
- OrbStack running and accessible via Docker CLI
- Backend server running with container service enabled
- Test project created and selected

### **2.1 Container Lifecycle**

#### **Test 2.1.1: Start Project Container**
```bash
# Command
zeblit container start

# Expected Results
- Container image pulled/built successfully
- Container starts with project workspace mounted
- Container status shows "running"
- Container logs show successful initialization

# Success Criteria
- Exit code 0
- Container ID returned
- Container accessible via Docker CLI
- Project files available inside container
```

#### **Test 2.1.2: Get Container Status**
```bash
# Command
zeblit container status

# Expected Results
- Container state displayed (running/stopped)
- Resource usage information
- Container uptime
- Health check status

# Success Criteria
- Accurate status information
- Resource metrics within expected limits
- Health checks passing
```

#### **Test 2.1.3: View Container Logs**
```bash
# Command
zeblit container logs

# Expected Results
- Container startup logs displayed
- Application logs streamed
- Timestamps and log levels shown
- Logs properly formatted

# Success Criteria
- Complete log history available
- Real-time log streaming works
- No log truncation issues
```

#### **Test 2.1.4: Stop Project Container**
```bash
# Command
zeblit container stop

# Expected Results
- Graceful container shutdown
- Container status shows "stopped"
- Resources properly released
- Data persistence confirmed

# Success Criteria
- Clean shutdown process
- No data loss
- Container removed from Docker
```

### **2.2 Container File Operations**

#### **Test 2.2.1: Execute Commands in Container**
```bash
# Commands
zeblit container exec "ls -la"
zeblit container exec "python --version"
zeblit container exec "npm --version"

# Expected Results
- Commands execute successfully
- Output displayed in CLI
- Exit codes propagated correctly
- Interactive commands supported

# Success Criteria
- All standard development tools available
- Command output properly captured
- Error handling for invalid commands
```

#### **Test 2.2.2: File Upload to Container**
```bash
# Command
zeblit files upload local_file.txt /workspace/uploaded_file.txt

# Expected Results
- File transferred to container
- File permissions preserved
- Upload progress displayed
- Confirmation of successful transfer

# Success Criteria
- File integrity maintained
- Proper error handling for large files
- Overwrite protection where appropriate
```

#### **Test 2.2.3: File Download from Container**
```bash
# Command
zeblit files download /workspace/output.txt local_output.txt

# Expected Results
- File transferred from container
- Local file created successfully
- Download progress displayed
- File metadata preserved

# Success Criteria
- Complete file transfer
- Binary file support
- Network interruption handling
```

### **2.3 Container Persistence & Cleanup**

#### **Test 2.3.1: Data Persistence**
```bash
# Test Steps
1. zeblit container start
2. zeblit container exec "echo 'test data' > /workspace/test.txt"
3. zeblit container stop
4. zeblit container start
5. zeblit container exec "cat /workspace/test.txt"

# Expected Results
- Data survives container restart
- File permissions maintained
- No data corruption

# Success Criteria
- 100% data persistence
- Consistent filesystem state
```

#### **Test 2.3.2: Resource Limits**
```bash
# Commands
zeblit container exec "stress --cpu 8 --timeout 10s"
zeblit container exec "dd if=/dev/zero of=/tmp/bigfile bs=1M count=1000"

# Expected Results
- CPU limits enforced
- Memory limits enforced  
- Storage limits enforced
- Container remains stable

# Success Criteria
- Limits prevent resource exhaustion
- Graceful handling of limit breaches
- System stability maintained
```

#### **Test 2.3.3: Automatic Cleanup**
```bash
# Test Steps
1. Create multiple containers
2. Leave containers idle beyond timeout
3. Check cleanup policies executed

# Expected Results
- Idle containers stopped automatically
- Old containers removed
- Resources reclaimed
- Database records updated

# Success Criteria
- Configurable cleanup policies
- No resource leaks
- Proper database synchronization
```

---

## ⏳ **PHASE 3: REAL-TIME FEATURES**

### **Status: INFRASTRUCTURE EXISTS**
WebSocket endpoints implemented, needs comprehensive testing.

### **Prerequisites**
- Backend WebSocket server running on `/api/v1/ws/connect`
- Frontend or test client for WebSocket connections
- Valid authentication credentials

### **3.1 WebSocket Connectivity**

#### **Test 3.1.1: WebSocket Connection Establishment**
```javascript
// Test Code
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/connect');
ws.onopen = () => console.log('Connected');
ws.onerror = (error) => console.error('Error:', error);

// Expected Results
- Successful WebSocket handshake
- Connection established event fired
- Ready to send/receive messages

// Success Criteria
- Clean connection establishment
- Proper error handling for failed connections
- Connection state properly managed
```

#### **Test 3.1.2: Authentication over WebSocket**
```javascript
// Test Code
ws.send(JSON.stringify({
  type: 'auth',
  token: 'zbl_3fde4dc9_b565978b892be11f6bc90db3be0e2a4e'
}));

// Expected Results
- Authentication token validated
- User session established
- Access permissions applied

// Success Criteria
- Secure authentication flow
- Invalid token rejection
- Session management working
```

#### **Test 3.1.3: Connection Persistence**
```bash
# Test Steps
1. Establish WebSocket connection
2. Send periodic heartbeat messages
3. Simulate network interruption
4. Verify automatic reconnection

# Expected Results
- Connection maintained during normal operation
- Automatic reconnection on disconnection
- Message queue preserved during reconnection

# Success Criteria
- Robust connection handling
- No message loss during reconnection
- Configurable heartbeat intervals
```

### **3.2 Console Streaming**

#### **Test 3.2.1: Real-time Console Output**
```bash
# Commands
zeblit console stream
zeblit container exec "for i in {1..10}; do echo Line $i; sleep 1; done"

# Expected Results
- Console output streamed in real-time
- No buffering delays
- Proper line termination
- Timestamps included

# Success Criteria
- < 100ms latency for output
- Complete output capture
- Proper formatting preserved
```

#### **Test 3.2.2: Interactive Console**
```bash
# Commands
zeblit console connect
# Interactive shell session in container

# Expected Results
- Bidirectional communication
- Input commands processed
- Output displayed immediately
- Shell features working (tab completion, history)

# Success Criteria
- Full terminal emulation
- Keyboard shortcuts working
- Session state maintained
```

### **3.3 Agent Status Broadcasting**

#### **Test 3.3.1: Agent Status Updates**
```bash
# Commands
zeblit chat send "Create a Python web application"
# Monitor WebSocket for agent status changes

# Expected Results
- Agent status changes broadcast: idle → thinking → working → idle
- Multiple clients receive updates
- Status includes progress information

# Success Criteria
- Real-time status propagation
- Accurate status information
- Multi-client broadcasting
```

---

## ⏳ **PHASE 4: TASK SCHEDULING**

### **Status: MODELS & APIS EXIST**
Database schema and endpoints ready, needs implementation testing.

### **4.1 Task Management**

#### **Test 4.1.1: Create Scheduled Tasks**
```bash
# Commands
zeblit task create --name "daily-backup" --schedule "0 2 * * *" --command "backup.sh"
zeblit task create --name "hourly-health" --schedule "0 * * * *" --command "health-check.py"

# Expected Results
- Tasks created in database
- Cron expressions validated
- Task metadata stored

# Success Criteria
- Valid cron expression parsing
- Task conflict detection
- Proper validation errors
```

#### **Test 4.1.2: List and Filter Tasks**
```bash
# Commands
zeblit task list
zeblit task list --status pending
zeblit task list --project-id <project-id>

# Expected Results
- All tasks displayed with details
- Filtering works correctly
- Pagination for large lists

# Success Criteria
- Accurate task information
- Efficient filtering
- Proper sorting options
```

### **4.2 Task Execution**

#### **Test 4.2.1: Manual Task Execution**
```bash
# Commands
zeblit task run daily-backup
zeblit task status daily-backup

# Expected Results
- Task executes immediately
- Status tracked through lifecycle
- Output captured and stored

# Success Criteria
- Successful task completion
- Error handling for failed tasks
- Complete output logging
```

### **4.3 Scheduling System**

#### **Test 4.3.1: Automatic Task Triggering**
```bash
# Test Steps
1. Create task with 1-minute schedule
2. Wait for automatic execution
3. Verify task ran at correct time

# Expected Results
- Task triggers automatically
- Timing accuracy within 10 seconds
- Multiple schedule types work

# Success Criteria
- Reliable schedule execution
- No missed executions
- Timezone handling correct
```

---

## 🚀 **PHASE 5: ADVANCED AGENT WORKFLOWS**

### **Status: BASIC CHAT WORKING**
Multi-agent capabilities need comprehensive testing.

### **5.1 Complex Agent Interactions**

#### **Test 5.1.1: Multi-Agent Conversations**
```bash
# Commands
zeblit chat send "I need to build a web app with user authentication, database, and API"

# Expected Results
- DevManager analyzes requirements
- Routes tasks to appropriate agents (Architect, Engineer, Data Analyst)
- Agents collaborate on solution
- Coordinated response provided

# Success Criteria
- Intelligent agent routing
- Context sharing between agents
- Coherent multi-agent responses
```

#### **Test 5.1.2: Agent Specialization**
```bash
# Commands
zeblit chat send --agent Engineer "Review this Python code for bugs"
zeblit chat send --agent Architect "Design scalable microservices architecture"
zeblit chat send --agent DataAnalyst "Design database schema for e-commerce"

# Expected Results
- Each agent responds with specialized knowledge
- Responses match agent expertise
- Agent-specific prompts and context used

# Success Criteria
- Clear specialization demonstrated
- Expert-level responses
- Consistent agent personalities
```

### **5.2 Agent Memory & Context**

#### **Test 5.2.1: Conversation History**
```bash
# Commands
zeblit chat history
zeblit chat send "Continue from where we left off yesterday"

# Expected Results
- Complete conversation history displayed
- Context carried across sessions
- References to previous conversations work

# Success Criteria
- Persistent conversation memory
- Contextual awareness
- Long-term project memory
```

---

## 🛡️ **PHASE 6: ERROR HANDLING & EDGE CASES**

### **6.1 Error Scenarios**

#### **Test 6.1.1: Network Connectivity Issues**
```bash
# Test Steps
1. Disconnect network during API call
2. Attempt operations with invalid endpoints
3. Test timeout scenarios

# Expected Results
- Graceful error messages
- Retry mechanisms activated
- User informed of connectivity issues

# Success Criteria
- No application crashes
- Clear error communication
- Automatic recovery when possible
```

#### **Test 6.1.2: Resource Exhaustion**
```bash
# Test Steps
1. Fill disk space completely
2. Exhaust memory limits
3. Consume all CPU resources

# Expected Results
- System remains responsive
- Error messages indicate resource issues
- Graceful degradation of services

# Success Criteria
- System stability maintained
- Users can still access basic functions
- Administrators notified of issues
```

---

## ⚡ **PHASE 7: PERFORMANCE & SCALABILITY**

### **7.1 Load Testing**

#### **Test 7.1.1: Concurrent Operations**
```bash
# Test Scripts
./load-test.py --concurrent-users 10 --duration 300s
./load-test.py --api-calls-per-second 100

# Expected Results
- System handles concurrent load
- Response times remain acceptable
- No data corruption under load

# Success Criteria
- < 2s response time for 95% of requests
- Zero data loss
- Graceful handling of peak load
```

---

## 🧪 **Testing Methodology**

### **Test Execution Process**
1. **🎯 Define Success Criteria** - Clear pass/fail conditions
2. **⚙️ Setup Prerequisites** - Environment configuration
3. **🧪 Execute Test Steps** - Follow documented procedures
4. **✅ Verify Results** - Check all expected outcomes
5. **📝 Document Issues** - Record bugs and improvements
6. **🔄 Iterate** - Fix issues and retest

### **Testing Tools & Resources**
- **CLI Commands**: Primary testing interface (`zeblit`)
- **API Testing**: Direct backend testing with `curl`
- **Database Verification**: SQL queries to verify data integrity
- **WebSocket Testing**: Browser dev tools and test clients
- **Load Testing**: Custom Python scripts in `scripts/`
- **Log Analysis**: Backend application logs for debugging

### **Issue Tracking Template**
```markdown
## Issue #XXX: [Brief Description]

**Test Phase**: [Phase Number and Name]
**Test Case**: [Specific test that failed]
**Severity**: [Critical/High/Medium/Low]

**Expected Behavior**:
[What should have happened]

**Actual Behavior**:
[What actually happened]

**Steps to Reproduce**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Environment**:
- OS: [Operating System]
- Backend Version: [Git commit hash]
- Dependencies: [Relevant package versions]

**Logs/Screenshots**:
[Attach relevant information]

**Resolution**:
[How the issue was fixed]
```

---

## 📊 **Test Progress Tracking**

### **Completion Status by Phase**
- **Phase 1**: ✅ 100% Complete (16/16 tests)
- **Phase 2**: 🔄 Ready for Testing (0/12 tests) - **Major fixes applied**
- **Phase 3**: ⏳ 0% Complete (0/9 tests)
- **Phase 4**: ✅ Ready for Testing (0/8 tests) - **Authentication fixed**
- **Phase 5**: ⏳ 0% Complete (0/6 tests)
- **Phase 6**: ⏳ 0% Complete (0/6 tests)
- **Phase 7**: ⏳ 0% Complete (0/4 tests)

### **Overall Progress**
- **Total Tests**: 61
- **Completed**: 16 (26%)
- **Ready for Testing**: 12 (20%) - Phase 2 with fixes
- **Remaining**: 45 (74%)

### **Next Priority**
**Phase 2: Container Management Testing** - Now that container command execution and file operations are fixed, comprehensive testing can proceed.

---

## 🎯 **Success Metrics**

### **Quality Gates**
- **Phase 2**: 100% container operations working reliably
- **Phase 3**: Real-time features with < 100ms latency
- **Phase 4**: Task scheduling with 99.9% reliability
- **Phase 5**: Multi-agent workflows demonstrating clear collaboration
- **Phase 6**: Zero critical failures under normal load
- **Phase 7**: Support for 10+ concurrent users with acceptable performance

### **Definition of Done**
A phase is complete when:
1. All test cases pass their success criteria
2. No critical or high-severity issues remain open
3. Performance metrics meet defined thresholds
4. Documentation is updated with any changes
5. Regression testing confirms no existing functionality broken

---

*This test plan is a living document and should be updated as the system evolves and new requirements emerge.*
