import asyncio

from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

from apps.manager.services.monitoring.log_sanitizer_service import LogSanitizerService
from apps.manager.services.monitoring.log_streamer_service import LogStreamerService


class LogsConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]

        if not user.is_authenticated or not user.is_staff:
            await self.close()
            return

        await self.accept()
        self.log_path = settings.APP_LOG_FILE_PATH
        self.sanitizer = LogSanitizerService()
        self.log_streamer = LogStreamerService(self.log_path)
        self.task = asyncio.create_task(self.stream_logs())

    async def disconnect(self, close_code):
        if hasattr(self, "task"):
            self.task.cancel()

    async def stream_logs(self):
        async for line in self.log_streamer.stream():
            sanitized_line = self.sanitizer.sanitize(line)
            await self.send(text_data=sanitized_line)
