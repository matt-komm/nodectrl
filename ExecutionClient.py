import logging
import threading
import os
import time 
import sys

import zmq

from CommandStatus import *
from CommandMessage import *
from DataMessage import *

from typing import Optional

class ExecutionClient(object):
    EVENT_POLL_TIMEOUT = 1 #in ms
    EVENT_DELAY_TIMEOUT = 1 #in ms
    COMMAND_REPLY_TIMEOUT = 500 #in ms
    COMMAND_RETIRES = 3

    HEARTBEAT_CHECK = 2000 #in ms (use more than for generation)
    
    def __init__(
        self,
        context,
        ipAddress, 
        commandPort: int, 
        dataPort: int, 
        serverPublicKey=None
    ):
        self._context = context
        self._ipAddress = ipAddress
        self._commandPort = commandPort
        self._dataPort = dataPort
        self._serverPublicKey = serverPublicKey
        

        self._isRunning = False

        self.commandIds = {}

        self.commandSocket = None

        '''
        self.commandSocket = self.context.socket(zmq.REQ)
        
        
        if serverPublicKey is not None:
            publicKeyCommand, privateKeyCommand = zmq.curve_keypair()
            self.commandSocket.curve_secretkey = privateKeyCommand 
            self.commandSocket.curve_publickey = publicKeyCommand
            self.commandSocket.curve_serverkey = self.serverPublicKey
            
            publicKeyData, privateKeyData = zmq.curve_keypair()
            self.dataSocket.curve_secretkey = privateKeyData
            self.dataSocket.curve_publickey = publicKeyData 
            self.dataSocket.curve_serverkey = self.serverPublicKey
        
        self.commandSocket.connect(f"tcp://{self.ipAddress}:{self.commandPort}")
        self.dataSocket.connect(f"tcp://{self.ipAddress}:{self.dataPort}")
        self.dataSocket.setsockopt(zmq.SUBSCRIBE,b"")
        
        self.eventLoopReady = threading.Event()
        self.eventConnectionReady = threading.Event()
        
        self.eventThread = threading.Thread(target=self._eventLoop, daemon=True)
        self.eventThread.start()
        
        self.commandQueue = queue.SimpleQueue()
        self.commandThreadReady = threading.Event()
        self.commandThread = threading.Thread(target=self._commandLoop, daemon=True)
        self.commandThread.start()
        
        self.eventLoopReady.wait()
        message = CommandMessage('emit_event','call',config={'channel':'connection'})
        self.commandSocket.send(message.encodeCommand())
        self.commandSocket.recv()
        #self.eventConnectionReady.wait()
        '''


    def connect(self, daemon: bool = False):
        logging.info("Starting data/command threads as daemons: "+str(daemon))
        if self._isRunning:
            logging.warning("Event and command thread already executing")
        else:
            self._dataThread = threading.Thread(
                target=ExecutionClient._dataLoop, 
                args=(self._context, self._ipAddress, self._dataPort, self._serverPublicKey),
                daemon=daemon
            )
            self._dataThread.start()

            self.commandSocket = self._context.socket(zmq.REQ)
            if self._serverPublicKey is not None:
                publicKeyCommand, privateKeyCommand = zmq.curve_keypair()
                self.commandSocket.curve_secretkey = privateKeyCommand 
                self.commandSocket.curve_publickey = publicKeyCommand
                self.commandSocket.curve_serverkey = self._serverPublicKey
            
            self.commandSocket.connect(f"tcp://{self._ipAddress}:{self._commandPort}")
            
            self._isRunning = True

    def _dataLoop(
        context: zmq.Context, 
        ipAddress: str,
        dataPort: int, 
        serverPublicKey: Optional[bytes]
    ):
        logging.info(f"Starting data socket on '{dataPort}'")
        try:
            dataSocket = context.socket(zmq.SUB)
            if serverPublicKey is not None:
                logging.info(f"Encrypting data socket using server public key")
                publicKeyData, privateKeyData = zmq.curve_keypair()
                dataSocket.curve_secretkey = privateKeyData
                dataSocket.curve_publickey = publicKeyData 
                dataSocket.curve_serverkey = serverPublicKey
            dataSocket.connect(f"tcp://{ipAddress}:{dataPort}")
            dataSocket.setsockopt(zmq.SUBSCRIBE,b"")
            
            dataSocketDistributer = context.socket(zmq.PUB)
            dataSocketDistributer.bind("inproc://datasub")
            zmq.device(zmq.FORWARDER, dataSocket, dataSocketDistributer)

        except BaseException as e:
            logging.critical("Exception during data socket setup")
            logging.exception(e)
            sys.exit(1)
        '''
        while True:
            rawMessage = dataSocket.recv()
            try:
                message = DataMessage.fromBytes(rawMessage)
                logging.debug(f"received data on channel '{message.channel()}' with payload '{message.payload()}'")
            except BaseException as e:
                logging.warning("Exception during processing of data socket message")
                logging.exception(e)
        '''

    def createCommandUniqueId(self, command) -> bytes:
        commandId = command.commandName()+"/"+command.commandType()
        if commandId in self.commandIds.keys():
            self.commandIds[commandId] += 1
        else:
            self.commandIds[commandId] = 0
        return (commandId+':'+str(self.commandIds[commandId])).encode('utf-8')
    
    def sendCommand(
        self, 
        commandName: str, 
        commandType: str, 
        config: 'dict[str,Any]' = {}, 
        arguments: 'list[str]' = [],
        onOutputCallback = None
    ):
        def _handleOutput(context, channelName, callbackFunction):
            try:
                dataSocket = context.socket(zmq.SUB)
                dataSocket.connect("inproc://datasub")
                dataSocket.setsockopt(zmq.SUBSCRIBE,channelName)
            except BaseException as e:
                logging.critical("Exception during data socket setup")
                logging.exception(e)
                sys.exit(1)
            while True:
                rawMessage = dataSocket.recv()
                try:
                    if not callbackFunction(rawMessage): #kill loop and thread on return False/None
                        break
                except BaseException as e:
                    logging.warning("Exception during processing of data socket message")
                    logging.exception(e)
                    
        commandMessage = CommandMessage(
            commandName=commandName,
            commandType=commandType,
            config=config,
            arguments=arguments
        )
        commandUniqueId = self.createCommandUniqueId(commandMessage)
        commandMessage.setUniqueId(commandUniqueId)
              
        if onOutputCallback is not None:
            callbackThread = threading.Thread(
                target=_handleOutput, 
                args=(self._context, commandUniqueId, onOutputCallback),
                daemon=True
            )
        
        self.commandSocket.send(commandMessage.encode())
        rawReply = self.commandSocket.recv()
        reply = CommandReply.fromBytes(rawReply)
        print("recv",reply)
        

        
    
