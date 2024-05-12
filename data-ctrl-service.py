import zmq

CTRL_PORT = 3333
DATA_PORT = 3334
#IP = "10.254.56.35"

IP = "localhost"

context = zmq.Context()
print ("Connecting to server...")
ctrl_socket = context.socket(zmq.REQ)
ctrl_socket.connect(f"tcp://{IP}:{CTRL_PORT}")

data_socket = context.socket(zmq.SUB)
data_socket.connect(f"tcp://{IP}:{DATA_PORT}")
data_socket.setsockopt(zmq.SUBSCRIBE,b"")



for request in range (1,10):
    print ("Sending request ", request,"...")
    ctrl_socket.send("Hello".encode('utf-8'))
    
    while (data_socket.poll(0,zmq.POLLIN)>0):
        message = data_socket.recv().decode('utf-8')
        print('data',message)
    
    #  Get the reply.
    message = ctrl_socket.recv().decode('utf-8')
    print("Received reply ", request, "[", message, "]")
    

print ("Sending request ", request,"...")
ctrl_socket.send("load_fw".encode('utf-8'))

while (data_socket.poll(1,zmq.POLLIN)>0):
    message = data_socket.recv(flags=zmq.NOBLOCK).decode('utf-8')
    print('data',message)
    
message = ctrl_socket.recv().decode('utf-8')
print("Received reply ", request, "[", message, "]")

while (data_socket.poll(1,zmq.POLLIN)>0):
    message = data_socket.recv(flags=zmq.NOBLOCK).decode('utf-8')
    print('>>>',message)
