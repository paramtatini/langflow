# Technical Context: Langflow

## Technologies Used

### Backend Stack
- **Python 3.10-3.13**: Core runtime environment
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM with async support
- **Alembic**: Database migration tool
- **Pydantic**: Data validation using Python type annotations
- **uvicorn**: ASGI server for production deployment
- **pytest**: Testing framework with async support

### Frontend Stack
- **React 18**: Modern React with concurrent features
- **TypeScript**: Static type checking for JavaScript
- **Vite**: Fast build tool and development server
- **React Flow**: Visual node-based editor
- **Zustand**: Lightweight state management
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Icon library

### Package Management & Build Tools
- **uv**: Fast Python package installer and resolver
- **npm**: Node.js package manager for frontend
- **Make**: Build automation and task orchestration
- **Docker**: Containerization for deployment
- **Biome**: Frontend code formatting and linting

### Development Tools
- **Ruff**: Fast Python linter and formatter
- **MyPy**: Static type checker for Python
- **Pre-commit**: Git hooks for code quality
- **Docusaurus**: Documentation site generator

## Development Setup

### Prerequisites
- **Python**: 3.10 to 3.13 (required for compatibility)
- **Node.js**: v22.12 LTS for frontend development
- **uv**: Package manager (install via `pipx install uv`)
- **npm**: Comes with Node.js installation

### Environment Setup Commands
```bash
# Initialize project
make init                    # Install all dependencies and setup

# Backend development
make install_backend         # Install Python dependencies
make backend                 # Start backend server (port 7860)

# Frontend development
make install_frontend        # Install Node.js dependencies
make frontend               # Start frontend dev server (port 3000)

# Full development setup
make run_cli                # Build frontend and start full application
```

### Development Servers
- **Backend**: http://localhost:7860 (FastAPI with auto-reload)
- **Frontend**: http://localhost:3000 (Vite dev server with HMR)
- **Documentation**: http://localhost:3001 (Docusaurus dev server)

## Technical Constraints

### Python Version Compatibility
- **Minimum**: Python 3.10 (required for modern async features)
- **Maximum**: Python 3.13 (latest supported version)
- **Reason**: Balance between modern features and ecosystem compatibility

### Browser Support
- **Modern Browsers**: Chrome, Firefox, Safari, Edge (latest versions)
- **JavaScript**: ES2020+ features required
- **WebAssembly**: Not currently used but may be future consideration

### Database Support
- **Development**: SQLite (default, zero-config)
- **Production**: PostgreSQL (recommended for scalability)
- **Optional**: Other SQLAlchemy-supported databases

### Memory and Performance
- **Backend**: Async-first design for high concurrency
- **Frontend**: Code splitting and lazy loading for performance
- **Database**: Connection pooling and query optimization

## Dependencies

### Core Backend Dependencies
```toml
# Core framework and API
"langflow-base~=0.5.0"
"fastapi"
"uvicorn"
"sqlalchemy[aiosqlite]>=2.0.38,<3.0.0"
"pydantic-settings>=2.2.0,<3.0.0"

# AI and ML integrations
"langchain==0.3.23"
"langchain-community~=0.3.21"
"openai>=1.68.2"
"litellm>=1.60.2,<2.0.0"

# Vector databases and storage
"chromadb==0.5.23"
"qdrant-client==1.9.2"
"weaviate-client==4.10.2"
"faiss-cpu==1.9.0.post1"

# Data processing
"pandas"
"numpy"
"beautifulsoup4==4.12.3"
"pyarrow==19.0.0"
```

### Development Dependencies
```toml
# Testing
"pytest>=8.2.0"
"pytest-asyncio>=0.23.0"
"pytest-cov>=5.0.0"
"httpx>=0.28.1"

# Code quality
"ruff>=0.12.7"
"mypy>=1.11.0"
"pre-commit>=3.7.0"

# Type stubs
"types-requests>=2.32.0"
"types-pyyaml>=6.0.12.8"
```

### Frontend Dependencies
```json
{
  "react": "^18.x",
  "typescript": "^5.x",
  "vite": "^5.x",
  "tailwindcss": "^3.x",
  "zustand": "^4.x",
  "reactflow": "^11.x",
  "lucide-react": "^0.x"
}
```

## Tool Usage Patterns

### Development Workflow
```bash
# Daily development cycle
make format_backend          # Format Python code (run first!)
make lint                   # Run linting checks
make unit_tests             # Run backend tests
make tests_frontend         # Run frontend tests (if configured)

# Component development
make backend                # Start backend for component testing
# Edit component in UI, then save to source
# Backend auto-restarts, refresh browser to see changes
```

### Testing Patterns
```bash
# Unit testing
make unit_tests             # All unit tests
make unit_tests args="-k test_specific"  # Specific test

# Integration testing
make integration_tests      # Full integration suite
make integration_tests_no_api_keys  # Without external APIs

# Load testing
make locust                 # Performance testing with Locust
```

### Build and Deployment
```bash
# Local builds
make build_frontend         # Build frontend static files
make build                  # Build entire project

# Docker builds
make docker_build           # Build Docker image
make docker_compose_up      # Run with Docker Compose

# Version management
make patch v=1.6.1          # Update version across all packages
```

### Code Quality Automation
```bash
# Pre-commit setup (run once)
uvx pre-commit install

# Manual quality checks
make format_backend         # Auto-fix formatting issues
make codespell             # Check spelling
make fix_codespell         # Fix spelling errors
```

## Configuration Management

### Environment Variables
```bash
# Development (.env file)
LANGFLOW_DATABASE_URL=sqlite:///./langflow.db
LANGFLOW_LOG_LEVEL=DEBUG
LANGFLOW_AUTO_LOGIN=true

# Production
LANGFLOW_DATABASE_URL=postgresql://user:pass@host:port/db
LANGFLOW_LOG_LEVEL=INFO
LANGFLOW_SECRET_KEY=your-secret-key
```

### Configuration Files
- **pyproject.toml**: Python project configuration and dependencies
- **src/frontend/package.json**: Frontend dependencies and scripts
- **Makefile**: Build automation and development tasks
- **docker-compose.yml**: Container orchestration
- **.env.example**: Environment variable template

## Performance Optimization

### Backend Optimization
- **Async Operations**: All I/O operations use async/await
- **Database Connection Pooling**: SQLAlchemy connection management
- **Caching**: Component and result caching strategies
- **Background Tasks**: Non-blocking background processing

### Frontend Optimization
- **Code Splitting**: Dynamic imports for large components
- **Bundle Analysis**: Regular bundle size monitoring
- **State Management**: Efficient Zustand store patterns
- **Rendering**: React optimization techniques

### Build Optimization
- **Parallel Builds**: Frontend and backend build in parallel
- **Incremental Builds**: Only rebuild changed components
- **Docker Layer Caching**: Optimized Dockerfile layers
- **Asset Optimization**: Minification and compression

## Deployment Considerations

### Local Development
- **Hot Reload**: Both frontend and backend support hot reload
- **Database**: SQLite for zero-configuration development
- **CORS**: Configured for local development

### Production Deployment
- **Database**: PostgreSQL recommended for production
- **Reverse Proxy**: Nginx or similar for static file serving
- **Process Management**: systemd, Docker, or Kubernetes
- **Monitoring**: Structured logging and health checks

### Scaling Strategies
- **Horizontal Scaling**: Stateless backend design
- **Load Balancing**: Multiple backend instances
- **Database Scaling**: Read replicas and connection pooling
- **CDN**: Static asset distribution

## Security Configuration

### Development Security
- **CORS**: Permissive for local development
- **Authentication**: Optional auto-login for development
- **HTTPS**: Not required for local development

### Production Security
- **HTTPS**: Required for production deployment
- **CORS**: Restrictive origin policies
- **Authentication**: JWT-based authentication required
- **Environment Variables**: Secure secret management
- **Database**: Encrypted connections and credentials

## Troubleshooting Common Issues

### Development Environment
- **Port Conflicts**: Backend (7860), Frontend (3000), Docs (3001)
- **Python Version**: Ensure Python 3.10-3.13 compatibility
- **Node Version**: Use Node.js v22.12 LTS
- **uv Installation**: Install via pipx for proper isolation

### Build Issues
- **Frontend Build Failures**: Clear node_modules and reinstall
- **Backend Import Errors**: Run `uv sync` to update dependencies
- **Test Failures**: Some database tests may need individual execution
- **Docker Issues**: Clear Docker cache and rebuild images

### Performance Issues
- **Slow Backend**: Check database connection and query performance
- **Slow Frontend**: Analyze bundle size and component rendering
- **Memory Usage**: Monitor async task cleanup and resource management
