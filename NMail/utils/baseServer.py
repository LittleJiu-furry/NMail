import asyncio
from typing import Optional
from .event import EventManager
from .logger import createLogger

logger = createLogger()

class AsyncSocketServer(EventManager):
    def __init__(self, port: int):
        super().__init__()
        logger.info(f"Server set port to {port}")
        self.port = port
        self.server: Optional[asyncio.Server] = None
        self.isConnected = False
        self.__setSubscribe()
    
    # 处理函数，这里主要用于处理链接后事件的触发
    async def __handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        # 触发事件
        self.emit("onHandle", reader, writer)

    async def start(self):
        self.server = await asyncio.start_server(self.__handler, "0.0.0.0", self.port)
        self.isConnected = True
        # 触发事件
        self.emit("onStart")
        await self.server.serve_forever()
    
    async def stop(self):
        if(self.server and self.isConnected):
            self.isConnected = False
            self.emit("onStop")
            self.server.close()
            await self.server.wait_closed()
            self.clear()
    
    async def onStart(self):
        logger.info("Server started")
        raise NotImplementedError("onStart method not implemented")

    async def onStop(self):
        logger.info("Server stopped")
        raise NotImplementedError("onStop method not implemented")
        

    def __setSubscribe(self):
        self.subscribe("onStart", self.onStart)
        self.subscribe("onStop", self.onStop)

    # 订阅装饰器
    def subscribeDecorator(self, event_type: str):
        def decorator(func):
            self.subscribe(event_type, func)
        return decorator
    



