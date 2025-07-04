# Architecture Overview

The `robotframework-realtimeresults` project consists of the following key components:

1. **Robot Framework listener**
2. **FastAPI backend (API only)**
3. **Dashboard frontend (HTML + JS)**
4. **Event store (in-memory or persistent database)**

---

## Data Flow Overview

```
[ Robot Framework Run (CLI) ]
        │
        ▼
[ Listener (RealTimeResults) ]
        │
        └───► Writes to (SQLite or HTTP FastAPI) ──►  Event Store 
                                                          ▲
                                                          │
                                               Reads from │ (or writes in case of in-memory mode)
                                                          │
                                                          ▼
                                                 [ FastAPI Backend ]
                                                          │
                                                Serves data to Dashboard
                                                          ▼
                                                   [ Dashboard UI ]
```
---

## Component Details

| Component        | Description                                                       | When to Start        | Example                                                   |
|------------------|-------------------------------------------------------------------|-----------------------|-----------------------------------------------------------|
| **Robot CLI**     | Entry point for running Robot tests                              | Manually              | `poetry run rt-robot tests/`                              |
| **Listener**      | Captures real-time test events during execution                  | Auto-started via CLI  | Triggered via `--listener` argument                       |
| **Event Store**   | Central storage of events (shared between Listener & Backend)    | Internal              | SQLite file or in-memory database                         |
| **Backend (API)** | Reads events from the Event Store and exposes them to frontend   | Auto or manual        | `poetry run uvicorn backend.main:app --reload`            |
| **Dashboard**     | Static HTML/JS frontend that polls `/events` endpoint            | Browser-based         | Access via `http://localhost:8000/dashboard`              |

---


## Normal Behaviour System Architecture Diagram

```
          ┌────────────┐
          │  rt-robot  │
          └─────┬──────┘
                │
                ▼
          ┌────────────┐
          │  Listener  │
          └─────┬──────┘
                │
         Writes to Event Store
                ▼
         ┌───────────────┐
         │  Event Store  │
         └──────┬────────┘
                │
         Reads from Store
                ▼
        ┌─────────────────┐
        │ FastAPI Backend │
        └───────┬─────────┘
                │
          Serves data to UI
                ▼
           ┌───────────┐
           │ Dashboard │
           └───────────┘
```

> **Note:** In "backend_http_inmemory" mode, the listener sends events to the backend, which stores them in an in-memory event store instead of writing to disk. Loki support is planned for future releases.