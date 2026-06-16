#!/bin/sh
set -e

echo "▶ Applying database schema…"
node shared/init-pg.js

echo "▶ Starting services…"
exec supervisord -c /app/supervisord.conf
