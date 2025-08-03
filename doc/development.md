# Development Guide

Guide for developers working on the Enhanced AI Agent OS v2 system.

## Development Environment Setup

### Prerequisites

- **Docker Desktop**: Latest version
- **Git**: Latest version
- **Python**: 3.9+ (for local development)
- **Node.js**: 16+ (for UI development)
- **IDE**: VS Code recommended with extensions:
  - Python
  - Docker
  - REST Client
  - GitLens

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/enhanced-ai-agent-os-v2.git
cd enhanced-ai-agent-os-v2

# Set up development environment
cp .env.example .env.development
# Edit .env.development with development settings

# Start development stack
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Development Configuration

```env
# .env.development
DEBUG_MODE=true
LOG_LEVEL=DEBUG
ENABLE_CORS=true
AUTO_RELOAD=true
MOCK_EXTERNAL_APIS=true
HOT_RELOAD=true
```

## Project Structure

```
enhanced-ai-agent-os-v2/
├── services/
│   ├── core_services/
│   │   └── orchestration/          # Core orchestration service
│   ├── creator_layer/
│   │   ├── ideation/               # Ideation agent
│   │   ├── design/                 # Design agent
│   │   ├── video/                  # Video agent
│   │   └── social_media/           # Social media manager
│   ├── enterprise_layer/
│   │   ├── compliance/             # Compliance engine
│   │   ├── audit/                  # Audit service
│   │   └── governance/             # Governance dashboard
│   ├── data_architecture/
│   │   ├── vector_search/          # Vector search service
│   │   └── memory_system/          # Memory system service
│   └── shared/
│       ├── database/               # Database models and migrations
│       ├── auth/                   # Authentication utilities
│       └── utils/                  # Common utilities
├── ui/                             # React frontend
├── deployment/                     # Deployment configurations
├── doc/                           # Documentation
├── tests/                         # Test suites
└── scripts/                       # Utility scripts
```

## Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/new-agent-capability

# Make changes to service
cd services/creator_layer/ideation/

# Test locally
docker-compose up -d ideation_agent
curl http://localhost:8001/health

# Run tests
python -m pytest tests/

# Commit changes
git add .
git commit -m "feat: add new ideation capability"
git push origin feature/new-agent-capability
```

### 2. Service Development

#### Creating a New Service

```python
# services/new_service/main.py
from fastapi import FastAPI
from shared.auth import AuthMiddleware
from shared.database import get_db_connection

app = FastAPI(title="New Service", version="1.0.0")
app.add_middleware(AuthMiddleware)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "new_service"}

@app.post("/api/v1/process")
async def process_data(data: dict):
    # Service logic here
    return {"result": "processed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
```

#### Service Configuration

```dockerfile
# services/new_service/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8010

CMD ["python", "main.py"]
```

```yaml
# Add to docker-compose.yml
services:
  new_service:
    build: ./services/new_service
    ports:
      - "8010:8010"
    environment:
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - postgres
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8010/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 3. Database Development

#### Creating Migrations

```python
# shared/database/migrations/001_create_new_table.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'new_table',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )

def downgrade():
    op.drop_table('new_table')
```

#### Running Migrations

```bash
# Generate migration
docker-compose exec core_orchestration alembic revision --autogenerate -m "Add new table"

# Apply migrations
docker-compose exec core_orchestration alembic upgrade head

# Rollback migration
docker-compose exec core_orchestration alembic downgrade -1
```

## Testing

### Unit Testing

```python
# tests/unit/test_ideation_agent.py
import pytest
from unittest.mock import Mock, patch
from services.creator_layer.ideation.main import IdeationAgent

class TestIdeationAgent:
    @pytest.fixture
    def agent(self):
        return IdeationAgent(config={"api_key": "test_key"})
    
    @patch('services.creator_layer.ideation.main.OpenRouterClient')
    def test_generate_ideas(self, mock_client, agent):
        # Mock external API response
        mock_client.return_value.generate.return_value = {
            "ideas": [{"title": "Test Idea", "description": "Test Description"}]
        }
        
        result = agent.generate_ideas("test topic", "test audience")
        
        assert len(result["ideas"]) == 1
        assert result["ideas"][0]["title"] == "Test Idea"
```

### Integration Testing

```python
# tests/integration/test_content_pipeline.py
import pytest
import requests

class TestContentPipeline:
    def test_full_content_creation_pipeline(self):
        # Test ideation
        ideation_response = requests.post(
            "http://localhost:8001/generate-ideas",
            json={"topic": "AI productivity", "target_audience": "developers"}
        )
        assert ideation_response.status_code == 200
        ideas = ideation_response.json()["ideas"]
        
        # Test design creation
        design_response = requests.post(
            "http://localhost:8002/create-design",
            json={"design_type": "social_media_post", "content": ideas[0]["title"]}
        )
        assert design_response.status_code == 200
        
        # Test compliance check
        compliance_response = requests.post(
            "http://localhost:8005/check-compliance",
            json={"content": {"text": ideas[0]["title"]}}
        )
        assert compliance_response.status_code == 200
```

### Running Tests

```bash
# Run all tests
docker-compose exec core_orchestration python -m pytest

# Run specific test file
docker-compose exec core_orchestration python -m pytest tests/unit/test_ideation_agent.py

# Run with coverage
docker-compose exec core_orchestration python -m pytest --cov=services

# Run integration tests
docker-compose exec core_orchestration python -m pytest tests/integration/
```

## API Development

### API Standards

#### Request/Response Format

```python
# Standard response format
from pydantic import BaseModel
from typing import Optional, List

class StandardResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    request_id: str

class PaginatedResponse(BaseModel):
    success: bool
    data: List[dict]
    pagination: dict
    request_id: str
```

#### Error Handling

```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse

class APIError(Exception):
    def __init__(self, status_code: int, message: str, details: dict = None):
        self.status_code = status_code
        self.message = message
        self.details = details

@app.exception_handler(APIError)
async def api_error_handler(request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "details": exc.details,
                "request_id": request.headers.get("X-Request-ID")
            }
        }
    )
```

#### Authentication

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/protected-endpoint")
async def protected_endpoint(current_user: str = Depends(get_current_user)):
    return {"user_id": current_user}
```

## Frontend Development

### React Development Setup

```bash
# Navigate to UI directory
cd ui/

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

### Component Development

```jsx
// ui/src/components/AgentStatus.jsx
import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Chip } from '@mui/material';

const AgentStatus = ({ agentName, port }) => {
  const [status, setStatus] = useState('unknown');
  const [lastCheck, setLastCheck] = useState(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`http://localhost:${port}/health`);
        const data = await response.json();
        setStatus(data.status);
        setLastCheck(new Date());
      } catch (error) {
        setStatus('error');
        setLastCheck(new Date());
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, [port]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6">{agentName}</Typography>
        <Chip 
          label={status} 
          color={getStatusColor(status)} 
          size="small" 
        />
        {lastCheck && (
          <Typography variant="caption" display="block">
            Last checked: {lastCheck.toLocaleTimeString()}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default AgentStatus;
```

## Code Quality

### Linting and Formatting

```bash
# Python code formatting
docker-compose exec core_orchestration black .
docker-compose exec core_orchestration isort .
docker-compose exec core_orchestration flake8 .

# JavaScript/React formatting
cd ui/
npm run lint
npm run format
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
```

### Code Review Guidelines

1. **Functionality**: Does the code work as intended?
2. **Readability**: Is the code easy to understand?
3. **Performance**: Are there any performance concerns?
4. **Security**: Are there any security vulnerabilities?
5. **Testing**: Are there adequate tests?
6. **Documentation**: Is the code properly documented?

## Debugging

### Local Debugging

```python
# Add debugging to service
import pdb; pdb.set_trace()  # Python debugger

# Or use logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.post("/debug-endpoint")
async def debug_endpoint(data: dict):
    logger.debug(f"Received data: {data}")
    # Process data
    logger.debug(f"Processed result: {result}")
    return result
```

### Remote Debugging

```python
# For remote debugging with VS Code
import debugpy
debugpy.listen(("0.0.0.0", 5678))
debugpy.wait_for_client()  # Optional: wait for debugger to attach
```

```yaml
# Add to docker-compose.dev.yml
services:
  core_orchestration:
    ports:
      - "8000:8000"
      - "5678:5678"  # Debug port
    environment:
      - PYTHONPATH=/app
      - DEBUGPY_ENABLED=true
```

## Performance Optimization

### Profiling

```python
# Profile API endpoints
import cProfile
import pstats

@app.middleware("http")
async def profile_middleware(request, call_next):
    if request.url.path.startswith("/api/"):
        pr = cProfile.Profile()
        pr.enable()
        response = await call_next(request)
        pr.disable()
        
        # Save profile data
        pr.dump_stats(f"profile_{request.url.path.replace('/', '_')}.prof")
        return response
    return await call_next(request)
```

### Database Optimization

```python
# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True
)
```

### Caching

```python
# Implement caching
from functools import lru_cache
import redis

redis_client = redis.Redis(host='redis', port=6379, db=0)

@lru_cache(maxsize=128)
def expensive_computation(param):
    # Expensive operation
    return result

def cached_api_call(key, func, *args, **kwargs):
    cached_result = redis_client.get(key)
    if cached_result:
        return json.loads(cached_result)
    
    result = func(*args, **kwargs)
    redis_client.setex(key, 3600, json.dumps(result))  # Cache for 1 hour
    return result
```

## Deployment

### Development Deployment

```bash
# Deploy to development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Update single service
docker-compose up -d --build ideation_agent
```

### Production Deployment

```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Deploy to production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### CI/CD Pipeline

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          docker-compose up -d
          docker-compose exec -T core_orchestration python -m pytest
      - name: Run linting
        run: |
          docker-compose exec -T core_orchestration black --check .
          docker-compose exec -T core_orchestration flake8 .

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          # Deployment commands
```

## Contributing

### Contribution Guidelines

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests for new functionality**
5. **Update documentation**
6. **Submit a pull request**

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Integration tests updated

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
```

### Release Process

1. **Version Bump**: Update version numbers
2. **Changelog**: Update CHANGELOG.md
3. **Testing**: Run full test suite
4. **Tag Release**: Create git tag
5. **Deploy**: Deploy to production
6. **Monitor**: Monitor deployment health
