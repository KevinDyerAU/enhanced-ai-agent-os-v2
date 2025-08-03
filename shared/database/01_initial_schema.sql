
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL, -- 'ideation', 'design', 'video', 'social_media', 'orchestration'
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'inactive', 'maintenance'
    capabilities JSONB NOT NULL DEFAULT '{}',
    configuration JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE agent_type_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type VARCHAR(100) NOT NULL,
    policy_name VARCHAR(255) NOT NULL,
    policy_rules JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    type VARCHAR(100) NOT NULL, -- 'content_creation', 'design', 'video', 'campaign'
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'failed', 'cancelled'
    priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
    assigned_agent_id UUID REFERENCES agents(id),
    requester_id VARCHAR(255),
    input_data JSONB NOT NULL DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE creative_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id),
    type VARCHAR(100) NOT NULL, -- 'image', 'video', 'text', 'design', 'campaign'
    asset_type VARCHAR(100) NOT NULL, -- 'image', 'video', 'text', 'design', 'campaign'
    title VARCHAR(500),
    description TEXT,
    content_url VARCHAR(1000),
    file_url VARCHAR(1000),
    file_metadata JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'pending_review', 'approved', 'rejected', 'published'
    brand_compliance_score DECIMAL(3,2),
    quality_metrics JSONB DEFAULT '{}',
    created_by_agent_id UUID REFERENCES agents(id),
    reviewed_by VARCHAR(255),
    approved_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL, -- 'task_created', 'asset_approved', 'policy_violation', etc.
    entity_type VARCHAR(100) NOT NULL, -- 'task', 'asset', 'agent', 'user'
    entity_id UUID NOT NULL,
    actor_type VARCHAR(50) NOT NULL, -- 'agent', 'user', 'system'
    actor_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE compliance_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(100) NOT NULL, -- 'task', 'asset', 'campaign'
    entity_id UUID NOT NULL,
    asset_id UUID REFERENCES creative_assets(id),
    validation_type VARCHAR(100) NOT NULL, -- 'brand_guidelines', 'legal_review', 'content_policy'
    status VARCHAR(50) NOT NULL, -- 'pending', 'passed', 'failed', 'requires_review'
    score DECIMAL(3,2),
    findings JSONB DEFAULT '{}',
    validated_by VARCHAR(255),
    validated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE ai_product_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_name VARCHAR(255) NOT NULL, -- 'canva', 'descript', 'openai', etc.
    integration_type VARCHAR(100) NOT NULL, -- 'api', 'webhook', 'oauth'
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'inactive', 'error'
    configuration JSONB NOT NULL DEFAULT '{}',
    rate_limits JSONB DEFAULT '{}',
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE integration_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_id UUID REFERENCES ai_product_integrations(id),
    agent_id UUID REFERENCES agents(id),
    task_id UUID REFERENCES tasks(id),
    operation VARCHAR(255) NOT NULL,
    request_data JSONB DEFAULT '{}',
    response_data JSONB DEFAULT '{}',
    status VARCHAR(50) NOT NULL, -- 'success', 'error', 'timeout'
    duration_ms INTEGER,
    cost_cents INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE social_media_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'scheduled', 'active', 'paused', 'completed'
    target_platforms TEXT[] NOT NULL, -- ['linkedin', 'twitter', 'facebook']
    campaign_objectives JSONB DEFAULT '{}',
    target_audience JSONB DEFAULT '{}',
    budget_cents INTEGER,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    created_by_agent_id UUID REFERENCES agents(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE social_media_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES social_media_campaigns(id),
    asset_id UUID REFERENCES creative_assets(id),
    platform VARCHAR(50) NOT NULL, -- 'linkedin', 'twitter', 'facebook'
    content TEXT NOT NULL,
    media_urls TEXT[],
    hashtags TEXT[],
    mentions TEXT[],
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'scheduled', 'published', 'failed'
    scheduled_for TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    platform_post_id VARCHAR(255),
    engagement_metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_agents_type ON agents(type);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_assigned_agent ON tasks(assigned_agent_id);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_creative_assets_status ON creative_assets(status);
CREATE INDEX idx_creative_assets_task_id ON creative_assets(task_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_compliance_validations_asset_id ON compliance_validations(asset_id);
CREATE INDEX idx_integration_usage_timestamp ON integration_usage(timestamp);
CREATE INDEX idx_social_media_posts_campaign_id ON social_media_posts(campaign_id);
CREATE INDEX idx_social_media_posts_status ON social_media_posts(status);
