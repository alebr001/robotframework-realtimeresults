# Robotframework-RealtimeResults

**Robotframework-RealtimeResults** is a modular, extensible system for collecting, processing, and visualizing test results, application logs, and metrics in real time. It is designed for use with [Robot Framework](https://robotframework.org/) but also supports ingestion application logs and custom metrics. The system is suitable for both local development and CI/CD pipelines.

---

## Features

- **Realtime Dashboard**: Live web dashboard for monitoring Robot Framework test runs, application logs, and metrics.
- **Automatic Service Management**: CLI automatically starts backend APIs and log tailers as needed.
- **Multi-source Log Ingestion**: Tail and ingest logs from multiple sources/files, each with its own label and timezone.
- **Metric Tracking**: Ingest and store custom metrics alongside logs and test events. (todo)
- **Flexible Storage**: Supports SQLite (file or in-memory); Loki integration (planned).
- **Pluggable Sinks**: Easily extend with new sinks (e.g., HTTP, Loki, custom).
- **Configurable via Wizard**: Interactive setup wizard for easy configuration.
- **REST API**: FastAPI-based endpoints for event ingestion and dashboard queries.
- **Extensible**: Modular codebase for adding new readers, sinks, or event types.

---

## Architecture Overview

```
[ Robot Framework Run ]
        │
        │
        ├──► Listener writes to (SQLite / FastApi Ingest) ──►  Event Store 
        │                                                      ▲  │
        │                                                      │  │
        └─────► [ Log Tailer(s) (FastApi Ingest) ] ────────────┘  │
                                                                  │
                                                       Reads from │ (or writes in case of in-memory mode)
                                                                  ▼
                                                        [ FastAPI Viewer ]
                                                                  │
                                                        Serves data to Dashboard
                                                                  ▼
                                                          [ Dashboard UI ]
```

---

## Components

### 1. Robot Framework Listener

- Captures test events (suite/test start/end, log messages) in real time.
- Sends events to a configured sink (SQLite, HTTP API, or Loki).
- Supports unique test IDs, timestamps, tags, and more.
- See [`producers/listener/listener.py`](producers/listener/listener.py).

### 2. Log Tailer

- Tails one or more application log files and sends parsed log lines to the ingest API.
- Supports per-source configuration (label, event type, timezone, poll interval).
- Parses timestamps, log levels, and message content using robust regex patterns.
- See [`producers/log_producer/log_tails.py`](producers/log_producer/log_tails.py).

### 3. Metric Ingestion (todo)

- Supports ingestion of custom metrics (name, value, unit, source).
- Metrics are stored in the same event store and can be visualized or queried.
- See [`shared/sinks/sqlite_async.py`](shared/sinks/sqlite_async.py).

### 4. Backend APIs

- **Viewer API**: Serves dashboard, test events, and application logs.
  - Endpoints: `/events`, `/applog`, `/events/clear`, `/dashboard`
  - See [`api/viewer/main.py`](api/viewer/main.py)
- **Ingest API**: Receives logs and metrics via POST.
  - Endpoints: `/log` (async), `/event` (sync)
  - See [`api/ingest/main.py`](api/ingest/main.py)

### 5. Dashboard

- Live web dashboard (HTML + JS) for real-time visualization.
- Displays test status, failures, elapsed time, and live application logs.
- Accessible at `/dashboard` on the viewer backend.
- See [`dashboard/index.html`](dashboard/index.html).

### 6. Sinks

- **SQLite Sink**: Persistent storage for test events and logs.
- **Async SQLite Sink**: Async variant for log/metric ingestion.
- **Memory Sink**: In-memory storage for ephemeral runs.
- **HTTP Sink**: For sending events to remote APIs.
- **Loki Sink**: (Planned) Integration with Grafana Loki for log aggregation.
- All sinks inherit from [`shared/sinks/base.py`](shared/sinks/base.py).

---

## Installation

### From PyPI

```sh
pip install robotframework-realtimeresults
```

### From Source

```sh
git clone https://github.com/alebr001/robotframework-realtimeresults
cd robotframework-realtimeresults
pip install poetry
poetry install
poetry run rt-robot tests/
```

---

## CLI Usage

Run your Robot Framework tests with real-time results:

```sh
rt-robot tests/
```

- The CLI will auto-start backend services and log tailers but it is preferable to start manually.
- If no config file is found, an interactive setup wizard will guide you.
- run ingest service first, because this will initialize the database for you. If you run the viewer without a database this will result in errors

### Prefered usage 

- **Terminal 1:**
rt-robot --runservice api.ingest.main:app --config path/to/custom_config.json

- **Terminal 2:**
rt-robot --runservice api.viewer.main:app --config path/to/custom_config.json

- **Terminal 3:**
rt-robot --runservice producers/log_producer/log_tails.py

- **Terminal 4:**
rt-robot --runservice python producers/metrics/metric_scraper.py


### Custom Config Path

```sh
rt-robot --config path/to/custom_config.json tests/
```

### Stopping Services

When services are started via CLI, and rt-robot is used, backend PIDs are stored in `backend.pid`. Stop them with:

```sh
rt-robot --killbackend
```

---

## Configuration

If no config file is found, the CLI launches a wizard. Example config:

```json
{
  "listener_sink_type": "sync",
  "database_url": "sqlite:///eventlog.db, sqlite:///inmemory, postgresql://realtime:realtimepass@db:5432/realtime_db, etc",
  "viewer_backend_host": "127.0.0.1",
  "viewer_backend_port": 8002,
  "ingest_backend_host": "127.0.0.1",
  "ingest_backend_port": 8001,
  "source_log_tails": [
    {
      "path": "../logs/app.log",
      "label": "app",
      "poll_interval": 1.0,
      "event_type": "app_log",
      "log_level": "INFO",
      "tz_info": "Europe/Amsterdam"
    }
  ],
  "log_level": "INFO"
}
```

- **source_log_tails**: List of log files to tail, each with its own label, event type, poll interval, and timezone.
- **metric_scaper** logs cpu usage and memory to the database
- **listener_sink_type**: Choose between `sync`, `http`, or `loki` (planned).
- **ingest_sink_type**: For the ingest API, typically `async`.

---

## REST API Endpoints

### Viewer API

- `GET /events` — List all test events.
- `GET /applog` — List all application logs.
- `GET /events/clear` — Clear all test events.
- `GET /dashboard` — Dashboard UI.

### Ingest API

- `POST /log` — Ingest application log or metric (JSON payload).
- `POST /event` — Ingest test event (sync, for legacy use).

---

## Dashboard

Open [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard) to view:

- Live test status (PASS/FAIL/SKIP)
- Failure details
- Suite execution time
- Live application logs

---

## Extending Functionality

- **Add new sinks**: Inherit from `EventSink` or `AsyncEventSink` in [`shared/sinks/base.py`](shared/sinks/base.py).
- **Add new event types**: Update SQL schema and ingestion logic.
- **Custom log parsing**: Extend [`shared/helpers/log_line_parser.py`](shared/helpers/log_line_parser.py) and [`shared/helpers/log_line_datetime_patterns.py`](shared/helpers/log_line_datetime_patterns.py).

---

## Project Structure

```
.
├── api/
│   ├── ingest/         # Log + metric ingestion API
│   └── viewer/         # Dashboard and query API
├── dashboard/          # Static frontend dashboard
├── producers/
│   ├── listener/       # Robot Framework listener
│   └── log_producer/   # Tail logfiles and send to backend
├── shared/
│   └── helpers/        # Config loader, setup wizard, logging, parsing
│   └── sinks/          # http (sync/async), sqlite (sync/async/memory), loki (planned)
├── cli.py              # CLI entrypoint
└── pyproject.toml
```

## Requirements

- Python 3.9 or later (tested on 3.9 – 3.13)
- Works on macOS, Linux, Windows

---

## Planned Features

- Grafana Loki integration for log aggregation. 
- Advanced dashboard filtering and tag support.
- Metric visualization.
- Optional authentication for APIs.

---

## License

MIT — use and modify freely.

---

## Contributing

Contributions are welcome! Please open issues or pull requests on