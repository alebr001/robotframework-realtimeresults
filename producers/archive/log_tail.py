# import asyncio
# import sys
# import httpx
# from pathlib import Path
# from datetime import datetime, timezone
# from shared.helpers.config_loader import load_config
# import argparse

# def parse_args():
#     parser = argparse.ArgumentParser(description="Tail a log file and send to ingest API")
#     parser.add_argument("--ingest_host", help="Ingest API host")
#     parser.add_argument("--ingest_port", type=int, help="Ingest API port")
#     parser.add_argument("-p", "--path", help="Path to the log file to tail")
#     parser.add_argument("-s", "--source_label", help="Label to identify the source of this log")
#     parser.add_argument("-i", "--poll_interval", type=float, default=1.0, help="Polling interval in seconds")
#     return parser.parse_args()

# async def post_log(message: str):
#     payload = {
#         "timestamp": datetime.now(timezone.utc).isoformat(),
#         "event_type": "app_log",
#         "message": message,
#         "source": SOURCE_LABEL,
#         "level": "INFO"  # of None
#     }
#     try:
#         async with httpx.AsyncClient(timeout=2.0) as client:
#             print(f"[log_tail] Payload: {payload}")
#             await client.post(INGEST_ENDPOINT, json=payload, timeout=0.5)
#     except Exception as e:
#         print(f"[log_tail] Failed to send log: {e}")

# async def tail_log_file(log_path: str, poll_interval: float):
#     file = Path(log_path)
#     last_size = file.stat().st_size if file.exists() else 0

#     while True:
#         await asyncio.sleep(poll_interval)
#         if not file.exists():
#             Exception(f"[log_tail] Log file {log_path} does not exist.")

#         size = file.stat().st_size
#         if size > last_size:
#             with file.open("r", encoding="utf-8", errors="replace") as f:
#                 f.seek(last_size)
#                 new_lines = f.readlines()
#                 last_size = size

#                 for line in new_lines:
#                     if line.strip():
#                         print(line.strip())  # Schrijf naar stdout
#                         await post_log(line.strip())

# # if __name__ == "__main__":
# #     print(f"[log_tail] Watching {LOG_FILE_PATH}, sending to {INGEST_ENDPOINT}")
# #     try:
# #         asyncio.run(tail_log_file())
# #     except KeyboardInterrupt:
# #         print("[log_tail] Stopped.")

# if __name__ == "__main__":
#     args = parse_args()
#     config = load_config()

#     INGEST_HOST = args.ingest_host or config.get("ingest_backend_host", "127.0.0.1")
#     INGEST_PORT = args.ingest_port or config.get("ingest_backend_port", 8001)
#     INGEST_ENDPOINT = f"http://{INGEST_HOST}:{INGEST_PORT}/log"
#     LOG_FILE_PATH = args.path or config.get("source_log_path", "../flask-logging-demo/single_file_app_pattern/app.log")
#     SOURCE_LABEL = args.source_label or config.get("source_label", "flask-app")
#     POLL_INTERVAL =  args.poll_interval or float(config.get("log_tail_poll_interval", 1.0))

#     if not LOG_FILE_PATH:
#         print("[log_tail] Error: No log path provided via --path or config.json")
#         sys.exit(1)

#     print(f"[log_tail] Watching {LOG_FILE_PATH}, sending to {INGEST_ENDPOINT} (label: {SOURCE_LABEL})")
#     try:
#         asyncio.run(tail_log_file(
#             log_path=LOG_FILE_PATH,
#             poll_interval=POLL_INTERVAL
#         ))
#     except KeyboardInterrupt:
#         print("[log_tail] Stopped.")