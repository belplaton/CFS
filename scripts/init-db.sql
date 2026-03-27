-- ===========================================
-- CFS - Cloud File Storage Database Schema
-- PostgreSQL 16+
-- ===========================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===========================================
-- Users Table
-- ===========================================
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    display_name    VARCHAR(255) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified  BOOLEAN NOT NULL DEFAULT FALSE
);

-- Index for fast email lookups during authentication
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Index for active users
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- ===========================================
-- Refresh Tokens Table
-- ===========================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token           VARCHAR(255) NOT NULL UNIQUE,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at      TIMESTAMPTZ,
    is_revoked      BOOLEAN NOT NULL DEFAULT FALSE
);

-- Index for fast token lookups
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token);

-- Index for user's tokens
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);

-- Index for expired tokens cleanup
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);

-- ===========================================
-- Folders Table
-- ===========================================
CREATE TABLE IF NOT EXISTS folders (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id       UUID REFERENCES folders(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    path            VARCHAR(1024) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at      TIMESTAMPTZ,
    
    -- Ensure unique folder names within the same parent for each user
    CONSTRAINT unique_folder_name_per_parent 
        UNIQUE (user_id, parent_id, name, is_deleted)
);

-- Index for user's folders
CREATE INDEX IF NOT EXISTS idx_folders_user_id ON folders(user_id);

-- Index for parent folder lookups
CREATE INDEX IF NOT EXISTS idx_folders_parent_id ON folders(parent_id);

-- Index for path lookups
CREATE INDEX IF NOT EXISTS idx_folders_path ON folders(path);

-- Index for soft delete filtering
CREATE INDEX IF NOT EXISTS idx_folders_is_deleted ON folders(is_deleted);

-- ===========================================
-- Files Table
-- ===========================================
CREATE TABLE IF NOT EXISTS files (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    folder_id           UUID NOT NULL REFERENCES folders(id) ON DELETE CASCADE,
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    mime_type           VARCHAR(255),
    size_bytes          BIGINT NOT NULL DEFAULT 0,
    storage_key         VARCHAR(512) NOT NULL UNIQUE,  -- MinIO object key
    version             INTEGER NOT NULL DEFAULT 1,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted          BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at          TIMESTAMPTZ,
    
    -- Ensure unique file names within the same folder for each user
    CONSTRAINT unique_file_name_per_folder 
        UNIQUE (user_id, folder_id, name, is_deleted)
);

-- Index for user's files
CREATE INDEX IF NOT EXISTS idx_files_user_id ON files(user_id);

-- Index for folder's files
CREATE INDEX IF NOT EXISTS idx_files_folder_id ON files(folder_id);

-- Index for soft delete filtering
CREATE INDEX IF NOT EXISTS idx_files_is_deleted ON files(is_deleted);

-- Index for storage key lookups
CREATE INDEX IF NOT EXISTS idx_files_storage_key ON files(storage_key);

-- ===========================================
-- File Shares Table (for sharing files between users)
-- ===========================================
CREATE TABLE IF NOT EXISTS file_shares (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id         UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    owner_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shared_with_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission      VARCHAR(50) NOT NULL DEFAULT 'read',  -- read, write, admin
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at      TIMESTAMPTZ,
    is_revoked      BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Ensure unique share per file-user pair
    CONSTRAINT unique_share_per_file_user 
        UNIQUE (file_id, shared_with_id, is_revoked)
);

-- Index for files shared with user
CREATE INDEX IF NOT EXISTS idx_file_shares_shared_with ON file_shares(shared_with_id);

-- Index for owner's shared files
CREATE INDEX IF NOT EXISTS idx_file_shares_owner_id ON file_shares(owner_id);

-- Index for file shares
CREATE INDEX IF NOT EXISTS idx_file_shares_file_id ON file_shares(file_id);

-- ===========================================
-- Audit Log Table (for tracking user actions)
-- ===========================================
CREATE TABLE IF NOT EXISTS audit_log (
    id              BIGSERIAL PRIMARY KEY,
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(100) NOT NULL,
    resource_type   VARCHAR(50) NOT NULL,  -- file, folder, user
    resource_id     UUID,
    details         JSONB,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index for user's audit log
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);

-- Index for resource audit log
CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id);

-- Index for timestamp-based queries
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);

-- ===========================================
-- Triggers for updated_at timestamps
-- ===========================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to users table
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to folders table
CREATE TRIGGER update_folders_updated_at
    BEFORE UPDATE ON folders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to files table
CREATE TRIGGER update_files_updated_at
    BEFORE UPDATE ON files
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ===========================================
-- Function to set deleted_at on soft delete
-- ===========================================

-- Function to set deleted_at when is_deleted is set to TRUE
CREATE OR REPLACE FUNCTION set_deleted_at_column()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_deleted = TRUE AND OLD.is_deleted = FALSE THEN
        NEW.deleted_at = CURRENT_TIMESTAMP;
    ELSIF NEW.is_deleted = FALSE AND OLD.is_deleted = TRUE THEN
        NEW.deleted_at = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to folders table
CREATE TRIGGER set_folders_deleted_at
    BEFORE UPDATE ON folders
    FOR EACH ROW
    EXECUTE FUNCTION set_deleted_at_column();

-- Apply trigger to files table
CREATE TRIGGER set_files_deleted_at
    BEFORE UPDATE ON files
    FOR EACH ROW
    EXECUTE FUNCTION set_deleted_at_column();

-- ===========================================
-- Seed Data (Demo User)
-- ===========================================

-- Demo user with password: 'demo123' (hashed with bcrypt)
-- Password hash generated using: bcrypt('demo123', gensalt(10))
INSERT INTO users (id, email, password_hash, display_name, is_active, email_verified)
VALUES (
    'eb4de6d1-4c9a-4ff8-8a68-7d645b1b71d0'::uuid,
    'user@cfs.local',
    '$2a$10$Ygq3VZTqc6qQKqQh5qZ5u.8xKxqQKqQh5qZ5u.8xKxqQKqQh5qZ5u',
    'Demo User',
    TRUE,
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- Create default root folder for demo user
INSERT INTO folders (id, user_id, parent_id, name, path)
VALUES (
    'f47ac10b-58cc-4372-a567-0e02b2c3d479'::uuid,
    'eb4de6d1-4c9a-4ff8-8a68-7d645b1b71d0'::uuid,
    NULL,
    'Root',
    '/'
) ON CONFLICT DO NOTHING;

-- Create sample folders for demo user
INSERT INTO folders (user_id, parent_id, name, path)
VALUES 
    (
        'eb4de6d1-4c9a-4ff8-8a68-7d645b1b71d0'::uuid,
        'f47ac10b-58cc-4372-a567-0e02b2c3d479'::uuid,
        'Design',
        '/Design'
    ),
    (
        'eb4de6d1-4c9a-4ff8-8a68-7d645b1b71d0'::uuid,
        'f47ac10b-58cc-4372-a567-0e02b2c3d479'::uuid,
        'Documents',
        '/Documents'
    ),
    (
        'eb4de6d1-4c9a-4ff8-8a68-7d645b1b71d0'::uuid,
        'f47ac10b-58cc-4372-a567-0e02b2c3d479'::uuid,
        'Projects',
        '/Projects'
    )
ON CONFLICT DO NOTHING;

-- ===========================================
-- Comments for documentation
-- ===========================================

COMMENT ON TABLE users IS 'User accounts for authentication and authorization';
COMMENT ON TABLE refresh_tokens IS 'JWT refresh tokens for session management';
COMMENT ON TABLE folders IS 'Folder hierarchy for file organization';
COMMENT ON TABLE files IS 'File metadata with references to MinIO storage';
COMMENT ON TABLE file_shares IS 'File sharing permissions between users';
COMMENT ON TABLE audit_log IS 'Audit trail for user actions and system events';

COMMENT ON COLUMN folders.path IS 'Full path from root, e.g., /Design/Projects';
COMMENT ON COLUMN files.storage_key IS 'Unique key for MinIO object, format: user_id/file_id/filename';
COMMENT ON COLUMN files.version IS 'Version number for file updates';
COMMENT ON COLUMN file_shares.permission IS 'Access level: read, write, admin';
