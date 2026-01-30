import time

import psutil


class ResourceService:

    @staticmethod
    def get_disk_free_percent() -> float:
        disk = psutil.disk_usage("/")
        return disk.free * 100 / disk.total

    @staticmethod
    def get_memory_percent() -> float:
        return psutil.virtual_memory().percent

    @staticmethod
    def get_uptime_hours() -> float:
        boot_time = psutil.boot_time()
        return round((time.time() - boot_time) / 3600, 1)
