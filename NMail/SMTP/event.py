from ..utils.event import EventManager

class SessionEventManager(EventManager):
    def subscribeDecorator(self, event_type: str):
        def wrapper(func):
            self.subscribe(event_type, func)
            return func
        return wrapper

    def getListeners(self):
        return self._listeners

    def hasEvent(self, event_type: str):
        return event_type in self._listeners