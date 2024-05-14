import time
import logging
import threading

import zmq
from zmq.auth.thread import ThreadAuthenticator

#from HeartbeatGenerator import *
from CommandMessage import *
from EventMessage import *
from Command import *

class ExecutionServer(object):    
    COMMAND_REPLY_TIMEOUT = 100 #in ms

    HEARTBEAT_GENERATION = 500 #in ms

    def __init__(
        self, 
        commandPort: int,
        dataPort: int, 
        allowedIpAdresses=None, 
        publicKey=None, 
        privateKey=None
    ):
        self.commandPort = commandPort
        self.dataPort = dataPort
        self.allowedIpAdresses = allowedIpAdresses
        self.publicKey = publicKey
        self.privateKey = privateKey
        
        self.registeredCallCommands = {}
        self.registeredSpawnCommands = {}

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

        self.spawns = []
    
        self.context = zmq.Context()
        
        self.commandSocket = self.context.socket(zmq.REP)
        self.dataSocket = self.context.socket(zmq.PUB)
            
        if self.publicKey is not None and self.privateKey is not None:
            if self.allowedIpAdresses is not None:
                self.auth = ThreadAuthenticator(self.context)
                self.auth.start()
                self.auth.configure_curve(domain="*", location=zmq.auth.CURVE_ALLOW_ANY)
                self.auth.allow(self.allowedIpAdresses)
        
            self.commandSocket.curve_secretkey = self.privateKey
            self.commandSocket.curve_publickey = self.publicKey
            self.commandSocket.curve_server = True
            
            self.dataSocket.curve_secretkey = self.privateKey
            self.dataSocket.curve_publickey = self.publicKey
            self.dataSocket.curve_server = True
        
        
        self.commandSocket.bind(f"tcp://*:{self.commandPort}")
        self.dataSocket.bind(f"tcp://*:{self.dataPort}")
        
        self.commandThread = threading.Thread(target=self._commandLoop, daemon=True)
        self.commandThread.start()
        '''
        self.heartbeat = HeartbeatGenerator(
            intervalInMS = ExecutionServer.HEARTBEAT_GENERATION,
            callbackFunction=lambda: self.dataSocket.send("heartbeat".encode('utf-8'))
        )
        '''

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

    def _commandLoop(self):
        while True:
            if (self.commandSocket.poll(ExecutionServer.COMMAND_REPLY_TIMEOUT,zmq.POLLIN)>0):
                try:
                    message = CommandMessage.fromBytes(self.commandSocket.recv())
                    logging.debug(f"Command {message.commandType()}/{message.commandName()} received")
                    if message.commandType()=='call' and message.commandName() in self.registeredCallCommands.keys():
                        command = self.registeredCallCommands[message.commandName()]
                        logging.debug(f"Issue call command {message.commandType()}/{message.commandName()}")
                        result = command(message.config(),message.arguments())
                        replyMessage = CommandReply(
                            commandName=message.commandName(),
                            commandType=message.commandType(),
                            requestId=-1,
                            success=True,
                            payload=result
                        )
                        logging.debug(f"Command {message.commandType()}/{message.commandName()} sucessful")

                    elif message.commandType()=='spawn' and message.commandName() in self.registeredSpawnCommands.keys():
                        command = self.registeredSpawnCommands[message.commandName()]
                        logging.debug(f"Issue spawn command {message.commandType()}/{message.commandName()}")
                        spawn = command.spawn(message.config(),message.arguments())
                        replyMessage = CommandReply(
                            commandName=message.commandName(),
                            commandType=message.commandType(),
                            requestId=-1,
                            success=True,
                            payload={}
                        )
                        logging.debug(f"Command {message.commandType()}/{message.commandName()} sucessful")
                    else:
                        raise RuntimeError(f"Command {message.commandType()}/{message.commandName()} not known")
                    
                except BaseException as e:
                    logging.exception(e)
                    replyMessage = CommandReply(
                        commandName=message.commandName(),
                        commandType=message.commandType(),
                        requestId=-1,
                        success=False,
                        payload={'exception': {'type': str(type(e)), 'message': str(e)}}
                    )
                    logging.debug(f"Command {message.commandType()}/{message.commandName()} failed")

                self.commandSocket.send(replyMessage.encodeReply())
        
    
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
        
    
        
