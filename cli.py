#!/usr/bin/env python
import subprocess
import sys
import logging
import platform
import time
import socket
from helpers.config_loader import load_config
from robot.running.builder import TestSuiteBuilder
from helpers.logger import setup_root_logging

config = load_config()
BACKEND_HOST = config.get("backend_host", "127.0.0.1")
BACKEND_PORT = int(config.get("backend_port", 8000)
                   )
setup_root_logging(config.get("log_level", "info"))
logger = logging.getLogger("rt-cli")
component_level_logging = config.get("log_level_cli")

if component_level_logging:
    logger.setLevel(getattr(logging, component_level_logging.upper(), logging.INFO))

def is_port_open(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((host, port)) == 0

def start_backend(silent=True):
    logger.debug("backend not running, starting it now...")
   
    command = [
        "poetry", "run", "uvicorn",
        "backend.main:app",
        "--host", BACKEND_HOST,
        "--port", str(BACKEND_PORT),
        "--reload"
    ]

    stdout_dest = subprocess.DEVNULL if silent else None
    stderr_dest = subprocess.DEVNULL if silent else None

    if platform.system() == "Windows":
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        process = subprocess.Popen(
            command,
            creationflags=CREATE_NEW_PROCESS_GROUP, # prevents ctrl+C to stop the run
            stdout=stdout_dest,
            stderr=stderr_dest
        )
    else:
        process = subprocess.Popen(
            command,
            start_new_session=True, # prevents ctrl+C to stop the run
            stdout=stdout_dest,
            stderr=stderr_dest
        )

    with open("backend.pid", "w") as f:
        f.write(str(process.pid))

    #wait for the backend to listen on the port
    for _ in range(20):
        if is_port_open(BACKEND_HOST, BACKEND_PORT):
            logger.info("Backend running in background.")
            return process.pid
        time.sleep(0.25)
    logger.warning("Timeout starting backend.")
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

    pid = None
    if not is_port_open(BACKEND_HOST, BACKEND_PORT):
        pid = start_backend()
    logger.info(f"Backend running on http://{BACKEND_HOST}:{BACKEND_PORT}")
    logger.debug("------DEBUGTEST----------")

    command = [
        "robot",
        "--listener", f"realtimeresults.listener.RealTimeResults:totaltests={total}"
    ] + args

    try:
        subprocess.run(command)
    except KeyboardInterrupt:
        logger.warning("Test run interrupted by user (Ctrl+C)")
        sys.exit(130)

    logger.info(f"Testrun finished. Dashboard: http://{BACKEND_HOST}:{BACKEND_PORT}/dashboard")
    if pid:
        logger.info("Backend running in background.")
        logger.info("For backend logging run this command in seperate terminal:")
        logger.info(f"poetry run uvicorn backend.main:app --reload --host {BACKEND_HOST} --port {BACKEND_PORT}")
        logger.info(f"PID to kill current back-end: {pid}")
        
if __name__ == "__main__":
    main()