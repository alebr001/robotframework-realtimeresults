# RealtimeResults

**RealtimeResults** is a modular system for collecting, processing, and visualizing test results, logs, and metrics in real time. It started as a Robot Framework listener but now also supports application log ingestion and basic metric tracking. It works both locally and in CI/CD pipelines.

## Features

- Realtime dashboard for Robot Framework test runs
- Automatic startup of backend services (if needed)
- Combine test events, log lines, and metrics in one system
- Pluggable sinks (SQLite now, Loki planned)
- Supports multiple log sources (files, etc.)
- Metric ingestion (basic support, dashboard integration planned)

## Installation

### Option 1: Install from PyPI

```bash
pip install robotframework-realtimeresults
```

> Requires Python 3.9 or later. Tested on Python 3.9–3.12.

### Option 2: Clone the repository for local development

```bash
git clone https://github.com/alebr001/robotframework-realtimeresults
cd robotframework-realtimeresults
pip install poetry
poetry install
poetry run rt-robot tests/
```

## CLI usage

After installing the package, you can use the `rt-robot` command to run your test suite:

```bash
rt-robot tests/
```

The `rt-robot` command is a wrapper around the `robot` command.

It automatically starts required services like the backend APIs and log tailers if they are not already running.

If no config file exists, a setup wizard is launched interactively.

### Preferred usage

While `rt-robot` can automatically start all required services, the preferred approach is to start the services manually in separate terminals for better visibility and control:

```bash
# Terminal 1
uvicorn api.viewer.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2
uvicorn api.ingest.main:app --host 127.0.0.1 --port 8001 --reload

# Terminal 3 (optional, if using applog ingestion)
python producers/log_producer/log_tails.py
```

### Custom config path

To run with a custom configuration file instead of the default `realtimeresults_config.json` you can use json or toml:

```bash
rt-robot --config path/to/custom_config.json tests/
```

### Stop all services started by the CLI

When `rt-robot` starts backend services automatically, it records their PIDs in a file called `backend.pid`.

You can stop them by running:

```bash
python kill_backend.py
```

## Project structure

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
│   └── helpers/        # Config loader, setup wizard, logging
│   └── sinks/          # http (sync/async), sqlite (sync/async/memory), loki (to be implemented)
├── cli.py              # CLI entrypoint
└── pyproject.toml
```

## Configuration

When no config file is found, the CLI generates one using an interactive wizard. Example:

```json
{
  "backend_strategy": "sqlite",
  "listener_sink_type": "sqlite",
  "sqlite_path": "eventlog.db",
  "viewer_backend_host": "127.0.0.1",
  "viewer_backend_port": 8000,
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

## Sink strategy overview

| `backend_strategy` | `listener_sink_type`      | Behavior                                                                 |
|--------------------|---------------------------|--------------------------------------------------------------------------|
| `sqlite`           | `sqlite`                  | Listener writes to local SQLite file; backend reads only                 |
| `sqlite`           | `backend_http_inmemory`   | Listener sends events via HTTP; backend keeps data in memory only       |
| `sqlite`           | `loki` *(planned)*        | Listener sends logs to Loki; backend is bypassed                         |

Note: When using `backend_http_inmemory`, the data is not persisted.

## Dashboard

Open the live dashboard in your browser:

```
http://127.0.0.1:8000/dashboard
```

The dashboard shows:

- Test status (PASS/FAIL/SKIP)
- Error messages
- Suite execution time
- Application logs and metrics (if configured)

## Planned features

- Improved dashboard filtering and tags
- Loki integration with Grafana
- Optional authentication for the API

## License

MIT — use and modify freely.