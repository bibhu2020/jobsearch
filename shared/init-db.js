#!/usr/bin/env node
const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');

const dbPath = process.env.DATABASE_PATH || path.join(__dirname, 'job_tracker.db');
const sqlPath = path.join(__dirname, 'init.sql');

// Ensure parent directory exists
fs.mkdirSync(path.dirname(dbPath), { recursive: true });

const db = new Database(dbPath);
const sql = fs.readFileSync(sqlPath, 'utf-8');
db.exec(sql);

// Non-destructive column additions (safe to run repeatedly)
const migrations = [
  "ALTER TABLE job_suggestions ADD COLUMN match_score INTEGER DEFAULT 0",
  "ALTER TABLE job_suggestions ADD COLUMN matching TEXT DEFAULT '[]'",
  "ALTER TABLE job_suggestions ADD COLUMN gaps TEXT DEFAULT '[]'",
  "ALTER TABLE job_suggestions ADD COLUMN recommendation TEXT DEFAULT 'consider'",
  "ALTER TABLE user_profiles ADD COLUMN location TEXT",
  "ALTER TABLE user_profiles ADD COLUMN resume_text TEXT",
];
for (const m of migrations) {
  try { db.exec(m); } catch (_) { /* column already exists */ }
}

db.close();

console.log(`✓ Database initialized at: ${dbPath}`);
