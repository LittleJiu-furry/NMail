from .baseServer import baseSMTPService
from . import handler

class SMTPServer:
    def __init__(self):
        self.sessionEvent = handler.getSessionEventManager()
        self.server465 = baseSMTPService(self.sessionEvent, 465, "", "")
        self.server587 = baseSMTPService(self.sessionEvent, 587, "", "")