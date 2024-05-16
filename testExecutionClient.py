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

client.addDataListener("test",handleOutput)
time.sleep(0.1)
server.sendData("test",{})



'''
for _ in range(10):
    client.sendCommand('test','call',callbackFunction=handleOutput)
'''
#time.sleep(5)


'''
server.registerSpawnCommand(ShellCommand(
    name = 'list_dir',
    description = 'list directory',
    command = ['ls','-lh'],
))








print(client.queryCommands())




#time.sleep(1)
'''
