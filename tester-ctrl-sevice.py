import sys
import os
import time
import logging
import subprocess
import threading


sys.path.append('/home/matthias/.local/lib/python3.10/site-packages')


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        stream=sys.stdout,
        format="%(levelname)s > %(message)s [%(asctime)s, thread=%(threadName)s, %(filename)s:%(lineno)d]",
        datefmt="%H:%M:%S"
    )
    
    logging.info("START")
    
    
if __name__ == '__main__':
    main()

'''

import zmq


CTRL_PORT = 3333
DATA_PORT = 3334

context = zmq.Context()
ctrl_socket = context.socket(zmq.REP)
ctrl_socket.bind("tcp://*:%s" % CTRL_PORT)

data_socket = context.socket(zmq.PUB)
data_socket.bind("tcp://*:%s" % DATA_PORT)




while True:
    message = ctrl_socket.recv().decode('utf-8')
    print ("Received request: ", message)
    
    if message=="load_fw":
        print ("loading FW")
        proc = subprocess.Popen(
            #['fw-loader','load','tileboard-tester-v2p0'],
            ['/media/matthias/MadMax/Projects/tester-ctrl/cmdRoot.sh'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            #shell=True
        )
        os.set_blocking(proc.stdout.fileno(), False)
        os.set_blocking(proc.stderr.fileno(), False)
        
        while proc.poll() is None:
        
            line = proc.stdout.readline()
            while len(line)>0:
                print ("PROC OUT",line)
                data_socket.send(line)
                line = proc.stdout.readline()
                
            line = proc.stderr.readline()
            while len(line)>0:
                print ("PROC ERR",line)
                data_socket.send(line)
                line = proc.stderr.readline()
        
        print ("PROC TERMINATED",proc.returncode)
        
        line = proc.stdout.readline()
        while len(line)>0:
            print ("PROC OUT",line)
            data_socket.send(line)
            line = proc.stdout.readline()
            
        line = proc.stderr.readline()
        while len(line)>0:
            print ("PROC ERR",line)
            data_socket.send(line)
            line = proc.stderr.readline()
        
        
    
    ctrl_socket.send("ACK".encode('utf-8'))
    
    #data_socket.send("processing".encode('utf-8'))
'''
    
