# log_tail.py
import asyncio
from pathlib import Path

async def tail_log_file(path: str, callback):
    file = Path(path)
    last_size = 0

    while True:
        await asyncio.sleep(1)
        if not file.exists():
            continue

        size = file.stat().st_size
        if size > last_size:
            with file.open("r") as f:
                f.seek(last_size)
                new_lines = f.read()
                await callback(new_lines.strip())
            last_size = size