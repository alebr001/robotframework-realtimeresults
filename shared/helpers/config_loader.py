import json
import tomllib
from pathlib import Path
from typing import Union

def load_config(config_path: Union[str, Path] = "realtimeresults_config.json") -> dict:
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")

    ext = config_path.suffix.lower()
    with config_path.open("rb") as f:
        if ext == ".json":
            return json.load(f)
        elif ext == ".toml":
            return tomllib.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {ext}")