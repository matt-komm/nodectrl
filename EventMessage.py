from Message import *

class EventMessage(object):
    def __init__(
        self,
        channel:str,
        payload: 'dict[str,Any]' = {}
    ):
        self._channel = channel
        self._payload = payload
        
    def channel(self):
        return self._channel
        
    def payload(self):
        return self._payload
    
    def encodeEvent(self) -> bytes:
        eventJSON = {
            'channel': self._channel,
            'payload': self._payload,
        }
        return Message.encodeJSON(eventJSON)
        
    @staticmethod
    def fromBytes(data: bytes) -> 'EventMessage':
        eventJSON = Message.decodeJSON(data)
        message = EventMessage(
            channel = eventJSON['channel'],
            payload = eventJSON['payload']
        )
        return message
