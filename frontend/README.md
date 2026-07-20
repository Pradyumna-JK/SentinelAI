# SentinelAI Frontend

React + Vite dashboard for SentinelAI — AI-Powered Industrial Safety Intelligence Platform. This is the placeholder UI shell: all pages run against dummy JSON in `src/data/mockData.js` via the `src/services/` layer, with no backend required yet.

## Stack

React 18 · Vite · Tailwind CSS · React Router · Axios · Recharts

## Getting Started

```bash
npm install
npm run dev
```

Then open the printed local URL (default `http://localhost:5173`). The app redirects `/` to `/dashboard`.

## Folder Structure

```
src/
├── pages/        Dashboard, Camera Monitoring, Alerts, Compliance Copilot, Incident Reports, Analytics, Settings
├── components/   Reusable UI: Button, Card, Table, Chart, Sidebar, Navbar, Modal, Toast, StatusBadge,
│                 RiskMeter, AlertCard, CameraTile, Timeline, ChatWindow, LoadingSkeleton
├── layouts/       MainLayout — Navbar + responsive Sidebar/drawer + page outlet
├── services/       One module per API resource group, currently returning mock data
├── hooks/          useToast (notification context), useRealtimeFeed (simulated live updates)
├── data/           mockData.js — all dummy JSON fixtures
└── assets/         Static assets (logo, etc.)
```

Naming and structure follow `docs/09_FRONTEND_SPECIFICATION.md`, `docs/10_COMPONENT_LIBRARY.md`, and `docs/12_FOLDER_STRUCTURE.md` in the project's `docs/` folder.

## Wiring a Real Backend

Each file in `src/services/` currently imports from `src/data/mockData.js` and resolves it through a simulated delay. To connect a real backend once `docs/08_API_SPECIFICATION.md` is implemented:

1. Replace the mock-returning function body with an `apiClient.get/post(...)` call (see `src/services/apiClient.js`).
2. Set `VITE_API_BASE_URL` in a `.env` file (see `.env.example`).
3. No page or component changes are required — they only depend on the service function's return shape.

## Notes

- All data on screen is dummy/placeholder — nothing persists between reloads except in-memory state.
- Responsive: sidebar collapses into a mobile drawer below the `md` breakpoint; all pages reflow to single-column layouts on small screens.
- Theme: dark "industrial safety" palette (navy base, safety-orange/yellow/red/green accents) defined in `tailwind.config.js`.
