import struct
import json
from typing import Any

class Message():
    @staticmethod
    def encodeString(data: str) -> bytes:
        utf8String = data.encode('utf-8')
        binaryData = struct.pack(
            '!s', #'!' => network encoding (ie. big endian); 's' => string
            utf8String
        )
        return binaryData

    @staticmethod
    def decodeString(data: bytes) -> str:
        utf8String = struct.unpack(
            '!s', #'!' => network encoding (ie. big endian); 's' => string
            data
        )
        decodedString = utf8String.decode('utf-8')
        return decodedString

    @staticmethod
    def encodeJSON(data: dict[Any,Any]) -> bytes:
        jsonString = json.dump(data)
        return Message.encodeString(jsonString)

    @staticmethod
    def decodeJSON(data: bytes) -> dict[Any,Any]:
        jsonString = Message.decodeString(data)
        return json.loads(data)

    @staticmethod
    def encodeList(data: list[Any]) -> bytes:
        return Message.encodeJSON(data)

    @staticmethod
    def decodeList(data: bytes) -> list[Any]:
        return Message.decodeJSON(data)
    