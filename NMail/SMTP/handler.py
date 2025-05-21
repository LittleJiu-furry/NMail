import asyncio
import re
from ..utils.logger import createLogger
from .event import SessionEventManager
from typing import Optional
from . import type
from ..utils.context import AppContext
from .sessionModel import SessionModel
import email
from email.parser import Parser
from .emailModule import Email

logger = createLogger()
sessionEvent = SessionEventManager()
ctx = AppContext()


def getSessionEventManager():
    return sessionEvent


# 以下是参考代码
# sessionEvent.subscribeDecorator() 的参数是字符串
# 要求写成onEVENT，EVENT是你要处理的 SMTP 指令
# 指令可以参考types.py中的两个枚举
# EVENT要参考的是枚举的具体值，而不是枚举的变量
# 当然可以用模板字符串直接拼接
# 拼接方法是func(f"on{type.SMTPCommand.AUTH}") <-- 参考
# @sessionEvent.subscribeDecorator("onEVENT")
# async def handleEvent(session):
#     ...

# @sessionEvent.subscribeDecorator("")
# def syncFunction(session):
#     ...


@sessionEvent.subscribeDecorator(f"on{type.SMTPCommand.HELO}")
async def handleHELO(session: SessionModel, client_domain: str):
    logger.info(f"Client({client_domain}) Hello")
    await session.send(250, f"{ctx.get("server_domain")}")


@sessionEvent.subscribeDecorator(f"on{type.SMTPCommand.EHLO}")
async def handleEHLO(session: SessionModel, client_domain: str):
    logger.info(f"Client({client_domain}) Extened Hello")
    # TODO: 发送多行


@sessionEvent.subscribeDecorator(f"on{type.SMTPCommand.MAIL}")
async def handleMAIL(session: SessionModel, MAIL_command: str, mail_address: str):
    logger.info(f"MAIL {MAIL_command} {mail_address}")
    counter = False
    session.createEmail()
    address = ""
    for i in mail_address:
        if counter == False and i != "<":
            continue
        counter = True
        if i != ">":
            address += i
        else:
            break
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.match(pattern, address):
        logger.warning(f"Invalid email address format: {address}")
        await session.send(550, "Invalid email address format")
        return
    await session.send(250, "OK")
    # TODO 这是一个标记，这里还没做完！
    session.getEmail().setFrom(address)  # type: ignore


@sessionEvent.subscribeDecorator(f"on{type.SMTPCommand.RCPT}")
async def handleRCPT(session: SessionModel, RCPT_command: str, mail_address: str):
    logger.info(f"RCPT {RCPT_command} {mail_address}")
    if session.getEmail() is None:
        await session.send(550, "Currently not accepting this instruction")
        return
    counter = False
    address = ""
    for i in mail_address:
        if counter == False and i != "<":
            continue
        counter = True
        if i != ">":
            address += i
        else:
            break
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.match(pattern, address):
        logger.warning(f"Invalid email address format: {address}")
        await session.send(550, "Invalid email address format")
        return
    session.getEmail().setTo(address)  # type: ignore
    await session.send(250, "OK")


@sessionEvent.subscribeDecorator(f"on{type.SMTPCommand.DATA}")
async def handleDATA(session: SessionModel, introduced_text: str):
    logger.info(f"DATA \n {introduced_text}")
    if session.getEmail() is None:
        await session.send(550, "Currently not accepting this instruction")
        return
    text = introduced_text[: (len(introduced_text) - 4)]
    msg = Parser().parsestr(text)
    mail = {"From": msg["From"], "To": msg["To"], "Subject": msg["Subject"]}
    session.getEmail().setHeaders(mail)  # type: ignore
    for part in msg.walk():
        if part.get_content_type() == "text/plain":

            session.getEmail().setBody(part.get_payload(decode=True).decode())
            break
    await session.emit("_inspect")


@sessionEvent.subscribeDecorator("_inspect")
async def isInspect(session: SessionModel, introduced_text: str): ...


@sessionEvent.subscribeDecorator(f"on{type.SMTPCommand.RSET}")
async def handleRSET(session: SessionModel):
    logger.info(f"RSTE")
    # await session.send(250, "OK")


@sessionEvent.subscribeDecorator(f"on{type.SMTPCommand.NOOP}")
async def handleNOOP(session: SessionModel):
    logger.info(f"NOOP")
    # await session.send(250, "OK")
