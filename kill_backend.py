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

    system = platform.system()
    killed = False

    with open(PID_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if "=" not in line:
                continue
            name, pid_str = line.split("=", 1)
            try:
                pid = int(pid_str)
            except ValueError:
                print(f"Ignoring invalid PID line: {line}")
                continue

            try:
                if system == "Windows":
                    print(f"Terminating {name} (PID {pid}) on Windows...")
                    os.system(f"taskkill /PID {pid} /F")
                else:
                    print(f"Sending SIGTERM to {name} (PID {pid}) on {system}...")
                    os.kill(pid, signal.SIGTERM)
                killed = True
            except ProcessLookupError:
                print(f"No process found with PID {pid} for {name}.")
            except Exception as e:
                print(f"Failed to kill {name} (PID {pid}): {e}")

    if killed:
        os.remove(PID_FILE)
        print("All listed processes are terminated and PID file removed.")
    else:
        os.remove(PID_FILE)
        print("No listed processes are terminated please remove PID file if it still exists.")

if __name__ == "__main__":
    kill_backend()