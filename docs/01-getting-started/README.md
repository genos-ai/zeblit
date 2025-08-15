# 🚀 Getting Started with Zeblit

*Everything you need to get up and running with the Zeblit AI Development Platform*

## 📋 **Setup Checklist**

### **Prerequisites**
- [ ] Python 3.12+ installed
- [ ] Node.js 20+ installed  
- [ ] PostgreSQL 15+ running
- [ ] Redis 7+ running
- [ ] Git configured
- [ ] Code editor ready (VS Code recommended)

### **Quick Setup Path**
1. **[Development Setup](./development-setup.md)** - Complete local environment setup
2. **[Backend Setup](./backend-setup.md)** - Start the backend services
3. **[CLI Installation](../05-clients/cli-client/README.md)** - Install and configure CLI
4. **[First Project](../05-clients/cli-client/commands.md)** - Create your first project

---

## 📖 **Documentation Index**

### **[development-setup.md](./development-setup.md)**
Complete guide for setting up your development environment including:
- Installing dependencies (Python, Node.js, PostgreSQL, Redis)
- Configuring environment variables
- Database initialization
- Running development servers
- Verification steps

### **[backend-setup.md](./backend-setup.md)**  
Backend-specific setup instructions covering:
- Python virtual environment setup
- Installing backend dependencies
- Database configuration and migrations
- Starting the FastAPI server
- API health checks

### **[production-deployment.md](./production-deployment.md)**
Production deployment checklist including:
- Environment preparation
- Security configurations
- Database setup and migrations
- Container deployment
- Monitoring and logging
- Performance optimization

### **[troubleshooting.md](./troubleshooting.md)**
Common issues and solutions:
- Connection problems
- Database issues  
- Authentication errors
- Performance troubleshooting
- Debugging tools and techniques

---

## ⚡ **Quick Start Commands**

### **Backend Startup**
```bash
# Navigate to project root
cd zeblit

# Start backend with health checks
python start_backend.py --check-only  # Verify setup
python start_backend.py              # Start server
```

### **CLI Client Setup**
```bash
# Install CLI client
cd clients/zeblit-cli
pip install -e .

# Login and verify
zeblit auth login
zeblit project list
```

### **Create First Project**
```bash
# Create a new project
zeblit create my-first-app --template=python-web

# Start chatting with agents
zeblit chat "Create a simple REST API with user authentication"
```

---

## 🎯 **What's Next?**

### **For Developers:**
1. [**Understand the Architecture**](../02-architecture/README.md)
2. [**Explore the Agent System**](../04-agents/README.md)  
3. [**Review Testing Strategy**](../06-development/testing/README.md)

### **For Users:**
1. [**Try the Web Interface**](../05-clients/web-interface/README.md)
2. [**Learn CLI Commands**](../05-clients/cli-client/commands.md)
3. [**Explore Project Templates**](../05-clients/README.md)

### **For Contributors:**
1. [**Development Workflow**](../06-development/workflow/README.md)
2. [**Coding Standards**](../08-reference/style-guides/README.md)
3. [**Testing Guidelines**](../06-development/testing/testing-strategy.md)

---

## 🆘 **Need Help?**

- **🐛 Issues**: Check [troubleshooting.md](./troubleshooting.md)
- **💬 Questions**: Review [debugging guide](./troubleshooting.md)
- **📖 Documentation**: Browse the [main docs](../README.md)
- **🔧 Development**: See [development workflows](../06-development/README.md)

---

## 📊 **Verification Steps**

After setup, verify everything works:

```bash
# Check backend health
curl http://localhost:8000/health

# Test CLI authentication  
zeblit auth status

# Run comprehensive tests
python test_comprehensive.py

# Verify agent system
zeblit project create test-project
zeblit chat "Hello, can you help me build an app?"
```

**All green?** You're ready to build with Zeblit! 🎉

---

*Setup taking too long? Check our [troubleshooting guide](./troubleshooting.md) for common solutions.*
