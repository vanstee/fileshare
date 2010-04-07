#!/usr/bin/env python

import SocketServer, socket


class connHandle(SocketServer.BaseRequestHandler):

    def handle(self):
        f = open('servers.txt', 'r')

        conn = socket.gethostbyname(socket.gethostname())
        servers = f.read()
        servers += conn
        self.request.send(servers)
        print "DONE"
        self.request.close()

if __name__ == "__main__":
    HOST, PORT = "spider6.cs.clemson.edu", 2345
    server = SocketServer.TCPServer((HOST, PORT