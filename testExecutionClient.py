import time

from ExecutionClient import *
from ExecutionServer import *

from ShellCommand import *

import logging
logging.basicConfig(level=logging.DEBUG)

context = zmq.Context()
publicKeyServer, privateKeyServer = zmq.curve_keypair()

server = ExecutionServer(
    context,
    commandPort='3333',
    dataPort='3334', 
    publicKey=publicKeyServer, 
    privateKey=privateKeyServer
)
server.serve(True)


client = ExecutionClient(
    context,
    ipAddress='127.0.0.1', 
    commandPort='3333', 
    dataPort='3334', 
    serverPublicKey=publicKeyServer
)
client.connect(True)
for _ in range(10):
    client.sendCommand(CommandMessage('test','call').encode())

time.sleep(5)
'''
server.registerSpawnCommand(ShellCommand(
    name = 'list_dir',
    description = 'list directory',
    command = ['ls','-lh'],
))






print(client.queryCommands())




#time.sleep(1)
'''