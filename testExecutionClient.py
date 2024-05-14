import time

from ExecutionClient import *
from ExecutionServer import *

from ShellCommand import *

publicKeyServer, privateKeyServer = zmq.curve_keypair()

server = ExecutionServer(
    commandPort='3333',
    dataPort='3334', 
    #allowedIpAdresses='127.0.0.1', 
    publicKey=publicKeyServer, 
    privateKey=privateKeyServer
)
'''
server.registerSpawnCommand(ShellCommand(
    name = 'list_dir',
    description = 'list directory',
    command = ['ls','-lh'],
))
'''
client = ExecutionClient(
    ipAddress='127.0.0.1', 
    commandPort='3333', 
    dataPort='3334', 
    serverPublicKey=publicKeyServer
)
#time.sleep(0.1)



print(client.queryCommands())




time.sleep(1)
