import argparse
import os
import subprocess
import json
from shared.helpers.config_loader import load_config 

def resolve_host_port(appname, config):
    if "ingest" in appname:
        return config.get("ingest_backend_host", "127.0.0.1"), config.get("ingest_backend_port", 8001)
    elif "viewer" in appname:
        return config.get("viewer_backend_host", "127.0.0.1"), config.get("viewer_backend_port", 8000)
    else:
        raise ValueError(f"Kan host/port niet afleiden uit appname: {appname}")

parser = argparse.ArgumentParser(description="Start een uvicorn-app met config support.")
parser.add_argument("appname", help="Pad naar de app, bv. 'api.ingest.main:app'")
parser.add_argument("--config", default="config.json", help="Pad naar config.json (optioneel)")
args = parser.parse_args()

# Zet env var zodat andere modules config kunnen vinden
os.environ["REALTIME_RESULTS_CONFIG"] = args.config

# Laad config en bepaal host/port
config = load_config(args.config)
host, port = resolve_host_port(args.appname, config)

# Start uvicorn
cmd = [
    "poetry", "run", "uvicorn",
    args.appname,
    "--host", host,
    "--port", str(port),
    "--reload"
]
subprocess.run(cmd)