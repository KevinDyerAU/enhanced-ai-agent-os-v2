# Training Validation Service

## Overview

The Training Validation Service is a core component of the Enhanced AI Agent OS that provides comprehensive validation of training materials against competency standards. It supports document processing, validation against training.gov.au standards, SMART question generation, and compliance reporting.

## Features

- **Document Processing**: Upload and process various document formats
- **Standards Validation**: Validate training materials against official competency standards
- **AI-Powered Analysis**: Leveraging OpenRouter for advanced LLM capabilities
- **SMART Question Generation**: Automatically generate assessment questions using AI
- **Compliance Reporting**: Generate detailed validation reports
- **Airlock Integration**: Review workflow integration for validation results
- **Monitoring**: Built-in Prometheus metrics and Grafana dashboards

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- PostgreSQL (included in Docker setup)
- [Training.gov.au API key](https://training.gov.au/Home/Tga) (for unit retrieval)
- [OpenRouter API key](https://openrouter.ai/keys) (for LLM capabilities)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/enhanced-ai-agent-os-v2.git
   cd enhanced-ai-agent-os-v2
   ```

2. Install dependencies using Poetry:
   ```bash
   cd services/training-validation/training_validation_service
   poetry install
   ```

## Running with Docker

1. Copy the example environment file and update with your API keys:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. Start the service with all dependencies:
   ```bash
   docker-compose up -d --build
   ```

3. Access the service at: http://localhost:8033

This will start:
- Training Validation Service (port 8033)
- PostgreSQL database
- Prometheus (port 9090)
- Grafana (port 3001)

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8033/docs
- ReDoc: http://localhost:8033/redoc

## Key Endpoints

### Session Management
- `POST /sessions/` - Create a new validation session
- `GET /sessions/` - List validation sessions
- `GET /sessions/{session_id}` - Get session details

### Document Processing
- `POST /documents/upload/{session_id}` - Upload a document for validation
- `POST /documents/process` - Process a document without validation

### Validation
- `POST /validation/{session_id}/execute` - Execute validation for a session
- `GET /validation/{session_id}/results` - Get validation results

### Reports
- `GET /reports/{session_id}` - Generate a comprehensive report
- `GET /reports/{report_id}/download` - Download a report

### Questions
- `POST /questions/generate/{session_id}` - Generate SMART questions
- `GET /questions/session/{session_id}` - Get questions for a session
- `GET /questions/search` - Search questions

## Monitoring

The service includes built-in monitoring with Prometheus and Grafana:

1. Metrics are automatically collected and available at `/metrics`
2. Access monitoring dashboards:
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3001 (admin/admin)

Pre-configured dashboards are included for:
- Service health and performance
- Request metrics and error rates
- Validation statistics
- Document processing metrics

## Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints for all function parameters and return values
- Document all public functions and classes with docstrings

### Testing
Run tests with:
```bash
pytest
```

### Environment Variables

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Required
TRAINING_GOV_API_KEY=your_training_gov_api_key

# LLM Configuration (OpenRouter)
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openai/gpt-4o  # Default model, can be changed to any OpenRouter supported model

# Database configuration
POSTGRES_USER=aos_user
POSTGRES_PASSWORD=aos_password
POSTGRES_DB=aos_db
DATABASE_URL=postgresql://aos_user:aos_password@postgres:5432/aos_db

# Monitoring
PROMETHEUS_MULTIPROC_DIR=/prometheus
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Write tests
4. Submit a pull request

## License

[Your License Here]
