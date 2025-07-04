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
from shared.helpers.setup_wizard import run_setup_wizard

# Split off our own --config argument, everything else is passed to robot
if "--config" in sys.argv:
    config_index = sys.argv.index("--config")
    config_path = sys.argv[config_index + 1]
    robot_args = sys.argv[1:config_index] + sys.argv[config_index + 2:] # 1:config_index = everything before --config, config_index + 2: = everything after the config path
else:
    config_path = "realtimeresults_config.json"
    robot_args = sys.argv[1:]


CONFIG_PATH = Path(config_path)

# Run wizard if config is missing
if not CONFIG_PATH.exists():
    print(f"No config found at {CONFIG_PATH}. Launching setup wizard...")
    run_tests = run_setup_wizard(CONFIG_PATH)
    if not run_tests:
        print(f"Please run the command again to run tests.")
        sys.exit(0)

config = load_config(CONFIG_PATH)

VIEWER_BACKEND_HOST = config.get("viewer_backend_host", "127.0.0.1")
VIEWER_BACKEND_PORT = int(config.get("viewer_backend_port", 8000))

INGEST_BACKEND_HOST = config.get("ingest_backend_host", "127.0.0.1")
INGEST_BACKEND_PORT = int(config.get("ingest_backend_port", 8001))

setup_root_logging(config.get("log_level", "info"))
logger = logging.getLogger("rt-cli")
component_level_logging = config.get("log_level_cli")

if component_level_logging:
    logger.setLevel(getattr(logging, component_level_logging.upper(), logging.INFO))

def is_port_used(command):
    try:
        host = command[command.index("--host") + 1]
        port = int(command[command.index("--port") + 1])
    except (ValueError, IndexError):
        raise ValueError("Command must contain --host and --port with values")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((host, port)) == 0

def is_process_running(target_name):
    """
    Check if a process is running whose command (or script) contains the given name.
    Returns the PID of the first found process, or None.
    """
    for proc in psutil.process_iter(attrs=['pid', 'cmdline']):
        try:
            cmdline = proc.info['cmdline'] or []
            if any(target_name in part for part in cmdline):
                return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None

def start_process(command, silent=True):
    stdout_dest = subprocess.DEVNULL if silent else None
    stderr_dest = subprocess.DEVNULL if silent else None

    try:
        # Start subprocess with platform-specific behavior
        if platform.system() == "Windows":
            proc = subprocess.Popen(
                command,
                creationflags=0x00000200,  # CREATE_NEW_PROCESS_GROUP
                stdout=stdout_dest,
                stderr=stderr_dest
            )
        else:
            proc = subprocess.Popen(
                command,
                start_new_session=True,  # Start in new process group on Unix
                stdout=stdout_dest,
                stderr=stderr_dest
            )
        return proc.pid  # Process started successfully, return its PID
    except Exception as e:
        logger.error(f"Failed to start process: {command} — {e}")
        return None  # Any exception during startup is treated as failure


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
    # More then one logfile can be tailed, configure in the realtimeresults_config.json
    logs_tail_cmd = [
        "poetry", "run", "python", "producers/log_producer/log_tails.py"
    ]

    def extract_identifier(command):
        return next((part for part in command if part.endswith(".py") or ":" in part), None)

    # add commands to list to run
    processes = {
    extract_identifier(viewer_cmd): viewer_cmd,
    extract_identifier(ingest_cmd): ingest_cmd,
    }
    # if there are no source log tails in config then do not add cmd for tail
    if config.get("source_log_tails"): processes[extract_identifier(logs_tail_cmd)] = logs_tail_cmd


    pids = {}
    for name, command in processes.items():
        # Check if the service is already running on host and port
        if "--host" in command and "--port" in command:
            if is_port_used(command):
                pid = is_process_running(name)
                logger.info(f"{name} already running on {command[command.index('--host') + 1]}:{command[command.index('--port') + 1]} with PID {pid}")
                pids[name] = pid
                continue

        # If the command does not contain host or port, we assume it's a simple script path
        else:
            script_path = Path(name) if name else None
            # Check if the script exists
            if script_path and not script_path.exists():
                rel_path = script_path.relative_to(Path.cwd()) if script_path.is_absolute() else script_path
                logger.error(f"{command} not executed: {rel_path}")
                logger.error(f"Please check if the path is correct in your CLI config or code.")
                sys.exit(1)

            pid = is_process_running(name)
            if pid:
                logger.info(f"{name} already running with PID {pid}")
                pids[name] = pid
                continue

        # If the service is not running, start it
        pid = start_process(command)

        if pid:
            pids[name] = pid
            logger.info(f"Started {name} backend with PID {pid}")
        else:
            logger.exception(f"Failed to start {name} backend.")
            sys.exit(1)

    if pids:
        with open("backend.pid", "w") as f:
            for name, pid in pids.items():
                f.write(f"{name}={pid}\n")

     #wait for the services to listen
    for _ in range(20):
        if is_port_used(viewer_cmd) and is_port_used(ingest_cmd):
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
    logger.info(f"Dashboard: http://{VIEWER_BACKEND_HOST}:{VIEWER_BACKEND_PORT}/dashboard")


    command = [
        "robot",
        "--listener", f"producers.listener.listener.RealTimeResults:totaltests={total}"
    ] + robot_args

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