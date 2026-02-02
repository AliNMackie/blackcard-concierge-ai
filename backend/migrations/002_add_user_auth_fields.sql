-- Migration 002: Add user authentication and trainer-client linking fields
-- Run this against the production database after deployment

-- Add email field with unique constraint
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR UNIQUE;

-- Add role field (client, trainer, admin)
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'client';

-- Add trainer_id for trainer-client linking
ALTER TABLE users ADD COLUMN IF NOT EXISTS trainer_id VARCHAR REFERENCES users(id);

-- Create index for efficient trainer-client lookups
CREATE INDEX IF NOT EXISTS idx_users_trainer ON users(trainer_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Update existing demo user to be an admin for testing
UPDATE users SET role = 'admin' WHERE id = 'auth0|demo_user' OR id = 'demo_user';
