import json
import struct
import os
import platform
from typing import Any

from Message import *
from DataMessage import *

from typing import Optional


class CommandMessage(object):
    idDict = {}

    def __init__(
        self,
        commandName: str,
        commandType: str,
        uniqueId: Optional[int] = None,
        config: 'dict[str, Any]' = {},
        arguments: 'list[str]' = []
    ):
        self._commandName = commandName
        self._commandType = commandType
        self._uniqueId = self._createUniqueId() if uniqueId is None else uniqueId
        self._config = config
        self._arguments = arguments

    def _createUniqueId(self):
        offset = 100000
        k = self._commandName+":"+self._commandType
        if k in CommandMessage.idDict.keys():
            CommandMessage.idDict[k] +=offset*offset
        else:
            CommandMessage.idDict[k] = os.getpid()%offset+(hash(platform.node())%offset)*offset
        return CommandMessage.idDict[k]
    
    def getChannelName(self) -> bytes:
        return self._commandName+":"+self._commandType+":"+str(self._uniqueId)

    def commandName(self) -> str:
        return self._commandName
    
    def commandType(self) -> int:
        return self._commandType
        
    def uniqueId(self) -> int:
        return self._uniqueId

    def config(self) -> str:
        return self._config
    
    def arguments(self) -> 'list[str]':
        return self._arguments
    
    def createReply(self, success: bool, payload: 'dict[str,Any]' = {}) -> 'CommandReply':
        return CommandReply(
            commandName = self._commandName,
            commandType = self._commandType,
            success = success,
            uniqueId = self._uniqueId,
            payload = payload
        )

    def __str__(self):
        return f"CommandMessage(commandName={self._commandName}, commandType={self._commandType}, uniqueId={self._uniqueId}, config={self._config}, arguments={self._arguments})"

    def encode(self) -> bytes:
        commandJSON = {
            'name': self._commandName,
            'type': self._commandType,
            'id': self._uniqueId,
            'cfg': self._config,
            'args': self._arguments
        }
        return Message.encodeJSON(commandJSON)

    @staticmethod
    def fromBytes(data: bytes) -> 'CommandMessage':
        commandJSON = Message.decodeJSON(data)
        message = CommandMessage(
            commandName = commandJSON['name'],
            commandType = commandJSON['type'],
            uniqueId = commandJSON['id'],
            config = commandJSON['cfg'],
            arguments = commandJSON['args']
        )
        return message
        
    

class CommandReply(object):
    def __init__(
        self,
        commandName: str,
        commandType: str,
        success: bool,
        uniqueId: int = -1,
        payload: 'dict[str, Any]' = {}
    ):
        self._commandName = commandName
        self._commandType = commandType
        self._uniqueId = uniqueId
        self._success = success
        self._payload = payload

    def commandName(self) -> str:
        return self._commandName
    
    def commandType(self) -> str:
        return self._commandType
    
    def uniqueId(self) -> str:
        return self._uniqueId
    
    def success(self) -> bool:
        return self._success
    
    def payload(self) -> 'dict[str, Any]':
        return self._payload

    def encode(self) -> bytes:
        replyJSON = {
            'name': self._commandName,
            'type': self._commandType,
            'id': self._uniqueId,
            'success': self._success,
            'payload' : self._payload
        }
        return Message.encodeJSON(replyJSON)
    
    def __str__(self):
        return f"CommandReply(commandName={self._commandName}, commandType={self._commandType}, uniqueId={self._uniqueId}, success={self._success}, payload={self._payload})"


    @staticmethod
    def fromBytes(data: bytes) -> 'CommandReply':
        replyJSON = Message.decodeJSON(data)
        message = CommandReply(
            commandName = replyJSON['name'],
            commandType = replyJSON['type'],
            uniqueId = replyJSON['id'],
            success = replyJSON['success'],
            payload = replyJSON['payload']
        )
        return message
