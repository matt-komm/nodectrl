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
                args=(self._context, self._commandPort, self._registeredCallCommands, self._registeredSpawnCommands, self._publicKey, self._privateKey),
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

            #connect ipc socket to outgoing TCP socket; this will block forever
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
            time.sleep(0.25)

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

            #dataSocket = context.socket(zmq.PUB)
            #dataSocket.connect("ipc://datapub")

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
                    #dataSocket.send(DataMessage(message.getChannelName(),{}).encode())
                    result = command(context, message.getChannelName(),message.config(),message.arguments())
                    
                    
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
            dataSocket2 = context.socket(zmq.PUB)
            dataSocket2.connect("ipc://datapub")
            dataSocket2.send(DataMessage(message.getChannelName(),{"fromData":2}).encode())
            dataSocket2.setsockopt( zmq.LINGER, 0 ) 
            dataSocket2.close()
        
    
    def sendData(self, channel: str, payload: 'dict[str,Any]' = {}):
        message = DataMessage(channel=channel, payload=payload)
        if not self._isRunning or self._dataSocket is None:
            raise RuntimeError("Cannot send data when server has not yet started")
        self._dataSocket.send(message.encode())


    def registerCallCommand(self, command: CallCommand):
        self._registeredCallCommands[command.name()] = command

    def registerSpawnCommand(self, command: SpawnCommand):
        self._registeredSpawnCommands[command.name()] = command
        
    
