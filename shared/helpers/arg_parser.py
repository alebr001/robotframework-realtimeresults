import logging
from pathlib import Path
import sys

from shared.helpers.kill_backend import kill_backend
from shared.helpers.setup_wizard import run_setup_wizard

logger = logging.getLogger("rt-cli")

def arg_error(message: str):
    logger.error(f"Argument error: {message}")
    sys.exit(2)

def coerce_value(value: str):
    lower = value.lower()

    if lower in ("true", "yes", "1"):
        return True
    if lower in ("false", "no", "0"):
        return False

    # int?
    if lower.isdigit():
        return int(lower)

    return value

RT_FLAGS_WITH_VALUE = {
    "--runservice": "service",
    "--run": "service",
    "--start": "service",
    "--configfile": "path",
    "-c": "path",
    "--set": "kv",
}

RT_FLAGS_NO_VALUE = {
    "--setup",
    "--killbackend",
    "--kill_backend",
    "--kill",
    "-k",
    "--help",
    "-h",
}

def parse_args():
    service_name = None
    config_path = Path("realtimeresults_config.json")
    config_overrides = {}
    robot_args = []

    argv = sys.argv[1:]
    i = 0

    while i < len(argv):
        arg = argv[i]

        # ---- rt-robot flags zonder waarde ----
        if arg in RT_FLAGS_NO_VALUE:
            if arg in ("--setup",):
                run_setup_wizard()
                sys.exit(0)
            if arg in ("--killbackend", "--kill_backend", "--kill", "-k"):
                kill_backend()
                sys.exit(0)
            if arg in ("--help", "-h"):
                logger.info(
                    "Usage: python cli.py [options] [robot arguments]\n"
                    "Options:\n"
                    "  --help, -h           Show this help message and exit\n"
                    "  --setup              Create new configfile\n"
                    "  --runservice NAME    Start a single backend service (viewer, ingest, combined)\n"
                    "  --configfile, -c PATH        Use a custom config file\n"
                    "  --killbackend, -k    Stop all backend services\n"
                    " --set KEY=VALUE      Override config values from command line\n"
                    "\n"
                    "All other arguments are passed to Robot Framework.\n"
                    "Examples:\n"
                    "  rt-robot --runservice api.viewer.main:app --configfile myconfig.json\n"
                    "  rt-robot --configfile myconfig.json --outputdir examples/results/ --debugfile debug.log tests/\n"
                )
                sys.exit(0)

            i += 1
            continue

        # ---- rt-robot flags met waarde ----
        if arg in RT_FLAGS_WITH_VALUE:
            if i + 1 >= len(argv):
                arg_error(f"{arg} requires a value")

            value = argv[i + 1]
            if value.startswith("-"):
                arg_error(f"{arg} requires a value, got '{value}'")

            kind = RT_FLAGS_WITH_VALUE[arg]

            if kind == "service":
                if " " in value:
                    arg_error("Service name must not contain spaces")
                service_name = value

            elif kind == "path":
                config_path = Path(value)

            elif kind == "kv":
                if "=" not in value:
                    arg_error("--set requires KEY=VALUE")
                k, v = value.split("=", 1)
                config_overrides[k] = coerce_value(v)

            i += 2
            continue

        # ---- everything else ----
        # from here on: Robot Framework territory
        robot_args.append(arg)
        i += 1

    return service_name, config_path, config_overrides, robot_args
