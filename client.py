import zmq

msgToSend = "FROM KARL-VIRTUALBOX-WORK-LAPTOP"

context = zmq.Context()
socket = context.socket(zmq.PUSH)

socket.connect("tcp://0.0.0.0:5000")

# print the message size in bytes
print len(msgToSend)

socket.send(msgToSend)

print "Sent message"
