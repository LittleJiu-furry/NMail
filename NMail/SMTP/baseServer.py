from asyncio import StreamReader, StreamWriter
from ..utils.baseServer import AsyncSocketServer
from typing import Callable
from os import PathLike
from ..utils.logger import createLogger
from .session import SMTPSession
from .event import SessionEventManager

StrOrBytesPath = str | bytes | PathLike[str] | PathLike[bytes]
_PasswordType = Callable[[], str | bytes | bytearray] | str | bytes | bytearray | None

logger = createLogger()

class baseSMTPService(AsyncSocketServer):
    def __init__(self, sessionEvent: SessionEventManager, port: int, certfile: StrOrBytesPath, keyfile: StrOrBytesPath, password: _PasswordType = None):
        super().__init__(port, certfile, keyfile, password)
        self.sessionEvent = sessionEvent

    async def onStart(self):
        logger.info(f"SMTP server started on port {self.port}")

    async def onStop(self):
        logger.info(f"SMTP server stopped on port {self.port}")

    async def onHandle(self, reader: StreamReader, writer: StreamWriter):
        logger.info(f"SMTP server handling connection from {writer.get_extra_info('peername')}")
        connection = SMTPSession(self, reader, writer)
        await connection.sayHello()
        await connection.service()
