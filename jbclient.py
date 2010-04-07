mport socket, subprocess


HOST = 'spider6.cs.clemson.edu'
PORT = 2345

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST,PORT))

command = client.recv(4096)
client.close()

#client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#client.connect(('gecko3.cs.clemson.edu', 2345))

servers = command.split("\n");
print servers
for x in servers:
    print x
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    a = client.connect_ex((x, PORT))
    if a != 0:
        servers.remove(x)
    client.close()

print servers