import logging
import threading
import os
import time 
import queue

import zmq

from CommandStatus import *
from CommandMessage import *

class ExecutionClient(object):
    EVENT_LOOP_TIMEOUT = 10 #in ms
    COMMAND_REPLY_TIMEOUT = 500 #in ms
    COMMAND_RETIRES = 3

    HEARTBEAT_CHECK = 2000 #in ms (use more than for generation)
    
    def __init__(
        self,
        ipAddress, 
        commandPort: int, 
        monitorPort: int, 
        serverPublicKey=None
    ):
        self.ipAddress = ipAddress
        self.commandPort = commandPort
        self.monitorPort = monitorPort
        self.serverPublicKey = serverPublicKey
        
        self.context = zmq.Context()
        self.commandSocket = self.context.socket(zmq.REQ)
        self.monitorSocket = self.context.socket(zmq.SUB)
        
        if serverPublicKey is not None:
            publicKeyCommand, privateKeyCommand = zmq.curve_keypair()
            self.commandSocket.curve_secretkey = privateKeyCommand 
            self.commandSocket.curve_publickey = publicKeyCommand
            self.commandSocket.curve_serverkey = self.serverPublicKey
            
            publicKeyMonitor, privateKeyMonitor = zmq.curve_keypair()
            self.monitorSocket.curve_secretkey = privateKeyMonitor
            self.monitorSocket.curve_publickey = publicKeyMonitor 
            self.monitorSocket.curve_serverkey = self.serverPublicKey
        
        self.commandSocket.connect(f"tcp://{self.ipAddress}:{self.commandPort}")
        self.monitorSocket.connect(f"tcp://{self.ipAddress}:{self.monitorPort}")
        self.monitorSocket.setsockopt(zmq.SUBSCRIBE,b"")
        
        self.eventThread = threading.Thread(target=self._eventLoop, daemon=True)
        self.eventThread.start()
        
        self.commandQueue = queue.Queue()
        self.commandThread = threading.Thread(target=self._commandLoop, daemon=True)
        self.commandThread.start()

    def _eventLoop(self):
        while True:
            if (self.monitorSocket.poll(
                ExecutionClient.EVENT_LOOP_TIMEOUT,
                zmq.POLLIN
            )>0):
                message = self.monitorSocket.recv().decode('utf-8')
                print('event >>> ',message)
                
    def _commandLoop(self):
        while True:
            command = self.commandQueue.get()
            print ("proc",command.commandName())
            time.sleep(0.01)
            '''
            sendSuccess = False
            for _ in range(ExecutionClient.COMMAND_RETIRES):
                self.commandSocket.send(command.encode())
                if (self.commandSocket.poll(ExecutionClient.COMMAND_REPLY_TIMEOUT,zmq.POLLIN)>0):
                    message = self.commandSocket.recv().decode('utf-8')
                    logging.info("Command executed: "+command.name)
                    sendSuccess = True
                    break
                else:
                    sendSuccess = True
                    logging.error("Command lost: "+command.name)
                    #TODO: check heartbeat
            '''

    def sendCommand(self,command):
        #outputProcess, writeOutput = os.pipe()
        #readInput, inputProcess = os.pipe()
        self.commandQueue.put(command)
        #commandStatus = CommandStatus(inputProcess,outputProcess)
        #return commandStatus
        
    def onEvent(self):
        pass
        
    def queryCommands(self,timeout=-1):
        message = CommandMessage('query_commands','call')
        self.commandSocket.send(message.encodeCommand())
        if (self.commandSocket.poll(timeout,zmq.POLLIN)>0):
            reply = CommandReply.fromBytes(self.commandSocket.recv())
            if reply.success():
                return reply.payload()
            else:
                logging.error("")
                return None
    
        
    
