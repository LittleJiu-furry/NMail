import loguru
import sys
from .context import AppContext

def createLogger():
    ctx = AppContext()
    logger = loguru.logger
    if(ctx.has("logger_setted") and ctx.get("logger_setted")):
        return logger
    logger.remove()  # Remove the default logger
    logger.add(
        sys.stdout, 
        level="INFO", 
        format="[<cyan>{time:YYYY-MM-DD HH:mm:ss.SSS}</cyan>] [<bold><level>{level: ^8}</level></bold>] [{name}] <level>{message}</level>", 
        colorize=True
    )
    ctx.set("logger_setted", True)
    return logger

def loggerCatch(func):
    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except Exception as e:
            createLogger().error(f"Error occurred while executing function {func.__name__}: {e}")
    return wrapper
