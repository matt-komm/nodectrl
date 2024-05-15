from Message import *

class DataMessage(object):
    def __init__(
        self,
        channel: str,
        payload: 'dict[str,Any]' = {}
    ):
        self._channel = channel
        self._payload = payload
        
    def channel(self):
        return self._channel
        
    def payload(self):
        return self._payload
    
    def encode(self) -> bytes:
        eventJSON = {
            'channel': self._channel,
            'payload': self._payload,
        }
        return Message.encodeJSON(eventJSON)
        
    @staticmethod
    def fromBytes(data: bytes) -> 'DataMessage':
        eventJSON = Message.decodeJSON(data)
        message = DataMessage(
            channel = eventJSON['channel'],
            payload = eventJSON['payload']
        )
        return message
