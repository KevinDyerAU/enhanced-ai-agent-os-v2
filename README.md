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

## Development

See the `/docs` directory for detailed development guides and API documentation.
