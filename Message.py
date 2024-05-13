from typing import Any

class Message(object):

    @staticmethod
    def encodeString(data: str):
        utf8String = json.dump(jsonObject).encode('utf-8')
        binaryData = struct.pack(
            '!s', #'!' => network encoding (ie. big endian); 's' => string
            str.encode('utf-8')
        )
        return binaryData

    @staticmethod
    def decodeString(data: str):
        pass

    @staticmethod
    def encodeJSON(jsonObject: dict[Any,Any]):
        utf8String = json.dump(jsonObject).encode('utf-8')
        binaryData = struct.pack(
            '!s', #'!' => network encoding (ie. big endian); 's' => string
            utf8String
        )
        return binaryData

    @staticmethod
    def decodeJSON(jsonObject: dict[Any,Any]):
        utf8String = json.dump(jsonObject).encode('utf-8')
        binaryData = struct.pack(
            '!s', #'!' => network encoding (ie. big endian); 's' => string
            utf8String
        )
        return binaryData


    