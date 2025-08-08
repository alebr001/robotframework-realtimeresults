# Robotframework-RealtimeResults

**Robotframework-RealtimeResults** is a modular, extensible system for collecting, processing, and visualizing test results, application logs, and metrics in real time. It is designed for use with [Robot Framework](https://robotframework.org/) but also supports ingestion of application logs and custom metrics. The system is suitable for both local development and CI/CD pipelines.

---

## Features

* **Realtime Dashboard**: Live web dashboard for monitoring Robot Framework test runs, application logs, and metrics.
* **Automatic Service Management**: CLI automatically starts backend APIs and log tailers as needed.
* **Multi-source Log Ingestion**: Tail and ingest logs from multiple sources/files, each with its own label and timezone.
* **Metric Tracking**: Ingest and store custom metrics alongside logs and test events.
* **Flexible Storage**: Supports SQLite and PostgreSQL; Loki integration (planned).
* **Pluggable Sinks**: Easily extend with new sinks (e.g., HTTP, Loki, custom).
* **Docker Support**: Run all components using Docker (tested on macOS).
* **Configurable via Wizard**: Interactive setup wizard for easy configuration.
* **REST API**: FastAPI-based endpoints for event ingestion and dashboard queries.
* **Extensible**: Modular codebase for adding new readers, sinks, or event types.

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

* Captures test events (suite/test start/end, log messages) in real time.
* Sends events to a configured sink (HTTP, SQLite or Loki).
* See [`producers/listener/listener.py`](producers/listener/listener.py).

### 2. Log Tailer

* Tails one or more application log files and sends parsed log lines to the ingest API.
* Supports per-source configuration (label, event type, timezone, poll interval).
* Multi-line grouping, parses timestamps, log levels, and message content using regex patterns.
* See [`producers/log_producer/log_tails.py`](producers/log_producer/log_tails.py).

### 3. Metric Ingestion

* Periodically scrapes CPU, memory, or other system metrics.
* Stores as structured `metric` events in the database.
* See [`producers/metrics/metric_scraper.py`](producers/metrics/metric_scraper.py).

### 4. Backend APIs

- **Viewer API**: Serves dashboard, test events, and application logs.
  - Endpoints: `/events`, `/applog`, `/events/clear`, `/dashboard`
  - See [`api/viewer/main.py`](api/viewer/main.py)
- * **Ingest API**: Accepts incoming logs, metrics, and test events.

  * Endpoints: `/log`, `/metric`, `/event`, `/event/log_message`
  - See [`api/ingest/main.py`](api/ingest/main.py)

### 5. Dashboard

* HTML+JS-based dashboard served at `/dashboard`.
* Displays live results, failures, logs, and metrics.
* Accessible at `/dashboard` on the viewer backend.
* See [`dashboard/index.html`](dashboard/index.html).

### 6. Sinks

* **SQLite Sink**: Persistent storage for listener events and logs.
* **Async SQLite Sink**: Async variant for log/metric ingestion.
* **AsyncPostgresSink** Async variant for log/metric ingestion.
* **HTTP Sink**: For sending events to remote APIs.
* **Loki Sink**: (Planned) Integration with Grafana Loki for log aggregation.

---

## Installation

### From PyPI

```bash
pip install robotframework-realtimeresults
```

### From Source

```bash
git clone https://github.com/alebr001/robotframework-realtimeresults
cd robotframework-realtimeresults
pip install poetry
poetry install
poetry run rt-robot tests/
```

---

## CLI Usage

### Run listener

Run your Robot Framework tests with real-time results:

```bash
rt-robot tests/
```

* Wrapper can auto-start services if not running (`enable_autoservices = true`).
* If no config file is found, an interactive setup wizard will guide you.
* Always start ingest service first (initializes database).

### Stop Services

When services are started via CLI, and rt-robot is used, backend PIDs are stored in `backend.pid`. Stop them with:

```bash
rt-robot --killbackend
```

### Preferred Usage (Manual Startup)

```bash
# Terminal 1
rt-robot --runservice api.ingest.main:app --config config.json

# Terminal 2
rt-robot --runservice api.viewer.main:app --config config.json

# Terminal 3
rt-robot --runservice producers/log_producer/log_tails.py

# Terminal 4 (optional)
rt-robot --runservice python producers/metrics/metric_scraper.py
```

### Docker Usage

#### Requirements

* Docker

#### Example

```bash
docker compose up
```

When running Docker:
> Use `0.0.0.0` as the backend hosts  
> Use 127.0.0.1 as client host for Ingest (Viewer can stay on 0.0.0.0).
> Use postgresql as database_url
> Set enable_autoservices: false

---

## Configuration
### Custom Config Path

```bash
rt-robot --config config.json tests/
```

#### Example config.json

```json
{
  "listener_sink_type": "http",
  "database_url": "sqlite:///eventlog.db, sqlite:///inmemory, postgresql://realtime:realtimepass@db:5432/realtime_db, etc",
  "viewer_backend_host": "127.0.0.1",
  "viewer_backend_port": 8002,
  "ingest_backend_host": "127.0.0.1",
  "ingest_backend_port": 8001,
  "enable_autoservices": true,
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
  "log_level": "INFO",
  "log_level_listener": "",
  "log_level_backend": "",
  "log_level_cli": ""
}
```

#### Docker friendly example
```json
{
  "database_url": "postgresql://realtime:realtimepass@postgres:5432/realtime_db",
  "enable_auto_services": false,

  "_comment": "use this for binding the services",
  "ingest_backend_host": "0.0.0.0",
  "ingest_backend_port": 8001,
  "viewer_backend_host": "0.0.0.0",
  "viewer_backend_port": 8002,

  "_comment2": "use this to connect to the services",
  "ingest_client_host": "127.0.0.1",
  "ingest_client_port": 8001,
  "viewer_client_host": "0.0.0.0",
  "viewer_client_port": 8002,

  "source_log_tails": [
      {
          "path": "results/debug.log",
          "label": "rf-debug",
          "poll_interval": 1.0,
          "event_type": "rf-debug",
          "log_level": "INFO",
          "tz_info": "Europe/Amsterdam"
      }
  ],
  "listener_sink_type": "http",

  "log_level": "DEBUG",
  "log_level_listener": "",
  "log_level_backend": "",
  "log_level_cli": ""
}
```

---

## REST API Endpoints

### Viewer API

* `GET /events`
* `GET /applog`
* `GET /events/clear`
* `GET /dashboard`

### Ingest API

* `POST /log`
* `POST /metric`
* `POST /event`
* `POST /event/log_message`

---

## Dashboard

Go to: [http://localhost:8002/dashboard](http://localhost:8002/dashboard)

Displays:

* Real-time test status (PASS/FAIL/SKIP)
* Log messages
* Metrics (in future release)
* Failure stack traces

---

## Extending

* Add sinks via `EventSink` (in shared) or `AsyncEventSink` (in api/ingest) subclassing
* Extend log parsing in `log_line_parser.py`
* Add new event types by updating `sql_definitions.py`

---

## Project Structure

```
.
├── api/
│   ├── ingest/
│   │   └ sinks/
│   └── viewer/
│       └ readers/
├── dashboard/
├── producers/
│   ├── listener/
│   ├── log_producer/
│   └── metrics/
├── shared/
│   ├── helpers/
│   │   └ cli.py (entrypoint)
│   └── sinks/
└── pyproject.toml
```

## Requirements

* Python 3.9+
* Windows, Linux, macOS
## Planned Features

* Grafana Loki integration for log aggregation. 
* TestID support
* Advanced dashboard filtering and tag support.
* Metric visualization.
* Optional authentication for APIs.
---

## License

MIT

---

## Contributing

Contributions and feedback are welcome! Please open issues or pull requests on