import json
import sys
from pathlib import Path
import os

def ask_yes_no(question: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        answer = input(f"{question} {suffix}: ").strip().lower()
        if answer == "" and default is not None:
            return default
        if answer in ["y", "yes"]:
            return True
        if answer in ["n", "no"]:
            return False
        print("Please enter 'y' or 'n'.")


def ask_string(question: str, default: str = "") -> str:
    suffix = f"[{default}]" if default else ""
    answer = input(f"{question} {suffix}: ").strip()
    return answer if answer else default


def generate_event_type_from_path(path: str) -> str:
    filename = Path(path).name
    return filename.replace(".", "_")


def run_setup_wizard(config_path: Path = None):
    try:
        print("Welcome to the RealtimeResults setup wizard.")
        print("This wizard will help you generate a realtime config file.")
        print("JSON and TOML formats are supported.\n")

        if config_path is None:
            filename = ask_string("Filename for new config", "realtimeresults_config.json")
            config_path = Path(filename)

        config = {}

        # --- VIEWER ---
        use_viewer = ask_yes_no("Enable viewer backend (dashboard)?", True)
        if use_viewer:
            config["viewer_backend_host"] = ask_string("Viewer host", "127.0.0.1")
            config["viewer_backend_port"] = int(ask_string("Viewer port", "8002"))
        else:
            config["viewer_backend_host"] = "NONE"
            config["viewer_backend_port"] = 0

        # --- INGEST ---
        use_ingest = ask_yes_no("Enable ingest backend (for API-based writing to database)?", True)
        if use_ingest:
            config["ingest_backend_host"] = ask_string("Ingest host", "127.0.0.1")
            config["ingest_backend_port"] = int(ask_string("Ingest port", "8001"))
            
            # --- DATABASE URL ---
            config["database_url"] = ask_string(
            "Database URL (e.g. sqlite:///eventlog.db or postgresql://...)", "sqlite:///eventlog.db"
            )
            # --- STRATEGY / SINK TYPES ---

            config["listener_sink_type"] = "http"

            # --- LOG TAIL SOURCES ---
            support_app_logs = ask_yes_no("Do you want to tail log files?", True)
            source_log_tails = []

            while support_app_logs:
                print("You can add multiple log files. Each will be a separate source in the config.")

                log_path = ask_string("Log file path (relative to project root)")
                log_label = ask_string("Label for this source")
                event_type = generate_event_type_from_path(log_path)

                def get_system_timezone():
                    try:
                        localtime_path = os.path.realpath("/etc/localtime")
                        if "zoneinfo" in localtime_path:
                            return localtime_path.split("zoneinfo/")[-1]
                    except Exception:
                        pass
                    return "Europe/Amsterdam" # Fallback

                timezone = ask_string("Timezone (e.g. Europe/Amsterdam)", get_system_timezone())

                source_log_tails.append({
                    "path": log_path,
                    "label": log_label,
                    "poll_interval": 1.0,
                    "event_type": event_type,
                    "log_level": "INFO",
                    "tz_info": timezone
                })

                support_app_logs = ask_yes_no("Add another log file?", False)

            config["source_log_tails"] = source_log_tails
        else:
            # If no ingest API, set listener type
            print("Set a sink type for the robot framework listener, this can be direct to sqlite, use a http sink of direct to loki(todo)")
            config["listener_sink_type"] = ask_string("Sink type for the RF-listener (e.g. sqlite, http, loki [todo])", "sqlite")
            config["ingest_backend_host"] = "NONE"
            config["ingest_backend_port"] = 0
            config["source_log_tails"] = []

        # --- AUTO SERVICES ---
        enable_auto_services = ask_yes_no("Automatically start backend services?", True)
        config["enable_auto_services"] = enable_auto_services
        if not enable_auto_services:
                print("Always start desired backend services manually before running tests.")

        # --- LOGLEVELS ---
        config["log_level"] = "INFO"
        config["log_level_listener"] = ""
        config["log_level_backend"] = ""
        config["log_level_cli"] = ""

        # --- LOKI ---
        config["loki_endpoint"] = "http://localhost:3100"

        # --- WRITE TO FILE ---

        with config_path.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        print(f"\nConfig written to: {Path(config_path).resolve()}")
        return ask_yes_no("Continue?", True)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user (Ctrl+C). No config file was written.")
        sys.exit(130)