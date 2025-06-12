#!/usr/bin/env python
import subprocess
import sys
import os
import time
import socket
from robot.running.builder import TestSuiteBuilder
from helpers.logger import setup_logging
import logging

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
setup_logging("info")
logger = logging.getLogger("rt-robot")

def is_port_open(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((host, port)) == 0

def start_backend():
    logger.debug("backend not running, starting it now...")
    subprocess.Popen([
        "poetry", "run", "uvicorn", "backend.main:app",
        "--host", BACKEND_HOST, "--port", str(BACKEND_PORT),
        "--reload"
    ])
    #wait for the backend to listen on the port
    for _ in range(20):
        if is_port_open(BACKEND_HOST, BACKEND_PORT):
            return
        time.sleep(0.25)
    print("[rt-robot] Timeout starting backend.")
    sys.exit(1)

def count_tests(path):
    try:
        suite = TestSuiteBuilder().build(path)
        return suite.test_count
    except Exception as e:
        print(f"[rt-robot] Cannot count tests: {e}")
        return 0

def main():    
    args = sys.argv[1:]
    test_path = args[-1] if args else "tests/"
    total = count_tests(test_path)

    if not is_port_open(BACKEND_HOST, BACKEND_PORT):
        start_backend()
    logger.info(f"[rt-robot] Backend running on http://{BACKEND_HOST}:{BACKEND_PORT}")

    command = [
        "poetry", "run", "robot",
        "--listener", "realtimeresults.listener.RealTimeResults",
        "--variable", f"totaltests:{total}"
    ] + args

    logger.info(f"[rt-robot] Starting testrun... with total tests: {total}")
    subprocess.run(command)

    logger.info(f"\n[rt-robot] Testrun finished. Dashboard: http://{BACKEND_HOST}:{BACKEND_PORT}/dashboard")

if __name__ == "__main__":
    main()