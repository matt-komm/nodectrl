import time
import logging
import threading
import sys

import zmq

from CommandMessage import *
from DataMessage import *
from Command import *

from typing import Optional

class ExecutionServer(object):    
    COMMAND_REPLY_TIMEOUT = 100 #in ms

    def __init__(
        self, 
        context: zmq.Context,
        commandPort: int,
        dataPort: int, 
        publicKey=None, 
        privateKey=None
    ):
        self._context = context
        self._commandPort = commandPort
        self._dataPort = dataPort
        self._publicKey = publicKey
        self._privateKey = privateKey
        
        self._registeredCallCommands = {}
        self._registeredSpawnCommands = {}

        self._isRunning = False

        self._dataSocket = None
        
    def serve(self, daemon: bool = False):
        logging.info("Starting data/command threads as daemons: "+str(daemon))
        if self._isRunning:
            logging.warning("Event and command thread already executing")
        else:
            self._dataThread = threading.Thread(
                target=ExecutionServer._dataLoop, 
                args=(self._context, self._dataPort, self._publicKey, self._privateKey),
                daemon=daemon
            )
            self._dataThread.start()
            
            self.commandThread = threading.Thread(
                target=ExecutionServer._commandLoop, 
                args=(self._context, self._commandPort, self._publicKey, self._privateKey),
                daemon=daemon
            )
            self.commandThread.start()

            self.heartbeatThread = threading.Thread(
                target=ExecutionServer._heartbeatLoop, 
                args=(self._context,),
                daemon=daemon
            )
            self.heartbeatThread.start()

            #create a socket for main process to send data
            self._dataSocket = self._context.socket(zmq.PUB)
            self._dataSocket.connect("ipc://datapub")

            self._isRunning = True

    #do not expose any class member to this method; communicate only via zmq inproc
    def _dataLoop(
        context: zmq.Context, 
        dataPort: int, 
        publicKey: Optional[bytes], 
        privateKey: Optional[bytes]
    ):
        logging.info(f"Starting data socket on '{dataPort}'")
        try:
            dataSocketCollector = context.socket(zmq.SUB)
            dataSocketCollector.bind("ipc://datapub")
            dataSocketCollector.setsockopt(zmq.SUBSCRIBE, b"")

            dataSocket = context.socket(zmq.PUB)
            if publicKey is not None and privateKey is not None:
                logging.info(f"Encrypting data socket using keys")
                dataSocket.curve_secretkey = privateKey
                dataSocket.curve_publickey = publicKey
                dataSocket.curve_server = True
            dataSocket.bind(f"tcp://*:{dataPort}")

            #connect inproc socket to outgoing TCP socket; this will block forever
            zmq.device(zmq.FORWARDER, dataSocketCollector, dataSocket)

        except BaseException as e:
            logging.critical("Exception in data socket setup/loop")
            logging.exception(e)
            sys.exit(1)

    def _heartbeatLoop(
        context: zmq.Context
    ):
        dataSocket = context.socket(zmq.PUB)
        dataSocket.connect("ipc://datapub")
        while True:
            message = DataMessage(
                channel='heartbeat',
                payload={}
            )
            dataSocket.send(message.encode())
            time.sleep(0.5)

    #do not expose any class member to this method; communicate only via zmq inproc if needed
    def _commandLoop(
        context: zmq.Context, 
        commandPort: int, 
        publicKey: Optional[bytes], 
        privateKey: Optional[bytes]
    ):
        logging.info(f"Starting command socket on '{commandPort}'")
        spawns = []
        try:
            commandSocket = context.socket(zmq.REP)
            if publicKey is not None and privateKey is not None:
                logging.info(f"Encrypting command socket using keys")
                commandSocket.curve_secretkey = privateKey
                commandSocket.curve_publickey = publicKey
                commandSocket.curve_server = True
            commandSocket.bind(f"tcp://*:{commandPort}")

            dataSocket = context.socket(zmq.PUB)
            dataSocket.connect("ipc://datapub")

        except BaseException as e:
            logging.critical("Exception during command socket setup")
            logging.exception(e)
            sys.exit(1)

        while True:
            rawMessage = commandSocket.recv() #if this fails we are in trouble!
            try:
                message = CommandMessage.fromBytes(rawMessage)
                logging.debug(f"Command '{message.commandType()}/{message.commandName()}:{message.uniqueId()}' received")

                replyMessage = CommandReply(
                    commandName=message.commandName(),
                    commandType=message.commandType(),
                    uniqueId=message.uniqueId(),
                    success=True,
                    payload={'Hi':'OK'}
                )
                dataMessage = DataMessage(message.getChannelName(),{'output':'dbadads'})
                dataSocket.send(dataMessage.encode())

                '''
                if message.commandType()=='call' and message.commandName() in self.registeredCallCommands.keys():
                    command = self.registeredCallCommands[message.commandName()]
                    logging.debug(f"Issue call command '{message.commandType()}/{message.commandName()}'")
                    result = command(message.config(),message.arguments())
                    replyMessage = CommandReply(
                        commandName=message.commandName(),
                        commandType=message.commandType(),
                        requestId=-1,
                        success=True,
                        payload=result
                    )
                    logging.debug(f"Command '{message.commandType()}/{message.commandName()}' sucessful")

                elif message.commandType()=='spawn' and message.commandName() in self.registeredSpawnCommands.keys():
                    command = self.registeredSpawnCommands[message.commandName()]
                    logging.debug(f"Issue spawn command '{message.commandType()}/{message.commandName()}'")
                    spawn = command.spawn(message.config(),message.arguments())
                    replyMessage = CommandReply(
                        commandName=message.commandName(),
                        commandType=message.commandType(),
                        requestId=-1,
                        success=True,
                        payload={}
                    )
                    logging.debug(f"Command '{message.commandType()}/{message.commandName()}' sucessful")
                else:
                    raise RuntimeError(f"Command '{message.commandType()}/{message.commandName()}' not known")
                '''
            except BaseException as e:
                logging.warning("Exception during processing of command socket message")
                logging.exception(e)
                replyMessage = CommandReply(
                    commandName='',
                    commandType='',
                    success=False,
                    payload={'exception': {'type': str(type(e)), 'message': str(e)}}
                )
            commandSocket.send(replyMessage.encode())
        
    
    def sendData(self, channel: str, payload: 'dict[str,Any]' = {}):
        message = DataMessage(channel=channel, payload=payload)
        if not self._isRunning or self._dataSocket is None:
            raise RuntimeError("Cannot send data when server has not yet started")
        self._dataSocket.send(message.encode())
        
    
