import time

from ExecutionClient import *
from ExecutionServer import *


publicKeyServer, privateKeyServer = zmq.curve_keypair()

server = ExecutionServer(
    commandPort='3333',
    monitorPort='3334', 
    #allowedIpAdresses='127.0.0.1', 
    publicKey=publicKeyServer, 
    privateKey=privateKeyServer
)
server.registerCommand(LoadCommand())

client = ExecutionClient(
    ipAddress='127.0.0.1', 
    commandPort='3333', 
    monitorPort='3334', 
    serverPublicKey=publicKeyServer
)

server.emitEvent("blub".encode('utf-8'))
time.sleep(1)
