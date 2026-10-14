# Ajiri frontend

React + Vite, JavaScript/JSX, Tailwind 4, Radix primitives and lucide icons. API requests use src/api/client.js, including silent JWT refresh.

| Command | Purpose |
| --- | --- |
| npm ci | Install the committed lockfile; stop Vite first on Windows |
| npm run dev | Start the development server |
| npm run lint | Run oxlint |
| npm run test -- --run | Run Vitest + Testing Library in jsdom |
| npm run build | Produce static assets in dist |

Set VITE_API_BASE_URL to http://localhost:8000/api for local development. Clear that shell variable before producing a deployment build; production defaults to /api on the same host. VITE_* values are public, so never store secrets there.

Pages: Login, Register, JobList, JobDetail, Applications, Notifications, Profile, and the public Plans preview. Account data pages use protected routes. The plans page has no payments or account upgrades.

Use ../ajiri-backend/scripts/build_frontend.ps1 for the final package build, then commit ../ajiri-backend/frontend_build. The generated tree must match dist exactly. Do not run npm in frontend_build; it is deployment output, not the frontend source directory.

See ../docs/DESIGN_SYSTEM.md, ../docs/CHECKPOINT1_REVIEW.md, and ../docs/CI_PROPOSAL.md for usage, review steps and proposed CI changes.
