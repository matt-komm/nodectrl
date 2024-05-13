import json
import struct
from typing import Any

class CommandMessage(object):
    def __init__(
        self,
        commandName: str,
        cfg: dict[Any, Any] = {}
    ): 
        self.commandName = commandName
        self.cfg = cfg

    def encode(self):
        dataJSON = {
            'cmdName': self.commandName,
            'cfg': self.cfg
        }
        binaryData = struct.pack(
            '!s', #'!' => network encoding (ie. big endian); 's' => string
            json.dump(dataJSON).encode('utf-8')
        )
        return binaryData

    @staticmethod
    def decode(binaryData):
        pass