import time
import logging
import threading

import zmq
from zmq.auth.thread import ThreadAuthenticator

from HeartbeatGenerator import *


class ExecutionServer(object):    
    HEARTBEAT_GENERATION = 500 #in ms

    def __init__(
        self, 
        commandPort: int,
        monitorPort: int, 
        allowedIpAdresses=None, 
        publicKey=None, 
        privateKey=None
    ):
        self.commandPort = commandPort
        self.monitorPort = monitorPort
        self.allowedIpAdresses = allowedIpAdresses
        self.publicKey = publicKey
        self.privateKey = privateKey
        
        self.registeredCommands = {}
        self.runningCommands = []
    
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
        
        
        self.cmdSocket.bind(f"tcp://*:{self.commandPort}")
        self.dataSocket.bind(f"tcp://*:{self.monitorPort}")
        
        self.commandThread = threading.Thread(target=self._commandLoop, daemon=True)
        self.commandThread.start()
        
        self.heartbeat = HeartbeatGenerator(
            intervalInMS = ExecutionServer.HEARTBEAT_GENERATION,
            callbackFunction=lambda: self.dataSocket.send("heartbeat".encode('utf-8'))
        )
        
    def _commandLoop(self):
        while True:
            message = self.commandSocket.recv().decode('utf-8')
            print("rec:",message)
            time.sleep(0.4)
            self.commandSocket.send("OK".encode("utf-8"))
        
    def emitEvent(self,event):
        self.heartbeat.resetHeartbeatTimestamp()
        self.dataSocket.send(event)
        
    def registerCommand(self,command):
        if command.name not in self.registeredCommands.keys():
            self.registeredCommands[command.name] = command
        
        
        
