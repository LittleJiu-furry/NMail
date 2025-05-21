import asyncio
from ..utils.logger import createLogger
from .event import SessionEventManager
from typing import Optional
from . import type
from ..utils.context import AppContext
from .sessionModel import SessionModel
import email
from email.parser import Parser

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
    address = ""
    for i in mail_address:
        if counter == False and i != "<":
            continue
        counter = True
        if i != ">":
            address += i
        else:
            break
        # TODO 记得储存这个地址喵


@sessionEvent.subscribeDecorator(f"on{type.SMTPCommand.RCPT}")
async def handleRCPT(session: SessionModel, RCPT_command: str, mail_address: str):
    logger.info(f"RCPT {RCPT_command} {mail_address}")
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
        # TODO 记得储存这个地址喵


@sessionEvent.subscribeDecorator(f"on{type.SMTPCommand.DATA}")
async def handleDATA(session: SessionModel, introduced_text: str):
    logger.info(f"DATA \n {introduced_text}")
    text = introduced_text[: (len(introduced_text) - 4)]
    msg = Parser().parsestr(text)
    mail_from = msg["From"]
    mail_to = msg["To"]
    mail_subject = msg["Subject"]
    mail_body = ""
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            mail_body = part.get_payload(decode=True).decode()
            break


@sessionEvent.subscribeDecorator(f"on{type.SMTPCommand.RSET}")
async def handleRSET(session: SessionModel):
    logger.info(f"RSTE")
    # await session.send(250, "OK")


@sessionEvent.subscribeDecorator(f"on{type.SMTPCommand.NOOP}")
async def handleNOOP(session: SessionModel):
    logger.info(f"NOOP")
    # await session.send(250, "OK")
