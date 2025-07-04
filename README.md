# RealtimeResults

**RealtimeResults** is an extension for Robot Framework that lets you monitor test execution live through a realtime dashboard or send realtime results to an external source. The project consists of a listener, a backend (API + storage), and a frontend dashboard built with HTML/JavaScript.

## Features

- Realtime test results during execution
- Supports multiple storage strategies (in-memory or SQLite database)
- Backend API with endpoints to retrieve events
- Automatic backend startup if not already running

---

## Structure

```
realtimeresults/
|
├── backend/
│   ├── ingest/
│   │   ├── reader/
│   │   │   └── sqlite_event_reader.py
│   │   └── source/
│   │       └── log_tail.py
│   ├── sinks/
|   |   └── memory_sqlite.py
|   └── main.py                             # Backend API
|
├── dashboard/            
│   └── index.html                          # HTML frontend dashboard
|
├── listener/
│   ├── realtime_listener.py
│   ├── sqlite_sink.py
│   ├── memory_sqlite_sink.py
|
├── realtimeresults/
│   └── sinks/
|   |   ├── base.py
|   |   ├── sqlite.py
|   |   └── http.py
│   └── listener.py                          # Robot Framework listener
│
├── cli.py                                   # Entrypoint & CLI wrapper
├── pyproject.toml
└── README.md
```

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/realtimeresults.git
cd realtimeresults
```

2. Install dependencies via [Poetry](https://python-poetry.org/):
```bash
poetry install
```

3. Run Robot Framework tests with rt-robot
Use the cli wrapper instead of calling `robot` directly:
```bash
poetry run rt-robot tests/
```
---


This will:

- Start the backend on http://127.0.0.1:8000 (if not already running)
- Start the test run with realtime event publishing
- Launch the live dashboard at http://127.0.0.1:8000/dashboard

---

## Configuration

The Config supports json and toml and has the following options:

```json example
{
  "backend_strategy": "sqlite", // Options: sqlite (default), loki (planned), etc.
  "listener_sink_type": "sqlite", // Options: sqlite (default), backend_http_inmemory, loki (planned), etc.

  "backend_endpoint": "http://localhost:8000/event",
  "sqlite_path": "eventlog.db",

  "backend_host": "127.0.0.1",
  "backend_port": 8000,

  "source_log_type": "file", 
  "source_log_path": "source.log",
  
  "log_level": "INFO",
  "log_level_listener": "",
  "log_level_backend": "",
  "log_level_cli": ""
}
```
### Sink Strategy Overview

The following combinations of `backend_strategy` and `listener_sink_type` define how test events are stored and routed during execution:

| `backend_strategy` | `listener_sink_type`      | Behavior                                                                 |
|--------------------|---------------------------|--------------------------------------------------------------------------|
| `sqlite`           | `sqlite`                  | Listener writes directly to a local SQLite file (defined by `sqlite_path`). Backend only reads. |
| `sqlite`           | `backend_http_inmemory`   | Listener sends events via HTTP POST to the backend. Backend keeps events in memory (`MemorySqliteSink`). Suitable for dashboards during live test runs. |
| `sqlite`           | `loki` *(planned)*        | Listener sends logs to a Loki server. Backend does not receive test events. |
| `loki` *(planned)* | `loki` *(planned)*        | Intended for future support where both listener and backend interact with Loki via Grafana queries. |

### Notes

- When using `listener_sink_type: backend_http_inmemory`, the backend uses an **in-memory** SQLite database. No data is persisted after shutdown.
- Writing to the backend via `/event` is **disabled** for persistent strategies (e.g. `listener_sink_type: sqlite`) to avoid unintentional data corruption or inconsistencies.
- Loki support is not yet implemented but planned for a future release. This will enable log-based dashboards using the Grafana stack.

---

## Useful Commands

### Manually start the backend:

```bash
poetry run uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Show logs from background backend (after test run):

```bash
cat backend.pid
# then:
kill -9 <PID>    # to stop it
```

---

## Dashboard

- Realtime visualization of:
  - Number of tests per status (PASS, FAIL, SKIP)
  - Table with error messages
  - Total elapsed suite time

Open the dashboard in your browser:

```
http://127.0.0.1:8000/dashboard
```

---

## TODO

- Support for grouping multiple test projects in parallel
- Improved filtering/tag support
- Integration with Loki for application logs

---

## License

MIT — feel free to use and adapt.
