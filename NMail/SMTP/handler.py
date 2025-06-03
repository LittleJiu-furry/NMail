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


# 日志级别
# verbor 详细日志
# debug debug日志
# info 普通级别日志
# warning 警告级别日志
# error 错误级别日志
# fatal 致命错误级别日志

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
    send_str = [""]
    await session.sendLines(250, send_str)
    # TODO: 嘿，有谁完善一下这个发送的内容吗？


@sessionEvent.subscribeDecorator(f"on{type.SMTPCommand.MAIL}")
async def handleMAIL(session: SessionModel, MAIL_command: str, mail_address: str):
    logger.debug(f"MAIL {MAIL_command} {mail_address}")
    logger.info(f"Client({session.getPeerName()}) set mail from")
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
    logger.debug(f"RCPT {RCPT_command} {mail_address}")
    logger.info(f"Client({session.getPeerName()}) set rept to")
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
    logger.info(f"Client({session.getPeerName()}) set email data")
    _email = session.getEmail()
    if _email is None:
        await session.send(550, "Currently not accepting this instruction")
        logger.critical(
            f"Client({session.getPeerName()}) called data comand but get empty email object"
        )
        return
    text = introduced_text[: (len(introduced_text) - 4)]
    msg = Parser().parsestr(text)
    mail = {"From": msg["From"], "To": msg["To"], "Subject": msg["Subject"]}
    _email.setHeaders(mail)
    # TODO: 解析邮件
    # _email.setBody()
    await session.emit("_inspect")


@sessionEvent.subscribeDecorator("_inspect")
async def isInspect(session: SessionModel, introduced_text: str): ...


@sessionEvent.subscribeDecorator(f"on{type.SMTPCommand.RSET}")
async def handleRSET(session: SessionModel):
    logger.info(f"RSET")
    session.resetEmail()
    await session.send(250, "OK")


@sessionEvent.subscribeDecorator(f"on{type.SMTPCommand.NOOP}")
async def handleNOOP(session: SessionModel):
    # logger.info(f"NOOP")
    await session.send(250, "OK")


@sessionEvent.subscribeDecorator(f"on{type.SMTPCommand.STARTTLS}")
async def handleSTARTTLS(session: SessionModel):
    # 首先判断服务器是否支持这个指令
    # 其次在判断客户的连接是否已经升级过，避免重复指令
    # 最后再对客户端连接升级
    # await session.upgrade()
    # session.session.server.port 服务器端口
    # session.session.server.useSSL 是否已经升级过
    # TODO: 服务器是否支持当前指令
    if session.session.server.useSSL:
        await session.send(508, "Already in TLS mode")
        return
    if session.session.isUpgreaded:
        await session.send(508, "Already in TLS mode")
        return
    await session.upgrade()
    await session.send(220, "Ready to start TLS")
    return
