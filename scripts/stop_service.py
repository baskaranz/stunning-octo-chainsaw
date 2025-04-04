#!/usr/bin/env python3
"""
Stop Orchestrator API Service

This script gracefully stops a running orchestrator API service
by finding its process and sending a termination signal.
"""

import os
import signal
import subprocess
import sys
import time

def find_orchestrator_pid():
    """Find the PID of the running orchestrator API service."""
    try:
        # Look for the uvicorn process running the main.py app
        result = subprocess.run(
            ["pgrep", "-f", "uvicorn.*main"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            return None
        
        pids = result.stdout.strip().split('\n')
        return [int(pid) for pid in pids if pid]
    except Exception as e:
        print(f"Error finding orchestrator process: {e}")
        return None

def stop_orchestrator(graceful=True):
    """Stop the orchestrator API service.
    
    Args:
        graceful: If True, uses SIGTERM for graceful shutdown.
                 If False, uses SIGKILL for immediate termination.
    """
    pids = find_orchestrator_pid()
    
    if not pids:
        print("No running orchestrator API service found.")
        return
    
    signal_to_use = signal.SIGTERM if graceful else signal.SIGKILL
    signal_name = "SIGTERM" if graceful else "SIGKILL"
    
    for pid in pids:
        try:
            print(f"Stopping orchestrator API service (PID: {pid}) with {signal_name}...")
            os.kill(pid, signal_to_use)
        except OSError as e:
            print(f"Error stopping process {pid}: {e}")
    
    # Wait for processes to terminate
    if graceful:
        attempts = 0
        max_attempts = 5
        while attempts < max_attempts:
            time.sleep(1)
            remaining_pids = find_orchestrator_pid()
            if not remaining_pids:
                print("Orchestrator API service stopped successfully.")
                return
            attempts += 1
        
        print("Orchestrator service didn't stop within expected time.")
        print("Attempting forceful termination...")
        stop_orchestrator(graceful=False)
    else:
        print("Orchestrator API service forcefully terminated.")

if __name__ == "__main__":
    graceful = True
    
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        graceful = False
    
    stop_orchestrator(graceful)