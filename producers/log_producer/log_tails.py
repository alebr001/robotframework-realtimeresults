import asyncio
import sys
import httpx
from pathlib import Path
from shared.helpers.config_loader import load_config
from shared.helpers.log_line_parser import extract_timestamp_and_clean_message
from shared.sinks.http import AsyncHttpSink

async def post_log(message: str, source_label: str, event_type: str, tz_info: str, sink: AsyncHttpSink):
    timestamp, log_level, cleaned_message = extract_timestamp_and_clean_message(message, tz_info=tz_info)
    if isinstance(cleaned_message, tuple):
        cleaned_message = " ".join(cleaned_message)
    print(f"TIMESTAMP: {timestamp}")
    print(f"message after: {cleaned_message}")

    payload = {
        "timestamp": timestamp,
        "event_type": event_type,
        "message": cleaned_message,
        "source": source_label,
        "level": log_level
    }
    try:
        print(f"[log_tail] Payload: {payload}")
        await sink.async_handle_event(payload)
    except Exception as e:
        print(f"[log_tail] Failed to send log from {source_label}: {e}")

async def tail_log_file(source: dict, sink):
    log_path = Path(source["path"])
    label = source.get("label", "unknown")
    event_type = source.get("event_type", "unknown")
    poll_interval = float(source.get("poll_interval", 1.0))
    
    # Timezone defaults to Europe/Amsterdam if not specified
    tz_info = source.get("tz_info", "Europe/Amsterdam")

    print(f"[log_tail] Watching {log_path} (label: {label}, interval: {poll_interval}s), timezone: {tz_info}, event_type: {event_type}")
    last_size = 0
    
    while not log_path.exists():
        print(f"[log_tail] File not found: {log_path}. Waiting...")
        await asyncio.sleep(poll_interval)

    last_size = log_path.stat().st_size

    while True:
        await asyncio.sleep(poll_interval)
        try:
            size = log_path.stat().st_size
            if size > last_size:
                with log_path.open("r", encoding="utf-8", errors="replace") as f:
                    f.seek(last_size)
                    new_lines = f.readlines()
                    last_size = size

                    for line in new_lines:
                        if line.strip():
                            print(f"[{label}] {line.strip()}")
                            await post_log(message=line.strip(), source_label=label, event_type= event_type, tz_info=tz_info, sink=sink)
        except FileNotFoundError:
            print(f"[log_tail] File not found again: {log_path}. Will retry.")

async def main():
    config = load_config()
    ingest_host = config.get("ingest_backend_host", "127.0.0.1")
    ingest_port = config.get("ingest_backend_port", 8001)
    ingest_endpoint = f"http://{ingest_host}:{ingest_port}"

    sink = AsyncHttpSink(endpoint=ingest_endpoint)

    sources = config.get("source_log_tails", [])
    if not sources:
        print("[log_tail] No source_log_tails defined in config.")
        sys.exit(10)

    # Ensure all sources have required fields
    async def safe_tail(source):
        try:
            await tail_log_file(source, sink)
        except Exception as e:
            print(f"[log_tail] Error in source {source.get('label', 'unknown')}: {e}")

    tasks = [asyncio.create_task(safe_tail(source)) for source in sources]

    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[log_tail] Stopped.")
