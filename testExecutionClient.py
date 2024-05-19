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
    dataInputPort='3334', 
    dataOutputPort='3335',
    publicKey=publicKeyServer, 
    privateKey=privateKeyServer
)

def callCmd(channel, config, arguments):
    print ("calling",channel,config,arguments)
    contextCallCmd = zmq.Context()
    print("sending to channel ",channel)
    dataSocket2 = contextCallCmd.socket(zmq.PUB)
    dataSocket2.connect("ipc://dataServerOutput")
    time.sleep(0.2) #need to wait for subscription to propage :-(
    for i in range(10):
        dataSocket2.send(DataMessage(channel,{"fromData":i}).encode())

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
    dataInputPort='3334', 
    dataOutputPort='3335',
    serverPublicKey=publicKeyServer
)
client.connect()


def printHearbeat(message: DataMessage, *args):
    print (message)
    return True

#client.addDataListener('heartbeat',printHearbeat)
#server.addDataListener('heartbeat',printHearbeat)

#time.sleep(1)

'''
def handleOutput(message: DataMessage):
    print("handling data message ",message)
    #time.sleep(1)
    return True #kills thread

reply = client.sendCommand(
    commandName='testCallCmd',
    commandType='call',
    config={"testenv":"/home"},
    arguments=["blub;"],
    callbackFunction=handleOutput
)
print (reply)
'''
time.sleep(1)