-- Create airlock_content_types table if it doesn't exist
CREATE TABLE IF NOT EXISTS airlock_content_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    schema_version VARCHAR(20) DEFAULT '1.0',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create airlock_items table if it doesn't exist
CREATE TABLE IF NOT EXISTS airlock_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_type_id INTEGER NOT NULL REFERENCES airlock_content_types(id),
    source_service VARCHAR(100) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    content JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    status VARCHAR(50) DEFAULT 'pending_review' CHECK (status IN ('pending_review', 'under_review', 'approved', 'rejected', 'revision_requested')),
    created_by_agent_id VARCHAR(255),
    assigned_reviewer_id VARCHAR(255),
    review_deadline TIMESTAMP WITH TIME ZONE,
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by VARCHAR(255),
    rejected_at TIMESTAMP WITH TIME ZONE,
    rejected_by VARCHAR(255),
    rejection_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_service, source_id)
);

CREATE TABLE airlock_chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    airlock_item_id UUID NOT NULL REFERENCES airlock_items(id) ON DELETE CASCADE,
    participant_type VARCHAR(20) NOT NULL CHECK (participant_type IN ('human', 'agent')),
    participant_id VARCHAR(255) NOT NULL,
    participant_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(airlock_item_id, participant_type, participant_id)
);

CREATE TABLE airlock_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES airlock_chat_sessions(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL CHECK (sender_type IN ('human', 'agent')),
    sender_id VARCHAR(255) NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text' CHECK (message_type IN ('text', 'feedback', 'approval', 'rejection', 'suggestion', 'question', 'file_attachment')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    parent_message_id UUID REFERENCES airlock_chat_messages(id),
    thread_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE airlock_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    airlock_item_id UUID NOT NULL REFERENCES airlock_items(id) ON DELETE CASCADE,
    feedback_type VARCHAR(50) NOT NULL CHECK (feedback_type IN ('approval', 'rejection', 'suggestion', 'question', 'rating', 'revision_request')),
    feedback_data JSONB NOT NULL,
    provided_by VARCHAR(255) NOT NULL,
    provided_by_type VARCHAR(20) DEFAULT 'human' CHECK (provided_by_type IN ('human', 'agent')),
    severity VARCHAR(20) DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'dismissed')),
    resolved_by VARCHAR(255),
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE airlock_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    airlock_item_id UUID NOT NULL REFERENCES airlock_items(id) ON DELETE CASCADE,
    revision_number INTEGER NOT NULL,
    previous_content JSONB,
    new_content JSONB NOT NULL,
    changes_summary TEXT,
    revision_type VARCHAR(50) DEFAULT 'content_update' CHECK (revision_type IN ('content_update', 'status_change', 'metadata_update', 'feedback_incorporation')),
    created_by VARCHAR(255) NOT NULL,
    created_by_type VARCHAR(20) DEFAULT 'human' CHECK (created_by_type IN ('human', 'agent')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(airlock_item_id, revision_number)
);

CREATE INDEX IF NOT EXISTS idx_airlock_items_status ON airlock_items(status);
CREATE INDEX IF NOT EXISTS idx_airlock_items_content_type ON airlock_items(content_type_id);
CREATE INDEX IF NOT EXISTS idx_airlock_items_source_service ON airlock_items(source_service);
CREATE INDEX IF NOT EXISTS idx_airlock_items_assigned_reviewer ON airlock_items(assigned_reviewer_id);
CREATE INDEX IF NOT EXISTS idx_airlock_items_created_at ON airlock_items(created_at);
CREATE INDEX IF NOT EXISTS idx_airlock_items_priority ON airlock_items(priority);

CREATE INDEX IF NOT EXISTS idx_airlock_chat_sessions_item_id ON airlock_chat_sessions(airlock_item_id);
CREATE INDEX IF NOT EXISTS idx_airlock_chat_sessions_participant ON airlock_chat_sessions(participant_type, participant_id);

CREATE INDEX IF NOT EXISTS idx_airlock_chat_messages_session_id ON airlock_chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_airlock_chat_messages_created_at ON airlock_chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_airlock_chat_messages_thread_id ON airlock_chat_messages(thread_id);

CREATE INDEX IF NOT EXISTS idx_airlock_feedback_item_id ON airlock_feedback(airlock_item_id);
CREATE INDEX IF NOT EXISTS idx_airlock_feedback_type ON airlock_feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_airlock_feedback_status ON airlock_feedback(status);

CREATE INDEX IF NOT EXISTS idx_airlock_revisions_item_id ON airlock_revisions(airlock_item_id);
CREATE INDEX IF NOT EXISTS idx_airlock_revisions_number ON airlock_revisions(airlock_item_id, revision_number);

INSERT INTO airlock_content_types (name, description) VALUES
    ('training_validation', 'Training validation results and assessments'),
    ('creative_asset', 'Creative content from ideation and design services'),
    ('compliance_report', 'Compliance validation reports and findings'),
    ('audit_finding', 'Audit results and recommendations'),
    ('social_media_content', 'Social media posts and campaigns'),
    ('video_content', 'Video assets and multimedia content'),
    ('document_analysis', 'Document processing and analysis results'),
    ('web_intelligence', 'Web scraping and intelligence gathering results'),
    ('general_content', 'General purpose content requiring review')
ON CONFLICT (name) DO NOTHING;

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_airlock_items_updated_at BEFORE UPDATE ON airlock_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_airlock_chat_messages_updated_at BEFORE UPDATE ON airlock_chat_messages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_airlock_feedback_updated_at BEFORE UPDATE ON airlock_feedback FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_airlock_content_types_updated_at BEFORE UPDATE ON airlock_content_types FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
