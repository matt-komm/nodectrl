import time
import logging
import threading
import sys

import zmq
from zmq.auth.thread import ThreadAuthenticator

#from HeartbeatGenerator import *
from CommandMessage import *
from DataMessage import *
from Command import *

from typing import Optional

class ExecutionServer(object):    
    COMMAND_REPLY_TIMEOUT = 100 #in ms

    HEARTBEAT_GENERATION = 500 #in ms

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
        '''
        self.registerCallCommand(
            CallCommand(
                name='query_commands',
                description='query commands',
                function=self._doQueryCommands
            )
        )
        
        self.registerCallCommand(
            CallCommand(
                name='emit_event',
                description='emits an event',
                function=self._doEmitEvent
            )
        )
        '''
        

        self._isRunning = False
        
        '''
        self.heartbeat = HeartbeatGenerator(
            intervalInMS = ExecutionServer.HEARTBEAT_GENERATION,
            callbackFunction=lambda: self.dataSocket.send("heartbeat".encode('utf-8'))
        )
        '''

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
            dataSocketCollector.bind("inproc://data")
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
            dataSocket.connect("inproc://data")

        except BaseException as e:
            logging.critical("Exception during command socket setup")
            logging.exception(e)
            sys.exit(1)

        while True:
            rawMessage = commandSocket.recv() #if this fails we are in trouble!
            try:
                message = CommandMessage.fromBytes(rawMessage)
                logging.debug(f"Command '{message.commandType()}/{message.commandName()}' received")

                replyMessage = CommandReply(
                    commandName=message.commandName(),
                    commandType=message.commandType(),
                    requestId=-1,
                    success=True,
                    payload={'Hi':'OK'}
                )
                dataMessage = DataMessage('command',{message.commandType():message.commandName()})
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
                    requestId=-1,
                    success=False,
                    payload={'exception': {'type': str(type(e)), 'message': str(e)}}
                )
            commandSocket.send(replyMessage.encode())
        
    '''
    def emitEvent(self, channel: str, payload: 'dict[str,Any]' = {}):
        #self.heartbeat.resetHeartbeatTimestamp()
        print ("emit event")
        message = EventMessage(channel,payload)
        self.dataSocket.send(message.encodeEvent())
        
    def registerCallCommand(self,command):
        if command.name not in self.registeredCallCommands.keys():
            self.registeredCallCommands[command.name] = command

    def registerSpawnCommand(self,command):
        if command.name not in self.registeredSpawnCommands.keys():
            self.registeredSpawnCommands[command.name] = command
        
    
        
    def _doQueryCommands(self, config: 'dict[str,Any]' = {}, args: 'list[str]' = []):
        result = {'call':{},'spawn':{}}
        for k,v in self.registeredCallCommands.items():
            result['call'][k] = v.description
        for k,v in self.registeredSpawnCommands.items():
            result['spawn'][k] = v.description
        return result
        
    def _doEmitEvent(self, config: 'dict[str,Any]' = {}, args: 'list[str]' = []):
        self.emitEvent(config['channel'])
        return {}
    '''