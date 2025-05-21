import asyncio
from .session import SMTPSession
import ssl
from ..utils.logger import createLogger

logger = createLogger()

class SessionModel:
    def __init__(self, session: SMTPSession):
        self.session = session

    async def send(self, code: int, message: str):
        await self.session.send(code, message)
        
    async def upgrade(self):
        # 升级协议
        logger.info(f"Client({self.session.getPeerName()}) upgrade to TLS")
        writer = self.session.writer
        secureContext = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        secureContext.load_cert_chain(certfile=self.session.server.certfile, keyfile=self.session.server.keyfile, password=self.session.server.password)
        await writer.start_tls(secureContext)