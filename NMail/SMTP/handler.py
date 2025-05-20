import asyncio
from ..utils.logger import createLogger
from .event import SessionEventManager
from typing import Optional
from . import type
from ..utils.context import AppContext
from .sessionModel import SessionModel

logger = createLogger()
sessionEvent = SessionEventManager()
ctx = AppContext()

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
    
    
