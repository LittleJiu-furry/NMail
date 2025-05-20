import asyncio
import ssl
from typing import Optional, TypeAlias, Callable
from .event import EventManager
from .logger import createLogger
from os import PathLike

logger = createLogger()
StrOrBytesPath: TypeAlias = str | bytes | PathLike[str] | PathLike[bytes]
_PasswordType: TypeAlias = Callable[[], str | bytes | bytearray] | str | bytes | bytearray

class AsyncSocketServer(EventManager):
    def __init__(self, port: int, cretfile: StrOrBytesPath, keyfile: StrOrBytesPath, password: Optional[_PasswordType] = None):
        super().__init__()
        logger.info(f"Server set port to {port}")
        self.port = port
        self.server: Optional[asyncio.Server] = None
        self.isConnected = False
        self.__setSubscribe()
        self.useSSL = False
        # SSL证书和密钥文件
        self.cretfile = cretfile
        self.keyfile = keyfile
        self.password = password
    
    # 处理函数，这里主要用于处理链接后事件的触发
    async def __handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        # 由于要保持链接，所以这里不能使用emit方法触发事件
        # 直接调用事件处理函数
        await self.onHandle(reader, writer)
        writer.close()
        await writer.wait_closed()
        

    async def start(self):
        if self.isConnected:
            logger.warning("Server is already running")
            return
        self.server = await asyncio.start_server(
            self.__handler, "0.0.0.0", self.port,
        )
        self.isConnected = True
        # 触发事件
        self.emit("onStart")
        await self.server.serve_forever()
    
    async def startWithSSL(self):
        if self.isConnected:
            logger.warning("Server is already running")
            return
        secureContext = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        secureContext.load_cert_chain(certfile=self.cretfile, keyfile=self.keyfile, password=self.password)
        self.useSSL = True
        self.server = await asyncio.start_server(
            self.__handler, "0.0.0.0", self.port, ssl = secureContext
        )
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
    
    async def onHandle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        logger.info("Client connected")
        raise NotImplementedError("onHandle method not implemented")

    def __setSubscribe(self):
        self.subscribe("onStart", self.onStart)
        self.subscribe("onStop", self.onStop)

    # 订阅装饰器
    def subscribeDecorator(self, event_type: str):
        def decorator(func):
            self.subscribe(event_type, func)
        return decorator

    # 处理链接协议的升级
    async def upgradeProtocol(self, writer: asyncio.StreamWriter):
        if not self.isConnected or self.server is None:
            logger.warning("Server is not running")
            return
        
        if self.useSSL:
            logger.warning("SSL is already enabled")
            return
        self.useSSL = True
        # 开始升级协议
        secureContext = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        secureContext.load_cert_chain(certfile=self.cretfile, keyfile=self.keyfile, password=self.password)
        await writer.start_tls(secureContext)
        # 触发事件
        self.emit("onUpgradeProtocol", writer)




    



