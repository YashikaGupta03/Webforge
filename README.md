# CampusAlly — MANIT Bhopal

CampusAlly is a frontend prototype for AI-assisted campus issue reporting, tracking, and administrative coordination.

## Features

* CampusAlly landing page and demo role selection
* Student dashboard, multi-step report submission, image evidence preview, issue tracking, and reopening
* Administrator dashboard, issue queue, incident details, assignment, and status updates
* Shared issue state with localStorage persistence
* Interactive stylized 3D campus built with React Three Fiber and Three.js
* Priority score breakdown and simulated classification / duplicate heuristics
* Department directory, analytics, notifications, and audit trail
* Responsive desktop, tablet, and mobile layouts
* English interface with natural Hinglish input support

## Requirements

* Node.js 20 or later recommended
* npm

## Run locally

```bash
npm install
npm run dev
```

Open the local URL printed by Vite.

## Production build

```bash
npm run build
npm run preview
```

## Deploying the frontend with the API

For separate frontend and backend hosting, configure `VITE_API_URL` in the frontend host's build environment to the backend API base URL, including `/api` (for example, `https://your-api.example.com/api`). Vite embeds this value during the build, so rebuild/redeploy the frontend after changing it. If unset, the app uses `/api`, which works with the local Vite proxy but requires the production web host to proxy `/api` to the backend.

On the backend, set `CORS_ORIGINS` to the exact deployed frontend origin (scheme and host, without a path), as well as production `DATABASE_URL`, `APP_ENVIRONMENT=production`, and a unique `SECRET_KEY`. Check the backend's `/health` endpoint to verify the service is running. Apply database migrations with `alembic upgrade head` before using sign-up or sign-in. Never put backend secrets in `VITE_*` variables; those are public in the built frontend.

### Vercel frontend and Render backend

In Vercel, set `VITE_API_URL` to the Render service URL followed by `/api` (for example, `https://your-service.onrender.com/api`) under the frontend project's environment variables, then redeploy. In Render, set `CORS_ORIGINS` to the Vercel frontend origin (for example, `https://your-project.vercel.app`, without a trailing path) and redeploy the backend. The root `vercel.json` rewrite sends client-side routes such as `/login` to the app so directly opening or refreshing them does not return Vercel's 404 page.
