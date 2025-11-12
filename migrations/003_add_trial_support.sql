-- Migration: Add Trial Support
-- Adds trial_ends_at field to track when free trials expire

-- Add trial_ends_at column to tenants table
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMP;

-- Create index for efficient trial expiration queries
CREATE INDEX IF NOT EXISTS idx_tenants_trial_ends_at ON tenants(trial_ends_at) WHERE trial_ends_at IS NOT NULL;

-- Handle existing tenants with trial status but no trial_ends_at
-- Set trial_ends_at to 7 days from now for active trials, or mark as expired if it's been too long
UPDATE tenants 
SET trial_ends_at = CURRENT_TIMESTAMP + INTERVAL '7 days'
WHERE subscription_status = 'trial' 
  AND trial_ends_at IS NULL
  AND created_at > CURRENT_TIMESTAMP - INTERVAL '7 days';

-- Mark old trial tenants without trial_ends_at as expired
UPDATE tenants 
SET subscription_status = 'expired',
    subscription_tier = 'free'
WHERE subscription_status = 'trial' 
  AND trial_ends_at IS NULL
  AND created_at <= CURRENT_TIMESTAMP - INTERVAL '7 days';

