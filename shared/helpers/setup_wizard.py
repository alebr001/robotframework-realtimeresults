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


def run_setup_wizard(config_path: Path = Path("realtimeresults_config.json")):
    try:
        print("Welcome to the RealtimeResults setup wizard.")
        print("This wizard will help you generate a realtimeresults config file.")
        print("Json and toml formats are supported. Default config is realtimeresults_config.json.")

        config = {}

        # --- ENABLE VIEWER ---
        use_viewer = ask_yes_no("Do you want to enable the viewer backend? (Required to use Dashboard)", True)
        if use_viewer:
            viewer_host = ask_string("Viewer backend host", "127.0.0.1")
            viewer_port = int(ask_string("Viewer backend port", "8000"))
        else:
            viewer_host = "NONE"
            viewer_port = 0
        config["viewer_backend_host"] = viewer_host
        config["viewer_backend_port"] = viewer_port

        # --- ENABLE INGEST API ---
        use_ingest = ask_yes_no(
            "Do you want to enable the ingest backend? (Required for logging via API)", True
        )
        if use_ingest:
            ingest_host = ask_string("Ingest backend host", "127.0.0.1")
            ingest_port = int(ask_string("Ingest backend port", "8001"))
            config["ingest_backend_host"] = ingest_host
            config["ingest_backend_port"] = ingest_port
           
            # --- DATABASE URL ---
            config["database_url"] = ask_string(
                "Enter the database URL (e.g. sqlite:///eventlog.db, postgresql://user:pass@host:port/dbname)",
                "sqlite:///eventlog.db"
            )

            # --- STRATEGY / SINK TYPES ---
            if use_ingest:
                config["listener_sink_type"] = "http"
                config["ingest_sink_type"] = ask_string("Sink type for the ingest API", "async")
            else:
                # If no ingest API, set listener type
                config["listener_sink_type"] = ask_string("Sink type for the RF-listener (e.g. sqlite, loki [todo])", "sqlite")

            # --- APPLICATION LOGGING ---
            support_app_logs = ask_yes_no("Do you want to support application log tailing?", True)
            source_log_tails = []

            while support_app_logs:
                print("You can add multiple log files. Each will be a separate source in the config.")
                print("please provide the full file path relative to the config file location.")
                log_path = ask_string("Enter the log file path relative to the config file")
                log_label = ask_string("Enter a label for this source")
                event_type = generate_event_type_from_path(log_path)
            
                def get_system_timezone():
                    try:
                        localtime_path = os.path.realpath("/etc/localtime")
                        if "zoneinfo" in localtime_path:
                            return localtime_path.split("zoneinfo/")[-1]
                    except Exception:
                        pass
                    return "Europe/Amsterdam"  # Fallback

                timezone = ask_string("Enter timezone (e.g. Europe/Amsterdam, UTC, etc.)", get_system_timezone())

                # Run wizard if config is missing
                source_log_tails.append({
                    "path": log_path,
                    "label": log_label,
                    "poll_interval": 1.0,
                    "event_type": event_type,
                    "log_level": "INFO",
                    "tz_info": timezone
                })

                support_app_logs = ask_yes_no("Do you want to add another log file?", False)

            config["source_log_tails"] = source_log_tails
        else:
            config["ingest_backend_host"] = "NONE"
            config["ingest_backend_port"] = 0
            config["source_log_tails"] = []

        # --- ENABLE AUTO SERVICES ---
        enable_auto_services = ask_yes_no("Automatically start backend services?", True)
        config["enable_auto_services"] = enable_auto_services

        if not enable_auto_services:
            print("Always start desired backend services manually before running tests.")

        # --- LOG LEVELS ---
        config["log_level"] = "INFO"
        config["log_level_listener"] = ""
        config["log_level_backend"] = ""
        config["log_level_cli"] = ""

        # --- LOKI PLACEHOLDER ---
        config["loki_endpoint"] = "http://localhost:3100"

        # --- BACKEND ENDPOINT ---
        config["backend_endpoint"] = f"http://{viewer_host}:{viewer_port}" if use_viewer else "NONE"

        # --- WRITE TO FILE ---
        config_path = Path(config_path)
        with config_path.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        print(f"\nConfiguration complete. Config written to: {config_path.resolve()}")

        return ask_yes_no("Continue?", True)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user (Ctrl+C). No config file was written.")
        sys.exit(130)