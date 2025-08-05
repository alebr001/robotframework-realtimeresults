import asyncio
import sys
import logging
import re

from pathlib import Path
from shared.helpers.config_loader import load_config
from shared.helpers.logger import setup_root_logging
from shared.helpers.log_line_parser import extract_timestamp_and_clean_message, parse_known_datetime_formats
from shared.sinks.http import AsyncHttpSink

config = load_config()
setup_root_logging(config.get("log_level", "info"))
logger = logging.getLogger("rt.logtail")

TIMESTAMP_LINE_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6} - \w+ - ")

def group_log_lines(lines: list[str], tz_info: str) -> list[tuple[str, str]]:
    grouped = []
    buffer = []
    last_valid_timestamp = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("~~~~~") or stripped.startswith("=====") or stripped.startswith("-----"):
            continue

        timestamp, _ = parse_known_datetime_formats(stripped, tz_info=tz_info)

        if timestamp:
            if buffer:
                grouped.append(("\n".join(buffer), last_valid_timestamp))
            buffer = [stripped]
            last_valid_timestamp = timestamp
        else:
            buffer.append(stripped)

    if buffer:
        grouped.append(("\n".join(buffer), last_valid_timestamp))

    return grouped

async def post_log(message: str, source_label: str, event_type: str, tz_info: str, sink: AsyncHttpSink, timestamp_override: str):
    try:
        _, log_level, cleaned_message = extract_timestamp_and_clean_message(message, tz_info=tz_info)
        if isinstance(cleaned_message, tuple):
            cleaned_message = " ".join(cleaned_message)

        payload = {
            "timestamp": timestamp_override,
            "event_type": event_type,
            "message": cleaned_message,
            "source": source_label,
            "level": log_level
        }

        logger.debug(f"[{source_label}] Payload: {payload}")
        await sink.async_handle_event(payload)
    except Exception as e:
        logger.exception(f"[{source_label}] Failed to send log: {e}")

async def tail_log_file(source: dict, sink: AsyncHttpSink):
    log_path = Path(source["path"])
    label = source.get("label", "unknown")
    event_type = source.get("event_type", "unknown")
    poll_interval = float(source.get("poll_interval", 5.0))
    tz_info = source.get("tz_info", "Europe/Amsterdam")

    logger.info(f"Watching {log_path} (label={label}, interval={poll_interval}s, tz={tz_info}, type={event_type})")

    while not log_path.exists():
        logger.warning(f"[{label}] File not found: {log_path}. Retrying every {poll_interval}s...")
        await asyncio.sleep(poll_interval)

    logger.info(f"[{label}] File found: {log_path.resolve()}")
    last_size = log_path.stat().st_size

    while True:
        await asyncio.sleep(poll_interval)
        try:
            size = log_path.stat().st_size

            if size < last_size:
                logger.warning(f"[{label}] File was truncated or replaced. Resetting read position.")
                last_size = 0

            if size > last_size:
                logger.debug(f"[{label}] New data found ({size - last_size} bytes)")
                with log_path.open("r", encoding="utf-8", errors="replace") as f:
                    f.seek(last_size)
                    new_lines = f.readlines()
                    last_size = size

                    grouped = group_log_lines(new_lines, tz_info=tz_info)
                    logger.debug(f"[{label}] Grouped {len(grouped)} events from {len(new_lines)} lines")

                    for message, timestamp in grouped:
                        if not timestamp:
                            logger.warning(f"[{label}] Skipping group without timestamp:\n{message}")
                            continue
                        await post_log(message, label, event_type, tz_info, sink, timestamp_override=timestamp)

            else:
                logger.debug(f"[{label}] No new data (size={size})")

        except FileNotFoundError:
            logger.warning(f"[{label}] File disappeared: {log_path}. Retrying...")

async def main():
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

    ingest_host = config.get("ingest_backend_host", "127.0.0.1")
    ingest_port = config.get("ingest_backend_port", 8001)
    ingest_endpoint = f"http://{ingest_host}:{ingest_port}"
    logger.info(f"Using ingest endpoint: {ingest_endpoint}")

    # Create one sink instance; reuse it for all events
    sink = AsyncHttpSink(endpoint=ingest_endpoint)

    sources = config.get("source_log_tails", [])
    if not sources:
        logger.error("No 'source_log_tails' defined in config.")
        sys.exit(10)

    async def safe_tail(source):
        try:
            await tail_log_file(source, sink)
        except Exception as e:
            logger.exception(f"Error in source '{source.get('label', 'unknown')}': {e}")

    tasks = [asyncio.create_task(safe_tail(source)) for source in sources]
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Log tailer stopped by user.")
