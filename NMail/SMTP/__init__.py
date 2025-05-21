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
        await asyncio.gather(
            self.server465.startWithSSL(),
            self.server587.start()
        )

    async def stop(self):
        logger.info("Stopping SMTP server...")
        await self.server465.stop()
        await self.server587.stop()