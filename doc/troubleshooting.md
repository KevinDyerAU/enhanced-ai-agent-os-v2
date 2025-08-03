# Troubleshooting Guide

Common issues, solutions, and debugging procedures for the Enhanced AI Agent OS v2.

## Quick Diagnostics

### Health Check All Services

```bash
# Check all service health endpoints
curl http://localhost:8000/health  # Core Orchestration
curl http://localhost:8001/health  # Ideation Agent
curl http://localhost:8002/health  # Design Agent
curl http://localhost:8003/health  # Video Agent
curl http://localhost:8004/health  # Social Media Manager
curl http://localhost:8005/health  # Compliance Engine
curl http://localhost:8006/health  # Audit Service
curl http://localhost:8007/health  # Governance Dashboard
curl http://localhost:8008/health  # Vector Search
curl http://localhost:8009/health  # Memory System
```

### Docker Service Status

```bash
# Check container status
docker-compose ps

# View service logs
docker-compose logs [service-name]

# Follow logs in real-time
docker-compose logs -f [service-name]

# Check resource usage
docker stats
```

## Common Issues

### 1. Services Won't Start

#### Symptoms
- Containers exit immediately
- "Connection refused" errors
- Services show as "Exited" in `docker-compose ps`

#### Diagnosis
```bash
# Check container logs
docker-compose logs core_orchestration

# Check for port conflicts
netstat -tulpn | grep :8000

# Verify environment variables
docker-compose exec core_orchestration env | grep -E "(API_KEY|DATABASE)"
```

#### Solutions

**Missing Environment Variables**:
```bash
# Verify .env file exists
ls -la .env

# Check required variables
grep -E "(OPENROUTER_API_KEY|POSTGRES_PASSWORD)" .env
```

**Port Conflicts**:
```bash
# Find processes using ports
lsof -i :8000
lsof -i :3000

# Kill conflicting processes
sudo kill -9 [PID]
```

**Docker Issues**:
```bash
# Restart Docker Desktop
# On Windows: Restart Docker Desktop application
# On Linux: sudo systemctl restart docker

# Clean Docker cache
docker system prune -a

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 2. Database Connection Issues

#### Symptoms
- "Connection to database failed" errors
- Services can't connect to PostgreSQL
- Database-related health checks fail

#### Diagnosis
```bash
# Check PostgreSQL container
docker-compose logs postgres

# Test database connection
docker-compose exec postgres psql -U postgres -d ai_agent_os -c "SELECT 1;"

# Check database configuration
docker-compose exec core_orchestration python -c "
from config import settings
print(f'Database URL: {settings.DATABASE_URL}')
"
```

#### Solutions

**Database Not Ready**:
```bash
# Wait for database initialization
docker-compose logs postgres | grep "database system is ready"

# Restart services after database is ready
docker-compose restart core_orchestration
```

**Wrong Credentials**:
```bash
# Verify database credentials in .env
grep POSTGRES .env

# Reset database password
docker-compose down
docker volume rm enhanced-ai-agent-os-v2_postgres_data
docker-compose up -d postgres
```

**Connection Pool Issues**:
```bash
# Check active connections
docker-compose exec postgres psql -U postgres -c "
SELECT count(*) FROM pg_stat_activity;
"

# Restart services to reset connections
docker-compose restart
```

### 3. API Key Errors

#### Symptoms
- "Invalid API key" errors
- External service integration failures
- 401/403 HTTP responses

#### Diagnosis
```bash
# Check API key configuration
docker-compose exec core_orchestration python -c "
import os
print('OpenRouter:', 'SET' if os.getenv('OPENROUTER_API_KEY') else 'NOT SET')
print('Canva:', 'SET' if os.getenv('CANVA_API_KEY') else 'NOT SET')
print('Pinecone:', 'SET' if os.getenv('PINECONE_API_KEY') else 'NOT SET')
"

# Test API connectivity
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/models
```

#### Solutions

**Missing API Keys**:
1. Obtain API keys from respective services
2. Add to `.env` file
3. Restart services: `docker-compose restart`

**Invalid API Keys**:
1. Verify key format and validity
2. Check API key permissions
3. Regenerate keys if necessary

**API Rate Limits**:
1. Check service logs for rate limit errors
2. Implement exponential backoff
3. Upgrade API plan if needed

### 4. Memory and Performance Issues

#### Symptoms
- Slow response times
- High memory usage
- Services becoming unresponsive

#### Diagnosis
```bash
# Check system resources
docker stats

# Monitor memory usage
free -h
df -h

# Check service performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
```

#### Solutions

**High Memory Usage**:
```bash
# Restart memory-intensive services
docker-compose restart ideation_agent design_agent

# Increase Docker memory limits
# Docker Desktop -> Settings -> Resources -> Memory
```

**Slow Database Queries**:
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

**Cache Issues**:
```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL

# Restart caching services
docker-compose restart redis
```

### 5. Vector Search Issues

#### Symptoms
- Search returns no results
- Embedding generation fails
- Pinecone connection errors

#### Diagnosis
```bash
# Check Pinecone connection
curl -H "Api-Key: $PINECONE_API_KEY" \
     https://controller.$PINECONE_ENVIRONMENT.pinecone.io/databases

# Test vector search service
curl -X POST http://localhost:8008/search \
     -H "Content-Type: application/json" \
     -d '{"query": "test search", "limit": 5}'
```

#### Solutions

**Pinecone Configuration**:
1. Verify API key and environment
2. Check index exists and is active
3. Verify embedding dimensions match

**Empty Search Results**:
1. Check if content has been indexed
2. Verify embedding generation
3. Test with different search queries

### 6. UI/Frontend Issues

#### Symptoms
- Dashboard won't load
- API calls from UI fail
- CORS errors in browser console

#### Diagnosis
```bash
# Check React development server
docker-compose logs ui

# Test API from browser console
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(console.log)

# Check CORS configuration
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     http://localhost:8000/api/v1/tasks
```

#### Solutions

**CORS Issues**:
```python
# Update CORS settings in FastAPI
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Build Issues**:
```bash
# Rebuild UI container
docker-compose build ui
docker-compose up -d ui
```

## Monitoring and Debugging

### Log Analysis

#### Centralized Logging
```bash
# View all logs
docker-compose logs

# Filter by service
docker-compose logs ideation_agent | grep ERROR

# Follow logs with timestamps
docker-compose logs -f -t

# Export logs for analysis
docker-compose logs > system_logs_$(date +%Y%m%d).txt
```

#### Log Levels
```bash
# Set debug logging
export LOG_LEVEL=DEBUG
docker-compose restart

# View debug logs
docker-compose logs | grep DEBUG
```

### Performance Monitoring

#### Grafana Dashboards
1. Access Grafana: http://localhost:3001
2. Login: admin / [your_grafana_password]
3. Check pre-configured dashboards:
   - System Overview
   - Service Health
   - API Performance
   - Database Metrics

#### Prometheus Metrics
```bash
# Check metrics endpoint
curl http://localhost:9090/metrics

# Query specific metrics
curl 'http://localhost:9090/api/v1/query?query=up'
```

### Database Debugging

#### Query Performance
```sql
-- Enable query logging
ALTER SYSTEM SET log_statement = 'all';
SELECT pg_reload_conf();

-- Check slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements 
WHERE mean_time > 100
ORDER BY mean_time DESC;
```

#### Connection Issues
```sql
-- Check active connections
SELECT 
    datname,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    query
FROM pg_stat_activity 
WHERE state = 'active';
```

## Emergency Procedures

### System Recovery

#### Complete System Reset
```bash
# Stop all services
docker-compose down

# Remove all data (WARNING: This deletes all data)
docker-compose down -v
docker system prune -a

# Restart from scratch
cp .env.example .env
# Configure .env with your settings
docker-compose up -d
```

#### Service-Specific Recovery
```bash
# Restart single service
docker-compose restart [service-name]

# Rebuild and restart service
docker-compose up -d --build [service-name]

# View service logs during restart
docker-compose logs -f [service-name]
```

### Data Recovery

#### Database Backup and Restore
```bash
# Create backup
docker-compose exec postgres pg_dump -U postgres ai_agent_os > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U postgres ai_agent_os < backup.sql
```

#### Configuration Backup
```bash
# Backup configuration
cp .env .env.backup
cp docker-compose.yml docker-compose.yml.backup

# Restore configuration
cp .env.backup .env
cp docker-compose.yml.backup docker-compose.yml
```

## Preventive Measures

### Regular Maintenance

#### Weekly Tasks
- Check service health endpoints
- Review error logs
- Monitor resource usage
- Update API keys if needed

#### Monthly Tasks
- Database maintenance and optimization
- Security updates
- Performance analysis
- Backup verification

### Monitoring Setup

#### Alerts Configuration
```yaml
# prometheus/alerts.yml
groups:
  - name: ai-agent-os-alerts
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        annotations:
          summary: "Service {{ $labels.instance }} is down"
      
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        annotations:
          summary: "High memory usage on {{ $labels.container_label_com_docker_compose_service }}"
```

#### Health Check Automation
```bash
#!/bin/bash
# health_check.sh
SERVICES=("8000" "8001" "8002" "8003" "8004" "8005" "8006" "8007" "8008" "8009")

for port in "${SERVICES[@]}"; do
    if curl -f -s "http://localhost:$port/health" > /dev/null; then
        echo "✓ Service on port $port is healthy"
    else
        echo "✗ Service on port $port is unhealthy"
    fi
done
```

## Getting Additional Help

### Documentation Resources
- [Installation Guide](installation.md)
- [Configuration Guide](configuration.md)
- [API Reference](api-reference.md)
- [Architecture Overview](architecture.md)

### Support Channels
1. Check service logs first
2. Review this troubleshooting guide
3. Search project documentation
4. Check GitHub issues
5. Contact system administrators

### Reporting Issues

When reporting issues, include:
- Error messages and logs
- Steps to reproduce
- System configuration
- Docker and service versions
- Environment details

```bash
# Collect system information
echo "=== System Info ===" > debug_info.txt
docker --version >> debug_info.txt
docker-compose --version >> debug_info.txt
echo "=== Service Status ===" >> debug_info.txt
docker-compose ps >> debug_info.txt
echo "=== Recent Logs ===" >> debug_info.txt
docker-compose logs --tail=100 >> debug_info.txt
```
