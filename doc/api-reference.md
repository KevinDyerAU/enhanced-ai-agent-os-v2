# API Reference

Complete API documentation for all Enhanced AI Agent OS v2 services.

## Base URLs

- **Core Orchestration**: http://localhost:8000
- **Ideation Agent**: http://localhost:8001
- **Design Agent**: http://localhost:8002
- **Video Agent**: http://localhost:8003
- **Social Media Manager**: http://localhost:8004
- **Compliance Engine**: http://localhost:8005
- **Audit Service**: http://localhost:8006
- **Governance Dashboard**: http://localhost:8007
- **Vector Search**: http://localhost:8008
- **Memory System**: http://localhost:8009

## Authentication

All API endpoints require authentication via API key in the header:

```http
Authorization: Bearer your_api_key
Content-Type: application/json
```

## Core Orchestration Agent (Port 8000)

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z",
  "services": {
    "database": "connected",
    "vector_store": "connected"
  }
}
```

### Task Management

#### Create Task
```http
POST /tasks
```

**Request Body:**
```json
{
  "task_type": "content_creation",
  "priority": "high",
  "parameters": {
    "topic": "AI productivity",
    "deadline": "2024-01-20T00:00:00Z"
  }
}
```

#### Get Task Status
```http
GET /tasks/{task_id}
```

#### List Tasks
```http
GET /tasks?status=pending&limit=10
```

## Creator Layer Services

### Ideation Agent (Port 8001)

#### Generate Ideas
```http
POST /generate-ideas
```

**Request Body:**
```json
{
  "topic": "AI productivity tools",
  "target_audience": "tech professionals",
  "content_type": "blog_post",
  "market_context": "B2B SaaS",
  "num_ideas": 5
}
```

**Response:**
```json
{
  "ideas": [
    {
      "id": "idea_123",
      "title": "10 AI Tools That Will Transform Your Workflow",
      "description": "Comprehensive guide to productivity AI tools",
      "market_score": 8.5,
      "trend_alignment": "high",
      "keywords": ["AI", "productivity", "automation"],
      "estimated_engagement": 1250,
      "content_outline": [
        "Introduction to AI productivity",
        "Top 10 tools breakdown",
        "Implementation strategies"
      ]
    }
  ],
  "market_insights": {
    "trending_topics": ["automation", "efficiency"],
    "competitor_analysis": "summary",
    "audience_preferences": "detailed_breakdown"
  }
}
```

#### Get Market Intelligence
```http
GET /market-intelligence?topic=AI&timeframe=30d
```

### Design Agent (Port 8002)

#### Create Design
```http
POST /create-design
```

**Request Body:**
```json
{
  "design_type": "social_media_post",
  "content": "Your content text here",
  "brand_guidelines": {
    "colors": ["#FF6B35", "#004E89"],
    "fonts": ["Roboto", "Open Sans"],
    "logo_url": "https://example.com/logo.png"
  },
  "dimensions": "1080x1080",
  "platform": "linkedin"
}
```

**Response:**
```json
{
  "design_id": "design_456",
  "design_url": "https://canva.com/design/xyz",
  "preview_url": "https://canva.com/preview/xyz",
  "brand_compliance_score": 9.2,
  "compliance_details": {
    "color_compliance": "excellent",
    "font_compliance": "good",
    "layout_compliance": "excellent"
  },
  "variations": [
    {
      "variation_id": "var_1",
      "description": "Alternative color scheme",
      "preview_url": "https://canva.com/preview/var1"
    }
  ]
}
```

#### Get Brand Guidelines
```http
GET /brand-guidelines
```

### Video Agent (Port 8003)

#### Create Video Content
```http
POST /create-video-content
```

**Request Body:**
```json
{
  "script": "Welcome to our AI productivity guide...",
  "voice_style": "professional",
  "duration": "60s",
  "platform": "linkedin",
  "video_style": "talking_head",
  "background_music": true
}
```

**Response:**
```json
{
  "video_id": "video_789",
  "video_url": "https://descript.com/video/xyz",
  "thumbnail_url": "https://descript.com/thumb/xyz",
  "duration": 58.5,
  "file_size": "15.2MB",
  "transcription": "Welcome to our AI productivity guide...",
  "chapters": [
    {
      "title": "Introduction",
      "start_time": 0,
      "end_time": 10
    }
  ]
}
```

### Social Media Manager (Port 8004)

#### Execute Campaign
```http
POST /execute-campaign
```

**Request Body:**
```json
{
  "campaign_name": "AI Productivity Launch",
  "content": {
    "text": "Discover the future of productivity with AI",
    "media": [
      {
        "type": "image",
        "url": "https://example.com/image.jpg"
      }
    ],
    "hashtags": ["#AI", "#Productivity", "#Tech"]
  },
  "platforms": ["linkedin", "twitter"],
  "schedule": {
    "linkedin": "2024-01-15T10:00:00Z",
    "twitter": "2024-01-15T10:30:00Z"
  },
  "targeting": {
    "audience": "tech_professionals",
    "location": "US",
    "interests": ["AI", "productivity"]
  }
}
```

**Response:**
```json
{
  "campaign_id": "camp_101",
  "status": "scheduled",
  "posts": [
    {
      "platform": "linkedin",
      "post_id": "linkedin_123",
      "scheduled_time": "2024-01-15T10:00:00Z",
      "status": "scheduled"
    }
  ],
  "estimated_reach": 5000,
  "estimated_engagement": 250
}
```

## Enterprise Layer Services

### Compliance Engine (Port 8005)

#### Check Content Compliance
```http
POST /check-compliance
```

**Request Body:**
```json
{
  "content": {
    "text": "Your content here",
    "media_urls": ["https://example.com/image.jpg"]
  },
  "content_type": "social_media_post",
  "platform": "linkedin"
}
```

**Response:**
```json
{
  "compliance_score": 8.5,
  "violations": [],
  "warnings": [
    {
      "type": "brand_guideline",
      "message": "Consider using primary brand colors",
      "severity": "low"
    }
  ],
  "recommendations": [
    "Add company hashtag",
    "Include call-to-action"
  ],
  "approval_required": false
}
```

#### Create Compliance Rule
```http
POST /compliance-rules
```

**Request Body:**
```json
{
  "rule_name": "Brand Color Guidelines",
  "description": "Ensure brand colors are used consistently",
  "criteria": {
    "required_colors": ["#FF6B35", "#004E89"],
    "forbidden_words": ["competitor_name"],
    "tone_requirements": "professional"
  },
  "severity": "high",
  "applies_to": ["social_media", "blog_posts"]
}
```

### Audit Service (Port 8006)

#### Get Audit Logs
```http
GET /audit-logs?start_date=2024-01-01&end_date=2024-01-15&user_id=user123
```

**Response:**
```json
{
  "logs": [
    {
      "id": "log_001",
      "timestamp": "2024-01-15T10:00:00Z",
      "user_id": "user123",
      "action": "content_created",
      "resource": "blog_post_456",
      "details": {
        "content_type": "blog_post",
        "title": "AI Productivity Guide"
      },
      "ip_address": "192.168.1.100"
    }
  ],
  "total_count": 150,
  "page": 1,
  "per_page": 10
}
```

## Data Architecture Services

### Vector Search Service (Port 8008)

#### Semantic Search
```http
POST /search
```

**Request Body:**
```json
{
  "query": "marketing strategies for B2B SaaS",
  "filters": {
    "content_type": "blog_post",
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-01-15"
    },
    "tags": ["marketing", "B2B"]
  },
  "limit": 10,
  "include_metadata": true
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "content_789",
      "title": "B2B SaaS Marketing Masterclass",
      "content_snippet": "Effective B2B SaaS marketing requires...",
      "similarity_score": 0.92,
      "metadata": {
        "author": "John Doe",
        "created_date": "2024-01-10",
        "tags": ["marketing", "B2B", "SaaS"]
      },
      "url": "https://example.com/content/789"
    }
  ],
  "total_results": 25,
  "query_time": "0.15s"
}
```

#### Add to Vector Store
```http
POST /vector-store
```

**Request Body:**
```json
{
  "content": "Your content to be indexed",
  "metadata": {
    "title": "Content Title",
    "type": "blog_post",
    "tags": ["AI", "productivity"],
    "author": "Jane Smith"
  },
  "namespace": "content_library"
}
```

### Memory System Service (Port 8009)

#### Store Memory
```http
POST /memory
```

**Request Body:**
```json
{
  "context": "user_preferences",
  "data": {
    "preferred_tone": "professional",
    "target_audience": "tech_professionals",
    "content_types": ["blog_posts", "social_media"]
  },
  "user_id": "user123",
  "expires_at": "2024-12-31T23:59:59Z"
}
```

#### Retrieve Memory
```http
GET /memory?context=user_preferences&user_id=user123
```

## Error Handling

All APIs use standard HTTP status codes:

- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **429**: Rate Limited
- **500**: Internal Server Error

### Error Response Format
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request is missing required parameters",
    "details": {
      "missing_fields": ["topic", "target_audience"]
    },
    "request_id": "req_123456"
  }
}
```

## Rate Limits

- **Standard endpoints**: 100 requests per minute
- **Content generation**: 10 requests per minute
- **Search endpoints**: 1000 requests per minute

Rate limit headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

## Webhooks

Configure webhooks to receive real-time notifications:

### Webhook Events
- `task.completed`
- `content.created`
- `compliance.violation`
- `campaign.executed`

### Webhook Payload Example
```json
{
  "event": "content.created",
  "timestamp": "2024-01-15T10:00:00Z",
  "data": {
    "content_id": "content_123",
    "content_type": "blog_post",
    "title": "AI Productivity Guide",
    "status": "published"
  }
}
```

## SDKs and Libraries

### Python SDK
```python
from ai_agent_os import Client

client = Client(api_key="your_api_key", base_url="http://localhost:8000")

# Generate ideas
ideas = client.ideation.generate_ideas(
    topic="AI productivity",
    target_audience="tech professionals"
)

# Create design
design = client.design.create_design(
    design_type="social_media_post",
    content="Your content here"
)
```

### JavaScript SDK
```javascript
import { AIAgentOSClient } from '@ai-agent-os/client';

const client = new AIAgentOSClient({
  apiKey: 'your_api_key',
  baseUrl: 'http://localhost:8000'
});

// Generate ideas
const ideas = await client.ideation.generateIdeas({
  topic: 'AI productivity',
  targetAudience: 'tech professionals'
});
```

## Testing

### Health Check All Services
```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
# ... for all services
```

### API Testing with Postman
Import the Postman collection available at `/docs/postman_collection.json`

### Integration Testing
```bash
# Run integration tests
docker-compose exec core_orchestration python -m pytest tests/integration/
```
