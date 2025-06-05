import asyncio
import re
from ..utils.logger import createLogger
from .event import SessionEventManager
from typing import Optional, TYPE_CHECKING
from .type import SMTPCommand, ExtenedSMTPCommand
from .sessionModel import SessionModel
from .emailModule import Email

if TYPE_CHECKING:
    from .baseServer import baseSMTPService


logger = createLogger()


class SMTPSession:
    def __init__(
        self,
        server: "baseSMTPService",
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        self.reader = reader
        self.writer = writer
        self.server = server
        self.inDataMode = False  # 是否处于数据模式
        self.requireClose = False
        self.email = None
        self.isUpgreaded = False
        self.HELO_username = ""

    async def send(self, code: int, message: str):
        """
        发送SMTP响应
        :param code: SMTP响应码
        :param message: SMTP响应消息
        """
        self.writer.write(f"{code} {message}\r\n".encode())
        await self.writer.drain()

    async def sendLines(self, code: int, lines: list[str]):
        """
        发送SMTP响应
        :param code: SMTP响应码
        :param lines: SMTP响应消息列表
        """
        if len(lines) == 0:
            return
        if len(lines) >= 2:
            for line in lines[:-1]:
                self.writer.write(f"{code}-{line}\r\n".encode())
        self.writer.write(f"{code} {lines[-1]}\r\n".encode())
        await self.writer.drain()

    async def sayHello(self):
        await self.send(220, "Welcome to NMail SMTP server")

    def getPeerName(self) -> str:
        """
        获取客户端的IP地址
        :return: 客户端的IP地址
        """
        return self.writer.get_extra_info("peername")[0]

    def parser(self, data: str) -> tuple[Optional[str], Optional[tuple[str, ...]]]:
        matcher = re.compile(r"(?P<command>[A-Za-z]+)(?:\s(?P<args>.*))?")
        result = matcher.match(data)
        if not result:
            return None, None
        command = result.group("command").upper()
        args = result.group("args")
        args_list = []
        if args and " " in args:
            args_list = args.split(" ")
        return command, tuple(args_list)

    async def __GetData(self):
        while not self.requireClose:
            await asyncio.sleep(0)
            if self.inDataMode:
                data = await self.reader.readuntil(b"\r\n.\r\n")
                yield data.decode()
                continue
            data = await self.reader.readline()
            if not data:
                break
            data = data.decode().strip()
            yield data
        yield None

    async def callEmit(self, event_type: str, *args, **kwargs):
        # 是否有对应的事件处理函数
        if not self.server.sessionEvent.hasEvent(event_type):
            logger.warning(
                f"Client({self.getPeerName()}) send invalid command: {event_type}"
            )
            await self.send(500, "Invalid command")
            return
        sessionModule = SessionModel(self)
        self.server.sessionEvent.emit(event_type, sessionModule, *args, **kwargs)

    async def service(self):
        async for data in self.__GetData():
            await asyncio.sleep(0)
            if data is None:
                logger.warning(
                    f"Client({self.getPeerName()}) session get none data, closing session"
                )
                self.requireClose = True
                break
            if self.inDataMode:
                # 数据模式下
                self.inDataMode = False
                await self.callEmit(f"on{SMTPCommand.DATA}", data)
                continue
            # 解析数据
            command, args = self.parser(data)
            if command is None and args is None:
                if data == "":
                    # 用户输入空行
                    # 不建议处理，忽略
                    continue
            if command == SMTPCommand.QUIT:
                self.requireClose = True
                await self.send(221, "Bye")
                break
            if command == SMTPCommand.DATA:
                # TODO: 校验指令执行序

                # 进入数据模式
                self.inDataMode = True
                await self.send(354, "End data with <CR><LF>.<CR><LF>")
                continue
            if command == SMTPCommand.HELO:
                # 处理HELO命令
                if args is None:
                    logger.warning(
                        f"Client({self.getPeerName()}) send invalid HELO command: {data}"
                    )
                    await self.send(500, "Invalid HELO command")
                    continue
                await self.callEmit(f"on{SMTPCommand.HELO}", *args)
                continue
            if command == SMTPCommand.EHLO:
                # 处理EHLO命令
                if args is None:
                    logger.warning(
                        f"Client({self.getPeerName()}) send invalid EHLO command: {data}"
                    )
                    await self.send(500, "Invalid EHLO command")
                    continue
                await self.callEmit(f"on{SMTPCommand.EHLO}", *args)
                continue
            if command == SMTPCommand.MAIL:
                # 处理MAIL命令
                if args is None:
                    logger.warning(
                        f"Client({self.getPeerName()}) send invalid MAIL command: {data}"
                    )
                    await self.send(500, "Invalid MAIL command")
                    continue
                await self.callEmit(f"on{SMTPCommand.MAIL}", *args)
                continue
            if command == SMTPCommand.RCPT:
                # 处理RCPT命令
                if args is None:
                    logger.warning(
                        f"Client({self.getPeerName()}) send invalid RCPT command: {data}"
                    )
                    await self.send(500, "Invalid RCPT command")
                    continue
                await self.callEmit(f"on{SMTPCommand.RCPT}", *args)
                continue
            if command == SMTPCommand.RSET:
                # 处理RSET命令
                await self.callEmit(f"on{SMTPCommand.RSET}")
                continue
            if command == SMTPCommand.VRFY:
                # 处理VRFY命令
                if args is None:
                    logger.warning(
                        f"Client({self.getPeerName()}) send invalid VRFY command: {data}"
                    )
                    await self.send(500, "Invalid VRFY command")
                    continue
                await self.callEmit(f"on{SMTPCommand.VRFY}", *args)
                continue
            if command == SMTPCommand.EXPN:
                # 处理EXPN命令
                if args is None:
                    logger.warning(
                        f"Client({self.getPeerName()}) send invalid EXPN command: {data}"
                    )
                    await self.send(500, "Invalid EXPN command")
                    continue
                await self.callEmit(f"on{SMTPCommand.EXPN}", *args)
                continue
            if command == SMTPCommand.HELP:
                # 处理HELP命令
                if args is None:
                    logger.warning(
                        f"Client({self.getPeerName()}) send invalid HELP command: {data}"
                    )
                    await self.send(500, "Invalid HELP command")
                    continue
                await self.callEmit(f"on{SMTPCommand.HELP}", *args)
                continue
            if command == SMTPCommand.NOOP:
                # 处理NOOP命令
                await self.callEmit(f"on{SMTPCommand.NOOP}")
                continue
            if command == SMTPCommand.AUTH:
                # TODO: 处理AUTH命令
                continue
            if command == SMTPCommand.STARTTLS:
                await self.callEmit(f"on{SMTPCommand.STARTTLS}")
                continue
            if command == SMTPCommand.ETRN:
                # 处理ETRN命令
                if args is None:
                    logger.warning(
                        f"Client({self.getPeerName()}) send invalid ETRN command: {data}"
                    )
                    await self.send(500, "Invalid ETRN command")
                    continue
                await self.callEmit(f"on{SMTPCommand.ETRN}", *args)
                continue
            if command == SMTPCommand.BDAT:
                # 处理BDAT命令
                if args is None:
                    logger.warning(
                        f"Client({self.getPeerName()}) send invalid BDAT command: {data}"
                    )
                    await self.send(500, "Invalid BDAT command")
                    continue
                await self.callEmit(f"on{SMTPCommand.BDAT}", *args)
                continue
            await self.send(500, "Invalid command")

    def createEmail(self):
        """
        创建邮件对象
        :return: 邮件对象
        """
        self.email = Email()
        return self.email

    def resetEmail(self):
        self.email = None
