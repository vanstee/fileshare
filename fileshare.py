import BaseHTTPServer
import urllib2
import sqlite3
import json
import sys
import os
import socket

class httpserver(BaseHTTPServer.HTTPServer):
	def __init__(self, server_address, RequestHandlerClass):
		self.actions = {
			"address_list": RequestHandlerClass.address_list,
			"ping": RequestHandlerClass.ping,
			"file_list": RequestHandlerClass.file_list,
			"search": RequestHandlerClass.search,
			"download": RequestHandlerClass.download		
		}	
			
		try:
			address_file = open("addressses", "r")
			self.log_message("Opening address list")			
			self.addresses = json.load(address_file)
		except:
			self.log_message("Creating address list")
			self.addresses = [socket.gethostname()]
			address_file = open("addresses" ,"w")
			address_file.write(json.dumps(self.addresses))
		finally:
			self.log_message("Loaded address list")			
			address_file.close()
		
		self.files = dict()
		
		self.log_message("Creating file list")
		
		for path, folders, files in os.walk("./"):
			for folder in folders:
				if folder.startswith("."):
					folders.remove(folder)
			for filename in files:
				self.files[filename] = [path, os.path.getsize(os.path.join(path, filename))]
				
		self.log_message("Loaded file list")
		
		self.log_message("Fileserver started")	
		
		BaseHTTPServer.HTTPServer.__init__(self, server_address, RequestHandlerClass)	
		
	def log_message(self, format, *args):
		print format % args

class fileserver(BaseHTTPServer.BaseHTTPRequestHandler):
	def __init__(self, request, client_address, server):
		BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, client_address, server)
	
	def do_GET(self):
		key = self.path.split("/")[1]
		
		self.log_message("%s requested", key)		
		
		if key in self.server.actions:
			self.server.actions[key](self)
		else:
			self.error_header("Unknown action")
		
		
		#self.actions[filter(lambda action: self.path.startswith(action), self.actions)[0]]()
		
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
		self.standard_header(json.dumps({ "result": self.server.addresses }))
		
	def ping(self):
		print "address =", self.client_address[0]
		self.add_address(self.client_address[0])
		self.standard_header("")			
		
	def file_list(self):
		self.standard_header(json.dumps({ "result": self.server.files }))
		
	def search(self):
		keyword = self.path.replace("/search/", "")
		self.standard_header(json.dumps({ "result": filter(lambda f: keyword in f, self.server.files) }))						
		
	def download(self):
		try:
			add_address(self.client_address[0])
			#print filename			
			fileitem = self.path.replace("/download/", "")
			filename = os.path.join(self.server.files[fileitem][0], fileitem)
			self.download_header(filename)
		except:
			self.wfile.flush()
			self.error_header("File does not exist")
	
	def add_address(self, address):
		if not address in self.server.addresses:
			self.log_message("Adding %s to address list", address)
			self.server.addresses.append(address)
			self.log_message("Saving address list")			
			try:
				f = open("addresses", "w")
				f.flush()
				f.write(json.dumps(self.server.addresses))
				f.close()
				self.log_message("Saved address list")				
			except:
				self.log_message("Could not save address list")
			
	def log_message(self, format, *args):
		print format % args
		
def main():
	server = httpserver((socket.gethostbyname(socket.gethostname()), 8080), fileserver)
	
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass
		
	print
	
	server.server_close()
				
if __name__ == "__main__":
	sys.exit(main())