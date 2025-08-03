# User Guide

Comprehensive guide to using the Enhanced AI Agent OS v2 for content creation, enterprise governance, and intelligent task orchestration.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Mission Control Dashboard](#mission-control-dashboard)
3. [Creator Layer Services](#creator-layer-services)
4. [Enterprise Governance](#enterprise-governance)
5. [Data Architecture & Search](#data-architecture--search)
6. [Workflows & Automation](#workflows--automation)
7. [Monitoring & Analytics](#monitoring--analytics)

## Getting Started

### Accessing the System

After installation, access the system through:
- **Primary Interface**: Mission Control Dashboard at http://localhost:3000
- **API Interface**: Direct API access at http://localhost:8000/docs
- **Monitoring**: Grafana dashboard at http://localhost:3001

### User Roles

The system supports different user roles:
- **Content Creator**: Generate ideas, create designs, produce content
- **Campaign Manager**: Execute and monitor marketing campaigns
- **Compliance Officer**: Set governance rules, review content
- **Administrator**: System configuration and monitoring

## Mission Control Dashboard

### Dashboard Overview

The Mission Control Dashboard provides a centralized interface for:
- **Agent Status**: Real-time health monitoring of all AI agents
- **Task Queue**: View and manage active tasks
- **Content Pipeline**: Track content creation progress
- **Compliance Status**: Monitor governance and approval workflows
- **Analytics**: Performance metrics and insights

### Key Features

#### Agent Activity Stream
- Real-time updates from all AI agents
- Task completion notifications
- Error alerts and system status
- Performance metrics

#### Task Management
- Create new tasks manually
- Monitor automated task execution
- Set priorities and deadlines
- Track completion status

#### Content Library
- Browse generated content
- Search by tags, type, or date
- Preview designs and videos
- Download assets

## Creator Layer Services

### Ideation Agent (Port 8001)

Generate market-intelligent content ideas.

#### Features
- **Market Intelligence**: Analyze trends and competitor content
- **Audience Targeting**: Tailor ideas to specific demographics
- **Content Formats**: Support for various content types
- **Semantic Search**: Leverage past successful content

#### Usage
```json
POST /generate-ideas
{
  "topic": "AI productivity tools",
  "target_audience": "tech professionals",
  "content_type": "blog_post",
  "market_context": "B2B SaaS"
}
```

#### Response
```json
{
  "ideas": [
    {
      "title": "10 AI Tools That Will Transform Your Workflow",
      "description": "Comprehensive guide to productivity AI tools",
      "market_score": 8.5,
      "trend_alignment": "high",
      "keywords": ["AI", "productivity", "automation"]
    }
  ]
}
```

### Design Agent (Port 8002)

Create branded visual content with Canva integration.

#### Features
- **Brand Consistency**: Automatic brand guideline enforcement
- **Template Library**: Access to professional templates
- **Multi-Format**: Social media, presentations, documents
- **Compliance Scoring**: Automated brand compliance checking

#### Usage
```json
POST /create-design
{
  "design_type": "social_media_post",
  "content": "Your content text here",
  "brand_guidelines": {
    "colors": ["#FF6B35", "#004E89"],
    "fonts": ["Roboto", "Open Sans"]
  },
  "dimensions": "1080x1080"
}
```

### Video Agent (Port 8003)

Generate video content with Descript integration.

#### Features
- **Text-to-Speech**: AI-generated voiceovers
- **Video Assembly**: Automated video creation
- **Script Generation**: AI-powered script writing
- **Multi-Platform**: Optimized for different platforms

#### Usage
```json
POST /create-video-content
{
  "script": "Your video script",
  "voice_style": "professional",
  "duration": "60s",
  "platform": "linkedin"
}
```

### Social Media Manager (Port 8004)

Execute multi-platform social media campaigns.

#### Features
- **Platform Integration**: LinkedIn, Twitter, Facebook
- **Scheduling**: Automated post scheduling
- **Analytics**: Performance tracking
- **A/B Testing**: Content variant testing

#### Usage
```json
POST /execute-campaign
{
  "content": {
    "text": "Your post content",
    "media": ["image_url", "video_url"]
  },
  "platforms": ["linkedin", "twitter"],
  "schedule": "2024-01-15T10:00:00Z"
}
```

## Enterprise Governance

### Compliance Engine (Port 8005)

Enforce organizational policies and brand guidelines.

#### Features
- **Policy Definition**: Create custom compliance rules
- **Content Scanning**: Automated policy violation detection
- **Risk Scoring**: Assess content risk levels
- **Approval Workflows**: Multi-stage review processes

#### Setting Up Compliance Rules
```json
POST /compliance-rules
{
  "rule_name": "Brand Guidelines",
  "criteria": {
    "required_colors": ["#FF6B35", "#004E89"],
    "forbidden_words": ["competitor_name"],
    "tone_requirements": "professional"
  },
  "severity": "high"
}
```

### Audit Service (Port 8006)

Track all system activities for compliance and security.

#### Features
- **Activity Logging**: Comprehensive audit trails
- **User Tracking**: Monitor user actions
- **Content History**: Track content modifications
- **Compliance Reports**: Generate audit reports

### Airlock System

Content review and approval workflow.

#### Workflow Stages
1. **Content Generation**: AI creates content
2. **Automated Screening**: Compliance engine review
3. **Human Review**: Manual approval if needed
4. **Final Approval**: Content released for publication
5. **Post-Publication Monitoring**: Ongoing compliance tracking

## Data Architecture & Search

### Vector Search Service (Port 8008)

Semantic search across all content and knowledge.

#### Features
- **Semantic Search**: Find content by meaning, not just keywords
- **Similarity Matching**: Discover related content
- **Recommendation Engine**: Suggest relevant content
- **Knowledge Retrieval**: Access organizational knowledge base

#### Usage
```json
POST /search
{
  "query": "marketing strategies for B2B SaaS",
  "filters": {
    "content_type": "blog_post",
    "date_range": "last_30_days"
  },
  "limit": 10
}
```

### Memory System Service (Port 8009)

Intelligent memory and context management.

#### Features
- **Context Preservation**: Maintain conversation context
- **Learning**: Improve responses based on feedback
- **Personalization**: Adapt to user preferences
- **Knowledge Integration**: Connect disparate information

## Workflows & Automation

### Creating Custom Workflows

1. **Define Trigger**: What starts the workflow
2. **Set Actions**: What happens in sequence
3. **Add Conditions**: Decision points in the workflow
4. **Configure Notifications**: Alert stakeholders
5. **Test & Deploy**: Validate workflow before activation

### Example Workflow: Content Creation Pipeline

```yaml
workflow_name: "Blog Post Creation"
trigger: "new_topic_request"
steps:
  - ideation: "generate_ideas"
  - design: "create_featured_image"
  - review: "compliance_check"
  - approval: "human_review"
  - publish: "schedule_publication"
```

## Monitoring & Analytics

### Grafana Dashboard (Port 3001)

Comprehensive system monitoring and analytics.

#### Key Metrics
- **Service Health**: Uptime and response times
- **Content Performance**: Engagement and conversion rates
- **User Activity**: System usage patterns
- **Error Rates**: System reliability metrics

#### Custom Dashboards
Create custom dashboards for:
- Campaign performance
- Content creation metrics
- Compliance monitoring
- Resource utilization

### Prometheus Metrics (Port 9090)

Raw metrics collection and alerting.

#### Available Metrics
- `agent_response_time`: Service response times
- `content_generation_rate`: Content creation volume
- `compliance_violations`: Policy violation counts
- `user_activity`: User interaction metrics

## Best Practices

### Content Creation
1. **Start with Research**: Use market intelligence for idea generation
2. **Maintain Brand Consistency**: Always apply brand guidelines
3. **Test Variations**: Create multiple content variants
4. **Monitor Performance**: Track engagement and adjust strategy

### Governance
1. **Define Clear Policies**: Establish comprehensive compliance rules
2. **Regular Reviews**: Periodically update governance policies
3. **Train Users**: Ensure team understands compliance requirements
4. **Monitor Continuously**: Use automated scanning and alerts

### System Management
1. **Regular Backups**: Backup database and configurations
2. **Monitor Resources**: Track system performance and capacity
3. **Update Dependencies**: Keep services and APIs current
4. **Security Reviews**: Regular security audits and updates

## Troubleshooting

### Common Issues

**Content Generation Fails**
- Check API key validity
- Verify service health endpoints
- Review error logs in Grafana

**Compliance Violations**
- Review compliance rules configuration
- Check content against brand guidelines
- Verify approval workflow settings

**Performance Issues**
- Monitor resource usage in Grafana
- Check database connection health
- Verify network connectivity

### Getting Support

1. Check service logs: `docker-compose logs [service-name]`
2. Review health endpoints: `/health` on each service
3. Monitor Grafana dashboards for system metrics
4. Consult the [Troubleshooting Guide](troubleshooting.md)

## Advanced Features

### API Integration
- Custom webhook endpoints
- Third-party service integration
- Batch processing capabilities
- Real-time event streaming

### Machine Learning
- Custom model training
- Performance optimization
- Feedback loop integration
- Continuous learning

### Scalability
- Horizontal service scaling
- Load balancing configuration
- Database optimization
- Caching strategies
