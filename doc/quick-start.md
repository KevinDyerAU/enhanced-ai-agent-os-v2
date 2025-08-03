# Quick Start Guide

Get up and running with Enhanced AI Agent OS v2 in minutes.

## Prerequisites

- Docker Desktop installed and running
- Git installed
- 8GB+ RAM available

## 5-Minute Setup

### 1. Clone and Configure

```bash
git clone https://github.com/your-org/enhanced-ai-agent-os-v2.git
cd enhanced-ai-agent-os-v2
cp .env.example .env
```

### 2. Add Essential API Keys

Edit `.env` and add at minimum:

```env
OPENROUTER_API_KEY=your_openrouter_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=your_pinecone_env
```

### 3. Start the System

```bash
docker-compose up -d
```

### 4. Access Mission Control

Open http://localhost:3000 in your browser.

## First Steps

### 1. Verify Services
Check that all services are healthy:
- Visit http://localhost:8000/health for core orchestration
- Visit http://localhost:3000 for the dashboard

### 2. Create Your First Content

1. **Generate Ideas**: Use the Ideation Agent
   ```bash
   curl -X POST http://localhost:8001/generate-ideas \
     -H "Content-Type: application/json" \
     -d '{"topic": "AI productivity tools", "target_audience": "tech professionals"}'
   ```

2. **Create Design**: Use the Design Agent
   ```bash
   curl -X POST http://localhost:8002/create-design \
     -H "Content-Type: application/json" \
     -d '{"design_type": "social_media_post", "content": "Your content here"}'
   ```

### 3. Monitor Activity

- **Grafana Dashboard**: http://localhost:3001 (admin/your_password)
- **Prometheus Metrics**: http://localhost:9090
- **API Documentation**: http://localhost:8000/docs

## Key Features to Try

### Content Creation Pipeline
1. Generate ideas with market intelligence
2. Create branded designs automatically
3. Produce video content with AI
4. Execute multi-platform campaigns

### Enterprise Governance
1. Set compliance rules
2. Review content in airlock system
3. Track audit logs
4. Monitor agent activity

### AI-Powered Search
1. Semantic search across content
2. Vector-based recommendations
3. Intelligent task routing
4. Knowledge base queries

## Common First Tasks

### Create a Marketing Campaign

1. **Generate Ideas**:
   - Topic: Your product/service
   - Audience: Your target market
   - Platform: LinkedIn, Twitter, etc.

2. **Design Assets**:
   - Use brand guidelines
   - Generate multiple variants
   - Review compliance scores

3. **Execute Campaign**:
   - Schedule posts
   - Monitor engagement
   - Track performance

### Set Up Governance

1. **Define Compliance Rules**:
   - Brand guidelines
   - Content policies
   - Approval workflows

2. **Configure Airlock**:
   - Review thresholds
   - Approval chains
   - Escalation rules

## Next Steps

- Read the full [User Guide](user-guide.md)
- Explore [API Reference](api-reference.md)
- Configure [Advanced Settings](configuration.md)
- Review [Architecture](architecture.md)

## Need Help?

- Check [Troubleshooting](troubleshooting.md)
- Review service logs: `docker-compose logs [service-name]`
- Verify health endpoints: `/health` on each service
