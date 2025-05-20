import asyncio
import re
from ..utils.logger import createLogger
from .event import SessionEventManager
from typing import Optional

logger = createLogger()
sessionEvent = SessionEventManager()

class SMTPSession:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.inDataMode = False # 是否处于数据模式
        self.requireClose = False
    
    async def send(self, code: int, message: str):
        """
        发送SMTP响应
        :param code: SMTP响应码
        :param message: SMTP响应消息
        """
        self.writer.write(f"{code} {message}\r\n".encode())
        await self.writer.drain()

    async def sayHello(self):
        await self.send(220, "Welcome to NMail SMTP server")
    

    async def parser(self, data: str) -> tuple[Optional[str], tuple[str, ...]]:
        matcher = re.compile(r"(?P<command>[A-Za-z]+)(?:\s(?P<args>.*))?")
        result = matcher.match(data)
        if not result:
            return None, ("",)
        command = result.group("command")
        args = result.group("args")
        args_list = []
        if (args and " " in args):
            args_list = args.split(" ")
        return command, tuple(args_list)

    async def __GetData(self):
        while not self.requireClose:
            yield await self.reader.readline()


    async def service(self):
        async for data in self.__GetData():
            ...


