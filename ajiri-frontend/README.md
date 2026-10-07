# Ajiri frontend

React + Vite single-page app. It talks to the Django API in `../ajiri-backend`.

| Command | What it does |
|---|---|
| `npm install` | Install dependencies (first time, or after `package.json` changes) |
| `npm run dev` | Dev server at http://localhost:5173 (API calls go to `.env.development`'s address) |
| `npm run lint` | Run oxlint |
| `npm run build` | Production build into `dist/` (API calls go to `/api`, per `.env.production`) |

To publish a build, run `..\ajiri-backend\scripts\build_frontend.ps1`. It builds and copies the
result into `ajiri-backend/frontend_build/`, which Django serves.

`VITE_*` values are baked in at build time and visible to every visitor: never put a secret in them.
