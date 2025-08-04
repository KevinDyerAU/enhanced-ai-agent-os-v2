# Configuration Guide

Comprehensive guide to configuring the Enhanced AI Agent OS v2 system.

## Environment Configuration

### Core Environment Variables

The system uses environment variables for configuration. Copy `.env.example` to `.env` and configure:

```env
# Database Configuration
POSTGRES_DB=ai_agent_os
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis Configuration (for caching)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# API Keys (Required)
OPENROUTER_API_KEY=your_openrouter_api_key
CANVA_API_KEY=your_canva_api_key
DESCRIPT_API_KEY=your_descript_api_key
LINKEDIN_API_KEY=your_linkedin_api_key
TWITTER_API_KEY=your_twitter_api_key
FACEBOOK_API_KEY=your_facebook_api_key

# Vector Database
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=ai-agent-os

# Monitoring
GRAFANA_ADMIN_PASSWORD=your_grafana_password
PROMETHEUS_RETENTION_TIME=15d

# Security
JWT_SECRET_KEY=your_jwt_secret_key
API_KEY_SALT=your_api_key_salt
ENCRYPTION_KEY=your_encryption_key

# System Configuration
LOG_LEVEL=INFO
DEBUG_MODE=false
MAX_CONCURRENT_TASKS=10
TASK_TIMEOUT=300
```

### Service-Specific Configuration

#### Ideation Agent
```env
# OpenRouter Configuration
OPENROUTER_MODEL=openai/gpt-4-turbo
OPENROUTER_MAX_TOKENS=2000
OPENROUTER_TEMPERATURE=0.7

# Market Intelligence
MARKET_INTELLIGENCE_ENABLED=true
TREND_ANALYSIS_DAYS=30
COMPETITOR_ANALYSIS_ENABLED=true
```

#### Design Agent
```env
# Canva Configuration
CANVA_TEAM_ID=your_canva_team_id
CANVA_BRAND_KIT_ID=your_brand_kit_id
CANVA_AUTO_PUBLISH=false

# Brand Guidelines
BRAND_PRIMARY_COLOR=#FF6B35
BRAND_SECONDARY_COLOR=#004E89
BRAND_FONT_PRIMARY=Roboto
BRAND_FONT_SECONDARY=Open Sans
```

#### Video Agent
```env
# Descript Configuration
DESCRIPT_PROJECT_ID=your_descript_project_id
DESCRIPT_VOICE_ID=your_preferred_voice_id
DESCRIPT_AUTO_TRANSCRIBE=true

# Video Settings
DEFAULT_VIDEO_DURATION=60
DEFAULT_VIDEO_QUALITY=1080p
BACKGROUND_MUSIC_ENABLED=true
```

#### Social Media Manager
```env
# Platform Configuration
LINKEDIN_COMPANY_ID=your_linkedin_company_id
TWITTER_HANDLE=your_twitter_handle
FACEBOOK_PAGE_ID=your_facebook_page_id

# Posting Configuration
AUTO_POSTING_ENABLED=false
POST_APPROVAL_REQUIRED=true
HASHTAG_LIMIT=5
```

## Service Configuration Files

### Docker Compose Override

Create `docker-compose.override.yml` for environment-specific settings:

```yaml
version: '3.8'
services:
  core_orchestration:
    environment:
      - LOG_LEVEL=DEBUG
    volumes:
      - ./custom_config:/app/config

  postgres:
    environment:
      - POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups

  grafana:
    volumes:
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
```

### Service Health Check Configuration

Configure health check intervals and timeouts:

```yaml
# In docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## Database Configuration

### PostgreSQL Connection Details

**Default Configuration:**
- **Host**: `postgres` (container name) / `localhost` (from host)
- **Port**: `5432`
- **Database**: `ai_agent_os`
- **Username**: `postgres`
- **Password**: Set via `POSTGRES_PASSWORD` environment variable

**Environment Variables:**
```env
POSTGRES_DB=ai_agent_os
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
```

**Connection Strings:**
```bash
# From host machine
postgresql://postgres:your_password@localhost:5432/ai_agent_os

# From Docker containers
postgresql://postgres:your_password@postgres:5432/ai_agent_os
```

**Docker Service Configuration:**
```yaml
postgres:
  image: postgres:13
  container_name: ai_agent_os_postgres
  environment:
    POSTGRES_DB: ${POSTGRES_DB}
    POSTGRES_USER: ${POSTGRES_USER}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256"
  ports:
    - "5432:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./database/init:/docker-entrypoint-initdb.d
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
    interval: 30s
    timeout: 10s
    retries: 3
```

### PostgreSQL Settings

#### Performance Tuning
```sql
-- In postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

#### Connection Pooling
```env
# PgBouncer configuration
PGBOUNCER_POOL_MODE=transaction
PGBOUNCER_MAX_CLIENT_CONN=100
PGBOUNCER_DEFAULT_POOL_SIZE=25
```

### Database Migrations

Automatic migrations run on startup. To run manually:

```bash
# Run pending migrations
docker-compose exec core_orchestration python manage.py migrate

# Create new migration
docker-compose exec core_orchestration python manage.py makemigrations

# Reset database (development only)
docker-compose exec core_orchestration python manage.py reset_db
```

## API Configuration

### Rate Limiting

Configure rate limits per endpoint:

```python
# In service configuration
RATE_LIMITS = {
    "default": "100/minute",
    "content_generation": "10/minute",
    "search": "1000/minute",
    "health_check": "1000/minute"
}
```

### CORS Settings

```python
# CORS configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-domain.com"
]
CORS_ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE"]
CORS_ALLOWED_HEADERS = ["*"]
```

### API Versioning

```python
# API versioning
API_VERSION = "v1"
API_PREFIX = "/api/v1"
DEPRECATED_VERSIONS = ["v0"]
```

## Security Configuration

### Authentication

```env
# JWT Configuration
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
JWT_REFRESH_EXPIRATION_DAYS=30

# API Key Configuration
API_KEY_LENGTH=32
API_KEY_PREFIX=aiaos_
```

### SSL/TLS Configuration

For production deployment:

```yaml
# nginx.conf
server {
    listen 443 ssl;
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
}
```

## Monitoring Configuration

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ai-agent-os'
    static_configs:
      - targets: ['core_orchestration:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'creator-layer'
    static_configs:
      - targets: 
        - 'ideation_agent:8001'
        - 'design_agent:8002'
        - 'video_agent:8003'
        - 'social_media_manager:8004'
```

### Grafana Configuration Details

**Access Information:**
- **URL**: http://localhost:3001
- **Username**: `admin`
- **Password**: Set via `GRAFANA_ADMIN_PASSWORD` environment variable
- **Host**: `grafana` (container name) / `localhost` (from host)
- **Port**: `3001` (mapped from container port 3000)

**Environment Variables:**
```env
GRAFANA_ADMIN_PASSWORD=your_grafana_password
GF_SECURITY_ADMIN_USER=admin
GF_USERS_ALLOW_SIGN_UP=false
GF_SECURITY_ALLOW_EMBEDDING=true
GF_SERVER_ROOT_URL=http://localhost:3001
```

**Docker Service Configuration:**
```yaml
grafana:
  image: grafana/grafana:latest
  container_name: ai_agent_os_grafana
  ports:
    - "3001:3000"
  environment:
    - GF_SECURITY_ADMIN_USER=admin
    - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
    - GF_USERS_ALLOW_SIGN_UP=false
    - GF_SECURITY_ALLOW_EMBEDDING=true
    - GF_SERVER_ROOT_URL=http://localhost:3001
    - GF_INSTALL_PLUGINS=grafana-piechart-panel,grafana-worldmap-panel
  volumes:
    - grafana_data:/var/lib/grafana
    - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
    - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:3000/api/health || exit 1"]
    interval: 30s
    timeout: 10s
    retries: 3
  depends_on:
    - prometheus
```

**Data Source Configuration:**
```yaml
# grafana/provisioning/datasources/prometheus.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    access: proxy
    isDefault: true
    basicAuth: false
    editable: true
  - name: PostgreSQL
    type: postgres
    url: postgres:5432
    database: ai_agent_os
    user: postgres
    secureJsonData:
      password: ${POSTGRES_PASSWORD}
    jsonData:
      sslmode: disable
      maxOpenConns: 0
      maxIdleConns: 2
      connMaxLifetime: 14400
```

**Dashboard Provisioning:**
```yaml
# grafana/provisioning/dashboards/dashboard.yml
apiVersion: 1
providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
```

**User Management:**
```bash
# Add new user via API
curl -X POST http://admin:${GRAFANA_ADMIN_PASSWORD}@localhost:3001/api/admin/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New User",
    "email": "user@example.com",
    "login": "newuser",
    "password": "userpassword",
    "orgId": 1
  }'

# Reset admin password
docker-compose exec grafana grafana-cli admin reset-admin-password newpassword
```

### Alerting Rules

```yaml
# alerts.yml
groups:
  - name: ai-agent-os
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.instance }}"
```

## Logging Configuration

### Centralized Logging

```yaml
# docker-compose.logging.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:7.14.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline

  kibana:
    image: docker.elastic.co/kibana/kibana:7.14.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

### Log Format Configuration

```python
# logging.conf
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

## Backup Configuration

### Database Backups

```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ai_agent_os_$TIMESTAMP.sql"

# Create backup
docker-compose exec -T postgres pg_dump -U postgres ai_agent_os > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

### Automated Backup Schedule

```yaml
# In docker-compose.yml
services:
  backup:
    image: postgres:13
    volumes:
      - ./backups:/backups
      - ./scripts/backup.sh:/backup.sh
    command: |
      sh -c "
        while true; do
          sleep 86400  # 24 hours
          /backup.sh
        done
      "
    depends_on:
      - postgres
```

## Performance Optimization

### Caching Configuration

```env
# Redis caching
CACHE_BACKEND=redis
CACHE_LOCATION=redis://redis:6379/1
CACHE_TIMEOUT=3600
CACHE_KEY_PREFIX=aiaos_

# Application caching
ENABLE_QUERY_CACHE=true
ENABLE_TEMPLATE_CACHE=true
ENABLE_API_RESPONSE_CACHE=true
```

### Resource Limits

```yaml
# docker-compose.yml
services:
  core_orchestration:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

## Development vs Production

### Development Configuration

```env
# .env.development
DEBUG_MODE=true
LOG_LEVEL=DEBUG
ENABLE_CORS=true
AUTO_RELOAD=true
MOCK_EXTERNAL_APIS=true
```

### Production Configuration

```env
# .env.production
DEBUG_MODE=false
LOG_LEVEL=WARNING
ENABLE_CORS=false
AUTO_RELOAD=false
MOCK_EXTERNAL_APIS=false
SSL_REQUIRED=true
```

## Configuration Validation

### Startup Checks

The system validates configuration on startup:

```python
# config_validator.py
def validate_config():
    required_vars = [
        'POSTGRES_PASSWORD',
        'OPENROUTER_API_KEY',
        'PINECONE_API_KEY',
        'JWT_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ConfigurationError(f"Missing required environment variables: {missing_vars}")
```

### Health Checks

Configuration health checks available at `/health/config`:

```json
{
  "config_status": "healthy",
  "database_connection": "ok",
  "external_apis": {
    "openrouter": "connected",
    "canva": "connected",
    "descript": "error",
    "pinecone": "connected"
  },
  "missing_optional_config": [
    "TWITTER_API_KEY"
  ]
}
```

## Troubleshooting Configuration

### Common Issues

**Environment Variables Not Loading**
- Check `.env` file exists in project root
- Verify file permissions (readable by Docker)
- Check for syntax errors in `.env` file

**Database Connection Issues**
- Verify database credentials
- Check network connectivity
- Ensure PostgreSQL is running

**API Key Errors**
- Validate API key format
- Check API key permissions
- Verify service-specific configuration

### Configuration Testing

```bash
# Test configuration
docker-compose exec core_orchestration python -c "
from config import settings
print('Configuration loaded successfully')
print(f'Database: {settings.DATABASE_URL}')
print(f'Debug mode: {settings.DEBUG}')
"
```
