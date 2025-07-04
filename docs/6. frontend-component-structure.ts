// frontend/src/types/index.ts
/**
 * Core TypeScript types and interfaces for the AI Development Platform
 */

// User and Authentication
export interface User {
  id: string;
  email: string;
  username: string;
  fullName?: string;
  role: 'user' | 'admin' | 'superuser';
  preferences: UserPreferences;
  monthlyTokenLimit: number;
  monthlyTokensUsed: number;
  monthlyCostLimit: number;
  monthlyCostUsed: number;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  defaultModel: string;
  editorFontSize: number;
  autoSave: boolean;
}

// Projects
export interface Project {
  id: string;
  name: string;
  description?: string;
  ownerId: string;
  templateType?: string;
  status: 'active' | 'archived' | 'deleted';
  gitRepoUrl?: string;
  containerId?: string;
  previewUrl?: string;
  createdAt: string;
  lastAccessed: string;
}

export interface ProjectFile {
  id: string;
  projectId: string;
  filePath: string;
  fileName: string;
  fileType: string;
  content?: string;
  isDirectory: boolean;
  children?: ProjectFile[];
}

// Agents
export type AgentType = 
  | 'dev_manager'
  | 'product_manager'
  | 'data_analyst'
  | 'engineer'
  | 'architect'
  | 'platform_engineer';

export interface Agent {
  id: string;
  agentType: AgentType;
  name: string;
  description: string;
  status: 'idle' | 'thinking' | 'working' | 'waiting';
  currentTask?: string;
  currentLoad: number;
}

// Conversations and Messages
export interface Conversation {
  id: string;
  projectId: string;
  agentId: string;
  title: string;
  isActive: boolean;
  lastMessageAt: string;
  messages: Message[];
}

export interface Message {
  id: string;
  conversationId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  agentType?: AgentType;
  timestamp: string;
  tokenCount?: number;
  modelUsed?: string;
}

// Tasks
export interface Task {
  id: string;
  projectId: string;
  title: string;
  description: string;
  status: 'pending' | 'assigned' | 'in_progress' | 'completed' | 'failed';
  assignedAgents: AgentType[];
  primaryAgent?: AgentType;
  progress?: number;
  results?: any;
}

// WebSocket Events
export interface WSMessage {
  type: 'agent_update' | 'file_change' | 'task_progress' | 'build_log' | 'preview_ready';
  payload: any;
}

export interface AgentUpdate {
  agentType: AgentType;
  status: Agent['status'];
  currentTask?: string;
  message?: string;
}

// Component Props Interfaces
export interface LayoutProps {
  children: React.ReactNode;
}

export interface EditorProps {
  file?: ProjectFile;
  onChange: (content: string) => void;
  theme?: 'vs-dark' | 'vs-light';
}

export interface ChatProps {
  projectId: string;
  onSendMessage: (message: string) => void;
}

// ========================================
// frontend/src/components/layout/AppShell.tsx
// ========================================
import React, { useState } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { MainContent } from './MainContent';
import { AgentTabs } from './AgentTabs';
import { ResizablePanel, ResizablePanelGroup, ResizableHandle } from '@/components/ui/resizable';

export const AppShell: React.FC = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="h-screen flex flex-col bg-background">
      <Header />
      
      <div className="flex-1 flex overflow-hidden">
        <ResizablePanelGroup direction="horizontal">
          {/* Left Sidebar - Agent Chat */}
          <ResizablePanel
            defaultSize={20}
            minSize={15}
            maxSize={30}
            collapsible
            onCollapse={() => setSidebarCollapsed(true)}
            onExpand={() => setSidebarCollapsed(false)}
          >
            <Sidebar collapsed={sidebarCollapsed} />
          </ResizablePanel>
          
          <ResizableHandle />
          
          {/* Center - Code Editor */}
          <ResizablePanel defaultSize={50} minSize={30}>
            <MainContent />
          </ResizablePanel>
          
          <ResizableHandle />
          
          {/* Right - Preview */}
          <ResizablePanel defaultSize={30} minSize={20} maxSize={50}>
            <PreviewPane />
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
      
      {/* Bottom - Agent Status Tabs */}
      <div className="h-48 border-t">
        <AgentTabs />
      </div>
    </div>
  );
};

// ========================================
// frontend/src/components/agent/AgentChat.tsx
// ========================================
import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useChat } from '@/hooks/useChat';
import { Message } from '@/types';

interface AgentChatProps {
  projectId: string;
}

export const AgentChat: React.FC<AgentChatProps> = ({ projectId }) => {
  const [input, setInput] = useState('');
  const [model, setModel] = useState('claude-3-5-sonnet');
  const scrollRef = useRef<HTMLDivElement>(null);
  
  const { messages, sendMessage, isLoading } = useChat(projectId);
  const { subscribe } = useWebSocket();

  useEffect(() => {
    // Subscribe to agent messages
    const unsubscribe = subscribe('agent_update', (data) => {
      console.log('Agent update:', data);
    });
    
    return unsubscribe;
  }, [subscribe]);

  useEffect(() => {
    // Auto-scroll to bottom
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = () => {
    if (input.trim() && !isLoading) {
      sendMessage(input, model);
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Model Selector */}
      <div className="p-4 border-b">
        <Select value={model} onValueChange={setModel}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="claude-3-5-sonnet">Claude 3.5 Sonnet</SelectItem>
            <SelectItem value="claude-3-opus">Claude 3 Opus</SelectItem>
            <SelectItem value="gpt-4">GPT-4</SelectItem>
            <SelectItem value="gemini-pro">Gemini Pro</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isLoading && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <div className="animate-pulse">Thinking...</div>
          </div>
        )}
      </ScrollArea>

      {/* Input */}
      <div className="p-4 border-t">
        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me to build something..."
            className="resize-none"
            rows={3}
          />
          <Button onClick={handleSend} disabled={isLoading || !input.trim()}>
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

const MessageBubble: React.FC<{ message: Message }> = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`flex gap-3 mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
          <Bot className="w-4 h-4" />
        </div>
      )}
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted'
        }`}
      >
        <div className="text-sm whitespace-pre-wrap">{message.content}</div>
        {message.agentType && (
          <div className="text-xs opacity-70 mt-1">
            {message.agentType} • {message.modelUsed}
          </div>
        )}
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
          <User className="w-4 h-4 text-primary-foreground" />
        </div>
      )}
    </div>
  );
};

// ========================================
// frontend/src/components/editor/CodeEditor.tsx
// ========================================
import React, { useRef, useEffect } from 'react';
import * as monaco from 'monaco-editor';
import { useTheme } from '@/hooks/useTheme';
import { ProjectFile } from '@/types';

interface CodeEditorProps {
  file?: ProjectFile;
  value: string;
  onChange: (value: string) => void;
  language?: string;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  file,
  value,
  onChange,
  language = 'typescript'
}) => {
  const editorRef = useRef<HTMLDivElement>(null);
  const monacoRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const { theme } = useTheme();

  useEffect(() => {
    if (editorRef.current && !monacoRef.current) {
      // Initialize Monaco Editor
      monacoRef.current = monaco.editor.create(editorRef.current, {
        value,
        language,
        theme: theme === 'dark' ? 'vs-dark' : 'vs-light',
        automaticLayout: true,
        minimap: { enabled: true },
        fontSize: 14,
        wordWrap: 'on',
        lineNumbers: 'on',
        renderWhitespace: 'selection',
        scrollBeyondLastLine: false,
      });

      // Set up change listener
      monacoRef.current.onDidChangeModelContent(() => {
        const currentValue = monacoRef.current?.getValue() || '';
        onChange(currentValue);
      });
    }

    return () => {
      monacoRef.current?.dispose();
    };
  }, []);

  useEffect(() => {
    // Update editor value when file changes
    if (monacoRef.current && value !== monacoRef.current.getValue()) {
      monacoRef.current.setValue(value);
    }
  }, [value]);

  useEffect(() => {
    // Update language when file changes
    if (monacoRef.current && file) {
      const model = monacoRef.current.getModel();
      if (model) {
        monaco.editor.setModelLanguage(model, getLanguageFromFile(file));
      }
    }
  }, [file]);

  useEffect(() => {
    // Update theme
    monaco.editor.setTheme(theme === 'dark' ? 'vs-dark' : 'vs-light');
  }, [theme]);

  return <div ref={editorRef} className="h-full w-full" />;
};

function getLanguageFromFile(file: ProjectFile): string {
  const ext = file.fileName.split('.').pop()?.toLowerCase();
  const languageMap: Record<string, string> = {
    ts: 'typescript',
    tsx: 'typescript',
    js: 'javascript',
    jsx: 'javascript',
    py: 'python',
    json: 'json',
    html: 'html',
    css: 'css',
    scss: 'scss',
    md: 'markdown',
    yml: 'yaml',
    yaml: 'yaml',
  };
  return languageMap[ext || ''] || 'plaintext';
}

// ========================================
// frontend/src/components/explorer/FileExplorer.tsx
// ========================================
import React, { useState } from 'react';
import {
  Folder,
  FolderOpen,
  File,
  ChevronRight,
  ChevronDown,
  Plus,
  Trash,
  Edit,
  FileCode,
  FileText,
  FileImage,
} from 'lucide-react';
import { ContextMenu, ContextMenuContent, ContextMenuItem, ContextMenuTrigger } from '@/components/ui/context-menu';
import { ProjectFile } from '@/types';
import { cn } from '@/lib/utils';

interface FileExplorerProps {
  files: ProjectFile[];
  selectedFile?: string;
  onSelectFile: (file: ProjectFile) => void;
  onCreateFile: (path: string, isDirectory: boolean) => void;
  onDeleteFile: (file: ProjectFile) => void;
  onRenameFile: (file: ProjectFile, newName: string) => void;
}

export const FileExplorer: React.FC<FileExplorerProps> = ({
  files,
  selectedFile,
  onSelectFile,
  onCreateFile,
  onDeleteFile,
  onRenameFile,
}) => {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [renamingFile, setRenamingFile] = useState<string | null>(null);

  const toggleFolder = (path: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedFolders(newExpanded);
  };

  const getFileIcon = (file: ProjectFile) => {
    if (file.isDirectory) {
      return expandedFolders.has(file.filePath) ? FolderOpen : Folder;
    }
    
    const ext = file.fileName.split('.').pop()?.toLowerCase();
    const codeExtensions = ['ts', 'tsx', 'js', 'jsx', 'py', 'java', 'cpp', 'c', 'go'];
    const textExtensions = ['md', 'txt', 'json', 'yml', 'yaml', 'xml'];
    const imageExtensions = ['png', 'jpg', 'jpeg', 'gif', 'svg', 'ico'];
    
    if (codeExtensions.includes(ext || '')) return FileCode;
    if (textExtensions.includes(ext || '')) return FileText;
    if (imageExtensions.includes(ext || '')) return FileImage;
    return File;
  };

  const renderFile = (file: ProjectFile, depth: number = 0) => {
    const Icon = getFileIcon(file);
    const isExpanded = expandedFolders.has(file.filePath);
    const isSelected = selectedFile === file.filePath;
    const isRenaming = renamingFile === file.id;

    return (
      <div key={file.id}>
        <ContextMenu>
          <ContextMenuTrigger>
            <div
              className={cn(
                'flex items-center gap-2 py-1 px-2 cursor-pointer hover:bg-accent rounded',
                isSelected && 'bg-accent',
              )}
              style={{ paddingLeft: `${depth * 16 + 8}px` }}
              onClick={() => {
                if (file.isDirectory) {
                  toggleFolder(file.filePath);
                } else {
                  onSelectFile(file);
                }
              }}
            >
              {file.isDirectory && (
                <div className="w-4 h-4">
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4" />
                  ) : (
                    <ChevronRight className="w-4 h-4" />
                  )}
                </div>
              )}
              <Icon className="w-4 h-4 text-muted-foreground" />
              {isRenaming ? (
                <input
                  type="text"
                  defaultValue={file.fileName}
                  className="flex-1 bg-transparent border-b outline-none"
                  autoFocus
                  onBlur={(e) => {
                    onRenameFile(file, e.target.value);
                    setRenamingFile(null);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      onRenameFile(file, e.currentTarget.value);
                      setRenamingFile(null);
                    }
                    if (e.key === 'Escape') {
                      setRenamingFile(null);
                    }
                  }}
                />
              ) : (
                <span className="text-sm flex-1">{file.fileName}</span>
              )}
            </div>
          </ContextMenuTrigger>
          <ContextMenuContent>
            <ContextMenuItem onClick={() => setRenamingFile(file.id)}>
              <Edit className="w-4 h-4 mr-2" />
              Rename
            </ContextMenuItem>
            <ContextMenuItem onClick={() => onDeleteFile(file)}>
              <Trash className="w-4 h-4 mr-2" />
              Delete
            </ContextMenuItem>
            {file.isDirectory && (
              <>
                <ContextMenuItem
                  onClick={() => onCreateFile(file.filePath + '/newfile.ts', false)}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  New File
                </ContextMenuItem>
                <ContextMenuItem
                  onClick={() => onCreateFile(file.filePath + '/newfolder', true)}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  New Folder
                </ContextMenuItem>
              </>
            )}
          </ContextMenuContent>
        </ContextMenu>

        {file.isDirectory && isExpanded && file.children && (
          <div>
            {file.children.map((child) => renderFile(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-full overflow-auto p-2">
      <div className="flex items-center justify-between mb-2 px-2">
        <h3 className="text-sm font-semibold">Files</h3>
        <div className="flex gap-1">
          <button
            className="p-1 hover:bg-accent rounded"
            onClick={() => onCreateFile('/newfile.ts', false)}
          >
            <File className="w-4 h-4" />
          </button>
          <button
            className="p-1 hover:bg-accent rounded"
            onClick={() => onCreateFile('/newfolder', true)}
          >
            <Folder className="w-4 h-4" />
          </button>
        </div>
      </div>
      <div>{files.map((file) => renderFile(file))}</div>
    </div>
  );
};

// ========================================
// frontend/src/components/preview/PreviewPane.tsx
// ========================================
import React, { useState, useEffect, useRef } from 'react';
import { RefreshCw, ExternalLink, AlertCircle, Loader } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useWebSocket } from '@/hooks/useWebSocket';

interface PreviewPaneProps {
  projectId: string;
  previewUrl?: string;
}

export const PreviewPane: React.FC<PreviewPaneProps> = ({ projectId, previewUrl }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [consoleLogs, setConsoleLogs] = useState<ConsoleLog[]>([]);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const { subscribe } = useWebSocket();

  useEffect(() => {
    // Subscribe to console logs
    const unsubscribe = subscribe('build_log', (data) => {
      setConsoleLogs((prev) => [...prev, data]);
    });

    return unsubscribe;
  }, [subscribe]);

  const handleRefresh = () => {
    if (iframeRef.current) {
      iframeRef.current.src = iframeRef.current.src;
      setIsLoading(true);
      setError(null);
    }
  };

  const handleOpenExternal = () => {
    if (previewUrl) {
      window.open(previewUrl, '_blank');
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Preview Header */}
      <div className="flex items-center justify-between p-2 border-b">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Preview</span>
          {isLoading && <Loader className="w-4 h-4 animate-spin" />}
        </div>
        <div className="flex gap-1">
          <Button variant="ghost" size="icon" onClick={handleRefresh}>
            <RefreshCw className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleOpenExternal}>
            <ExternalLink className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Preview Content */}
      <div className="flex-1">
        <Tabs defaultValue="preview" className="h-full">
          <TabsList className="w-full">
            <TabsTrigger value="preview" className="flex-1">Preview</TabsTrigger>
            <TabsTrigger value="console" className="flex-1">
              Console
              {consoleLogs.length > 0 && (
                <span className="ml-2 text-xs bg-primary/20 px-1 rounded">
                  {consoleLogs.length}
                </span>
              )}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="preview" className="h-full">
            {error ? (
              <Alert variant="destructive" className="m-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : previewUrl ? (
              <iframe
                ref={iframeRef}
                src={previewUrl}
                className="w-full h-full border-0"
                onLoad={() => setIsLoading(false)}
                onError={() => {
                  setIsLoading(false);
                  setError('Failed to load preview');
                }}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <div className="text-center">
                  <p>No preview available</p>
                  <p className="text-sm">Start your development server to see the preview</p>
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="console" className="h-full">
            <ConsoleOutput logs={consoleLogs} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

interface ConsoleLog {
  id: string;
  type: 'log' | 'error' | 'warn' | 'info';
  message: string;
  timestamp: string;
}

const ConsoleOutput: React.FC<{ logs: ConsoleLog[] }> = ({ logs }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const getLogColor = (type: ConsoleLog['type']) => {
    switch (type) {
      case 'error':
        return 'text-red-500';
      case 'warn':
        return 'text-yellow-500';
      case 'info':
        return 'text-blue-500';
      default:
        return 'text-foreground';
    }
  };

  return (
    <ScrollArea className="h-full p-4 font-mono text-sm" ref={scrollRef}>
      {logs.length === 0 ? (
        <div className="text-muted-foreground">No console output</div>
      ) : (
        logs.map((log) => (
          <div key={log.id} className={`mb-2 ${getLogColor(log.type)}`}>
            <span className="text-muted-foreground text-xs">
              [{new Date(log.timestamp).toLocaleTimeString()}]
            </span>{' '}
            {log.message}
          </div>
        ))
      )}
    </ScrollArea>
  );
};

// ========================================
// frontend/src/components/agent/AgentTabs.tsx
// ========================================
import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader, CheckCircle, XCircle, Clock } from 'lucide-react';
import { useAgentStatus } from '@/hooks/useAgentStatus';
import { AgentType, Agent } from '@/types';

const AGENT_CONFIG: Record<AgentType, { label: string; icon: string; color: string }> = {
  dev_manager: { label: 'Dev Manager', icon: '👔', color: 'bg-blue-500' },
  product_manager: { label: 'Product Manager', icon: '📊', color: 'bg-purple-500' },
  data_analyst: { label: 'Data Analyst', icon: '📈', color: 'bg-green-500' },
  engineer: { label: 'Sr. Engineer', icon: '💻', color: 'bg-orange-500' },
  architect: { label: 'Architect', icon: '🏗️', color: 'bg-indigo-500' },
  platform_engineer: { label: 'Platform Eng', icon: '🔧', color: 'bg-red-500' },
};

export const AgentTabs: React.FC = () => {
  const { agents, conversations } = useAgentStatus();
  const [activeTab, setActiveTab] = useState<AgentType>('dev_manager');

  const getStatusIcon = (status: Agent['status']) => {
    switch (status) {
      case 'idle':
        return <Clock className="w-3 h-3" />;
      case 'thinking':
      case 'working':
        return <Loader className="w-3 h-3 animate-spin" />;
      case 'waiting':
        return <Clock className="w-3 h-3 text-yellow-500" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: Agent['status']) => {
    switch (status) {
      case 'idle':
        return 'default';
      case 'thinking':
        return 'secondary';
      case 'working':
        return 'default';
      case 'waiting':
        return 'outline';
      default:
        return 'default';
    }
  };

  return (
    <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as AgentType)} className="h-full">
      <TabsList className="grid grid-cols-6 w-full">
        {Object.entries(AGENT_CONFIG).map(([type, config]) => {
          const agent = agents[type as AgentType];
          const status = agent?.status || 'idle';
          
          return (
            <TabsTrigger key={type} value={type} className="flex items-center gap-2">
              <span>{config.icon}</span>
              <span className="hidden md:inline">{config.label}</span>
              <Badge variant={getStatusColor(status)} className="ml-1 h-5">
                {getStatusIcon(status)}
              </Badge>
            </TabsTrigger>
          );
        })}
      </TabsList>

      {Object.keys(AGENT_CONFIG).map((type) => {
        const agent = agents[type as AgentType];
        const conversation = conversations[type as AgentType];
        
        return (
          <TabsContent key={type} value={type} className="h-full mt-0">
            <AgentPanel agent={agent} conversation={conversation} />
          </TabsContent>
        );
      })}
    </Tabs>
  );
};

interface AgentPanelProps {
  agent?: Agent;
  conversation?: any[];
}

const AgentPanel: React.FC<AgentPanelProps> = ({ agent, conversation = [] }) => {
  if (!agent) {
    return <div className="p-4">Agent not available</div>;
  }

  return (
    <div className="h-full flex flex-col">
      {/* Agent Status Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold">{agent.name}</h3>
            <p className="text-sm text-muted-foreground">
              Status: {agent.status} {agent.currentTask && `- ${agent.currentTask}`}
            </p>
          </div>
          <div className="text-sm text-muted-foreground">
            Load: {agent.currentLoad} tasks
          </div>
        </div>
      </div>

      {/* Conversation/Activity Log */}
      <ScrollArea className="flex-1 p-4">
        {conversation.length === 0 ? (
          <div className="text-muted-foreground text-center">No activity yet</div>
        ) : (
          <div className="space-y-3">
            {conversation.map((entry, index) => (
              <div key={index} className="border-l-2 border-muted pl-4">
                <div className="text-sm text-muted-foreground">
                  {new Date(entry.timestamp).toLocaleTimeString()}
                </div>
                <div className="text-sm">{entry.message}</div>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
};