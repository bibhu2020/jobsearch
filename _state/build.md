# Build

## Current architecture
- Frontend: Vue 3 app in `frontend/`
- Gateway: NestJS in `services/gateway/src/`
- Agents: Python/FastAPI in `agents/`
- Shared config and schema in `shared/`

## Local run commands
```bash
npm install
pip install .
playwright install chromium
npm start
```

## Build commands
```bash
npm run build
```

## Local setup alternatives
```bash
npm run setup
npm run setup:local
```

## Key runtime ports
- Gateway: 3000
- Agents: 8000
- Frontend: 5173

## Build notes
- The root project uses concurrent services for dev.
- The Python agents rely on `PYTHONPATH=.`, which is set by the `npm start` script.
- The frontend uses Vite and Tailwind.
- The backend is NestJS with modules for auth, jobs, pipeline, kits, suggestions, and interviewer.

## Validation practices
- Check Python syntax for changed agent files with `python3 -m py_compile ...`.
- Validate app changes with the relevant route or UI workflow.
- Confirm env vars are loaded from `.env` before relying on provider configuration.

## Important implementation patterns
- Gateway and agents communicate through HTTP and env-driven configuration.
- Database access in gateway is user-scoped and typically includes `user_id` filters.
- AI calls are centralized and should honor configured provider and fallback logic.
- GitHub storage is treated as the canonical artifact backing store.
