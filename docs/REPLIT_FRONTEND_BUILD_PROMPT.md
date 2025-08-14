# **Zeblit AI Development Platform - Frontend Build Prompt for Replit**

## **Project Overview**

Create a modern, Replit-style web-based IDE frontend with integrated AI agent assistance. This is a React TypeScript application that mimics Replit's interface but adds 6 specialized AI agents that help users build applications through natural language conversations.

**IMPORTANT**: This frontend will use mock data and simulated APIs for all backend functionality. No real backend integration is needed at this stage.

## **Technology Stack Requirements**

```json
{
  "framework": "React 18.3.1 with TypeScript 5.6.3",
  "bundler": "Vite 6.0.5",
  "styling": "Tailwind CSS 3.4.17",
  "routing": "wouter 3.0.0",
  "icons": "lucide-react",
  "editor": "monaco-editor (VS Code editor)",
  "http": "axios",
  "websocket": "native WebSocket API (mocked)",
  "ui_components": "Build from scratch with Tailwind",
  "state_management": "React Context API + useReducer"
}
```

## **Visual Layout Specification**

### **Overall Structure**
```
┌─────────────────────────────────────────────────────────────────────────┐
│ Top Navigation Bar (48px height)                                        │
│ ┌─────┬────────────────┬─────────┬──────────────┬────────┬──────────┐ │
│ │Logo │ Project Name   │ Run Btn │ Agent Status │ Share  │ User Menu│ │
│ └─────┴────────────────┴─────────┴──────────────┴────────┴──────────┘ │
├─────────────┬─────────────────────────────────┬─────────────────────────┤
│             │                                   │                         │
│ LEFT PANEL  │      CENTER PANEL                │     RIGHT PANEL         │
│ (320px)     │      (flexible)                  │     (400px)             │
│             │                                   │                         │
│ ┌─────────┐ │ ┌─────────────────────────────┐ │ ┌─────────────────────┐ │
│ │File Tree│ │ │ Agent Tabs                  │ │ │Preview/Console Tabs │ │
│ │         │ │ │ [DevMgr][PM][Data][Eng]... │ │ │ [Preview][Console]  │ │
│ │- src/   │ │ ├─────────────────────────────┤ │ ├─────────────────────┤ │
│ │  - App  │ │ │                             │ │ │                     │ │
│ │  - main │ │ │   Active Agent Interface    │ │ │  Live Preview       │ │
│ │- public │ │ │                             │ │ │    or              │ │
│ │- pkg.js │ │ │   Chat + Specialized UI     │ │ │  Console Output     │ │
│ │         │ │ │                             │ │ │                     │ │
│ └─────────┘ │ └─────────────────────────────┘ │ └─────────────────────┘ │
│             │                                   │                         │
│ Search Box  │ Message Input Bar (when needed)  │ Error Count / Network   │
└─────────────┴─────────────────────────────────┴─────────────────────────┘
```

### **Color Scheme**
```css
/* Dark theme - Similar to Replit's dark mode */
--bg-primary: #0e1525;        /* Main background */
--bg-secondary: #1c2333;      /* Panel backgrounds */
--bg-tertiary: #252d3d;       /* Hover states */
--border: #2d3548;            /* Borders */
--text-primary: #f5f9fc;      /* Primary text */
--text-secondary: #94a3b8;    /* Secondary text */
--accent-blue: #3b82f6;       /* Primary actions */
--accent-green: #10b981;      /* Success/Run button */
--accent-orange: #f59e0b;     /* Warnings */
--accent-red: #ef4444;        /* Errors */
--accent-purple: #8b5cf6;     /* AI agents */
```

## **Component Structure**

### **1. Top Navigation Bar**

```typescript
interface TopNavigationProps {
  projectName: string;
  onRun: () => void;
  isRunning: boolean;
}

// Features:
- Logo (clickable, goes to dashboard)
- Project name (editable inline)
- Run button (green play button, red stop when running)
- Agent status indicators (6 dots showing agent states)
- Share button (shows share modal)
- User menu (avatar + dropdown)
```

### **2. Left Panel - File Explorer**

```typescript
interface FileNode {
  id: string;
  name: string;
  type: 'file' | 'folder';
  children?: FileNode[];
  content?: string;
  language?: string;
}

// Features:
- Collapsible file tree
- File/folder icons based on type
- Right-click context menu (New File, New Folder, Rename, Delete)
- Search box at bottom
- Drag and drop to move files
- File indicators (modified, new, deleted)
```

### **3. Center Panel - Agent Interfaces**

```typescript
interface Agent {
  id: string;
  type: 'dev_manager' | 'product_manager' | 'data_analyst' | 'engineer' | 'architect' | 'platform_engineer';
  name: string;
  status: 'idle' | 'thinking' | 'working' | 'error';
  avatar: string;
}

// Agent Tabs:
- 6 tabs with agent names and status indicators
- Active tab highlighted
- Status dot (gray=idle, yellow=thinking, green=working, red=error)
- Notification badge for unread messages

// Each Agent Interface includes:
1. Agent header with avatar and description
2. Specialized UI based on agent type (see details below)
3. Chat interface at bottom
```

### **4. Right Panel - Preview/Console**

```typescript
interface ConsoleMessage {
  id: string;
  type: 'log' | 'error' | 'warn' | 'info';
  timestamp: Date;
  message: string;
  source?: string;
}

// Features:
- Tab switcher (Preview, Console, Network, Errors)
- Preview: iframe with refresh button and URL bar
- Console: Filtered log output with clear button
- Network: Request list with timing
- Errors: Error summary with stack traces
```

## **Agent-Specific Interfaces**

### **1. Development Manager**
```typescript
// Specialized UI components:
- Task board (Kanban style)
- Team overview (other agents' workload)
- Sprint progress
- Blockers list
- Timeline view

// Mock data:
const mockTasks = [
  { id: '1', title: 'Set up authentication', status: 'in_progress', assignee: 'engineer', priority: 'high' },
  { id: '2', title: 'Design user dashboard', status: 'todo', assignee: 'product_manager', priority: 'medium' }
];
```

### **2. Product Manager**
```typescript
// Specialized UI:
- User stories list
- Feature roadmap
- Requirements checklist
- Wireframe viewer
- Acceptance criteria editor

// Mock data:
const mockUserStories = [
  { id: '1', title: 'As a user, I want to log in', status: 'defined', points: 3 }
];
```

### **3. Data Analyst**
```typescript
// Specialized UI:
- Database schema visualizer
- Query builder
- Performance metrics
- Data flow diagrams
- Table relationships

// Mock data:
const mockSchema = {
  tables: [
    { name: 'users', columns: ['id', 'email', 'created_at'] }
  ]
};
```

### **4. Senior Engineer**
```typescript
// Specialized UI:
- Code snippets library
- Test results panel
- Debugging tools
- Performance profiler
- Git diff viewer

// Mock data:
const mockCodeSnippets = [
  { id: '1', title: 'API endpoint template', language: 'typescript', code: '...' }
];
```

### **5. Architect**
```typescript
// Specialized UI:
- System diagram editor
- Technology stack builder
- Architecture decisions log
- Component dependency graph
- Performance budgets

// Mock data:
const mockArchitecture = {
  components: ['Frontend', 'API', 'Database'],
  stack: ['React', 'FastAPI', 'PostgreSQL']
};
```

### **6. Platform Engineer**
```typescript
// Specialized UI:
- Deployment pipeline
- Environment manager
- Container status
- Monitoring dashboard
- Infrastructure costs

// Mock data:
const mockDeployments = [
  { id: '1', environment: 'staging', status: 'deployed', version: '1.2.3' }
];
```

## **Core Features to Implement**

### **1. Authentication Flow**
```typescript
// Mock login (always succeeds with mock data)
const mockLogin = async (email: string, password: string) => {
  await simulateDelay(1000);
  return {
    token: 'mock-jwt-token',
    user: { id: '1', email, username: email.split('@')[0] }
  };
};

// Pages needed:
- /login - Email/password form
- /register - Registration form with validation
- /dashboard - Project list
- /projects/:id - Main IDE interface
```

### **2. Project Management**
```typescript
interface Project {
  id: string;
  name: string;
  description: string;
  language: 'python' | 'javascript' | 'typescript';
  framework: string;
  createdAt: Date;
  lastModified: Date;
}

// Mock projects data
const mockProjects: Project[] = [
  {
    id: '1',
    name: 'AI Chat Bot',
    description: 'Customer service chatbot with GPT-4',
    language: 'python',
    framework: 'FastAPI',
    createdAt: new Date('2024-01-01'),
    lastModified: new Date('2024-01-15')
  }
];
```

### **3. File Operations**
```typescript
// Mock file system in localStorage
class MockFileSystem {
  private files: Map<string, FileNode> = new Map();
  
  createFile(path: string, content: string) {
    this.files.set(path, { 
      id: generateId(), 
      name: path.split('/').pop(), 
      type: 'file', 
      content 
    });
  }
  
  readFile(path: string): string {
    return this.files.get(path)?.content || '';
  }
  
  // ... other operations
}
```

### **4. Mock WebSocket for Real-time Updates**
```typescript
class MockWebSocket {
  private handlers: Map<string, Function[]> = new Map();
  
  constructor(url: string) {
    // Simulate connection
    setTimeout(() => this.emit('open'), 100);
    
    // Simulate agent messages
    setInterval(() => {
      this.simulateAgentMessage();
    }, 5000);
  }
  
  private simulateAgentMessage() {
    const messages = [
      { type: 'agent_status', agent: 'engineer', status: 'working' },
      { type: 'console_log', message: 'Building application...' },
      { type: 'file_update', path: '/src/App.tsx', content: '...' }
    ];
    
    const randomMsg = messages[Math.floor(Math.random() * messages.length)];
    this.emit('message', { data: JSON.stringify(randomMsg) });
  }
}
```

### **5. Console Capture**
```typescript
// Override console methods to capture logs
const originalConsole = { ...console };
const capturedLogs: ConsoleMessage[] = [];

console.log = (...args) => {
  capturedLogs.push({
    id: generateId(),
    type: 'log',
    timestamp: new Date(),
    message: args.join(' ')
  });
  originalConsole.log(...args);
};

// Similar for error, warn, info
```

### **6. Monaco Editor Integration**
```typescript
interface EditorProps {
  file: FileNode;
  onChange: (content: string) => void;
  onSave: () => void;
}

// Monaco configuration
const editorOptions = {
  theme: 'vs-dark',
  fontSize: 14,
  minimap: { enabled: false },
  automaticLayout: true,
  wordWrap: 'on',
  lineNumbers: 'on',
  scrollBeyondLastLine: false
};
```

## **State Management Structure**

### **1. Auth Context**
```typescript
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<{
  state: AuthState;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}>(null);
```

### **2. Project Context**
```typescript
interface ProjectState {
  currentProject: Project | null;
  files: FileNode[];
  activeFile: string | null;
  unsavedChanges: Set<string>;
}
```

### **3. Agent Context**
```typescript
interface AgentState {
  agents: Agent[];
  activeAgent: string;
  conversations: Map<string, Message[]>;
  agentStates: Map<string, AgentStatus>;
}
```

### **4. Layout Context**
```typescript
interface LayoutState {
  leftPanelWidth: number;
  rightPanelWidth: number;
  leftPanelCollapsed: boolean;
  rightPanelCollapsed: boolean;
  centerPanelTab: string;
  rightPanelTab: string;
}
```

## **Mock Data Generators**

```typescript
// Simulate realistic delays
const simulateDelay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Generate mock chat responses
const generateAgentResponse = (agentType: string, userMessage: string): string => {
  const responses = {
    dev_manager: [
      "I'll coordinate with the team to implement that feature.",
      "Let me break this down into tasks for the team.",
      "I'll assign this to the engineer and track progress."
    ],
    engineer: [
      "I'll implement that using React hooks and TypeScript.",
      "Let me write a clean, efficient solution for that.",
      "I'll add error handling and tests for this feature."
    ],
    // ... other agents
  };
  
  return responses[agentType][Math.floor(Math.random() * responses[agentType].length)];
};

// Generate mock file content
const generateMockFile = (filename: string): string => {
  if (filename.endsWith('.tsx')) {
    return `import React from 'react';\n\nexport const Component = () => {\n  return <div>Hello from ${filename}</div>;\n};`;
  }
  // ... other file types
};
```

## **Responsive Design Requirements**

### **Breakpoints**
```typescript
const breakpoints = {
  mobile: '640px',   // Single panel, stack others
  tablet: '1024px',  // Two panels visible
  desktop: '1280px', // All three panels
};

// Mobile: Show only center panel, others slide in/out
// Tablet: Show center + one side panel
// Desktop: Show all three panels
```

### **Panel Resizing**
```typescript
// Implement drag-to-resize for panels
const MIN_PANEL_WIDTH = 200;
const MAX_LEFT_PANEL_WIDTH = 600;
const MAX_RIGHT_PANEL_WIDTH = 800;

// Save panel sizes to localStorage
// Restore on app load
```

## **Performance Optimizations**

1. **Code Splitting**
   - Lazy load Monaco Editor
   - Lazy load agent interfaces
   - Split routes into separate bundles

2. **Memoization**
   - Use React.memo for file tree nodes
   - useMemo for expensive computations
   - useCallback for event handlers

3. **Virtual Scrolling**
   - For file tree with many items
   - For console output
   - For chat messages

## **Error Handling**

```typescript
// Global error boundary
class ErrorBoundary extends React.Component {
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Application error:', error, errorInfo);
    // Show user-friendly error message
  }
}

// API error handling
const handleApiError = (error: any) => {
  if (error.response?.status === 401) {
    // Redirect to login
  } else if (error.response?.status === 404) {
    // Show not found message
  } else {
    // Show generic error toast
  }
};
```

## **Keyboard Shortcuts**

```typescript
const shortcuts = {
  'Cmd+S': 'Save file',
  'Cmd+P': 'Quick file search',
  'Cmd+Shift+P': 'Command palette',
  'Cmd+B': 'Toggle file explorer',
  'Cmd+J': 'Toggle console',
  'Cmd+Enter': 'Run code',
  'Escape': 'Close modals/panels'
};
```

## **Initial File Structure**

```
src/
├── App.tsx
├── main.tsx
├── index.css
├── components/
│   ├── layout/
│   │   ├── TopNavigation.tsx
│   │   ├── LeftPanel.tsx
│   │   ├── CenterPanel.tsx
│   │   ├── RightPanel.tsx
│   │   └── ResizeHandle.tsx
│   ├── agents/
│   │   ├── AgentTabs.tsx
│   │   ├── AgentChat.tsx
│   │   ├── DevManagerInterface.tsx
│   │   ├── ProductManagerInterface.tsx
│   │   ├── DataAnalystInterface.tsx
│   │   ├── EngineerInterface.tsx
│   │   ├── ArchitectInterface.tsx
│   │   └── PlatformEngineerInterface.tsx
│   ├── editor/
│   │   ├── MonacoEditor.tsx
│   │   ├── FileTree.tsx
│   │   └── FileSearch.tsx
│   ├── preview/
│   │   ├── PreviewFrame.tsx
│   │   ├── ConsoleOutput.tsx
│   │   └── NetworkMonitor.tsx
│   └── common/
│       ├── Button.tsx
│       ├── Modal.tsx
│       ├── Dropdown.tsx
│       └── Toast.tsx
├── contexts/
│   ├── AuthContext.tsx
│   ├── ProjectContext.tsx
│   ├── AgentContext.tsx
│   └── LayoutContext.tsx
├── pages/
│   ├── Login.tsx
│   ├── Register.tsx
│   ├── Dashboard.tsx
│   └── ProjectIDE.tsx
├── services/
│   ├── mockApi.ts
│   ├── mockWebSocket.ts
│   ├── mockFileSystem.ts
│   └── mockAgents.ts
├── hooks/
│   ├── useWebSocket.ts
│   ├── useLocalStorage.ts
│   ├── useKeyboardShortcuts.ts
│   └── useResizePanel.ts
├── utils/
│   ├── constants.ts
│   ├── helpers.ts
│   └── mockDataGenerators.ts
└── types/
    ├── index.ts
    ├── agent.ts
    ├── project.ts
    └── file.ts
```

## **Getting Started Instructions**

1. Create all the file structure above
2. Start with App.tsx and basic routing
3. Implement authentication flow with mock data
4. Build the three-panel layout
5. Add file tree and Monaco editor
6. Implement agent tabs and basic chat
7. Add specialized agent interfaces
8. Implement mock WebSocket for real-time updates
9. Add console capture and preview functionality
10. Polish with animations and responsive design

## **Key Implementation Notes**

1. **All data is mocked** - No real backend calls
2. **Use localStorage** for persistence between sessions
3. **Simulate realistic delays** (300-1000ms) for API calls
4. **Generate believable mock responses** from agents
5. **Include loading states** for all async operations
6. **Add smooth animations** for panel transitions
7. **Implement proper TypeScript types** for everything
8. **Follow React best practices** (hooks, composition, etc.)
9. **Make it feel real** - Include small details like typing indicators
10. **Test on mobile** - Ensure responsive design works

This frontend should feel like a fully functional IDE with AI assistance, even though everything is mocked. The goal is to create a compelling demo that can later be connected to the real backend. 