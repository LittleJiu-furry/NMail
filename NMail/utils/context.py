from .common import Singleton

class AppContext(Singleton):
    def __init__(self):
        self._context = {}

    def set(self, key: str, value):
        self._context[key] = value

    def get(self, key: str):
        return self._context.get(key, None)

    def remove(self, key: str):
        if key in self._context:
            del self._context[key]

    def clear(self):
        self._context.clear()
    
    def has(self, key: str) -> bool:
        return key in self._context

    def __contains__(self, key: str) -> bool:
        return self.has(key)
    def __getitem__(self, key: str):
        return self.get(key)
    def __setitem__(self, key: str, value):
        self.set(key, value)
    def __delitem__(self, key: str):
        self.remove(key)
    def __iter__(self):
        return iter(self._context)
    def __len__(self):
        return len(self._context)
    def __repr__(self):
        return f"AppContext({self._context})"
    def __str__(self):
        return f"AppContext({self._context})"
    