PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  email         TEXT    UNIQUE NOT NULL,
  password_hash TEXT    NOT NULL,
  name          TEXT,
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_profiles (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id         INTEGER UNIQUE NOT NULL,
  resume_path     TEXT,
  linkedin_url    TEXT,
  profile_summary TEXT,
  skills          TEXT,       -- JSON array of strings
  experience      TEXT,       -- JSON array of objects
  education       TEXT,       -- JSON array of objects
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS jobs (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER NOT NULL,
  title       TEXT,
  company     TEXT,
  location    TEXT,
  description TEXT,
  url         TEXT,
  source      TEXT,           -- 'manual_url' | 'manual_text' | 'search_agent'
  raw_content TEXT,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pipeline_cards (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id     INTEGER NOT NULL,
  user_id    INTEGER NOT NULL,
  stage      TEXT    NOT NULL DEFAULT 'wishlist',  -- wishlist|applied|interviewing|offer|rejected
  position   INTEGER NOT NULL DEFAULT 0,
  notes      TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (job_id)  REFERENCES jobs(id)  ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS generated_kits (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  pipeline_card_id  INTEGER NOT NULL,
  type              TEXT    NOT NULL,  -- cover_letter|resume|interview_questions|company_brief
  content           TEXT,              -- editable markdown
  file_path         TEXT,              -- saved PDF path
  created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (pipeline_card_id) REFERENCES pipeline_cards(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS job_suggestions (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id      INTEGER NOT NULL,
  title        TEXT,
  company      TEXT,
  location     TEXT,
  description  TEXT,
  url          TEXT,
  match_reason TEXT,
  source       TEXT,   -- remotive|arbeitnow|ddg|indeed|google
  status       TEXT    NOT NULL DEFAULT 'pending',  -- pending|added|dismissed
  search_date  DATE,
  created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Interviewer mode tables
CREATE TABLE IF NOT EXISTS interviewer_projects (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER NOT NULL,
  title       TEXT    NOT NULL,
  description TEXT,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS interviewer_candidates (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id        INTEGER NOT NULL,
  user_id           INTEGER NOT NULL,
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
  created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_id) REFERENCES interviewer_projects(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id)    REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS interviewer_pipeline_cards (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  candidate_id INTEGER NOT NULL,
  project_id   INTEGER NOT NULL,
  user_id      INTEGER NOT NULL,
  stage        TEXT    NOT NULL DEFAULT 'applied',
  position     INTEGER NOT NULL DEFAULT 0,
  created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (candidate_id) REFERENCES interviewer_candidates(id) ON DELETE CASCADE,
  FOREIGN KEY (project_id)   REFERENCES interviewer_projects(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id)      REFERENCES users(id) ON DELETE CASCADE
);
