import logging
import threading

import zmq 

from Message import *
from collections.abc import Callable

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


class DataListener():
    TIMEOUT = 1000

    @staticmethod
    def createListener(
        dataAddress: str,
        channelName: str, 
        callbackFunction: 'Callable[[DataMessage],bool]',
        callbackArguments: 'list[Any]' = []
    ):
        logging.info(f"Adding data listener for channel '{channelName}'")
        heartbeatDone = threading.Event()
        hasTimedOut = False
        def _dataLoop(dataAddress, channelName, callbackFunction, callbackArguments):
            logging.debug(f"Started output thread for channel '{channelName}'")
            try:
                context = zmq.Context()
                dataSocket = context.socket(zmq.SUB)
                dataSocket.connect(dataAddress)
                dataSocket.setsockopt(zmq.SUBSCRIBE,DataMessage.encodedChannel(channelName))
                
                heartbeatSocket = context.socket(zmq.SUB)
                heartbeatSocket.connect(dataAddress)
                heartbeatSocket.setsockopt(zmq.SUBSCRIBE,DataMessage.encodedChannel('heartbeat'))
                if heartbeatSocket.poll(DataListener.TIMEOUT, zmq.POLLIN):
                    heartbeatSocket.recv() #blocks until heartbeat is received
                else:
                    hasTimedOut = True
                heartbeatDone.set()
                heartbeatSocket.close()

            except BaseException as e:
                logging.critical(f"Exception during data socket setup for channel '{channelName}'")
                logging.exception(e)
            while True:
                rawMessage = dataSocket.recv()
                try:
                    message = DataMessage.fromBytes(rawMessage)
                    #kill loop and thread on return False; explicitly check for return True
                    ret = callbackFunction(message,*callbackArguments)
                    if ret is True:
                        continue
                    elif ret is False:
                        break
                    else:
                        raise RuntimeError("Callback return type needs to be {True|False}")
                except BaseException as e:
                    logging.warning(f"Exception during processing of data socket message of channel '{channelName}'")
                    logging.exception(e)
            logging.debug(f"Closing output thread for channel '{channelName}'")

        callbackThread = threading.Thread(
            target=_dataLoop,
            args=(dataAddress, channelName, callbackFunction, callbackArguments),
            daemon=True
        )
        callbackThread.start()
        heartbeatDone.wait()
        if hasTimedOut:
            return False
        return True