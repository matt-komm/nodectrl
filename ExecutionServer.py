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
    HEARTBEAT_INTERVAL = 200 #in ms


    DATA_SUFFIX = 1

    def __init__(
        self, 
        context: zmq.Context,
        commandPort: int,
        dataInputPort: int, 
        dataOutputPort: int, 
        publicKey=None, 
        privateKey=None
    ):
        self._context = context
        self._commandPort = commandPort
        self._dataInputPort = dataInputPort
        self._dataOutputPort = dataOutputPort
        self._publicKey = publicKey
        self._privateKey = privateKey

        self._dataInputAddress="ipc://dataServer/input"+str(os.getpid()*1000+ExecutionServer.DATA_SUFFIX)
        self._dataOutputAddress="ipc://dataServer/output"+str(os.getpid()*1000+ExecutionServer.DATA_SUFFIX)

        ExecutionServer.DATA_SUFFIX += 1
        
        self._registeredCallCommands = {}
        self._registeredSpawnCommands = {}

        self._isRunning = False

        self._dataSocket = None
        
    def serve(self, daemon: bool = False):
        logging.info("Starting data/command threads as daemons: "+str(daemon))
        if self._isRunning:
            logging.warning("Event and command thread already executing")
        else:
            self._dataOutputThread = threading.Thread(
                target=ExecutionServer._dataLoop, 
                args=(
                    self._context, 
                    self._dataOutputPort, 
                    self._dataOutputAddress,
                    True, # set as output 
                    self._publicKey, 
                    self._privateKey
                ),
                daemon=daemon
            )
            self._dataOutputThread.start()
            
            self._dataInputThread = threading.Thread(
                target=ExecutionServer._dataLoop, 
                args=(
                    self._context, 
                    self._dataInputPort, 
                    self._dataInputAddress,
                    False, # set as input 
                    self._publicKey, 
                    self._privateKey
                ),
                daemon=daemon
            )
            self._dataInputThread.start()

            self.commandThread = threading.Thread(
                target=ExecutionServer._commandLoop, 
                args=(self._context, self._commandPort, self._registeredCallCommands, self._registeredSpawnCommands, self._publicKey, self._privateKey),
                daemon=daemon
            )
            self.commandThread.start()

            self.heartbeatThread = threading.Thread(
                target=ExecutionServer._heartbeatLoop, 
                args=(self._context,self._dataOutputAddress),
                daemon=daemon
            )
            self.heartbeatThread.start()

            #create a socket for main process to send data
            self._dataSocket = self._context.socket(zmq.PUB)
            self._dataSocket.connect(self._dataOutputAddress)

            self._isRunning = True

    #do not expose any class member to this method; communicate only via zmq inproc
    def _dataLoop(
        context: zmq.Context, 
        dataPort: int,
        internalAddress: str,
        isOutput: bool,
        publicKey: Optional[bytes], 
        privateKey: Optional[bytes]
    ):
        logging.info(f"Starting data output socket on '{dataPort}'")
        try:
            dataSocketCollector = context.socket(zmq.XSUB if isOutput else zmq.XPUB)
            dataSocketCollector.bind(internalAddress)
            #dataSocketCollector.setsockopt(zmq.SUBSCRIBE, b"")

            dataSocket = context.socket(zmq.XPUB if isOutput else zmq.XSUB)
            if publicKey is not None and privateKey is not None:
                logging.info(f"Encrypting data socket using keys")
                dataSocket.curve_secretkey = privateKey
                dataSocket.curve_publickey = publicKey
                dataSocket.curve_server = True
            dataSocket.bind(f"tcp://*:{dataPort}")

            #connect ipc socket to outgoing TCP socket; this will block forever
            #zmq.device(zmq.FORWARDER, dataSocketCollector, dataSocket)
            if isOutput:
                zmq.proxy(dataSocketCollector, dataSocket)
            else:
                zmq.proxy(dataSocket, dataSocketCollector)

        except BaseException as e:
            logging.critical("Exception in data socket setup/loop")
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
                    payload={'origin': 'server'}
                )
                dataSocket.send(message.encode())
                time.sleep(ExecutionServer.HEARTBEAT_INTERVAL*1e-3)
        except BaseException as e:
            logging.critical("Exception in heartbeat loop")
            logging.exception(e)
            sys.exit(1)

    #do not expose any class member to this method; communicate only via zmq inproc if needed
    def _commandLoop(
        context: zmq.Context, 
        commandPort: int, 
        callCommands: 'dict[str,CallCommand]',
        spawnCommands: 'dict[str,SpawnCommand]',
        publicKey: Optional[bytes], 
        privateKey: Optional[bytes]
    ):
        logging.info(f"Starting command socket on '{commandPort}'")
        spawns = {}
        try:
            commandSocket = context.socket(zmq.REP)
            if publicKey is not None and privateKey is not None:
                logging.info(f"Encrypting command socket using keys")
                commandSocket.curve_secretkey = privateKey
                commandSocket.curve_publickey = publicKey
                commandSocket.curve_server = True
            commandSocket.bind(f"tcp://*:{commandPort}")

        except BaseException as e:
            logging.critical("Exception during command socket setup")
            logging.exception(e)
            sys.exit(1)

        while True:
            rawMessage = commandSocket.recv() #if this fails we are in trouble!
            message = CommandMessage.fromBytes(rawMessage)

            try:
                logging.debug(f"Command '{message.commandType()}/{message.commandName()}:{message.uniqueId()}' received")

                if message.commandType()=='call' and message.commandName() in callCommands.keys():
                    command = callCommands[message.commandName()]
                    logging.debug(f"Issue call command '{message.commandType()}/{message.commandName()}'")
                    result = command(message.getChannelName(),message.config(),message.arguments())

                    replyMessage = message.createReply(
                        success=True,
                        payload=result
                    )
                    logging.debug(f"Command '{message.commandType()}/{message.commandName()}' sucessful")

                elif message.commandType()=='spawn' and message.commandName() in spawnCommands.keys():
                    command = spawnCommands[message.commandName()]
                    logging.debug(f"Issue spawn command '{message.commandType()}/{message.commandName()}'")
                    spawn,result = command(message.getChannelName(),message.config(),message.arguments())
                    replyMessage = message.createReply(
                        success=True,
                        payload=result
                    )
                    #TODO: what is the channel?
                    spawns[f'{message.commandType()}/{message.commandName()}/{message.uniqueId()}'] = spawn
                    logging.debug(f"Command '{message.commandType()}/{message.commandName()}' sucessful")
                else:
                    raise RuntimeError(f"Command '{message.commandType()}/{message.commandName()}' not known")
                
            except BaseException as e:
                logging.warning("Exception during processing of command socket message")
                logging.exception(e)
                replyMessage = message.createReply(
                    success=False,
                    payload={'exception': {'type': type(e).__name__, 'message': str(e)}}
                )
            commandSocket.send(replyMessage.encode())
            

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
            args=(self._context, self._dataInputAddress, channelName, callbackFunction, callbackArguments),
            daemon=True
        )
        callbackThread.start()
        heartbeatOK.wait()
        
    
    def sendData(self, channel: str, payload: 'dict[str,Any]' = {}):
        message = DataMessage(channel=channel, payload=payload)
        if not self._isRunning or self._dataSocket is None:
            raise RuntimeError("Cannot send data when server has not yet started")
        self._dataSocket.send(message.encode())


    def registerCallCommand(self, command: CallCommand):
        self._registeredCallCommands[command.name()] = command

    def registerSpawnCommand(self, command: SpawnCommand):
        self._registeredSpawnCommands[command.name()] = command
        
    
