from Message import *

class DataMessage(object):
    def __init__(
        self,
        channel: bytes,
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
            'channel': ,
            'payload': ,
        }
        return Message.encodeString(self._channel+'//')+Message.encodeJSON(self._payload)
        
    @staticmethod
    def fromBytes(data: bytes) -> 'DataMessage':
        
        eventJSON = Message.decodeJSON(data)
        message = DataMessage(
            channel = eventJSON['channel'],
            payload = eventJSON['payload']
        )
        return message
