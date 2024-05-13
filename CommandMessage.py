import json
import struct
from typing import Any

from Message import *

class CommandMessage(object):
    def __init__(
        self,
        commandName: str,
        cfg: dict[str, str] = {},
        args: list[str] = {}
    ):
        self.commandName = commandName
        self.cfg = cfg
        self.args = args

    def encodeCommand(self) -> bytes:
        commandJSON = {
            'name': self.commandName,
            'cfg': self.cfg,
            'args': self.args
        }
        return Message.encodeJSON(commandJSON)

    @staticmethod
    def fromBytes(data: bytes) -> 'CommandMessage':
        commandJSON = Message.decodeJSON(data)
        message = CommandMessage(
            commandJSON['name'],
            commandJSON['cfg'],
            commandJSON['args']
        )
        return message
    
    @staticmethod
    def encodeReply(commandId,success,failureMessage) -> bytes:
        commandJSON = {
            'name': self.commandName,
            'cfg': self.cfg,
            'args': self.args
        }
        return Message.encodeJSON(commandJSON)
    
    @staticmethod
    def decodeReply(data: bytes) -> dict[Any,Any]:
        commandJSON = {
            'name': self.commandName,
            'cfg': self.cfg,
            'args': self.args
        }
        return Message.encodeJSON(commandJSON)