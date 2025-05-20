from enum import StrEnum

class SMTPCommand(StrEnum):
    HELO = "HELO" # 问候命令
    EHLO = "EHLO" # 扩展问候命令
    MAIL = "MAIL" # 邮件发送命令
    RCPT = "RCPT" # 邮件接收命令
    DATA = "DATA" # 邮件数据命令, 特殊指令
    RSET = "RSET" # 重置命令
    VRFY = "VRFY" # 验证命令, 暂时不用管
    EXPN = "EXPN" # 扩展命令, 暂时不用管
    HELP = "HELP" # 帮助命令, 暂时不用管
    NOOP = "NOOP" # 无操作命令
    QUIT = "QUIT" # 退出命令, 无需处理
    AUTH = "AUTH" # 身份验证命令， 特殊指令
    STARTTLS = "STARTTLS" # 启动TLS命令
    
    SIZE = "SIZE" # 邮件大小限制命令
    DSN = "DSN" # 交付状态通知命令
    ETRN = "ETRN" # 电子邮件传输命令
    PIPELINING = "PIPELINING" # 管道命令
    Eight_BITMIME = "8BITMIME" # 8位MIME命令
    BINARYMIME = "BINARYMIME" # 二进制MIME命令
    CHUNKING = "CHUNKING" # 分块命令
    DELIVERBY = "DELIVERBY" # 交付时间限制命令
    ENHANCEDSTATUSCODES = "ENHANCEDSTATUSCODES" # 扩展状态码命令
    SMTPUTF8 = "SMTPUTF8" # SMTPUTF8命令

class ExtenedSMTPCommand(StrEnum):
    SERVER_GET_MAIL_STATUS = "SERVER_GET_MAIL_STATUS" # 获取指定邮件的状态指令
    SERVER_GET_MAIL_SEND_LIST = "SERVER_GET_MAIL_SEND_LIST" # 获取待投递的邮件列表指令
    SERVER_ADD_BLACK_LIST = "SERVER_ADD_BLACK_LIST" # 添加黑名单指令
    SERVER_DEL_BLACK_LIST = "SERVER_DEL_BLACK_LIST" # 删除黑名单指令
    SERVER_GET_BLACK_LIST = "SERVER_GET_BLACK_LIST" # 获取黑名单指令
    SERVER_VERSION = "SERVER_VERSION" # 获取服务器版本指令
