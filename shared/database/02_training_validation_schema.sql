-- Create training_units table if it doesn't exist
CREATE TABLE IF NOT EXISTS training_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_code VARCHAR(20) NOT NULL UNIQUE, -- e.g., 'BSBCMM411'
    title VARCHAR(500) NOT NULL,
    description TEXT,
    field VARCHAR(200),
    level VARCHAR(50),
    points DECIMAL(4,2),
    elements JSONB DEFAULT '{}', -- Array of elements with performance criteria
    performance_criteria JSONB DEFAULT '{}',
    knowledge_evidence JSONB DEFAULT '{}',
    performance_evidence JSONB DEFAULT '{}',
    foundation_skills JSONB DEFAULT '{}',
    assessment_conditions JSONB DEFAULT '{}',
    raw_data JSONB DEFAULT '{}', -- Full scraped data from training.gov.au
    last_updated_from_source TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS validation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    training_unit_id UUID REFERENCES training_units(id),
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'failed'
    configuration JSONB DEFAULT '{}', -- Validation settings, strictness levels
    progress JSONB DEFAULT '{}', -- Current progress tracking
    created_by VARCHAR(255) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS validation_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES validation_sessions(id),
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_type VARCHAR(50) NOT NULL, -- 'pdf', 'docx', 'pptx', etc.
    file_size_bytes BIGINT,
    content_extracted TEXT, -- Extracted text content
    metadata JSONB DEFAULT '{}', -- File metadata, sections, etc.
    processing_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    processed_at TIMESTAMP WITH TIME ZONE,
    uploaded_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES validation_sessions(id),
    document_id UUID REFERENCES validation_documents(id),
    validation_type VARCHAR(100) NOT NULL, -- 'assessment_conditions', 'knowledge_evidence', 'performance_evidence', 'foundation_skills', 'epc'
    category VARCHAR(100), -- Specific category within validation type
    status VARCHAR(50) NOT NULL, -- 'passed', 'failed', 'partial', 'not_found'
    score DECIMAL(5,2), -- Percentage score or confidence level
    findings JSONB DEFAULT '{}', -- Detailed findings, gaps, recommendations
    evidence JSONB DEFAULT '{}', -- Supporting evidence found in documents
    recommendations JSONB DEFAULT '{}', -- Improvement suggestions
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS generated_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES validation_sessions(id),
    training_unit_id UUID REFERENCES training_units(id),
    question_type VARCHAR(50) NOT NULL, -- 'open_ended', 'multiple_choice', 'scenario_based'
    category VARCHAR(100) NOT NULL, -- 'knowledge_evidence', 'performance_evidence', 'foundation_skills'
    question_text TEXT NOT NULL,
    options JSONB DEFAULT '{}', -- For multiple choice questions
    benchmark_answer TEXT,
    assessment_guidance TEXT,
    difficulty_level VARCHAR(20) DEFAULT 'medium', -- 'easy', 'medium', 'hard'
    bloom_taxonomy_level VARCHAR(50), -- 'remember', 'understand', 'apply', 'analyze', 'evaluate', 'create'
    metadata JSONB DEFAULT '{}',
    quality_score DECIMAL(3,2), -- Quality assessment score
    review_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'needs_revision'
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS question_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_code VARCHAR(20) NOT NULL,
    question_id UUID REFERENCES generated_questions(id),
    tags TEXT[], -- Searchable tags
    usage_count INTEGER DEFAULT 0,
    average_rating DECIMAL(3,2),
    is_public BOOLEAN DEFAULT false,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS validation_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES validation_sessions(id),
    report_type VARCHAR(50) NOT NULL, -- 'summary', 'detailed', 'executive'
    format VARCHAR(20) NOT NULL, -- 'markdown', 'pdf', 'html'
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    file_path VARCHAR(1000),
    metadata JSONB DEFAULT '{}',
    generated_by VARCHAR(255) NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS training_validation_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES validation_sessions(id),
    event_type VARCHAR(100) NOT NULL, -- 'session_created', 'document_uploaded', 'validation_completed', 'question_generated'
    entity_type VARCHAR(100) NOT NULL, -- 'session', 'document', 'validation', 'question'
    entity_id UUID NOT NULL,
    actor_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_training_units_code ON training_units(unit_code);
CREATE INDEX idx_training_units_field ON training_units(field);
CREATE INDEX idx_validation_sessions_status ON validation_sessions(status);
CREATE INDEX idx_validation_sessions_created_by ON validation_sessions(created_by);
CREATE INDEX idx_validation_documents_session_id ON validation_documents(session_id);
CREATE INDEX idx_validation_documents_processing_status ON validation_documents(processing_status);
CREATE INDEX idx_validation_results_session_id ON validation_results(session_id);
CREATE INDEX idx_validation_results_validation_type ON validation_results(validation_type);
CREATE INDEX idx_generated_questions_session_id ON generated_questions(session_id);
CREATE INDEX idx_generated_questions_category ON generated_questions(category);
CREATE INDEX idx_generated_questions_review_status ON generated_questions(review_status);
CREATE INDEX idx_question_library_unit_code ON question_library(unit_code);
CREATE INDEX idx_question_library_tags ON question_library USING GIN(tags);
CREATE INDEX idx_validation_reports_session_id ON validation_reports(session_id);
CREATE INDEX idx_training_validation_audit_session_id ON training_validation_audit(session_id);
CREATE INDEX idx_training_validation_audit_timestamp ON training_validation_audit(timestamp);
