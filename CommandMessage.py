import json
import struct
from typing import Any

from Message import *

class CommandMessage(object):
    def __init__(
        self,
        commandName: str,
        commandType: str = 'spawn',
        config: 'dict[str, Any]' = {},
        arguments: 'list[str]' = {}
    ):
        self._commandName = commandName
        self._commandType = commandType
        self._config = config
        self._arguments = arguments

    def commandName(self) -> str:
        return self._commandName
    
    def commandType(self) -> int:
        return self._commandType
    
    def config(self) -> str:
        return self._config
    
    def arguments(self) -> 'list[str]':
        return self._arguments

    def encode(self) -> bytes:
        commandJSON = {
            'name': self._commandName,
            'type': self._commandType,
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
            config = commandJSON['cfg'],
            arguments = commandJSON['args']
        )
        return message
    

class CommandReply(object):
    def __init__(
        self,
        commandName: str,
        commandType: str,
        requestId: int,
        success: bool,
        payload: 'dict[str, Any]' = {}
    ):
        self._commandName = commandName
        self._commandType = commandType
        self._requestId = requestId
        self._success = success
        self._payload = payload

    def commandName(self) -> str:
        return self._commandName
    
    def commandType(self) -> str:
        return self._commandType
    
    def requestId(self) -> int:
        return self._requestId
    
    def success(self) -> bool:
        return self._success
    
    def payload(self) -> 'dict[str, Any]':
        return self._payload

    def encode(self) -> bytes:
        replyJSON = {
            'name': self._commandName,
            'type': self._commandType,
            'id': self._requestId,
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
            requestId = replyJSON['id'],
            success = replyJSON['success'],
            payload = replyJSON['payload']
        )
        return message