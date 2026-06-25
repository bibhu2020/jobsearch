-- PostgreSQL schema for Linear Lantern (Neon / any PostgreSQL)

CREATE TABLE IF NOT EXISTS users (
  id            SERIAL PRIMARY KEY,
  email         TEXT    UNIQUE NOT NULL,
  password_hash TEXT    NOT NULL,
  name          TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_profiles (
  id              SERIAL PRIMARY KEY,
  user_id         INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  resume_path     TEXT,           -- GitHub raw URL after upload
  resume_text     TEXT,           -- raw extracted text (cached for AI use)
  linkedin_url    TEXT,
  location        TEXT,
  profile_summary TEXT,
  skills          TEXT,           -- JSON array of strings
  experience      TEXT,           -- JSON array of objects
  education       TEXT,           -- JSON array of objects
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS jobs (
  id          SERIAL PRIMARY KEY,
  user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title       TEXT,
  company     TEXT,
  location    TEXT,
  description TEXT,
  url         TEXT,
  source      TEXT,               -- manual_url | manual_text | search_agent
  raw_content TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pipeline_cards (
  id         SERIAL PRIMARY KEY,
  job_id     INTEGER NOT NULL REFERENCES jobs(id)  ON DELETE CASCADE,
  user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  stage      TEXT    NOT NULL DEFAULT 'wishlist',  -- wishlist|applied|interviewing|offer|rejected
  position   INTEGER NOT NULL DEFAULT 0,
  notes      TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS generated_kits (
  id                SERIAL PRIMARY KEY,
  pipeline_card_id  INTEGER NOT NULL REFERENCES pipeline_cards(id) ON DELETE CASCADE,
  type              TEXT    NOT NULL,  -- cover_letter|resume|interview_questions|company_brief
  content           TEXT,              -- editable markdown
  file_path         TEXT,              -- GitHub raw URL after PDF generation
  created_at        TIMESTAMPTZ DEFAULT NOW(),
  updated_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS job_suggestions (
  id           SERIAL PRIMARY KEY,
  user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title        TEXT,
  company      TEXT,
  location     TEXT,
  description  TEXT,
  url          TEXT,
  match_reason TEXT,
  match_score  INTEGER DEFAULT 0,
  matching     TEXT    DEFAULT '[]',
  gaps         TEXT    DEFAULT '[]',
  recommendation TEXT  DEFAULT 'consider',
  source       TEXT,
  status       TEXT    NOT NULL DEFAULT 'pending',  -- pending|added|dismissed
  search_date  DATE,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Interviewer mode tables
ALTER TABLE users ADD COLUMN IF NOT EXISTS mode TEXT NOT NULL DEFAULT 'candidate';

CREATE TABLE IF NOT EXISTS interviewer_projects (
  id          SERIAL PRIMARY KEY,
  user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title       TEXT    NOT NULL,
  description TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS interviewer_candidates (
  id                SERIAL PRIMARY KEY,
  project_id        INTEGER NOT NULL REFERENCES interviewer_projects(id) ON DELETE CASCADE,
  user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name              TEXT    NOT NULL,
  email             TEXT,
  resume_path       TEXT,
  resume_text       TEXT,
  ai_summary        TEXT,
  ai_score          INTEGER DEFAULT 0,
  ai_matching       TEXT    DEFAULT '[]',
  ai_gaps           TEXT    DEFAULT '[]',
  ai_recommendation TEXT    DEFAULT 'consider',
  notes             TEXT,
  created_at        TIMESTAMPTZ DEFAULT NOW(),
  updated_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS interviewer_pipeline_cards (
  id           SERIAL PRIMARY KEY,
  candidate_id INTEGER NOT NULL REFERENCES interviewer_candidates(id) ON DELETE CASCADE,
  project_id   INTEGER NOT NULL REFERENCES interviewer_projects(id) ON DELETE CASCADE,
  user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  stage        TEXT    NOT NULL DEFAULT 'applied',  -- applied|screening|interview|offer|rejected
  position     INTEGER NOT NULL DEFAULT 0,
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  updated_at   TIMESTAMPTZ DEFAULT NOW()
);
