#!/usr/bin/env python
import subprocess
import psutil
import sys
import logging
import platform
import time
import socket
from pathlib import Path
from shared.helpers.config_loader import load_config
from robot.running.builder import TestSuiteBuilder
from shared.helpers.logger import setup_root_logging

config = load_config()
VIEWER_BACKEND_HOST = config.get("viewer_backend_host", "127.0.0.1")
VIEWER_BACKEND_PORT = int(config.get("viewer_backend_port", 8000))

INGEST_BACKEND_HOST = config.get("ingest_backend_host", "127.0.0.1")
INGEST_BACKEND_PORT = int(config.get("ingest_backend_port", 8001))

setup_root_logging(config.get("log_level", "info"))
logger = logging.getLogger("rt-cli")
component_level_logging = config.get("log_level_cli")

if component_level_logging:
    logger.setLevel(getattr(logging, component_level_logging.upper(), logging.INFO))

def is_port_open(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((host, port)) == 0

def is_process_running(script_name):
    for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
        try:
            if script_name in proc.info['cmdline']:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

def start_process(command, silent=True):
    script_path = Path(command[-1]) if command else None
    # Check if the script exists
    if script_path and not script_path.exists():
        rel_path = script_path.relative_to(Path.cwd()) if script_path.is_absolute() else script_path
        logger.error(f"Script {script_path.name} not found: {rel_path}")
        logger.error(f"Please check if the path is correct in your CLI config or code.")
        sys.exit(1)
    # Check if the script is already running
    if script_path and script_path.suffix == ".py":
        for proc in psutil.process_iter(attrs=["pid", "cmdline"]):
            try:
                cmdline = proc.info.get("cmdline") or []
                if any(script_path.name in part for part in cmdline):
                    logger.info(f"{script_path.name} is already running with PID {proc.info['pid']}, skipping start.")
                    return None
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    stdout_dest = subprocess.DEVNULL if silent else None
    stderr_dest = subprocess.DEVNULL if silent else None

    if platform.system() == "Windows":
        return subprocess.Popen(
            command,
            creationflags=0x00000200,
            stdout=stdout_dest,
            stderr=stderr_dest
        )
    else:
        return subprocess.Popen(
            command,
            start_new_session=True,
            stdout=stdout_dest,
            stderr=stderr_dest
        )


def start_services(silent=True):
    logger.debug("backend not running, starting it now...")
   
    viewer_cmd = [
        "poetry", "run", "uvicorn", "api.viewer.main:app", 
        "--host", VIEWER_BACKEND_HOST, "--port", str(VIEWER_BACKEND_PORT), "--reload"
    ]
    ingest_cmd = [
        "poetry", "run", "uvicorn", "api.ingest.main:app",
        "--host", INGEST_BACKEND_HOST, "--port", str(INGEST_BACKEND_PORT), "--reload"
    ]
    # Command to start the log tailing process
    # More then one logfile can be tailed, configure in the config.json
    logs_tail_cmd = [
        "poetry", "run", "python", "producers/log_producer/log_tails.py"
    ]

    pids = {}

    if not is_port_open(VIEWER_BACKEND_HOST, VIEWER_BACKEND_PORT):
        proc = start_process(viewer_cmd)
        if proc is not None:
            pids["viewer"] = proc.pid
            logger.info("Started viewer backend")
        else:
            logger.error("Failed to start viewer backend.")

    if not is_port_open(INGEST_BACKEND_HOST, INGEST_BACKEND_PORT):
        proc = start_process(ingest_cmd)
        if proc is not None:
            pids["ingest"] = proc.pid
            logger.info("Started ingest backend")
        else:
            logger.error("Failed to start ingest backend.")

    proc = start_process(logs_tail_cmd)
    if proc is not None:
        pids["logs_tail"] = proc.pid
        logger.info("Started logs tail")

    with open("backend.pid", "w") as f:
        for name, pid in pids.items():
            f.write(f"{name}={pid}\n")

    #wait for the services to listen
    for _ in range(20):
        if is_port_open(VIEWER_BACKEND_HOST, VIEWER_BACKEND_PORT) and is_port_open(INGEST_BACKEND_HOST, INGEST_BACKEND_PORT):
            return pids
        time.sleep(0.25)

    logger.warning("Timeout starting backend services.")
    sys.exit(1)

def count_tests(path):
    try:
        suite = TestSuiteBuilder().build(path)
        return suite.test_count
    except Exception as e:
        logger.error(f"Cannot count tests: {e}")
        return 0

def main():    
    args = sys.argv[1:]
    test_path = args[-1] if args else "tests/"
    total = count_tests(test_path)
    logger.info(f"Starting testrun... with total tests: {total}")

    pids = start_services()

    logger.debug(f"Viewer: http://{VIEWER_BACKEND_HOST}:{VIEWER_BACKEND_PORT}")
    logger.debug(f"Ingest: http://{INGEST_BACKEND_HOST}:{INGEST_BACKEND_PORT}")

    command = [
        "robot",
        "--listener", f"producers.listener.listener.RealTimeResults:totaltests={total}"
    ] + args

    try:
        subprocess.run(command)
    except KeyboardInterrupt:
        logger.warning("Test run interrupted by user (Ctrl+C)")
        sys.exit(130)

    logger.info(f"Testrun finished. Dashboard: http://{VIEWER_BACKEND_HOST}:{VIEWER_BACKEND_PORT}/dashboard")
    if pids:
        for name, pid in pids.items():
            logger.info(f"Service {name} started with PID {pid}")
        logger.info("Run 'python kill_backend.py' to terminate the background processes.")
        
if __name__ == "__main__":
    main()