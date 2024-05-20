import time

from ExecutionClient import *
from ExecutionServer import *

from DataMessage import *
import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)-8s: %(message)s [%(filename)s:%(lineno)d]")

publicKeyServer = b'm5+^m7-0)#^xl*hC5JJ=y-?>(7dd$:vOPv0M+8V?'

context2 = zmq.Context()
client = ExecutionClient(
    context2,
    ipAddress='127.0.0.1',
    commandPort='3333',
    dataInputPort='3334',
    dataOutputPort='3335',
    internalDataInputAddress='tcp://127.0.0.1:3338',
    internalDataOutputAddress='tcp://127.0.0.1:3339',
    serverPublicKey=publicKeyServer
)
client.connect()

'''
def printHearbeat(message: DataMessage, *args):
    print (message)
    return True

client.addDataListener('heartbeat',printHearbeat)
server.addDataListener('heartbeat',printHearbeat)
'''
#time.sleep(1)


def handleOutput(message: DataMessage):
    print("handling data message ",message)
    payload = message.payload()
    if 'stdout' in payload.keys():
        print (payload['stdout'])
    if 'stderr' in payload.keys():
        print (payload['stderr'])
    if 'terminated' in payload.keys():
        print ("Process terminated with status",payload['terminated'])
        return False
    return True 

reply = client.sendCommand(
    commandName='listdir',
    commandType='spawn',
    config={},
    arguments=[],
    callbackFunction=handleOutput
)
print (reply)
'''
while True:
    input("press to send command")

    reply = client.sendCommand(
        commandName='testCallCmd',
        commandType='call',
        config={"testenv":"/home"},
        arguments=["blub;"],
        callbackFunction=handleOutput
    )
    print (reply)

time.sleep(1)
'''