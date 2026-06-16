FROM python:3.11-slim

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates supervisor \
      # Playwright / Chromium runtime libs
      libnss3 libatk1.0-0 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1 \
      libgtk-3-0 libasound2 libx11-xcb1 libxss1 libxtst6 \
      fonts-liberation libappindicator3-1 xdg-utils wget \
    && rm -rf /var/lib/apt/lists/*

# ── Node.js 20 ───────────────────────────────────────────────────────────────
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python dependencies (includes Playwright) ─────────────────────────────────
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Install Playwright Chromium + system deps in one step
RUN playwright install chromium --with-deps

# ── Node dependencies ─────────────────────────────────────────────────────────
COPY package.json package-lock.json* ./
# Install all deps (including devDeps needed for build)
RUN npm ci

# ── Copy full source ──────────────────────────────────────────────────────────
COPY . .

# ── Build frontend (Vue → dist/frontend) and gateway (NestJS → dist/) ─────────
RUN npm run build

# ── Remove devDependencies to slim the final image ───────────────────────────
RUN npm prune --production

# ── Runtime environment ───────────────────────────────────────────────────────
ENV PORT=7860 \
    AGENTS_URL=http://localhost:8000 \
    NODE_ENV=production \
    PYTHONPATH=/app

EXPOSE 7860

RUN chmod +x /app/docker-entrypoint.sh
CMD ["/app/docker-entrypoint.sh"]
