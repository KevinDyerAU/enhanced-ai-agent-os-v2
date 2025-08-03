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

## Development

See the `/docs` directory for detailed development guides and API documentation.
