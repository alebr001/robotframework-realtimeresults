#!/usr/bin/env python
import subprocess
import sys
import logging
import platform
import time
import socket
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

def start_process(command, silent=True):
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
    log_tail_cmd = [
        "poetry", "run", "python", "ingest/source/log_tail.py"
    ]

    pids = {}

    if not is_port_open(VIEWER_BACKEND_HOST, VIEWER_BACKEND_PORT):
        proc = start_process(viewer_cmd)
        pids["viewer"] = proc.pid
        logger.info("Started viewer backend")

    if not is_port_open(INGEST_BACKEND_HOST, INGEST_BACKEND_PORT):
        proc = start_process(ingest_cmd)
        pids["ingest"] = proc.pid
        logger.info("Started ingest backend")

    proc = start_process(log_tail_cmd)
    pids["log_tail"] = proc.pid
    logger.info("Started log tail")


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

    logger.info(f"Viewer: http://{VIEWER_BACKEND_HOST}:{VIEWER_BACKEND_PORT}")
    logger.info(f"Ingest: http://{INGEST_BACKEND_HOST}:{INGEST_BACKEND_PORT}")

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
            logger.info(f"PID to kill current back-end: {pid}")
        logger.info(f"poetry run uvicorn backend.main:app --reload --host {VIEWER_BACKEND_HOST} --port {VIEWER_BACKEND_PORT}")
        
if __name__ == "__main__":
    main()