#!/usr/bin/env python3
"""
coresightctl - Technical CLI for ARM CoreSight Diagnostics.
Utility to manage hardware topology and trace capture.
"""

import argparse
import sys
import os

# Ensure modules are importable from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.topology_manager import TopologyManager
from core.trace_capture import TraceCapture

def main():
    parser = argparse.ArgumentParser(description="CoreSight Diagnostic Control Tool")
    subparsers = parser.add_subparsers(dest="command")

    # List
    subparsers.add_parser("list", help="List all detected CoreSight devices")
    
    # Topology
    subparsers.add_parser("topology", help="Show hardware topology graph (Tree view)")
    
    # Path
    path_parser = subparsers.add_parser("path", help="Find valid path between source and sink")
    path_parser.add_argument("source", help="Source device name (e.g., etm0)")
    path_parser.add_argument("sink", help="Sink device name (e.g., tmc_etr0)")

    # Capture
    cap_parser = subparsers.add_parser("capture", help="Trace capture control")
    cap_parser.add_argument("action", choices=["start", "stop", "status"], help="Action to perform")
    cap_parser.add_argument("--source", help="Source device (required for start)")
    cap_parser.add_argument("--sink", help="Sink device (required for start)")
    cap_parser.add_argument("--buffer", type=int, default=1024, help="Buffer size in KB (default: 1024)")

    # Rescan
    subparsers.add_parser("rescan", help="Invalidate cache and rescan hardware bus")

    args = parser.parse_args()
    
    # Initialize TopologyManager (Singleton)
    # Support overriding the path via environment variable for testing
    base_path = os.environ.get("CORESIGHT_BUS_PATH", "/sys/bus/coresight/devices/")
    topo = TopologyManager(base_path=base_path)
    cap = TraceCapture()

    if args.command == "list":
        print(f"{'Device Name':18} | {'Type':10} | {'Subtype':12} | {'Enabled'}")
        print("-" * 55)
        for name, dev in topo.devices.items():
            state = "YES" if dev.enabled else "NO"
            print(f"{name:18} | {dev.type.name:10} | {dev.subtype:12} | {state}")
            
    elif args.command == "topology":
        topo.print_topology()
        
    elif args.command == "rescan":
        topo.refresh_topology()
        print("Rescan complete.")

    elif args.command == "path":
        try:
            p = topo.find_path(args.source, args.sink)
            print("Valid physical path detected:")
            print("  " + " -> ".join(p))
        except Exception:
            print("Path lookup failed")

    elif args.command == "capture":
        if args.action == "start":
            if not args.source or not args.sink:
                print("Error: --source and --sink are required for 'capture start'.")
                return
            try:
                cap.capture_start(args.source, args.sink, args.buffer)
                print("Capture started successfully")
            except Exception:
                print("Capture start failed")
        elif args.action == "stop":
            if cap.capture_stop():
                print("Capture stopped and hardware deactivated.")
            else:
                print("No active capture session found.")
        elif args.action == "status":
            stat = cap.status()
            if stat["capturing"]:
                print("Capture ACTIVE: " + " -> ".join(stat["path"]))
            else:
                print("Capture IDLE")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
