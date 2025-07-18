#!/usr/bin/env python
import os
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

def parse_args():
    """Simple manual parsing to support --runservice and --config."""
    service_name = None
    config_path = "realtimeresults_config.json"
    robot_args = []

    if "--runservice" in sys.argv:
        runservice_index = sys.argv.index("--runservice")
        service_name = sys.argv[runservice_index + 1]

    if "--config" in sys.argv:
        config_index = sys.argv.index("--config")
        config_path = sys.argv[config_index + 1]
        robot_args = sys.argv[1:config_index] + sys.argv[config_index + 2:]
    else:
        robot_args = sys.argv[1:]

    return service_name, Path(config_path), robot_args

def get_command(appname: str, config: dict) -> list[str]:
    if appname.endswith(".py"):
        return [sys.executable, appname]

    if "ingest" in appname:
        host = config.get("ingest_backend_host", "127.0.0.1")
        port = config.get("ingest_backend_port", 8001)
    elif "viewer" in appname:
        host = config.get("viewer_backend_host", "127.0.0.1")
        port = config.get("viewer_backend_port", 8000)
    elif "combined" in appname:
        host = config.get("combined_backend_host", "127.0.0.1")
        port = config.get("combined_backend_port", 8080)
    else:
        raise ValueError(f"Unknown appname '{appname}'")

    return [
        sys.executable, "-m", "uvicorn",
        appname,
        "--host", host,
        "--port", str(port),
        "--reload"
    ]

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
    for proc in psutil.process_iter(attrs=['pid', 'cmdline']):
        try:
            cmdline = proc.info['cmdline'] or []
            if any(target_name in part for part in cmdline):
                return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None

def start_process(command, env, silent=True):
    stdout_dest = subprocess.DEVNULL if silent else None
    stderr_dest = subprocess.DEVNULL if silent else None

    try:
        if platform.system() == "Windows":
            proc = subprocess.Popen(
                command,
                creationflags=0x00000200,  # CREATE_NEW_PROCESS_GROUP
                stdout=stdout_dest,
                stderr=stderr_dest,
                env=env
            )
        else:
            proc = subprocess.Popen(
                command,
                start_new_session=True,
                stdout=stdout_dest,
                stderr=stderr_dest,
                env=env
            )
        return proc.pid
    except Exception as e:
        logger.error(f"Failed to start process: {command} — {e}")
        return None

def start_services(config, env, silent=True):
    logger.debug("Backend not running, starting it now...")
    services_to_start = [
        "api.viewer.main:app",
        "api.ingest.main:app",
    ]
    if config.get("source_log_tails"):
        services_to_start.append("producers/log_producer/log_tails.py")
        
    # Build the processes dict with service name as key
    processes = {service: get_command(service, config) for service in services_to_start}
    
    pids = {}
    for name, command in processes.items():
        # Check if the command contains --host and --port
        # if the port is already in use, skip starting it
        if "--host" in command and "--port" in command:
            if is_port_used(command):
                pid = is_process_running(name)
                logger.info(f"{name} already running with PID {pid}")
                pids[name] = pid
                continue
        pid = start_process(command, env=env)
        if pid:
            pids[name] = pid
            logger.info(f"Started {name} with PID {pid}")
        else:
            logger.error(f"Failed to start {name}")
            sys.exit(1)

    # filter commands that use ports, this is to avoid checking processes that do not use ports
    port_commands = [
        command for command in processes.values() if "--host" in command and "--port" in command
    ]

    for _ in range(20):
        # Check only commands that use ports
        if all(is_port_used(cmd) for cmd in port_commands):
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
    service_name, config_path, robot_args = parse_args()

    if not config_path.exists():
        print(f"No config found at {config_path}. Launching setup wizard...")
        if not run_setup_wizard(config_path):
            print("Setup completed. Please re-run this command.")
            sys.exit(0)

    config = load_config(config_path)
    # set up environment variable for config path
    env = os.environ.copy()
    env["REALTIME_RESULTS_CONFIG"] = str(config_path)

    setup_root_logging(config.get("log_level", "info"))
    global logger
    logger = logging.getLogger("rt-cli")
    if lvl := config.get("log_level_cli"):
        logger.setLevel(getattr(logging, lvl.upper(), logging.INFO))

    if service_name:
        command = get_command(service_name, config)
        # also inject all env vars (incl config path) into the process
        subprocess.run(command, env=env)
        return

    test_path = robot_args[-1] if robot_args else "tests/"
    total = count_tests(test_path)
    logger.info(f"Starting testrun... total tests: {total}")

    # also inject all env vars (incl config path) into the subprocesses
    pids = start_services(config, env=env)

    logger.debug(f"Viewer: http://{config.get('viewer_backend_host', '127.0.0.1')}:{config.get('viewer_backend_port', 8000)}")
    logger.debug(f"Ingest: http://{config.get('ingest_backend_host', '127.0.0.1')}:{config.get('ingest_backend_port', 8001)}")
    logger.info(f"Dashboard: http://{config.get('viewer_backend_host', '127.0.0.1')}:{config.get('viewer_backend_port', 8000)}/dashboard")
    command = [
        "robot", "--listener",
        f"producers.listener.listener.RealTimeResults:totaltests={total}"
    ] + robot_args

    try:
        subprocess.run(command)
    except KeyboardInterrupt:
        logger.warning("Test run interrupted by user")
        sys.exit(130)

    logger.info(f"Testrun finished. Dashboard: http://{config.get('viewer_backend_host', '127.0.0.1')}:{config.get('viewer_backend_port', 8000)}/dashboard")
    for name, pid in pids.items():
        logger.info(f"Service {name} started with PID {pid}")
    logger.info("Run 'python kill_backend.py' to stop background processes.")

if __name__ == "__main__":
    main()
