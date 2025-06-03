from .baseServer import baseSMTPService
from . import handler
import asyncio
from ..utils.logger import createLogger

logger = createLogger()


class SMTPServer:
    def __init__(self):
        self.sessionEvent = handler.getSessionEventManager()
        self.server465 = baseSMTPService(self.sessionEvent, 465, "", "")
        self.server587 = baseSMTPService(self.sessionEvent, 587, "", "")

    async def start(self):
        logger.info("Starting SMTP server...")
        tasks = [
            # asyncio.create_task(self.server465.startWithSSL(), name="SMTPServer465"),
            asyncio.create_task(self.server465.start(), name="SMTPServer465"),
            asyncio.create_task(self.server587.start(), name="SMTPServer587"),
        ]
        for task in tasks:
            try:
                await task
            except Exception as e:
                logger.error(f"Error when starting {task.get_name()}: {e}")

    async def stop(self):
        logger.info("Stopping SMTP server...")
        await self.server465.stop()
        await self.server587.stop()
