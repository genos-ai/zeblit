# 📚 Zeblit AI Development Platform - Documentation

*Comprehensive documentation for the Zeblit AI Development Platform*

## 🎯 **Quick Navigation**

### 🚀 **New to Zeblit?** Start Here:
- [**Development Setup**](./01-getting-started/development-setup.md) - Get your environment ready
- [**Architecture Overview**](./02-architecture/architecture-summary.md) - Understand the system design
- [**Backend Setup**](./01-getting-started/backend-setup.md) - Setup the backend services

### 🔧 **For Developers:**
- [**Backend Documentation**](./03-backend/README.md) - API, database, configuration
- [**Agent System**](./04-agents/README.md) - AI agent architecture and development
- [**Testing Guide**](./06-development/testing/test-guide.md) - Testing strategies and tools

### 📱 **For Client Development:**
- [**Web Interface**](./05-clients/web-interface/README.md) - React frontend implementation
- [**CLI Client**](./05-clients/cli-client/README.md) - Command-line interface
- [**Telegram Bot**](./05-clients/telegram-bot/README.md) - Bot implementation

---

## 📂 **Documentation Structure**

### **01-getting-started/** - Setup & Quick Start
Quick setup guides and troubleshooting for new developers.
- [Development Setup](./01-getting-started/development-setup.md)
- [Backend Setup](./01-getting-started/backend-setup.md)
- [Production Deployment](./01-getting-started/production-deployment.md)
- [Troubleshooting](./01-getting-started/troubleshooting.md)

### **02-architecture/** - System Design
High-level architecture and design decisions.
- [Architecture Summary](./02-architecture/architecture-summary.md)
- [Backend-First Approach](./02-architecture/backend-first-approach.md)
- [Diagrams](./02-architecture/diagrams/) - Visual architecture representations

### **03-backend/** - Backend Implementation
Complete backend documentation including API, database, and configuration.
- [API Documentation](./03-backend/api/README.md)
- [Database Schema](./03-backend/database/README.md)
- [Configuration](./03-backend/configuration/README.md)
- [Deployment](./03-backend/deployment/README.md)

### **04-agents/** - AI Agent System
Everything about the AI agents that power the platform.
- [Agent Overview](./04-agents/overview/README.md)
- [Individual Agents](./04-agents/individual-agents/) - Documentation for each agent
- [Development Guide](./04-agents/development/README.md)

### **05-clients/** - Client Implementations
Documentation for all client interfaces (web, CLI, mobile).
- [Web Interface](./05-clients/web-interface/README.md)
- [CLI Client](./05-clients/cli-client/README.md)
- [Telegram Bot](./05-clients/telegram-bot/README.md)

### **06-development/** - Development Workflows
Development processes, testing, debugging, and tools.
- [Workflow](./06-development/workflow/README.md)
- [Testing](./06-development/testing/README.md)
- [Debugging](./06-development/debugging/README.md)
- [Tools](./06-development/tools/README.md)

### **07-implementation/** - Project Tracking
Implementation phases, checklists, and progress reports.
- [Implementation Phases](./07-implementation/phases/README.md)
- [Checklists](./07-implementation/checklists/README.md)
- [Reports](./07-implementation/reports/README.md)

### **08-reference/** - Quick Reference
API references, style guides, and external documentation.
- [API Reference](./08-reference/api-reference/README.md)
- [Style Guides](./08-reference/style-guides/README.md)
- [External Documents](./08-reference/external/README.md)

---

## 🎯 **Platform Overview**

### **What is Zeblit?**
Zeblit is a browser-based AI development platform that enables users to build applications through natural language conversations with specialized AI agents.

### **Key Features:**
- **🤖 7 Specialized AI Agents**: Development Manager, Product Manager, Data Analyst, Senior Engineer, System Architect, Platform Engineer, Security Engineer
- **🌐 Backend-First Architecture**: All business logic in the backend, clients as thin presentation layers
- **📱 Multiple Clients**: Web interface, CLI client, Telegram bot
- **🔒 Enterprise Security**: Comprehensive security assessment and compliance
- **⚡ Real-time Collaboration**: WebSocket-based real-time updates
- **🐳 Container Integration**: OrbStack/Docker for isolated execution environments

### **Technology Stack:**
- **Backend**: Python + FastAPI + PostgreSQL + Redis
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **AI**: Claude Sonnet 4, GPT-4, with multi-provider support
- **Infrastructure**: Docker + Kubernetes ready
- **Testing**: Comprehensive test suite with 100% coverage

---

## 🚀 **Getting Started**

### **Prerequisites:**
- Python 3.12+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- Git

### **Quick Start:**
```bash
# 1. Clone the repository
git clone https://github.com/your-org/zeblit.git
cd zeblit

# 2. Setup backend
cd modules/backend
pip install -r requirements.txt
python start_backend.py

# 3. Setup CLI client
cd clients/zeblit-cli
pip install -e .
zeblit auth login

# 4. Start building!
zeblit create my-app --template=python-web
zeblit chat "Build a todo API with authentication"
```

### **Next Steps:**
1. [**Complete Development Setup**](./01-getting-started/development-setup.md)
2. [**Understand the Architecture**](./02-architecture/architecture-summary.md)
3. [**Explore the Agents**](./04-agents/README.md)
4. [**Try the CLI Client**](./05-clients/cli-client/README.md)

---

## 📖 **Documentation for AI Models**

This documentation is structured to provide optimal context for AI coding assistants:

### **For Understanding Architecture:**
- Start with [Architecture Summary](./02-architecture/architecture-summary.md)
- Review [Backend-First Approach](./02-architecture/backend-first-approach.md)
- Check [Database Schema](./03-backend/database/schema-documentation.md)

### **For Agent Development:**
- [Agent System Overview](./04-agents/overview/agent-system.md)
- [Individual Agent Documentation](./04-agents/individual-agents/)
- [Agent Development Patterns](./04-agents/development/agent-patterns.md)

### **For API Integration:**
- [API Endpoints](./03-backend/api/endpoints.md)
- [Authentication](./03-backend/api/authentication.md)
- [API Reference](./08-reference/api-reference/)

### **For Client Development:**
- [Web Interface Components](./05-clients/web-interface/component-structure.md)
- [CLI Client Architecture](./05-clients/cli-client/README.md)
- [WebSocket Protocol](./06-development/debugging/websocket-protocol.md)

---

## 🤝 **Contributing**

### **Development Workflow:**
1. Read [Implementation Plan](./06-development/workflow/implementation-plan.md)
2. Follow [Testing Strategy](./06-development/testing/testing-strategy.md)
3. Use [Style Guides](./08-reference/style-guides/)

### **Adding Documentation:**
- Place files in appropriate numbered folders
- Update relevant README files
- Follow the established naming conventions
- Include clear examples and context

---

## 📞 **Support & Resources**

- **Troubleshooting**: [Debugging Guide](./01-getting-started/troubleshooting.md)
- **Testing**: [Comprehensive Test Guide](./06-development/testing/test-guide.md)
- **Style Guidelines**: [Frontend](./08-reference/style-guides/frontend-style-guide.md)
- **Project Status**: [Current Status](./07-implementation/reports/project-status.md)

---

*Last Updated: January 15, 2025*
*Documentation Version: 2.0.0*
