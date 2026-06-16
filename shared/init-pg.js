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

  await client.end();
  console.log('✓ Done');
}

main().catch((err) => { console.error(err); process.exit(1); });
