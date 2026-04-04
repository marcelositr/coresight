"""
Disk Monitoring Module for CoreSight.
Responsive Edition.
"""

import psutil
import config
import utils
from i18n import labels

class Disco:
    def __init__(self):
        self.disks = []

    def update(self):
        try:
            self.disks = []
            partitions = psutil.disk_partitions()
            for partition in partitions:
                if 'loop' in partition.device or partition.fstype == '' or 'snap' in partition.mountpoint: continue
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    self.disks.append({'mount': partition.mountpoint, 'total': usage.total, 'used': usage.used, 'percent': usage.percent})
                except Exception: continue
            return self.disks
        except Exception: return []

    def format(self):
        lines = []
        bar_w = getattr(config, 'DYNAMIC_BAR_WIDTH', 30)
        lbl_w = getattr(config, 'DYNAMIC_LABEL_WIDTH', 25)
        for disk in self.disks:
            mount = disk['mount']
            if len(mount) > lbl_w: mount = "..." + mount[-(lbl_w-3):]
            bar = utils.create_progress_bar(disk['percent'], width=bar_w)
            val = f"{disk['percent']:6.2f} % ({utils.format_bytes(disk['used'])} / {utils.format_bytes(disk['total'])})"
            lines.append(f"{mount:>{lbl_w}} {bar} {val}")
        return lines
