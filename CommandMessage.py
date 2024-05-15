import json
import struct
from typing import Any

from Message import *

from typing import Optional

class CommandMessage(object):
    def __init__(
        self,
        commandName: str,
        commandType: str,
        uniqueId: bytes = b'',
        config: 'dict[str, Any]' = {},
        arguments: 'list[str]' = []
    ):
        self._commandName = commandName
        self._commandType = commandType
        self._uniqueId = uniqueId
        self._config = config
        self._arguments = arguments

    def commandName(self) -> str:
        return self._commandName
    
    def commandType(self) -> int:
        return self._commandType
        
    def uniqueId(self) -> bytes:
        return self._uniqueId
        
    def setUniqueId(self, uniqueId: bytes):
        self._uniqueId = uniqueId

    def config(self) -> str:
        return self._config
    
    def arguments(self) -> 'list[str]':
        return self._arguments

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
        uniqueId: bytes = b'',
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
    
    def uniqueId(self) -> bytes:
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
