import json
import tomllib
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

class ConfigError(Exception):
    """Raised when the config file is invalid or required keys are missing."""


_cached_config: Optional[Dict[str, Any]] = None

def load_config(path: Union[str, Path, None] = None, override_with_env: bool = True) -> dict:
    global _cached_config

    if _cached_config is not None:
        return _cached_config
 
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
        # Define all possible config keys
        KNOWN_CONFIG_KEYS = [
            "listener_sink_type", "database_url",
            "viewer_backend_host", "viewer_backend_port",
            "viewer_client_host", "viewer_client_port",
            "ingest_backend_host", "ingest_backend_port", 
            "ingest_client_host", "ingest_client_port", 
            "enable_autoservices", "log_level", "log_level_cli", 
            "log_level_listener", "loki_endpoint"
        ]
        
        # Check ALL known keys + any existing config keys
        all_keys = set(KNOWN_CONFIG_KEYS) | set(config.keys())

        for key in all_keys:
            env_key = key.upper()
            env_value = os.getenv(env_key)
            if env_value is not None:
                print(f"[CONFIG] Overriding '{key}' with environment variable '{env_key}'")
                config[key] = env_value

    REQUIRED_KEYS = ["listener_sink_type"]
    missing = [k for k in REQUIRED_KEYS if not config.get(k)]
    if missing:
        raise ConfigError(f"[CONFIG ERROR] Missing required config key(s): {', '.join(missing)}")

    _cached_config = config
    return config

def clear_config_cache():
    """Clear cached config (useful for testing)."""
    global _cached_config
    _cached_config = None