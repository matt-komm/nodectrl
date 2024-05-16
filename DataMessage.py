from Message import *

class DataMessage(object):
    SEPARATOR = '||'
    def __init__(
        self,
        channel: str,
        payload: 'dict[str,Any]' = {}
    ):
        if channel.find(DataMessage.SEPARATOR)>=0:
            raise RuntimeError(f"Channel name cannot contain '{DataMessage.SEPARATOR}' which is used as a delimiter")
        self._channel = channel
        self._payload = payload
        
    def channel(self):
        return self._channel
        
    def payload(self):
        return self._payload
    
    @staticmethod
    def encodedChannel(data: str) -> bytes:
        return Message.encodeString(data+DataMessage.SEPARATOR)
    
    def encode(self) -> bytes:
        return DataMessage.encodedChannel(self._channel)+Message.encodeString(Message.jsonToString(self._payload))
    
    def __str__(self):
        return f"DataMessage(channel={self._channel}, payload={self._payload})"
            
    @staticmethod
    def fromBytes(data: bytes) -> 'DataMessage':
        messageString = Message.decodeString(data)
        messageSplit = messageString.split(DataMessage.SEPARATOR,2)

        if len(messageSplit)!=2:
            raise RuntimeError(f"Error while decoding data message '{messageString}' using channel delimiter '{DataMessage.SEPARATOR}'")
        message = DataMessage(
            channel = messageSplit[0],
            payload = Message.stringToJSON(messageSplit[1])
        )
        return message
