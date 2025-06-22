import asyncio
import sys
import httpx
from pathlib import Path
from shared.helpers.config_loader import load_config
from shared.helpers.log_line_parser import extract_timestamp_and_clean_message

async def post_log(message: str, source_label: str, ingest_endpoint: str, event_type: str):
    message, timestamp, log_level = extract_timestamp_and_clean_message(message)
    payload = {
        "timestamp": timestamp,
        "event_type": event_type,
        "message": message,
        "source": source_label,
        "level": log_level
    }
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            print(f"[log_tail] Payload: {payload}")
            await client.post(ingest_endpoint, json=payload, timeout=0.5)
    except Exception as e:
        print(f"[log_tail] Failed to send log from {source_label}: {e}")

async def tail_log_file(source: dict, ingest_endpoint: str):
    log_path = Path(source["path"])
    label = source.get("label", "unknown")
    event_type = source.get("event_type", "unknown")
    log_level = source.get("log_level", "INFO")
    
    poll_interval = float(source.get("poll_interval", 1.0))
    last_size = log_path.stat().st_size if log_path.exists() else 0

    print(f"[log_tail] Watching {log_path} (label: {label}, interval: {poll_interval}s)")

    while True:
        await asyncio.sleep(poll_interval)
        if not log_path.exists():
            print(f"[log_tail] File not found: {log_path}")
            continue

        size = log_path.stat().st_size
        if size > last_size:
            with log_path.open("r", encoding="utf-8", errors="replace") as f:
                f.seek(last_size)
                new_lines = f.readlines()
                last_size = size

                for line in new_lines:
                    if line.strip():
                        print(f"[{label}] {line.strip()}")
                        await post_log(line.strip(), label, ingest_endpoint, event_type)

async def main():
    config = load_config()

    ingest_host = config.get("ingest_backend_host", "127.0.0.1")
    ingest_port = config.get("ingest_backend_port", 8001)
    ingest_endpoint = f"http://{ingest_host}:{ingest_port}/log"

    sources = config.get("source_log_tails", [])
    if not sources:
        print("[log_tail] No source_log_tails defined in config.")
        sys.exit(1)

    tasks = [asyncio.create_task(tail_log_file(source, ingest_endpoint)) for source in sources]
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[log_tail] Stopped.")