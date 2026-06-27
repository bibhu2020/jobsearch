#!/usr/bin/env node
/**
 * Initializes the PostgreSQL schema on first run.
 * Safe to run repeatedly — uses IF NOT EXISTS throughout.
 * Usage: node shared/init-pg.js
 */
const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

async function main() {
  const url = process.env.DATABASE_URL;
  if (!url) {
    console.error('❌  DATABASE_URL not set. Add it to .env first.');
    process.exit(1);
  }

  const client = new Client({
    connectionString: url,
    ssl: { rejectUnauthorized: false },
  });

  await client.connect();
  console.log('✓ Connected to PostgreSQL');

  const sql = fs.readFileSync(path.join(__dirname, 'schema.pg.sql'), 'utf-8');
  await client.query(sql);
  console.log('✓ Schema applied');

  // Additive migrations — safe to re-run
  const migrations = [
    `ALTER TABLE interviewer_projects    ADD COLUMN IF NOT EXISTS location TEXT`,
    `ALTER TABLE interviewer_project_members ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'editor'`,
    `ALTER TABLE interviewer_candidates  ADD COLUMN IF NOT EXISTS phone    TEXT`,
    `ALTER TABLE interviewer_candidates  ADD COLUMN IF NOT EXISTS location TEXT`,
  ];
  for (const m of migrations) {
    await client.query(m);
  }
  console.log('✓ Migrations applied');

  await client.end();
  console.log('✓ Done');
}

main().catch((err) => { console.error(err); process.exit(1); });
