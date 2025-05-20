import asyncio
from .event import SessionEventManager

sessionEvent = SessionEventManager()
class SessionModel:
    def __init__(self):...

    async def send(self, code: int, message: str):
        sessionEvent.emit("_send", code, message)
        
    def sendSync(self, code: int, message: str):
        sessionEvent.emit("_send", code, message)
    