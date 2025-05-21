from .common import Singleton
from typing import Callable, Dict, List, Union, Awaitable
import asyncio
from .logger import loggerCatch

Callback = Union[Callable[..., Awaitable[None]], Callable[..., None]]  # 回调函数类型
EventListeners = Dict[str, List[Callback]]

# 一个简单事件管理器
class EventManager:
    def __init__(self):
        self._listeners: EventListeners = {}

    def subscribe(self, event_type: str, callback: Callback):
        if not self._listeners.get(event_type, None):
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callback):
        if event_type in self._listeners:
            self._listeners[event_type].remove(callback)

    def emit(self, event_type: str, *args, **kwargs):
        if not self._listeners.get(event_type, None):
            return
        for callback in self._listeners[event_type]:
            if asyncio.iscoroutinefunction(callback):
                asyncio.create_task(self.__createWrapper(callback)(*args, **kwargs)) # type: ignore
            else:
                asyncio.get_event_loop().run_in_executor(None, self.__createWrapper(callback), *args, **kwargs)
    
    def __createWrapper(self, func: Callback):
        
        @loggerCatch
        async def wrapperAsync(*args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                await func(*args, **kwargs)

        @loggerCatch
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return wrapperAsync
        else:
            return wrapper
      
        
    def clear(self):
        self._listeners.clear()

    