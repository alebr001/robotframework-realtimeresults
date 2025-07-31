import json
import tomllib
import os
from pathlib import Path
from typing import Union

def load_config(path: Union[str, Path, None] = None, override_with_env: bool = True) -> dict:
    # First check the environment variable if path is not provided
    if path is None:
        # If REALTIME_RESULTS_CONFIG is set in cli wrapper, use that; otherwise, default to 'realtimeresults_config.json'
        path = os.environ.get("REALTIME_RESULTS_CONFIG", "realtimeresults_config.json")

    config_path = Path(path)
    config: dict = {}

    # read configfile
    if config_path.exists():
        ext = config_path.suffix.lower()
        try:
            with config_path.open("rb") as f:
                if ext == ".json":
                    config = json.load(f)
                elif ext == ".toml":
                    config = tomllib.load(f)
                else:
                    raise ConfigError(f"Unsupported config file format: {ext}")
        except Exception as e:
            raise ConfigError(f"Failed to load config from {config_path}: {e}")
    else:
        print(f"Config file not found at {config_path}, continuing with empty config")

    # Override with env vars
    if override_with_env:
        for key in list(config.keys()):
            env_key = key.upper()
            env_value = os.getenv(env_key)
            if env_value is not None:
                print(f"[CONFIG] Overriding '{key}' with environment variable '{env_key}'")
                config[key] = env_value

    REQUIRED_KEYS = ["database_url", "ingest_sink_type"]
    missing = [k for k in REQUIRED_KEYS if not config.get(k)]
    if missing:
        raise ConfigError(f"[CONFIG ERROR] Missing required config key(s): {', '.join(missing)}")

    return config


class ConfigError(Exception):
    """Raised when the config file is invalid or required keys are missing."""

