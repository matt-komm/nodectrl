import zmq
import logging
import threading

class ExecutionClient(object):
    EVENT_LOOP_TIMEOUT = 10 #in ms
    COMMAND_REPLY_TIMEOUT = 500 #in ms
    COMMAND_RETIRES = 3

    HEARTBEAT_CHECK = 600 #in ms (use 3x more than for generation)
    
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
        
        self.commandQueue = []
        self.commandQueueLock = threading.Lock()
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
            self.commandSocket.send("Hello".encode('utf-8'))
            if (self.commandSocket.poll(ExecutionClient.COMMAND_REPLY_TIMEOUT,zmq.POLLIN)>0):
                message = self.commandSocket.recv().decode('utf-8')
                print ("Command executed:",message)
            else:
                print ("Command lost")
                #TODO: check heartbeat

    def sendCommand(self,command):
        outputProcess, writeOutput = os.pipe() 
        readInput, inputProcess = os.pipe() 
        with self.commandQueueLock:
            self.commandQueue.append(command)
        commandStatus = CommandStatus(inputProcess,outputProcess)
        return commandStatus
        
    def onEvent(self):
        pass
        
    def queryCommands(self):
        pass
    
        
    
