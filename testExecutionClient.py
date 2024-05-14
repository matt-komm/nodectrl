import time

from ExecutionClient import *
from ExecutionServer import *

from ShellCommand import *

publicKeyServer, privateKeyServer = zmq.curve_keypair()

server = ExecutionServer(
    commandPort='3333',
    monitorPort='3334', 
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
    monitorPort='3334', 
    serverPublicKey=publicKeyServer
)
for _ in range(10):
    client.sendCommand(CommandMessage('test','spawns'))

print(client.queryCommands())

'''
server.emitEvent("blub".encode('utf-8'))
time.sleep(1)
'''