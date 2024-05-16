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

def callCmd(context, channel, config, arguments):
    print ("calling",channel,config,arguments)
    #contextCallCmd = zmq.Context()
    print("sending to channel ",channel)
    
    #time.sleep(1)
    return {"awesome":1}

server.registerCallCommand(CallCommand('testCallCmd',callCmd))
server.serve()
#time.sleep(1)

context2 = zmq.Context()
client = ExecutionClient(
    context2,
    ipAddress='127.0.0.1', 
    commandPort='3333', 
    dataPort='3334', 
    serverPublicKey=publicKeyServer
)
client.connect()
#time.sleep(1)

def handleOutput(message: DataMessage):
    print("handling data message ",message)
    return True #kills thread

def testCallback(message: DataMessage):
    print ('recv test callback: ',message)
    return True

client.addDataListener('testCallback',testCallback)
server.sendData('testCallback',{})

reply = client.sendCommand(
    commandName='testCallCmd',
    commandType='call',
    config={"testenv":"/home"},
    arguments=["blub;"],
    callbackFunction=handleOutput
)
print (reply)