-- Migration: Add Trial Support (SQLite version)
-- Adds trial_ends_at field to track when free trials expire

-- Add trial_ends_at column to tenants table
-- SQLite doesn't support IF NOT EXISTS for ALTER TABLE ADD COLUMN
-- So we'll check if column exists first (application-level check)

-- Note: SQLite migration should be handled in application code
-- This file is for reference only
-- See app/storage/tenant_db.py for actual schema initialization

-- For SQLite, the column is added in tenant_db.py schema initialization
-- Existing data handling should be done in Python code

