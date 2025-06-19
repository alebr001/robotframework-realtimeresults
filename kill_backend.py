#!/usr/bin/env python
import os
import signal
import sys
import platform

PID_FILE = "backend.pid"

def kill_backend():
    if not os.path.exists(PID_FILE):
        print(f"PID file '{PID_FILE}' not found.")
        sys.exit(1)

    with open(PID_FILE, "r") as f:
        try:
            pid = int(f.read().strip())
        except ValueError:
            print("Invalid PID file content.")
            sys.exit(1)

    system = platform.system()

    try:
        if system == "Windows":
            print(f"Attempting to terminate process {pid} on Windows...")
            os.system(f"taskkill /PID {pid} /F")
        else:
            print(f"Sending SIGTERM to process {pid} on {system}...")
            os.kill(pid, signal.SIGTERM)

        print("Process terminated.")
        os.remove(PID_FILE)

    except ProcessLookupError:
        print(f"No process found with PID {pid}.")
        os.remove(PID_FILE)
    except Exception as e:
        print(f"Failed to kill process {pid}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    kill_backend()