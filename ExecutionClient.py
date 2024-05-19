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
from collections.abc import Callable

class ExecutionClient(object):
    HEARTBEAT_INTERVAL = 200 #in ms

    DATA_SUFFIX = 1
    
    def __init__(
        self,
        context,
        ipAddress, 
        commandPort: int, 
        dataInputPort: int, 
        dataOutputPort: int, 
        serverPublicKey=None
    ):
        self._context = context
        self._ipAddress = ipAddress
        self._commandPort = commandPort
        self._dataInputPort = dataInputPort
        self._dataOutputPort = dataOutputPort
        self._serverPublicKey = serverPublicKey
        
        self._dataInputAddress="ipc://dataClient/input"+str(os.getpid()*1000+ExecutionClient.DATA_SUFFIX)
        self._dataOutputAddress="ipc://dataClient/output"+str(os.getpid()*1000+ExecutionClient.DATA_SUFFIX)

        ExecutionClient.DATA_SUFFIX += 1

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
            self._dataOutputThread = threading.Thread(
                target=ExecutionClient._dataLoop, 
                args=(
                    self._context, 
                    self._ipAddress, 
                    self._dataOutputPort, 
                    self._dataOutputAddress, 
                    True, #set as output
                    self._serverPublicKey
                ),
                daemon=daemon
            )
            self._dataOutputThread.start()

            self._dataInputThread = threading.Thread(
                target=ExecutionClient._dataLoop, 
                args=(
                    self._context, 
                    self._ipAddress, 
                    self._dataInputPort, 
                    self._dataInputAddress, 
                    False, #set as input
                    self._serverPublicKey
                ),                
                daemon=daemon
            )
            self._dataInputThread.start()

            self.commandSocket = self._context.socket(zmq.REQ)
            if self._serverPublicKey is not None:
                publicKeyCommand, privateKeyCommand = zmq.curve_keypair()
                self.commandSocket.curve_secretkey = privateKeyCommand 
                self.commandSocket.curve_publickey = publicKeyCommand
                self.commandSocket.curve_serverkey = self._serverPublicKey
            
            self.commandSocket.connect(f"tcp://{self._ipAddress}:{self._commandPort}")

            self._heartbeatThread = threading.Thread(
                target=ExecutionClient._heartbeatLoop, 
                args=(self._context,self._dataInputAddress),
                daemon=daemon
            )
            self._heartbeatThread.start()
            
            self._isRunning = True

    def _dataLoop(
        context: zmq.Context, 
        ipAddress: str,
        dataPort: int, 
        internalAddress: str,
        isOutput: bool,
        serverPublicKey: Optional[bytes]
    ):
        logging.info(f"Starting data socket on '{dataPort}'")
        try:
            dataSocket = context.socket(zmq.XSUB if isOutput else zmq.XPUB)
            if serverPublicKey is not None:
                logging.info(f"Encrypting data socket using server public key")
                publicKeyData, privateKeyData = zmq.curve_keypair()
                dataSocket.curve_secretkey = privateKeyData
                dataSocket.curve_publickey = publicKeyData 
                dataSocket.curve_serverkey = serverPublicKey
            dataSocket.connect(f"tcp://{ipAddress}:{dataPort}")
            
            dataSocketDistributer = context.socket(zmq.XPUB if isOutput else zmq.XSUB)
            dataSocketDistributer.bind(internalAddress)

            if isOutput:
                zmq.proxy(dataSocket, dataSocketDistributer)
            else:
                zmq.proxy(dataSocketDistributer, dataSocket)

        except BaseException as e:
            logging.critical("Exception during data socket setup")
            logging.exception(e)
            sys.exit(1)

    def _heartbeatLoop(
        context: zmq.Context,
        internalAddress: str
    ):
        try:
            dataSocket = context.socket(zmq.PUB)
            dataSocket.connect(internalAddress)
            while True:
                message = DataMessage(
                    channel='heartbeat',
                    payload={'origin': 'client'}
                )
                dataSocket.send(message.encode())
                time.sleep(ExecutionClient.HEARTBEAT_INTERVAL*1e-3)
        except BaseException as e:
            logging.critical("Exception in heartbeat loop")
            logging.exception(e)
            sys.exit(1)

    def addDataListener(self, 
        channelName: str, 
        callbackFunction: 'Callable[[DataMessage],bool]',
        callbackArguments: 'list[Any]' = []
    ):
        logging.info(f"Adding data listener for channel '{channelName}'")
        heartbeatOK = threading.Event()
        def _dataLoop(context, dataAddress, channelName, callbackFunction, callbackArguments):
            logging.debug(f"Started output thread for channel '{channelName}'")
            try:
                dataSocket = context.socket(zmq.SUB)
                dataSocket.connect(dataAddress)
                dataSocket.setsockopt(zmq.SUBSCRIBE,DataMessage.encodedChannel(channelName))
                
                heartbeatSocket = self._context.socket(zmq.SUB)
                heartbeatSocket.connect(dataAddress)
                heartbeatSocket.setsockopt(zmq.SUBSCRIBE,DataMessage.encodedChannel('heartbeat'))
                heartbeatSocket.recv() #blocks until heartbeat is received
                time.sleep(0.1) #need to wait a bit to ensure connection is established :-(
                heartbeatOK.set()
                heartbeatSocket.close()

            except BaseException as e:
                logging.critical(f"Exception during data socket setup for channel '{channelName}'")
                logging.exception(e)
                sys.exit(1)
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
            args=(self._context, self._dataOutputAddress, channelName, callbackFunction, callbackArguments),
            daemon=True
        )
        callbackThread.start()
        heartbeatOK.wait()
        
    def sendCommand(
        self, 
        commandName: str, 
        commandType: str, 
        config: 'dict[str,Any]' = {}, 
        arguments: 'list[str]' = [],
        callbackFunction: 'Optional[Callable[[DataMessage],bool]]' = None,
        callbackArguments: 'list[Any]' = [],
        timeout:int = -1
    ):
        
        commandMessage = CommandMessage(
            commandName=commandName,
            commandType=commandType,
            config=config,
            arguments=arguments
        )
        
        if callbackFunction is not None:
            self.addDataListener(commandMessage.getChannelName(),callbackFunction,callbackArguments)

        self.commandSocket.send(commandMessage.encode())
        rawReply = self.commandSocket.recv()
        reply = CommandReply.fromBytes(rawReply)
        return reply
        

        
    
