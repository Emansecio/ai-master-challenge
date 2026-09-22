CREATE TABLE IF NOT EXISTS settings (id boolean PRIMARY KEY DEFAULT true CHECK(id), policy_hash text NOT NULL, policy jsonb NOT NULL);
CREATE TABLE IF NOT EXISTS source_records (table_name text NOT NULL, record_key text NOT NULL, doc jsonb NOT NULL, PRIMARY KEY(table_name,record_key));
CREATE TABLE IF NOT EXISTS opportunities (id text PRIMARY KEY, version bigint NOT NULL CHECK(version>0), doc jsonb NOT NULL, updated_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX IF NOT EXISTS opportunity_agent ON opportunities((doc->>'sales_agent'));
CREATE INDEX IF NOT EXISTS opportunity_manager ON opportunities((doc->>'manager'));
CREATE TABLE IF NOT EXISTS opportunity_versions (opportunity_id text NOT NULL REFERENCES opportunities(id), version bigint NOT NULL, doc jsonb NOT NULL, actor text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(opportunity_id,version));
CREATE TABLE IF NOT EXISTS users (id text PRIMARY KEY, token_hash text NOT NULL UNIQUE, role text NOT NULL CHECK(role IN ('admin','manager','seller')), scope text NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS sessions (token_hash text PRIMARY KEY, user_id text NOT NULL REFERENCES users(id), expires_at timestamptz NOT NULL);
CREATE TABLE IF NOT EXISTS classifications (
 opportunity_id text NOT NULL, version bigint NOT NULL, policy_hash text NOT NULL, response jsonb NOT NULL,
 origin text NOT NULL, current_at_commit boolean NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(opportunity_id,version,policy_hash), FOREIGN KEY(opportunity_id,version) REFERENCES opportunity_versions(opportunity_id,version)
);
CREATE TABLE IF NOT EXISTS jobs (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), opportunity_id text NOT NULL, version bigint NOT NULL, policy_hash text NOT NULL,
 state jsonb NOT NULL, policy jsonb NOT NULL, status text NOT NULL CHECK(status IN ('pending','running','succeeded','stale','failed')),
 attempts integer NOT NULL DEFAULT 0 CHECK(attempts>=0), lease_token uuid, lease_until timestamptz,
 available_at timestamptz NOT NULL DEFAULT now(), error text NOT NULL DEFAULT '', created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(opportunity_id,version,policy_hash), FOREIGN KEY(opportunity_id,version) REFERENCES opportunity_versions(opportunity_id,version)
);
CREATE INDEX IF NOT EXISTS jobs_ready ON jobs(status,available_at,lease_until);
CREATE TABLE IF NOT EXISTS job_attempts (job_id uuid NOT NULL REFERENCES jobs(id), attempt integer NOT NULL, outcome text NOT NULL, elapsed_ms bigint NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(job_id,attempt));
-- An expired lease cannot supply a measured provider-call duration.
ALTER TABLE job_attempts ALTER COLUMN elapsed_ms DROP NOT NULL;
CREATE TABLE IF NOT EXISTS provider_gate (id boolean PRIMARY KEY DEFAULT true CHECK(id), next_start timestamptz NOT NULL DEFAULT now());
INSERT INTO provider_gate(id) VALUES(true) ON CONFLICT DO NOTHING;
