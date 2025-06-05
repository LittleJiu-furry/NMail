import asyncio
from typing import TYPE_CHECKING
import ssl
from ..utils.logger import createLogger

if TYPE_CHECKING:
    from .session import SMTPSession

logger = createLogger()


class SessionModel:
    def __init__(self, session: "SMTPSession"):
        self.session = session

    def setHELO_username(self, name: str):
        self.session.HELO_username = name

    async def send(self, code: int, message: str):
        """
        发送SMTP响应

        params:
            code int SMTP响应码
            message str SMTP响应消息
        """
        await self.session.send(code, message)

    async def sendLines(self, code: int, lines: list[str]):
        """
        发送SMTP响应

        params:
            code int SMTP响应码
            lines list[str] SMTP响应消息列表
        """
        await self.session.sendLines(code, lines)

    async def upgrade(self):
        """
        升级到TLS协议
        """
        # 升级协议
        logger.info(f"Client({self.session.getPeerName()}) upgrade to TLS")
        writer = self.session.writer
        secureContext = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        secureContext.load_cert_chain(
            certfile=self.session.server.certfile,
            keyfile=self.session.server.keyfile,
            password=self.session.server.password,
        )
        await writer.start_tls(secureContext)

    def getEmail(self):
        return self.session.email

    def createEmail(self):
        self.session.createEmail()

    def resetEmail(self):
        self.session.resetEmail()

    async def emit(self, event: str, *args):
        """
        触发事件

        params:
            event str 事件名称
            args tuple 事件参数
        """
        await self.session.callEmit(event, *args)

    def getPeerName(self):
        """
        获取客户端的IP地址
        return str 客户端的IP地址
        """
        return self.session.getPeerName()
