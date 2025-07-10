# Zeblit - AI-Powered Development Platform

<p align="center">
  <img src="docs/images/zeblit-logo.png" alt="Zeblit Logo" width="200">
</p>

<p align="center">
  <a href="https://github.com/zeblit/zeblit/actions"><img src="https://github.com/zeblit/zeblit/workflows/CI/CD/badge.svg" alt="CI/CD Status"></a>
  <a href="https://codecov.io/gh/zeblit/zeblit"><img src="https://codecov.io/gh/zeblit/zeblit/branch/main/graph/badge.svg" alt="Code Coverage"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="https://zeblit.com/docs"><img src="https://img.shields.io/badge/docs-latest-brightgreen.svg" alt="Documentation"></a>
</p>

## 🚀 Overview

Zeblit is an AI-powered development platform that enables users to build applications through natural language interactions with a team of specialized AI agents. Each user gets an isolated development container with full IDE capabilities, making coding accessible to everyone.

### Key Features

- **🤖 6 Specialized AI Agents**: Work with a team of AI experts (Dev Manager, Product Manager, Data Analyst, Engineer, Architect, Platform Engineer)
- **💻 Full IDE Experience**: Monaco editor, file explorer, terminal, and live preview
- **🔄 Real-time Collaboration**: WebSocket-based real-time updates and agent communication
- **📦 Isolated Containers**: Each project runs in its own secure container
- **🔌 Git Integration**: Full version control with agent-specific branches
- **📊 Cost Tracking**: Monitor AI usage and costs in real-time
- **🔒 Enterprise Security**: JWT authentication, rate limiting, and comprehensive audit logs

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  React Frontend │────▶│  FastAPI Backend│────▶│  AI Agents      │
│  (TypeScript)   │     │  (Python 3.12)  │     │  (Claude/GPT-4) │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│     Nginx       │     │   PostgreSQL    │     │   User          │
│   (Static/Proxy)│     │   (Database)    │     │   Containers    │
│                 │     │                 │     │   (Docker)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 🚦 Getting Started

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (or Bun)
- Python 3.12+
- PostgreSQL 16+
- Redis 7+

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/zeblit/zeblit.git
   cd zeblit
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the platform**
   - Frontend: http://localhost
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Development Setup

1. **Backend Setup**
   ```bash
   # Create Python virtual environment
   conda create -n zeblit python=3.12
   conda activate zeblit
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Run migrations
   alembic upgrade head
   
   # Seed initial data
   python -m src.backend.seed_data
   
   # Start backend
   python -m uvicorn src.backend.main:app --reload
   ```

2. **Frontend Setup**
   ```bash
   # Navigate to frontend
   cd frontend
   
   # Install dependencies (using Bun)
   bun install
   
   # Start development server
   bun run dev
   ```

## 📁 Project Structure

```
zeblit/
├── src/backend/          # Python FastAPI backend
│   ├── api/             # REST API endpoints
│   ├── agents/          # AI agent implementations
│   ├── services/        # Business logic
│   ├── models/          # SQLAlchemy models
│   ├── repositories/    # Data access layer
│   └── core/           # Core utilities
├── frontend/            # React TypeScript frontend
│   ├── src/
│   │   ├── components/ # UI components
│   │   ├── pages/      # Route pages
│   │   ├── hooks/      # Custom hooks
│   │   └── lib/        # Utilities
│   └── e2e/            # Playwright tests
├── k8s/                # Kubernetes manifests
├── scripts/            # Utility scripts
└── docs/              # Documentation
```

## 🧪 Testing

### Backend Tests
```bash
pytest src/backend/tests -v --cov=src/backend
```

### Frontend Tests
```bash
cd frontend
bun test
```

### E2E Tests
```bash
cd frontend
bunx playwright test
```

### Load Testing
```bash
locust -f load_test.py --host http://localhost:8000
```

## 🚀 Deployment

### Using Kubernetes

1. **Build and push images**
   ```bash
   docker build -f Dockerfile.backend -t zeblit/backend:latest .
   docker build -f Dockerfile.frontend -t zeblit/frontend:latest .
   docker push zeblit/backend:latest
   docker push zeblit/frontend:latest
   ```

2. **Deploy to Kubernetes**
   ```bash
   kubectl apply -k k8s/overlays/production
   ```

3. **Verify deployment**
   ```bash
   kubectl get pods -n production
   kubectl get svc -n production
   ```

### Using Docker Compose (Production)
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Monitoring

The platform includes comprehensive monitoring with Prometheus and Grafana:

- **Metrics**: Application metrics, response times, error rates
- **Logs**: Centralized logging with Loki
- **Alerts**: Automated alerts for critical issues
- **Dashboards**: Pre-configured Grafana dashboards

Access monitoring:
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

## 🔒 Security

- **Authentication**: JWT-based authentication
- **Authorization**: Role-based access control (RBAC)
- **Encryption**: TLS/SSL for all communications
- **Secrets**: Kubernetes secrets management
- **Audit**: Comprehensive audit logging
- **Rate Limiting**: API rate limiting per user
- **Container Isolation**: Secure container sandboxing

## 📚 API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ using FastAPI, React, and TypeScript
- AI powered by Anthropic Claude and OpenAI
- Infrastructure powered by Kubernetes and Docker

## 📞 Support

- **Documentation**: [https://zeblit.com/docs](https://zeblit.com/docs)
- **Issues**: [GitHub Issues](https://github.com/zeblit/zeblit/issues)
- **Discord**: [Join our community](https://discord.gg/zeblit)
- **Email**: support@zeblit.com

---

<p align="center">Made with ❤️ by the Zeblit Team</p> 