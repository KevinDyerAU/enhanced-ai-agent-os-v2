# Enhanced AI Agent OS v2

A comprehensive AI-powered operating system for autonomous content creation, enterprise governance, and intelligent task orchestration.

## Overview

This system provides a multi-layered architecture for AI agents to collaborate on content creation tasks while maintaining enterprise-grade compliance and governance controls.

## Architecture

- **Creator Layer**: AI agents for ideation, design, video creation, and social media management
- **Enterprise Layer**: Compliance engines and audit services for governance
- **Core Services**: Orchestration and task management
- **Airlock System**: Content approval and review workflows
- **Data Architecture**: Vector search and intelligent memory systems

## Getting Started

1. Copy `.env.example` to `.env` and configure your environment variables
2. Run `docker-compose up` to start all services
3. Access the Mission Control Dashboard at `http://localhost:3000`

## Phase 1: Foundation & Core Infrastructure ✅ COMPLETE

### Completed Components:
- ✅ Project structure and Git repository initialization
- ✅ PostgreSQL database with comprehensive schema (10 tables)
- ✅ Docker Compose orchestration with all services
- ✅ Core Orchestration Agent (FastAPI service on port 8000)
- ✅ React UI with Mission Control Dashboard (port 3000)
- ✅ Monitoring stack (Prometheus on port 9090, Grafana on port 3001)

## Phase 2: Creator Layer Service Implementation ✅ COMPLETE

### Completed Components:
- ✅ **Ideation Agent** (port 8001): MarketIntelligenceEngine + IdeationEngine with OpenRouter LLM integration
- ✅ **Design Agent** (port 8002): CanvaAPIClient + BrandConsistencyEngine with Canva API integration
- ✅ **Video Agent** (port 8003): DescriptAPIClient with text-to-speech and video assembly capabilities
- ✅ **Social Media Manager** (port 8004): PlatformAdapter for LinkedIn with campaign execution

### API Endpoints:
- **POST /generate-ideas**: Returns structured content ideas with market insights
- **POST /create-design**: Generates Canva designs with brand compliance scoring
- **POST /create-video-content**: Creates video content with Descript integration
- **POST /execute-campaign**: Executes multi-platform social media campaigns

### Services Running:
- **Ideation Agent**: localhost:8001 (health check: healthy, database: connected)
- **Design Agent**: localhost:8002 (health check: healthy, database: connected)
- **Video Agent**: localhost:8003 (health check: healthy, database: connected)
- **Social Media Manager**: localhost:8004 (health check: healthy, database: connected)

All Phase 2 acceptance criteria have been met successfully.

## Phase 3: Enterprise Governance & UI Implementation ✅ COMPLETE

### Completed Components:
- ✅ **Compliance Engine** (port 8005): `/validate-action` endpoint with predefined compliance rules
- ✅ **Audit Service** (port 8006): `/log-event` endpoint with structured logging to audit_logs table
- ✅ **Airlock System** (port 8007): Complete content approval workflow with status management
- ✅ **Mission Briefing Workflow**: Conversational task creation interface integrated with orchestration
- ✅ **Airlock Review Interface**: Content governance with approve/reject functionality
- ✅ **Complete Frontend-Backend Integration**: Functional workflows connecting UI to all services

### API Endpoints:
- **POST /validate-action**: Validates actions against compliance rules (No external posts without approval, Brand guidelines, Content policy)
- **POST /log-event**: Structured logging to audit_logs table with full audit trail
- **POST /request-review**: Changes creative_assets status to 'pending_review'
- **POST /approve/{asset_id}**: Approves assets and logs action to audit_logs
- **POST /reject/{asset_id}**: Rejects assets with reason and logs action to audit_logs

### Services Running:
- **Compliance Engine**: localhost:8005 (health check: healthy, database: connected)
- **Audit Service**: localhost:8006 (health check: healthy, database: connected)
- **Airlock System**: localhost:8007 (health check: healthy, database: connected)

### UI Features:
- **Mission Control Dashboard**: Functional backend integration with task management
- **New Mission Button**: Launches Mission Briefing Workflow for task creation
- **Airlock Review Button**: Opens content approval interface
- **Complete Approval Workflow**: Assets move from pending_review → approved/rejected with full audit logging

All Phase 3 acceptance criteria have been met successfully.

## Phase 4: Advanced Features & Optimization ✅ COMPLETE

### Completed Components:
- ✅ **Data Architecture Service** (port 8020): Vector search and knowledge management with Pinecone integration
- ✅ **Vector Search Integration**: PineconeVectorClient for task memory and semantic search capabilities
- ✅ **Real-Time Notifications**: Kafka event streaming with KafkaEventManager for system-wide events
- ✅ **Agent Activity Stream**: UI component for operational history and audit log visualization
- ✅ **Enhanced Orchestration Agent**: Vector storage after task completion with embedding generation
- ✅ **Enhanced Ideation Agent**: Semantic search integration for contextually aware idea generation

### API Endpoints:
- **POST /knowledge/store**: Store vector documents with embeddings in Pinecone
- **GET /knowledge/search**: Semantic search across stored task memory
- **POST /events/publish**: Publish structured events to Kafka topics
- **GET /events/topics**: List configured Kafka topics and their status
- **POST /compliance/validate-processing**: Validate data processing compliance

### Services Running:
- **Data Architecture Service**: localhost:8020 (health check: healthy, Pinecone: connected, Kafka: connected)
- **Kafka**: localhost:9092 (topics: task.completed, asset.approved, system_errors, agent.activities)
- **Zookeeper**: localhost:2181 (coordination service for Kafka)

### Key Features:
- **Task Memory**: Completed tasks automatically stored as vector embeddings in Pinecone
- **Semantic Search**: Ideation Agent queries relevant past tasks before generating new ideas
- **Real-Time Events**: Task completions and asset approvals trigger Kafka events
- **Activity Monitoring**: Agent Activity Stream displays real-time operational history
- **Contextual Intelligence**: Agents leverage past task context for improved performance

### Integration Points:
- Orchestration Agent → Vector storage after task completion
- Ideation Agent → Semantic search before idea generation  
- Airlock System → Event publishing for approval/rejection actions
- UI Dashboard → Real-time activity stream and notifications

All Phase 4 acceptance criteria have been met successfully.

---

## Data Ingestion Layer ✅

**Status:** COMPLETE

### Implemented Services:
- **Document Processing Service** (Port 8031): File upload and parsing using unstructured.io
- **Web Intelligence Service** (Port 8032): Web scraping and crawling using Firecrawl API

### Key Components:
- **Unstructured API** (Port 8030): Self-hosted document processing engine
- **Document Engine**: FastAPI service with `/parse` endpoint for file uploads
- **Web Intelligence**: FastAPI service with `/scrape` endpoint for URL scraping
- **DocumentParser Class**: Handles communication with local unstructured.io API
- **FirecrawlClient Class**: Encapsulates Firecrawl API interactions

### API Endpoints:
- **POST /parse**: Upload and parse documents (PDF, TXT, DOCX, etc.) returning structured JSON
- **POST /scrape**: Scrape web pages returning markdown content and metadata
- **GET /healthz**: Health check endpoints for both services

### Services Running:
- **Document Engine**: localhost:8031 (health check: healthy, unstructured.io: integrated)
- **Web Intelligence Service**: localhost:8032 (health check: healthy, Firecrawl: integrated)
- **Unstructured API**: localhost:8030 (document processing backend)

### Configuration Updates:
- Updated `.env.example` with `UNSTRUCTURED_API_URL`, `UNSTRUCTURED_API_KEY`, `FIRECRAWL_API_KEY`
- Updated `docker-compose.yml` with new service definitions and dependencies
- Both services include health checks and proper error handling

The Enhanced AI Agent OS v2 now includes comprehensive data ingestion capabilities for both document processing and web intelligence gathering.

---

## Training Validation System - Phase 1 ✅

**Status:** COMPLETE

### Implemented Services:
- **Training Validation Service** (Port 8033): Core validation service with session management
- **Web Intelligence Integration**: Automated scraping of training.gov.au for unit data
- **Document Processing Integration**: Automated processing of training documents

### Key Components:
- **Database Schema Extension**: 8 new tables for training validation workflow
- **Training Unit Management**: Retrieve and cache training units from training.gov.au
- **Validation Session Management**: Create and manage validation sessions
- **Document Upload and Processing**: Upload documents and extract content
- **Integration Clients**: WebIntelligenceClient and DocumentProcessingClient
- **Frontend Dashboard**: React component for session management

### API Endpoints:
- **POST /api/v1/training-units/retrieve**: Retrieve training unit data from training.gov.au
- **POST /api/v1/validation-sessions**: Create new validation sessions
- **GET /api/v1/validation-sessions**: List validation sessions
- **POST /api/v1/validation-sessions/{id}/documents**: Upload documents for validation
- **POST /api/v1/validation-sessions/{id}/validate**: Execute validation
- **GET /api/v1/validation-sessions/{id}/results**: Get validation results

### Services Running:
- **Training Validation Service**: localhost:8033 (health check: healthy, integrations: connected)

Phase 1 foundation is complete and ready for Phase 2: Core Validation Capabilities.

## Training Validation System - Phase 2 ✅

**Status:** COMPLETE

### Core Validation Capabilities:
- **4 Validation Engines**: Assessment Conditions, Knowledge Evidence, Performance Evidence, Foundation Skills
- **Validation Coordinator**: Orchestrates all validation engines with configurable strictness levels
- **Airlock Integration**: Validation reports created as creative assets for user review and feedback
- **Comprehensive Reporting**: Markdown-formatted validation reports with detailed findings and recommendations

### Key Features:
- **Configurable Strictness Levels**: lenient, normal, strict validation modes
- **Error Handling**: Robust error handling with partial validation results
- **Semantic Analysis**: Content relevance detection and keyword matching
- **User Feedback Loop**: Integration with airlock system for report review and approval
- **Audit Trail**: Complete audit logging through existing AOS audit system

### API Endpoints:
- **POST /api/v1/validation-sessions/{id}/validate**: Execute comprehensive validation with airlock integration
- **POST /api/v1/validation-reports/{asset_id}/submit-review**: Submit validation report for airlock review
- **GET /api/v1/validation-reports/{asset_id}/status**: Get airlock status of validation report
- **GET /api/v1/validation-reports/pending**: Get all pending validation reports

### Validation Workflow:
1. Create validation session and upload training documents
2. Execute validation with all 4 engines (AC, KE, PE, FS)
3. Generate comprehensive validation report
4. Create report as creative asset in airlock system
5. Submit for user review and feedback
6. User can approve/reject with comments for improvements

Phase 2 core validation capabilities complete and fully tested - ready for Phase 3: Advanced Features.

### Validation Testing Results:
- ✅ All 4 validation engines operational (AC, KE, PE, FS)
- ✅ Validation coordinator successfully orchestrates all engines
- ✅ Comprehensive validation reports generated in Markdown format
- ✅ Creative assets created and submitted to airlock system
- ✅ User feedback loop functional through airlock integration
- ✅ Database operations working correctly with audit trail
- ✅ Error handling robust with partial validation support

## Universal Airlock System Usage

The Universal Airlock System provides a comprehensive human-in-the-loop AI governance platform for reviewing, approving, and refining AI-generated content across all services.

### Quick Start

1. **Access the Dashboard**
   ```bash
   # Start the system
   docker-compose up -d
   
   # Access the Universal Airlock Dashboard
   open http://localhost:5173
   ```

2. **Submit Content for Review**
   ```bash
   curl -X POST http://localhost:8007/api/v1/airlock/submit \
     -H "Content-Type: application/json" \
     -d '{
       "content_type": "training_validation",
       "source_service": "training_validation_service",
       "source_id": "unit_001",
       "title": "Training Unit Validation",
       "description": "Validation results for BSBWHS311",
       "content": {
         "unit_code": "BSBWHS311",
         "validation_results": {
           "overall_score": 85,
           "status": "pass"
         }
       },
       "priority": "medium"
     }'
   ```

3. **Review and Approve Content**
   - Navigate to the dashboard at http://localhost:5173
   - View pending items in the "Pending Review" section
   - Click on items to view detailed content
   - Use the chat interface for real-time collaboration
   - Approve or reject items with feedback

### API Reference

#### Core Endpoints

**Submit Content**
```http
POST /api/v1/airlock/submit
Content-Type: application/json

{
  "content_type": "string",
  "source_service": "string", 
  "source_id": "string",
  "title": "string",
  "description": "string",
  "content": {},
  "metadata": {},
  "priority": "low|medium|high"
}
```

**List Items**
```http
GET /api/v1/airlock/items?status=pending_review&limit=50&offset=0
```

**Update Item Status**
```http
PATCH /api/v1/airlock/items/{id}/status
Content-Type: application/json

{
  "status": "approved|rejected|requires_changes",
  "assigned_reviewer_id": "reviewer_001"
}
```

**Submit Feedback**
```http
POST /api/v1/airlock/items/{id}/feedback
Content-Type: application/json

{
  "feedback_type": "suggestion|approval|rejection|rating",
  "feedback_data": {
    "category": "assessment_conditions",
    "issue": "Missing context",
    "suggestion": "Add more details",
    "severity": "medium"
  },
  "provided_by": "reviewer_001"
}
```

#### WebSocket Chat System

Connect to real-time chat for collaborative review:

```javascript
const ws = new WebSocket('ws://localhost:8007/ws/chat/{item_id}');

// Send message
ws.send(JSON.stringify({
  type: 'message',
  sender_type: 'human',
  sender_id: 'reviewer_001',
  content: 'This needs more context',
  room_id: item_id
}));

// Send typing indicator
ws.send(JSON.stringify({
  type: 'typing',
  sender_id: 'reviewer_001',
  room_id: item_id,
  is_typing: true
}));
```

### Content Types Supported

- **training_validation**: Training unit validation results
- **creative_asset**: Generated designs, videos, social media content
- **ideation**: Content ideas and market intelligence
- **compliance_report**: Compliance validation results
- **document_analysis**: Processed document insights

### Review Workflow

1. **Content Submission**: AI services submit content for review
2. **Automated Screening**: Basic validation and compliance checks
3. **Human Review**: Reviewers examine content using the dashboard
4. **Collaborative Discussion**: Real-time chat for feedback and questions
5. **Decision**: Approve, reject, or request changes
6. **Audit Trail**: Complete history of all actions and decisions

## Monitoring and Observability

### Health Checks

Monitor system health across all components:

```bash
# Universal Airlock System
curl http://localhost:8007/api/v1/airlock/health

# Training Validation Service  
curl http://localhost:8033/api/v1/health

# Other services
curl http://localhost:8001/health  # Ideation Agent
curl http://localhost:8020/health  # Data Architecture
```

### Prometheus Metrics

Access comprehensive metrics at:
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

#### Key Metrics Available

**Universal Airlock System Metrics:**
- `airlock_requests_total` - Total API requests by method, endpoint, status
- `airlock_request_duration_seconds` - Request duration histogram
- `airlock_websocket_connections_active` - Active WebSocket connections
- `airlock_items_total` - Total items by status
- `airlock_database_operations_total` - Database operations by type
- `airlock_chat_messages_total` - Chat messages by type
- `airlock_feedback_submissions_total` - Feedback submissions by type

**System-wide Metrics:**
- Service health and uptime
- Database connection status
- API response times
- Error rates and exceptions

### Structured Logging

All services use structured JSON logging for production observability:

```bash
# View airlock system logs
docker-compose logs airlock_system

# View all service logs
docker-compose logs -f

# Filter logs by level
docker-compose logs airlock_system | grep '"level":"error"'
```

Log entries include:
- Timestamp (ISO format)
- Service name and version
- Log level (DEBUG, INFO, WARN, ERROR)
- Structured context (user_id, item_id, operation, etc.)
- Performance metrics (duration_ms, response_time)
- Error details and stack traces

### Grafana Dashboards

Access pre-configured dashboards at http://localhost:3001:

1. **System Overview**: Service health, response times, error rates
2. **Universal Airlock**: Content submission rates, review times, approval ratios
3. **Database Performance**: Query performance, connection pools
4. **WebSocket Activity**: Connection counts, message throughput

## Production Deployment

### Environment Configuration

Required environment variables for production:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname
POSTGRES_USER=aos_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=aos_db

# External APIs
OPENROUTER_API_KEY=your_openrouter_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Security
JWT_SECRET_KEY=your_jwt_secret_key
ENCRYPTION_KEY=your_encryption_key

# Monitoring
LOG_LEVEL=INFO
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
GRAFANA_ADMIN_PASSWORD=secure_admin_password

# Service URLs (adjust for production)
TRAINING_VALIDATION_SERVICE_URL=http://training_validation_service:8033
IDEATION_AGENT_URL=http://ideation_agent:8001
AUDIT_SERVICE_URL=http://audit_service:8006
AIRLOCK_SERVICE_URL=http://airlock_system:8007
```

### Security Considerations

1. **API Keys**: Store all API keys in secure environment variables
2. **Database**: Use strong passwords and SSL connections
3. **JWT Tokens**: Generate secure JWT secret keys
4. **Network**: Configure firewalls and VPNs for production access
5. **HTTPS**: Enable SSL/TLS for all external endpoints
6. **Monitoring**: Set up alerts for security events and anomalies

### Scaling Configuration

For high-traffic production environments:

```yaml
# docker-compose.prod.yml
services:
  airlock_system:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    environment:
      - WORKERS=4
      - MAX_CONNECTIONS=100
      
  postgres:
    environment:
      - POSTGRES_MAX_CONNECTIONS=200
      - POSTGRES_SHARED_BUFFERS=256MB
```

### Backup and Recovery

```bash
# Database backup
docker-compose exec postgres pg_dump -U aos_user aos_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U aos_user aos_db < backup.sql

# Volume backup
docker run --rm -v enhanced-ai-agent-os-v2_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data.tar.gz /data
```

## Troubleshooting

### Common Issues

**Service Won't Start**
```bash
# Check service logs
docker-compose logs airlock_system

# Verify environment variables
docker-compose exec airlock_system env | grep -E "(DATABASE|API_KEY)"

# Check port conflicts
netstat -tulpn | grep :8007
```

**Database Connection Issues**
```bash
# Test database connectivity
docker-compose exec postgres psql -U aos_user -d aos_db -c "SELECT 1;"

# Check database schema
docker-compose exec postgres psql -U aos_user -d aos_db -c "\dt"

# Verify database logs
docker-compose logs postgres
```

**WebSocket Connection Failures**
```bash
# Test WebSocket endpoint
wscat -c ws://localhost:8007/ws/chat/test_room

# Check WebSocket logs
docker-compose logs airlock_system | grep -i websocket

# Verify active connections
curl http://localhost:8007/api/v1/airlock/health | jq '.components.websocket'
```

**Frontend Issues**
```bash
# Check frontend logs
docker-compose logs frontend

# Verify API connectivity
curl http://localhost:8007/api/v1/airlock/health

# Test frontend build
cd frontend/universal-airlock-ui && npm run build
```

**Monitoring Issues**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify metrics endpoint
curl http://localhost:8007/metrics

# Test Grafana connectivity
curl http://localhost:3001/api/health
```

### Performance Optimization

**Database Performance**
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;

-- Index optimization
CREATE INDEX CONCURRENTLY idx_airlock_items_status ON airlock_items(status);
CREATE INDEX CONCURRENTLY idx_airlock_items_created_at ON airlock_items(created_at);
```

**API Performance**
```bash
# Monitor response times
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8007/api/v1/airlock/items

# Load testing
ab -n 1000 -c 10 http://localhost:8007/api/v1/airlock/health
```

### Log Analysis

```bash
# Error analysis
docker-compose logs airlock_system | grep '"level":"error"' | jq '.error'

# Performance analysis
docker-compose logs airlock_system | grep '"duration_ms"' | jq '.duration_ms' | sort -n

# User activity analysis
docker-compose logs airlock_system | grep '"operation":"submit_content"' | jq '.content_type'
```

### Getting Support

1. **Check Health Endpoints**: Verify all services are healthy
2. **Review Logs**: Check structured logs for error details
3. **Monitor Metrics**: Use Grafana dashboards to identify issues
4. **Database Status**: Verify database connectivity and performance
5. **Network Connectivity**: Test service-to-service communication

For additional support, consult the detailed documentation in the `/docs` directory.

## Development

See the `/docs` directory for detailed development guides and API documentation.
