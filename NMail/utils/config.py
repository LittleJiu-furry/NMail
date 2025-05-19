import yaml
from dataclasses import dataclass
from typing import TypeAlias, Optional, Callable
from os import PathLike
from .common import Singleton
import dacite
from .context import AppContext

_PasswordType: TypeAlias = Callable[[], str | bytes | bytearray] | str | bytes | bytearray
StrOrBytesPath: TypeAlias = str | bytes | PathLike[str] | PathLike[bytes]

@dataclass
class ConfigSMTP:
    cert: StrOrBytesPath
    key: StrOrBytesPath
    password: Optional[_PasswordType] = None


@dataclass
class Config:
    smtp: ConfigSMTP

class ConfigManager(Singleton):
    def __init__(self, configPath: str):
        super().__init__()
        self.configPath = configPath
    
    def load(self) -> Config:
        with open(self.configPath, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        context = AppContext()
        result = dacite.from_dict(Config, config)
        context.set("config", result)
        return result
        
