import asyncio
import os

from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings


class LogsConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated or not user.is_staff:
            await self.close()
            return

        await self.accept()
        self.log_path = settings.APP_LOG_FILE_PATH
        self.task = asyncio.create_task(self.stream_logs())

    async def disconnect(self, close_code):
        if hasattr(self, "task"):
            self.task.cancel()

    async def stream_logs(self):
        last_inode = None

        while True:
            try:
                stat = os.stat(self.log_path)
                if stat.st_ino != last_inode:
                    last_inode = stat.st_ino
                    f = open(self.log_path, "r")
                    f.seek(0, os.SEEK_END)

                line = f.readline()
                if not line:
                    await asyncio.sleep(0.3)
                    continue

                await self.send(text_data=line)

            except FileNotFoundError:
                await asyncio.sleep(1)
            except Exception:
                await asyncio.sleep(1)
