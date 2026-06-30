# Design Specification: Phase 11 Frontend Dashboard

## 1. Goal
Scaffold and implement the AI Gateway Pro web frontend dashboard using React, TypeScript, Tailwind CSS, shadcn/ui, React Router, Zustand, and React Query. The interface should feel extremely premium, responsive, and alive with real-time stats, interactive graphs, and smooth theme switching.

## 2. Page & Routing Architecture
- **`/` (Dashboard)**:
  * Summary Cards: Active Provider/Model, Total Keys, Healthy vs. Disabled Keys, Today's API Requests, Avg Latency (ms), Total Cost ($).
  * Charts: Requests timeline (today/week/month), latency per provider bar chart.
- **`/providers` (Provider Management)**:
  * Master-detail view of active provider plugins.
  * Configure API Base URLs, parameters, custom headers.
  * Integration tests button.
- **`/keys` (API Key Management)**:
  * Datatable listing all keys across providers.
  * Fields: Priority, Status, Failure rate, Latency, Quota limit.
  * Actions: Test connection, Enable/Disable, Rotate key, Revoke.
- **`/routing` (Routing & Failover Configuration)**:
  * Strategy selector (Round Robin, Priority, Least Used, Fastest, AI-Optimized).
  * Settings for retry threshold, fallback chain configuration.
- **`/logs` (Request Logs Viewer)**:
  * Paginated table showing recent request logs (timestamp, provider, model, duration, tokens, cost, status).
- **`/settings` (Settings & Backups)**:
  * Environment profiles toggle (Development, Production, Testing).
  * JSON Import/Export of config.
  * Backup snapshots table: list backups, trigger manual backup, restore, delete.

## 3. UI/UX Style Guide
- **Colors**: Sleek slate/zinc dark mode, custom violet/indigo highlight accents, glassmorphic card overlays, neon-bordered status badges.
- **Micro-animations**: Smooth hover transitions, spinning refresh/test icons, slide-in sidebar, fading toast alerts.
- **Accessibility**: Semantic HTML, ARIA tags on active states, keyboard tab-navigable tables and forms.
