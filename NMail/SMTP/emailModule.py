from ..utils.logger import createLogger
import asyncio
import aiodns
import re
import ipaddress
import hashlib
import hmac
import base64

logger = createLogger()

class Email:
    def __init__(self):
        self.__from = None # 这里存储SMTP会话级别的发件人地址
        self.__to: set[str] = set() # 这里存储SMTP会话级别的收件人地址
        
        self.__headers: dict[str, str] = {}
        self.__body = None

    def setFrom(self, from_address: str):
        """设置发件人地址"""
        self.__from = from_address
    
    def setToList(self, to_list: list[str]):
        """添加收件人地址列表"""
        self.__to.update(to_list)

    def setTo(self, to_address: str):
        """添加单个收件人地址"""
        self.__to.add(to_address)

    def getFrom(self):
        """获取发件人地址"""
        return self.__from

    def getToList(self):
        """获取收件人地址列表"""
        return list(self.__to)

    def setHeader(self, key: str, value: str):
        """设置邮件头"""
        self.__headers.update({key: value})
    
    def setHeaders(self, headers: dict[str, str]):
        """设置邮件头"""
        self.__headers.update(headers)
    
    def getHeaders(self):
        """获取邮件头"""
        return self.__headers
    
    def getHeader(self, key: str):
        """获取邮件头"""
        return self.__headers.get(key, None)

    def setBody(self, body: str):
        """设置邮件正文"""
        self.__body = body

    def getBody(self):
        """获取邮件正文"""
        return self.__body

    def validate(self) -> bool:
        """简单验证邮件"""
        if not self.__from:
            return False
        if not self.__to:
            return False
        bodyFrom = self.__headers.get("From", None)
        if bodyFrom:
            if bodyFrom != self.__from:
                return False # 强制要求邮件头的发件人地址与SMTP会话的地址相同
        return True
    
    def toEml(self):
        """将邮件转换为EML格式存储"""
        eml = ""
        for key, value in self.__headers.items():
            eml += f"{key}: {value}\r\n"
        eml += f"\r\n{self.__body}"
        return eml

    def setDKIM(self):
        """计算并设置DKIM签名"""
        ...

    async def DMARC(self, domain: str, ip: str):
        """
        DMARC验证
        """
        # DKIM
        dkim_result = await self.DKIM()
        # SPF
        spf_result = await self.SPF(domain, ip)
        if (dkim_result == "pass"):
            return spf_result in ("pass", "softfail")
        elif (dkim_result == "fail"):
            return False
        elif (dkim_result == "policy"):
            return spf_result in ("pass", "softfail")
        return False

    async def SPF(self, domain: str, ip: str):
        try:
            answer = await aiodns.DNSResolver().query(domain, "TXT", "IN")
        except aiodns.error.DNSError as e:
            logger.error(f"Query domain({domain}) record error: {e}")
            return "temperror"

        # 解析SPF记录
        spf_record = None
        if not spf_record:
            for record in answer:
                await asyncio.sleep(0)
                if (record.type != "TXT"):
                    continue
                if (type(record.text) == bytes):
                    continue
                if (type(record.text) == str):
                    if (record.text.startswith("v=spf1")):
                        spf_record = record.text
                        break
        if not spf_record:
            return "none"
        
        records = spf_record.split(" ")
        if(records[0] != "v=spf1"):
            return "permerror"
        matcher = re.compile(
            r'(?P<qualifier>\+|-|~|\?)?' # 修饰符，可选
            r'(?P<mechanism>[a-zA-Z0-9]*)' # 机制名
            r'(?:\:(?P<value>[^ ]+))?'
        )
        for r in records[1:]:
            await asyncio.sleep(0)
            result = matcher.match(r)
            if not result:
                return "permerror"
            qualifier = result.group("qualifier")
            mechanism = result.group("mechanism")
            value = result.group("value")
            qualifier = qualifier if qualifier else "+"
            if not mechanism:
                return "permerror"
            # all规则匹配所有
            if (mechanism == "all"):
                if (qualifier == "+"):
                    return "pass"
                elif (qualifier == "-"):
                    return "fail"
                elif (qualifier == "~"):
                    return "softfail"
                elif (qualifier == "?"):
                    return "neutral"
                continue
            # ip4或者ip6规则匹配ip
            if (mechanism == "ip4" or mechanism == "ip6"):
                if not value:
                    return "permerror"
                try:
                    network = ipaddress.ip_network(value)
                except ValueError:
                    return "permerror"
                if (ipaddress.ip_address(ip) in network):
                    # 如果IP在网络中
                    if (qualifier == "+"):
                        return "pass"
                    elif (qualifier == "-"):
                        return "fail"
                    elif (qualifier == "~"):
                        return "softfail"
                    elif (qualifier == "?"):
                        return "neutral"
                continue
            if (mechanism == "include"):
                if not value:
                    return "permerror"
                # 递归调用
                result = await self.SPF(value, ip)
                if (result == "pass"):
                    if (qualifier == "+"):
                        return "pass"
                    elif (qualifier == "-"):
                        return "fail"
                    elif (qualifier == "~"):
                        return "softfail"
                    elif (qualifier == "?"):
                        return "neutral"
                continue
            if (mechanism == "exists"):
                if not value:
                    return "permerror"
                value = value.replace("%{s}", self.__from if self.__from else "")
                value = value.replace("%{l}", self.__from.split("@")[0] if self.__from else "")
                value = value.replace("%{o}", self.__from.split("@")[1] if self.__from else "")
                value = value.replace("%{d}", domain)
                value = value.replace("%{i}", ip)
                answer = []
                try:
                    answer.append(await aiodns.DNSResolver().query(value, "A", "IN"))
                except aiodns.error.DNSError as e:...

                try:
                    answer.append(await aiodns.DNSResolver().query(value, "AAAA", "IN"))
                except aiodns.error.DNSError as e:...
                if (len(answer) > 0):
                    if (qualifier == "+"):
                        return "pass"
                    elif (qualifier == "-"):
                        return "fail"
                    elif (qualifier == "~"):
                        return "softfail"
                    elif (qualifier == "?"):
                        return "neutral"
                continue
            if(mechanism == "a" or mechanism == "mx"):
                if not value:
                    return "permerror"
                try:
                    answer = await aiodns.DNSResolver().query(value, "A", "IN")
                except aiodns.error.DNSError as e:
                    return "permerror"
                answers = [str(record) for record in answer]
                if (ip in answers):
                    if (qualifier == "+"):
                        return "pass"
                    elif (qualifier == "-"):
                        return "fail"
                    elif (qualifier == "~"):
                        return "softfail"
                    elif (qualifier == "?"):
                        return "neutral"
                continue
            return "permerror"
                
                    
    async def DKIM(self):
        """
        DKIM验证
        """
        sign = self.__headers.get("DKIM-Signature", None)
        if(sign is None):
            return "neutral"
        # 解析DKIM签名
        dkimDict = {}
        matcher = re.compile(
            r'(?P<key>[a-zA-Z0-9\-]+)=(?P<value>[^;]+)'
        )
        # 按照分号切割每个键值对
        signKVs = sign.split(";")
        # 将每个键值对的头尾空格去掉
        signKVs = [kv.strip() for kv in signKVs]
        # 将键值对解析为字典
        for kv in signKVs:
            await asyncio.sleep(0)
            result = matcher.match(kv)
            if not result:
                return "permerror"
            key = result.group("key")
            value = result.group("value")
            dkimDict.update({key: value})
        # 获取签名的域名
        sign_domain = None
        try:
            v = dkimDict["v"]
            if (v != "1"):
                return "permerror"
            method = dkimDict["a"]
            c = dkimDict["c"]
            d = dkimDict["d"]
            s = dkimDict["s"]
            sign_domain = f"{s}._domainkey.{d}"
            headers = dkimDict["h"].split(":")
            bodyHash = dkimDict["bh"]
            b = dkimDict["b"]
            bodyLength = dkimDict.get("l", None)
            if(sign_domain == None):
                return "permerror"
            answer = await aiodns.DNSResolver().query(sign_domain, "TXT", "IN")
        except KeyError:
            return "permerror"
        except aiodns.error.DNSError as e:
            logger.error(f"DKIM domain({sign_domain}) error: {e}")
            return "temperror"
        # 解析DKIM记录
        dkim_record = None
        if not dkim_record:
            for record in answer:
                await asyncio.sleep(0)
                if (record.type != "TXT"):
                    continue
                if (type(record.text) == bytes):
                    continue
                if (type(record.text) == str):
                    if (record.text.startswith("v=DKIM1")):
                        dkim_record = record.text
                        break
        if not dkim_record:
            return "fail"
        dkim_record = dkim_record.replace(" ", "")
        dkim_record = dkim_record.split(";")
        key = None
        for record in dkim_record:
            await asyncio.sleep(0)
            if (record.startswith("p=")):
                key = record[2:]
                break
        if not key:
            return "fail"
        # 计算签名
        
        # 提取需要的header
        need_headers = {}
        for header in headers:
            await asyncio.sleep(0)
            need_headers.update({header: self.__headers.get(header, None)})

        # 只针对c = relaxed/simple的邮件
        if (c != "relaxed/simple"):
            return "policy"
        
        # 处理header
        sns = ""
        for header in need_headers:
            await asyncio.sleep(0)
            sns += f"{str(header).lower()}:{need_headers[header] if need_headers[header] else ''}\r\n"
        bodyContent = self.__body if self.__body else ""
        if (bodyLength):
            sns += f"{bodyContent[:bodyLength]}\r\n"
        else:
            sns += f"{bodyContent}\r\n"
        # 计算hash
        if (method == "rsa-sha256"):
            hash = hashlib.sha256()
            hash.update(sns.encode("utf-8"))
            dkim_hash = hash.hexdigest()
        elif (method == "hmac-sha256"):
            key = key.encode("utf-8")
            sns = sns.encode("utf-8")
            hash = hmac.new(key, sns, hashlib.sha256)
            dkim_hash = hash.hexdigest()
        else:
            return "policy"
        # 比较hash
        if (dkim_hash != base64.b64decode(b).decode("utf-8")):
            return "fail"
        return "pass"
