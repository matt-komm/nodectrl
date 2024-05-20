import threading
import logging

import zmq

class CommandStatus(object):
    def __init__(self, context, commandMessage):
        self._outputBuffer = []
        self._context = context
        self._commandMessage = commandMessage
        
        self._dataThread = threading.Thread(
            target=CommandStatus._dataLoop, 
            args=(self._context, commandMessage.uniqueId()),
            daemon=daemon
        )
        
    def _dataLoop(self, context, uniqueId):
        logging.info(f"Starting data socket on '{dataPort}'")
        try:
            dataSocket = context.socket(zmq.SUB)
            dataSocket.connect("inproc://datasub")
            dataSocket.setsockopt(zmq.SUBSCRIBE,uniqueId)
            
        except BaseException as e:
            logging.warning("Exception during data socket setup")
            logging.exception(e)
            
        while True:
            rawMessage = dataSocket.recv()
            decodedMessage = rawMessage.decode('utf-8')
            self._outputBuffer.append(decodedMessage)
            print (decodedMessage)
