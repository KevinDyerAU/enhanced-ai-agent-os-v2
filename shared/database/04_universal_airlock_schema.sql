-- Universal Airlock Tables
-- Create airlock_content_types table if it doesn't exist
CREATE TABLE IF NOT EXISTS airlock_content_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE, -- 'training_validation', 'creative_asset', 'ideation', etc.
    description TEXT,
    schema_definition JSONB, -- JSON schema for content validation
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create airlock_items table if it doesn't exist
CREATE TABLE IF NOT EXISTS airlock_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_type_id UUID NOT NULL REFERENCES airlock_content_types(id),
    source_service VARCHAR(100) NOT NULL, -- 'training_validation', 'ideation', etc.
    source_id VARCHAR(255) NOT NULL, -- ID in the source service
    title VARCHAR(500) NOT NULL,
    description TEXT,
    content JSONB NOT NULL, -- The actual content being reviewed
    metadata JSONB DEFAULT '{}', -- Additional metadata
    status VARCHAR(50) NOT NULL DEFAULT 'pending_review', -- 'pending_review', 'approved', 'rejected', 'requires_changes'
    priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
    created_by_agent_id UUID REFERENCES agents(id),
    assigned_reviewer_id VARCHAR(255), -- User ID of assigned reviewer
    reviewed_by VARCHAR(255), -- User ID of reviewer who made decision
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_deadline TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(source_service, source_id)
);

CREATE TABLE IF NOT EXISTS airlock_chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    airlock_item_id UUID NOT NULL REFERENCES airlock_items(id) ON DELETE CASCADE,
    participant_type VARCHAR(50) NOT NULL, -- 'human', 'agent'
    participant_id VARCHAR(255) NOT NULL, -- User ID or Agent ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS airlock_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES airlock_chat_sessions(id) ON DELETE CASCADE,
    sender_type VARCHAR(50) NOT NULL, -- 'human', 'agent'
    sender_id VARCHAR(255) NOT NULL, -- User ID or Agent ID
    message_type VARCHAR(50) DEFAULT 'text', -- 'text', 'feedback', 'suggestion', 'approval', 'rejection'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}', -- Additional data like feedback scores, suggestions, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS airlock_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    airlock_item_id UUID NOT NULL REFERENCES airlock_items(id) ON DELETE CASCADE,
    feedback_type VARCHAR(50) NOT NULL, -- 'approval', 'rejection', 'suggestion', 'rating'
    feedback_data JSONB NOT NULL, -- Structured feedback data
    provided_by VARCHAR(255) NOT NULL, -- User ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS airlock_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    airlock_item_id UUID NOT NULL REFERENCES airlock_items(id) ON DELETE CASCADE,
    revision_number INTEGER NOT NULL,
    content JSONB NOT NULL, -- The revised content
    changes_summary TEXT,
    created_by VARCHAR(255), -- User ID or 'system' for AI revisions
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(airlock_item_id, revision_number)
);

-- Indexes for performance
CREATE INDEX idx_airlock_items_status ON airlock_items(status);
CREATE INDEX idx_airlock_items_source ON airlock_items(source_service, source_id);
CREATE INDEX idx_airlock_items_reviewer ON airlock_items(assigned_reviewer_id);
CREATE INDEX idx_airlock_chat_messages_session ON airlock_chat_messages(session_id);
CREATE INDEX idx_airlock_feedback_item ON airlock_feedback(airlock_item_id);