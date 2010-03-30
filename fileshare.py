import BaseHTTPServer
import urllib2
import sqlite3
import json
import sys
import os
import socket

class fileserver(BaseHTTPServer.BaseHTTPRequestHandler):
	def __init__(self, request, client_address, server):
		self.actions = {
			"/address_list": self.address_list,
			"/ping": self.ping,
			"/file_list": self.file_list,
			"/search": self.search,
			"/download": self.download		
		}
			
		try:
			address_file = open("addressses", "r")
			self.addresses = json.load(address_file)
		except:
			self.addresses = [socket.gethostname()]
			address_file = open("addresses" ,"w")
			address_file.write(json.dumps(self.addresses))
		finally:
			address_file.close()
		
		self.files = dict()
		
		for path, folders, files in os.walk("./"):
			for folder in folders:
				if folder.startswith("."):
					folders.remove(folder)
			for filename in files:
				self.files[filename] = [path, os.path.getsize(os.path.join(path, filename))]
		
		#print self.files		
		
		BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, client_address, server)
	
	def do_GET(self):
		print self.path		
		#try:
		#	self.actions[filter(lambda action: self.path.startswith(action), self.actions)[0]]()
		#except:
		#	self.error_header("Unknown action")
		self.actions[filter(lambda action: self.path.startswith(action), self.actions)[0]]()
		
	def standard_header(self, response):
		self.send_response(200)
		self.send_header("Content-Type", "text/html")
		self.end_headers()		
		self.wfile.write(response)
		
	def download_header(self, filepath):
		self.send_response(200)
		self.send_header("Content-Type", "application/octet-stream"); 
		self.send_header("Content-Type", "application/download"); 
		self.send_header("Content-Transfer-Encoding", "binary");
		self.send_header("Content-Disposition", "attachment; filename=%s" % os.path.basename(filepath))
		self.end_headers()
		
		try:
			f = open(filepath, "r")
			self.wfile.write(f.read())
		except:
			self.wfile.flush()
			self.error_header("File does not exist")
		finally:
			f.close()
		
	def error_header(self, message):				
		self.send_response(404)
		self.send_header("Content-Type", "text/html")
		self.end_headers()		
		self.wfile.write(json.dumps({ "error": message }))		

	def address_list(self):
		self.standard_header(json.dumps({ "result": self.addresses }))
		
	def ping(self):
		print "address =", self.client_address[0]
		self.add_address(self.client_address[0])
		self.standard_header("")			
		
	def file_list(self):
		self.standard_header(json.dumps({ "result": self.files }))
		
	def search(self):
		keyword = self.path.replace("/search/", "")
		self.standard_header(json.dumps({ "result": filter(lambda f: keyword in f, self.files) }))						
		
	def download(self):
		try:
			add_address(self.client_address[0])
			#print filename			
			fileitem = self.path.replace("/download/", "")
			filename = os.path.join(self.files[fileitem][0], fileitem)
			self.download_header(filename)
		except:
			self.wfile.flush()
			self.error_header("File does not exist")
	
	def add_address(self, address):
		if not address in self.addresses:
			self.addresses.append(address)
			f = open("addresses", "w")
			f.flush()
			f.write(json.dumps(self.addresses))
			f.close()
			
	def log_message(self, format, *args):
		print format % args
		
def main():
	server = BaseHTTPServer.HTTPServer((socket.gethostname(), 8080), fileserver)
	
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass
		
	print
	
	server.server_close()
				
if __name__ == "__main__":
	sys.exit(main())