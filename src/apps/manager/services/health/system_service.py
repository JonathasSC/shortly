from .database_service import DatabaseService
from .resource_service import ResourceService


class SystemStatusService:

    @staticmethod
    def get_status() -> dict:
        return {
            "database": DatabaseService.get_status(),
            "disk_free_percent": ResourceService.get_disk_free_percent(),
            "memory_percent": ResourceService.get_memory_percent(),
            "uptime_hours": ResourceService.get_uptime_hours(),
        }
