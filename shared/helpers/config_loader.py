import json
import tomllib
import os
from pathlib import Path
from typing import Union

def load_config(path=None) -> dict:
    # First check the environment variable if path is not provided
    if path is None:
        # If REALTIME_RESULTS_CONFIG is set, use that; otherwise, default to 'realtimeresults_config.json'
        path = os.environ.get("REALTIME_RESULTS_CONFIG", "realtimeresults_config.json")
    
    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")

    ext = config_path.suffix.lower()
    try:
        with config_path.open("rb") as f:
            if ext == ".json":
                return json.load(f)
            elif ext == ".toml":
                return tomllib.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {ext}")
    except Exception as e:
        print(f"Failed to load config from {config_path}")
        exit(1)