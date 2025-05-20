from ..utils.common import Singleton
from ..utils.event import EventManager

class SessionEventManager(EventManager, Singleton):
    def subscribeDecorator(self, event_type: str):
        def wrapper(func):
            self.subscribe(event_type, func)
            return func
        return wrapper