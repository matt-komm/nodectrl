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
    TIMEOUT = 1000

    DATA_SUFFIX = 1
    
    def __init__(
        self,
        context,
        ipAddress, 
        commandPort: int, 
        dataInputPort: int, 
        dataOutputPort: int, 
        internalDataInputAddress: str,
        internalDataOutputAddress: str,
        serverPublicKey=None
    ):
        self._context = context
        self._ipAddress = ipAddress
        self._commandPort = commandPort
        self._dataInputPort = dataInputPort
        self._dataOutputPort = dataOutputPort
        self._serverPublicKey = serverPublicKey
        
        self._dataInputAddress=internalDataInputAddress
        self._dataOutputAddress=internalDataOutputAddress

        ExecutionClient.DATA_SUFFIX += 1

        self._isRunning = False

        self.commandIds = {}

        self.commandSocket = None

        #TODO
        #track status of connection; prevent sending commands in case of connection failure
        #but keep threads alive for possible reconnection
        #indicate critial errors, ie. due to config, and exit

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

            self._heartbeatThread = threading.Thread(
                target=ExecutionClient._heartbeatLoop, 
                args=(self._context,self._dataInputAddress),
                daemon=daemon
            )
            self._heartbeatThread.start()

            self.commandSocket = None
            self._openCommandSocket()


            self.eventSocket = self._context.socket(zmq.PUB)
            self.eventSocket.connect(self._dataInputAddress)

            self._isRunning = True

    def _openCommandSocket(self):
        if self.commandSocket is not None:
            self.commandSocket.setsockopt(zmq.LINGER, 0)
            self.commandSocket.close()

        self.commandSocket = self._context.socket(zmq.REQ)
        if self._serverPublicKey is not None:
            publicKeyCommand, privateKeyCommand = zmq.curve_keypair()
            self.commandSocket.curve_secretkey = privateKeyCommand 
            self.commandSocket.curve_publickey = publicKeyCommand
            self.commandSocket.curve_serverkey = self._serverPublicKey
        
        self.commandSocket.connect(f"tcp://{self._ipAddress}:{self._commandPort}")

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
        
    def sendCommand(
        self, 
        commandName: str, 
        commandType: str, 
        config: 'dict[str,Any]' = {}, 
        arguments: 'list[str]' = [],
        callbackFunction: 'Optional[Callable[[DataMessage],bool]]' = None,
        callbackArguments: 'list[Any]' = []
    ):
        commandMessage = CommandMessage(
            commandName=commandName,
            commandType=commandType,
            config=config,
            arguments=arguments
        )
        
        if callbackFunction is not None:
            if not DataListener.createListener(
                self._dataOutputAddress,
                commandMessage.getChannelName(),
                callbackFunction,
                callbackArguments
            ):
                return None

        self.commandSocket.send(commandMessage.encode())
        if self.commandSocket.poll(ExecutionClient.TIMEOUT, zmq.POLLIN):
            rawReply = self.commandSocket.recv()
            reply = CommandReply.fromBytes(rawReply)
            return reply
        else:
            self._openCommandSocket()
            return None
        
    def sendEvent(
        self,
        channel: bytes,
        payload: 'dict[str, Any]' = {}
    ):
        #TODO: check encoding of channel!!!
        self.eventSocket.send(DataMessage(channel,payload).encode())

        
    
