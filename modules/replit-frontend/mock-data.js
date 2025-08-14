export const mockProjects = [
  {
    id: "1",
    name: "AI Chat Assistant",
    description: "A sophisticated chatbot powered by GPT-4 with custom training on company documentation",
    framework: "Next.js",
    language: "TypeScript",
    created_at: "2024-01-15T10:30:00Z",
    updated_at: "2024-01-20T14:45:00Z",
    status: "active",
    container_status: "running",
    git_initialized: true,
    is_public: false,
    owner_id: "user1",
    preview_url: "https://ai-chat-demo.replit.app"
  },
  {
    id: "2",
    name: "E-commerce Dashboard",
    description: "Real-time analytics dashboard for monitoring sales, inventory, and customer behavior",
    framework: "React",
    language: "JavaScript",
    created_at: "2024-01-10T08:00:00Z",
    updated_at: "2024-01-18T16:20:00Z",
    status: "active",
    container_status: "stopped",
    git_initialized: true,
    is_public: true,
    owner_id: "user1",
    preview_url: null
  },
  {
    id: "3",
    name: "ML Model API",
    description: "FastAPI service for serving machine learning models with automatic scaling",
    framework: "FastAPI",
    language: "Python",
    created_at: "2024-01-05T12:00:00Z",
    updated_at: "2024-01-12T09:30:00Z",
    status: "active",
    container_status: "running",
    git_initialized: true,
    is_public: false,
    owner_id: "user1",
    preview_url: "https://ml-api-demo.replit.app"
  },
  {
    id: "4",
    name: "Mobile App Backend",
    description: "GraphQL API backend for a social media mobile application",
    framework: "Express",
    language: "TypeScript",
    created_at: "2023-12-20T15:45:00Z",
    updated_at: "2024-01-08T11:15:00Z",
    status: "active",
    container_status: "starting",
    git_initialized: false,
    is_public: false,
    owner_id: "user1",
    preview_url: null
  }
];

export const mockUser = {
  id: "user1",
  email: "demo@zeblit.com",
  full_name: "Demo User",
  role: "developer",
  is_active: true,
  created_at: "2023-12-01T00:00:00Z"
};

export const mockTemplates = [
  {
    id: "1",
    name: "Next.js Full Stack",
    description: "Modern full-stack application with Next.js, TypeScript, and Tailwind CSS",
    template_type: "nextjs-fullstack",
    category: "fullstack",
    language: "TypeScript",
    framework: "Next.js",
    icon: "⚡"
  },
  {
    id: "2",
    name: "FastAPI + React",
    description: "Python backend with React frontend, perfect for data-driven applications",
    template_type: "fastapi-react",
    category: "fullstack",
    language: "Python",
    framework: "FastAPI",
    icon: "🐍"
  },
  {
    id: "3",
    name: "Express API",
    description: "RESTful API with Express.js, MongoDB, and JWT authentication",
    template_type: "express-api",
    category: "backend",
    language: "JavaScript",
    framework: "Express",
    icon: "🚀"
  },
  {
    id: "4",
    name: "React SPA",
    description: "Single-page application with React, React Router, and modern tooling",
    template_type: "react-spa",
    category: "frontend",
    language: "JavaScript",
    framework: "React",
    icon: "⚛️"
  }
];

export const mockAgents = [
  {
    id: "1",
    name: "Development Manager",
    agent_type: "dev_manager",
    description: "Orchestrates the development workflow and coordinates other agents",
    status: "active",
    default_model: "claude-3-opus",
    capabilities: ["task_planning", "code_review", "deployment"]
  },
  {
    id: "2",
    name: "Senior Engineer",
    agent_type: "engineer",
    description: "Writes high-quality code and implements features",
    status: "active",
    default_model: "claude-3-sonnet",
    capabilities: ["code_generation", "debugging", "refactoring"]
  },
  {
    id: "3",
    name: "UI/UX Designer",
    agent_type: "designer",
    description: "Creates beautiful and intuitive user interfaces",
    status: "active",
    default_model: "claude-3-sonnet",
    capabilities: ["ui_design", "ux_optimization", "accessibility"]
  }
]; 