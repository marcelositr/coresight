"""
CoreSight Topology Manager.
Builds and maintains a graph-based representation of the hardware topology.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Set
import os
from modules.hardware_interface import HardwareInterface
from modules.exceptions import TopologyError
from modules.debug_logger import logger

class DeviceType(Enum):
    SOURCE = 1
    LINK = 2
    SINK = 3
    UNKNOWN = 0

@dataclass
class CoreSightDevice:
    name: str
    path: str
    type: DeviceType
    subtype: str
    connections: List[str] = field(default_factory=list)
    enabled: bool = False

class TopologyManager:
    """Singleton Manager for CoreSight Graph Topology."""
    _instance: Optional['TopologyManager'] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TopologyManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, base_path: str = "/sys/bus/coresight/devices/") -> None:
        if self._initialized: return
        self.hw = HardwareInterface(base_path=base_path)
        self.devices: Dict[str, CoreSightDevice] = {}
        self.graph: Dict[str, List[str]] = {}
        self._initialized = True
        self.refresh_topology()

    def refresh_topology(self) -> None:
        """Performs a full scan and builds the device graph."""
        logger.hw_discovery("Starting full topology scan...")
        self.devices.clear()
        self.graph.clear()
        
        try:
            raw_names = self.hw.list_raw_devices()
            for name in raw_names:
                dev = self._classify_device(name)
                self.devices[name] = dev
                self.graph[name] = dev.connections
                
            logger.topology(f"Graph built with {len(self.devices)} nodes.")
            self._validate_graph()
        except Exception as e:
            logger.error(f"Failed to build topology: {str(e)}")

    def _classify_device(self, name: str) -> CoreSightDevice:
        """Reads sysfs metadata to classify device type and subtype."""
        type_raw = self.hw.safe_read(name, "type")
        subtype_raw = self.hw.safe_read(name, "subtype")
        
        # Mapping based on Linux Kernel CS driver definitions
        dtype = DeviceType.UNKNOWN
        if type_raw == "1": dtype = DeviceType.SOURCE
        elif type_raw == "2": dtype = DeviceType.LINK
        elif type_raw == "3": dtype = DeviceType.SINK
        
        # Connections discovery (NR_LINKS or connection directories)
        conns = []
        dev_path = os.path.join(self.hw.base_path, name)
        if os.path.exists(dev_path):
            for item in os.listdir(dev_path):
                if item.startswith("connection"):
                    # Check both nested device folder and direct device link
                    potential_links = [
                        os.path.join(dev_path, item, "device"),
                        os.path.join(dev_path, item)
                    ]
                    for plink in potential_links:
                        if os.path.islink(plink):
                            try:
                                target_name = os.path.basename(os.readlink(plink))
                                if target_name in self.hw.list_raw_devices():
                                    conns.append(target_name)
                                    break
                            except OSError:
                                continue
        
        # Check if enabled (handling different node names)
        is_enabled = False
        if dtype == DeviceType.SOURCE:
            is_enabled = (self.hw.safe_read(name, "enable_source") == "1")
        else:
            is_enabled = (self.hw.safe_read(name, "enable_sink") == "1")
        
        return CoreSightDevice(
            name=name,
            path=dev_path,
            type=dtype,
            subtype=subtype_raw,
            connections=conns,
            enabled=is_enabled
        )

    def find_path(self, source: str, sink: str) -> List[str]:
        """BFS to find the physical path between source and sink."""
        if source not in self.devices or sink not in self.devices:
            raise TopologyError(f"Invalid source ({source}) or sink ({sink})")
            
        queue = [[source]]
        visited = {source}
        
        while queue:
            path = queue.pop(0)
            node = path[-1]
            
            if node == sink:
                return path
                
            for neighbor in self.graph.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)
        
        raise TopologyError(f"No valid path found from {source} to {sink}")

    def _validate_graph(self) -> None:
        """Detects orphans and potential cycles."""
        for name, dev in self.devices.items():
            if dev.type == DeviceType.SOURCE and not dev.connections:
                logger.topology(f"WARNING: Orphan Source detected: {name}")

    def print_topology(self) -> None:
        """Renders ASCII tree of the topology."""
        print("\nCoreSight Topology Graph:")
        visited: Set[str] = set()
        for name, dev in self.devices.items():
            if dev.type == DeviceType.SOURCE:
                self._print_recursive(name, "", visited)

    def _print_recursive(self, name: str, indent: str, visited: Set[str]) -> None:
        if name in visited: 
            print(f"{indent} {name} (Cycle/Shared)")
            return
        visited.add(name)
        dev = self.devices.get(name)
        if not dev: return
        
        type_str = dev.type.name
        print(f"{indent} {name} [{type_str}:{dev.subtype}]")
        for conn in dev.connections:
            print(f"{indent}  ↓")
            self._print_recursive(conn, indent + "    ", visited)
