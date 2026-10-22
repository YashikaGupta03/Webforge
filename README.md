# CampusAlly — MANIT Bhopal

CampusAlly is a frontend prototype for AI-assisted campus issue reporting, tracking, and administrative coordination.

## Features
- CampusAlly landing page and demo role selection
- Student dashboard, multi-step report submission, image evidence preview, issue tracking and reopening
- Administrator dashboard, issue queue, incident detail, assignment and status updates
- Shared issue state with localStorage persistence
- Interactive stylized 3D campus built with React Three Fiber / Three.js
- Priority score breakdown and simulated classification / duplicate heuristics
- Department directory, analytics, notifications, and audit trail
- Responsive desktop, tablet, and mobile layouts
- English interface with natural Hinglish input support

## Requirements
- Node.js 20 or later recommended
- npm

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

## Demo roles
Use `/login` to select Student, Warden, Administrator, Department Staff, or Super Admin. Role switching is available in the top bar. No real MANIT credentials are required.

## Demo data
The first run seeds illustrative sample incidents. New issues and administrative updates persist in browser localStorage. Use Settings → Reset demo data to restore the initial issue set.

## What is simulated
- Authentication and role permissions (frontend only; not production security)
- AI classification and confidence
- Priority recommendation inputs
- Duplicate detection (same-location heuristic)
- Staff availability and workload
- Notification delivery (in-app only)
- Analytics demo trend chart

The priority formula shown in the UI is:
`0.30 × Safety + 0.25 × Severity + 0.20 × Community Impact + 0.15 × Waiting Time + 0.10 × Related Reports`

## 3D campus note
The campus scene is a stylized illustrative model for the prototype, not a geographically accurate replica of MANIT. WebGL is required for the 3D view; use the searchable location selector if the 3D view is unavailable.

## Production integration
For deployment, connect a backend API and enforce authentication/authorization on the server. Store evidence securely, validate uploads server-side, implement real AI services, and define institution-approved privacy and SLA policies. Do not use localStorage as a production database.

## Troubleshooting
- If `npm install` fails, verify network access and Node/npm versions.
- If a 3D scene is blank, update graphics drivers and try a WebGL-enabled browser.
- If you encounter a dependency issue, remove `node_modules` and `package-lock.json`, then run `npm install` again.
