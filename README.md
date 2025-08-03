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

Phase 2 core validation capabilities complete - ready for Phase 3: Advanced Features.

## Development

See the `/docs` directory for detailed development guides and API documentation.
