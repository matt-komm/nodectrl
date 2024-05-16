import time

from ExecutionClient import *
from ExecutionServer import *

from DataMessage import *
import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)-8s: %(message)s [%(filename)s:%(lineno)d]")

context1 = zmq.Context()
publicKeyServer, privateKeyServer = zmq.curve_keypair()

server = ExecutionServer(
    context1,
    commandPort='3333',
    dataPort='3334', 
    publicKey=publicKeyServer, 
    privateKey=privateKeyServer
)

def callCmd(config, arguments):
    print ("calling",config,arguments)
    return {"awesome":1}

server.registerCallCommand(CallCommand('testCallCmd',callCmd))
server.serve()

context2 = zmq.Context()
client = ExecutionClient(
    context2,
    ipAddress='127.0.0.1', 
    commandPort='3333', 
    dataPort='3334', 
    serverPublicKey=publicKeyServer
)
client.connect()

def handleOutput(message: DataMessage):
    print("handling data message ",message)
    return False #kills thread

reply = client.sendCommand(
    commandName='testCallCmd',
    commandType='call',
    config={"testenv":"/home"},
    arguments=["blub;"],
    callbackFunction=handleOutput
)
print (reply)