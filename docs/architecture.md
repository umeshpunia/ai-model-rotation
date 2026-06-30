# System Architecture

This document describes the core design structures and execution lifecycles of **AI Gateway Pro**.

---

## 1. Request Lifecycle Flow

When a client application sends a completions request, the gateway routes it through the following logical sequence:

```
[ Client Request ]
       |
       v
[ FastAPI Router ] (validates JWT, parses OpenAI schemas)
       |
       v
[ Gateway Service ]
       |
       +---> [ Routing Engine ] (selects active candidates and orders by priority/latency)
       |
       v
[ Loop candidate keys ]
       |
       +---> [ Reveal Key ] (Decrypts raw API key using AES-256-GCM)
       |
       +---> [ Invoke Plugin ] (Executes HTTP async call to provider API)
       |
       +---> Success? Yes --> [ Return Response, Update Latency Stats ]
       |
       +---> Success? No (e.g., 429) --> [ Flag Key Cooldown, Try Next Candidate ]
```

---

## 2. Core Subsystems

### A. Routing Engine
Dynamically discovers valid API keys matching the requested model. Candidates are ordered based on the active routing policy:
- **Priority:** Orders candidates by priority weight (1 = highest).
- **Least Used:** Selects the key with the lowest usage count.
- **Fastest:** Selects keys with the lowest historical rolling average latency.
- **Round Robin:** Rotates selection sequentially across candidates.

### B. Failover & Key Rotator
Acts as the circuit breaker for upstream models:
- **Rate Limits (429):** Sets the key status to `cooldown` and applies a backoff lock.
- **Authentication Errors (401/403):** Flags the key as `invalid` and disables it permanently.
- **Network Failures / Timeouts:** Increments consecutive failure counters.

### C. Background Scheduler
An asynchronous background coordinator built on APScheduler:
- **Health Checks:** Runs scheduled checks on inactive keys to verify recovery.
- **Database Backups:** Compresses and manages SQLite database snapshots.
- **Statistics Rollups:** Aggregates hourly requests timelines and cost factors.
