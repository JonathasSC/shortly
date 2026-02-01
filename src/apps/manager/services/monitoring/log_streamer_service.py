import asyncio
import os


class LogStreamerService:
    def __init__(self, log_path: str):
        self.log_path = log_path
        self._inode = None
        self._file = None

    async def stream(self):
        while True:
            await self._ensure_file()

            line = self._file.readline() if self._file else None
            if line:
                yield line
            else:
                await asyncio.sleep(0.3)

    async def _ensure_file(self):
        try:
            stats = os.stat(self.log_path)

            if stats.st_ino != self._inode:
                self._inode = stats.st_ino
                if self._file:
                    self._file.close()

                self._file = open(self.log_path, "r")
                self._file.seek(0, os.SEEK_END)

        except FileNotFoundError:
            await asyncio.sleep(1)
