# Installation Guide

This guide provides step-by-step instructions for installing and setting up the Enhanced AI Agent OS v2.

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space
- **CPU**: 4 cores minimum, 8 cores recommended
- **Network**: Stable internet connection for API integrations

### Required Software
- **Docker Desktop**: Version 4.0 or higher
- **Docker Compose**: Version 2.0 or higher
- **Git**: Latest version
- **Node.js**: Version 16+ (for UI development)
- **Python**: Version 3.9+ (for service development)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/enhanced-ai-agent-os-v2.git
cd enhanced-ai-agent-os-v2
```

### 2. Environment Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit the `.env` file with your specific configuration:

```env
# Database Configuration
POSTGRES_DB=ai_agent_os
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# API Keys (Required)
OPENROUTER_API_KEY=your_openrouter_api_key
CANVA_API_KEY=your_canva_api_key
DESCRIPT_API_KEY=your_descript_api_key
LINKEDIN_API_KEY=your_linkedin_api_key

# Vector Database
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment

# Monitoring
GRAFANA_ADMIN_PASSWORD=your_grafana_password
```

### 3. Docker Setup

Start all services using Docker Compose:

```bash
docker-compose up -d
```

This will start the following services:
- PostgreSQL Database (port 5432)
- Core Orchestration Agent (port 8000)
- Creator Layer Services (ports 8001-8004)
- Enterprise Layer Services (ports 8005-8007)
- Data Architecture Services (ports 8008-8009)
- React UI (port 3000)
- Monitoring Stack (Prometheus: 9090, Grafana: 3001)

### 4. Verify Installation

Check that all services are running:

```bash
docker-compose ps
```

All services should show as "Up" status.

### 5. Access the System

- **Mission Control Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Monitoring (Grafana)**: http://localhost:3001
- **Metrics (Prometheus)**: http://localhost:9090

## API Key Setup

### OpenRouter API Key
1. Visit [OpenRouter](https://openrouter.ai/)
2. Create an account and generate an API key
3. Add to your `.env` file

### Canva API Key
1. Visit [Canva Developers](https://www.canva.com/developers/)
2. Create an app and get your API key
3. Add to your `.env` file

### Descript API Key
1. Visit [Descript API](https://www.descript.com/api)
2. Generate an API key
3. Add to your `.env` file

### LinkedIn API Key
1. Visit [LinkedIn Developers](https://developer.linkedin.com/)
2. Create an app and get API credentials
3. Add to your `.env` file

### Pinecone API Key
1. Visit [Pinecone](https://www.pinecone.io/)
2. Create a project and get your API key
3. Add to your `.env` file

## Database Initialization

The database will be automatically initialized when you first start the services. The schema includes:

- `agents` - Agent configurations and metadata
- `tasks` - Task definitions and status
- `content_items` - Generated content storage
- `campaigns` - Marketing campaign data
- `compliance_rules` - Enterprise governance rules
- `audit_logs` - System activity tracking
- `vector_embeddings` - AI-generated embeddings
- `knowledge_base` - Organizational knowledge
- `workflows` - Process definitions
- `integrations` - External service configurations

## Troubleshooting Installation

### Common Issues

**Docker not starting:**
- Ensure Docker Desktop is running
- Check available system resources
- Verify port availability

**Environment variables not loading:**
- Verify `.env` file exists in project root
- Check file permissions
- Ensure no syntax errors in `.env`

**API key errors:**
- Verify all required API keys are configured
- Check API key validity and permissions
- Ensure proper formatting in `.env` file

**Database connection issues:**
- Wait for PostgreSQL container to fully initialize
- Check database credentials in `.env`
- Verify network connectivity between containers

### Getting Help

If you encounter issues during installation:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review Docker logs: `docker-compose logs [service-name]`
3. Verify system requirements are met
4. Check the project's issue tracker for known problems

## Next Steps

After successful installation:

1. Read the [Quick Start Guide](quick-start.md)
2. Explore the [User Guide](user-guide.md)
3. Review the [Configuration Guide](configuration.md)
4. Check out the [API Reference](api-reference.md)
