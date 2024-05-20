import time

from ExecutionClient import *
from ExecutionServer import *

from DataMessage import *
from ShellCommand import *

import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)-8s: %(message)s [%(filename)s:%(lineno)d]")

context1 = zmq.Context()
#publicKeyServer, privateKeyServer = zmq.curve_keypair()

publicKeyServer = b'm5+^m7-0)#^xl*hC5JJ=y-?>(7dd$:vOPv0M+8V?'
privateKeyServer = b'yh$aDehg7+c0(HZn^xwc/$tg(O?IR/fOVJXiSqJq'


server = ExecutionServer(
    context1,
    commandPort='3333',
    dataInputPort='3334',
    dataOutputPort='3335',
    internalDataInputAddress='tcp://127.0.0.1:3336',
    internalDataOutputAddress='tcp://127.0.0.1:3337',
    publicKey=publicKeyServer, 
    privateKey=privateKeyServer
)

def callCmd(inputAddress, outputAddress, channel, config, arguments):
    print ("calling",channel,config,arguments)
    contextCallCmd = zmq.Context()
    dataSocket2 = contextCallCmd.socket(zmq.PUB)
    dataSocket2.connect(outputAddress)

    heartbeatSocket = contextCallCmd.socket(zmq.SUB)
    heartbeatSocket.connect(inputAddress)
    heartbeatSocket.setsockopt(zmq.SUBSCRIBE,DataMessage.encodedChannel('heartbeat'))
    if heartbeatSocket.poll(ExecutionClient.TIMEOUT, zmq.POLLIN):
        heartbeatSocket.recv()
    #can just send output regardless of heartbeat will only loose messages to client but not kill process

    #time.sleep(0.2) #need to wait for subscription to propage :-(
    for i in range(10):
        dataSocket2.send(DataMessage(channel,{"fromData":i}).encode())

    #time.sleep(1)
    return {"awesome":1}

server.registerCallCommand(CallCommand('testCallCmd',callCmd))
server.registerSpawnCommand(ShellCommand('listdir',['ls']))
server.serve()
#time.sleep(1)
