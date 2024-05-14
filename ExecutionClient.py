import logging
import threading
import os
import time 
import queue

import zmq

from CommandStatus import *
from CommandMessage import *
from EventMessage import *

class ExecutionClient(object):
    EVENT_POLL_TIMEOUT = 1 #in ms
    EVENT_DELAY_TIMEOUT = 1 #in ms
    COMMAND_REPLY_TIMEOUT = 500 #in ms
    COMMAND_RETIRES = 3

    HEARTBEAT_CHECK = 2000 #in ms (use more than for generation)
    
    def __init__(
        self,
        ipAddress, 
        commandPort: int, 
        dataPort: int, 
        serverPublicKey=None
    ):
        self.ipAddress = ipAddress
        self.commandPort = commandPort
        self.dataPort = dataPort
        self.serverPublicKey = serverPublicKey
        
        self.context = zmq.Context()
        self.commandSocket = self.context.socket(zmq.REQ)
        self.dataSocket = self.context.socket(zmq.SUB)
        
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
        
        self.eventConnectionReady = threading.Event()
        
        self.eventThread = threading.Thread(target=self._eventLoop, daemon=True)
        self.eventThread.start()
        
        self.commandQueue = queue.SimpleQueue()
        self.commandThreadReady = threading.Event()
        self.commandThread = threading.Thread(target=self._commandLoop, daemon=True)
        self.commandThread.start()
        
        message = CommandMessage('emit_event','call',config={'channel':'connection'})
        self.commandSocket.send(message.encodeCommand())
        self.commandSocket.recv()
        self.eventConnectionReady.wait()

    def _eventLoop(self):
        while True:
            
            if (self.dataSocket.poll(
                ExecutionClient.EVENT_POLL_TIMEOUT,
                zmq.POLLIN
            )>0):
                message = EventMessage.fromBytes(self.dataSocket.recv())
                print(f"received event on channel '{message.channel()}' with payload '{message.payload()}'")
                if message.channel()=='connection':
                    self.eventConnectionReady.set()
                
            #time.sleep(0.001*ExecutionClient.EVENT_DELAY_TIMEOUT)
            #self.eventThreadReady.set()
                
    def _commandLoop(self):
        while True:
            command = self.commandQueue.get()
            print ("proc",command.commandName())
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
    
        
    
