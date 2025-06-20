import asyncio
import httpx
from pathlib import Path
from datetime import datetime, timezone
from config import LOG_FILE_PATH, INGEST_ENDPOINT, POLL_INTERVAL, SOURCE_LABEL

async def post_log(message: str):
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": message,
        "source": SOURCE_LABEL,
        "level": "INFO"  # of None
    }
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(INGEST_ENDPOINT, json=payload)
    except Exception as e:
        print(f"[log_tail] Failed to send log: {e}")

async def tail_log_file():
    file = Path(LOG_FILE_PATH)
    last_size = file.stat().st_size if file.exists() else 0

    while True:
        await asyncio.sleep(POLL_INTERVAL)
        if not file.exists():
            continue

        size = file.stat().st_size
        if size > last_size:
            with file.open("r", encoding="utf-8", errors="replace") as f:
                f.seek(last_size)
                new_lines = f.readlines()
                last_size = size

                for line in new_lines:
                    if line.strip():
                        await post_log(line.strip())

if __name__ == "__main__":
    print(f"[log_tail] Watching {LOG_FILE_PATH}, sending to {INGEST_ENDPOINT}")
    try:
        asyncio.run(tail_log_file())
    except KeyboardInterrupt:
        print("[log_tail] Stopped.")