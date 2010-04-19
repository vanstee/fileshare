import BaseHTTPServer
import urllib2
import json
import sys
import os
import socket
import threading
import SocketServer
import Queue

class httpserver(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
	def __init__(self, server_address, RequestHandlerClass):
		BaseHTTPServer.HTTPServer.__init__(self, server_address, RequestHandlerClass)		
		
		self.actions = {
			"address_list": RequestHandlerClass.address_list,
			"ping": RequestHandlerClass.ping,
			"file_list": RequestHandlerClass.file_list,
			"search": RequestHandlerClass.search,
			"download": RequestHandlerClass.download,
			"ajax":	RequestHandlerClass.ajax,
			"ajaxbrowse": RequestHandlerClass.ajaxbrowse,
			"ajaxsearch": RequestHandlerClass.ajaxsearch,
		}

		temp_addresses = []
		self.addresses = []
		try:
			address_file = open("addresses", "r")
			self.log_message("Opening address list")      
			temp_addresses = json.loads(address_file.read())
			self.log_message("Loaded address list") 						
		except:
			self.log_message("Creating address list")

		while not self.addresses:
			if not temp_addresses:
				print 'Address list is empty.'
				valid_address = False
				while not valid_address:
					address = raw_input("Please enter server address: ")
					url = urllib2.urlopen("http://%s:8080/address_list" % address, timeout=5)
					temp_addresses = json.loads(url.read())["result"]
					url.close()
					valid_address = True
					
					#try:
					#	url = urllib2.urlopen("http://%s:8080/address_list" % address, timeout=5)
					#	temp_addresses = json.loads(url.read())["result"]
					#	url.close()
					#	valid_address = True
					#except:
					#	print "Invalid address."
					#	pass

			for address in temp_addresses:
				try:
					url = urllib2.urlopen("http://%s:8080/ping" % address, timeout=5)
					url.close()
					self.addresses.append(address)
				except:
					self.log_message("Removing %s" % address)
			temp_addresses = []
		
		address_file = open("addresses" ,"w")
		address_file.flush()
		address_file.write(json.dumps(self.addresses))
		
		self.files = {}
		
		self.log_message("Creating file list")		
		
		for path, folders, files in os.walk("./"):
			for folder in folders:
				if folder.startswith("."):
					folders.remove(folder)
			for filename in files:
				self.files[filename] = [socket.gethostbyname(socket.gethostname()), path, os.path.getsize(os.path.join(path, filename))]
				
		self.log_message("Loaded file list")
		
		self.log_message("Fileserver started")
		
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
		self.send_response(200)
		self.send_header("Content-Type", "text/html")
		self.end_headers()		
		self.wfile.write(json.dumps({ "error": message }))		

	def address_list(self):
		address = self.client_address[0]
		addresses = self.server.addresses[:]
		addresses.append(socket.gethostbyname(socket.gethostname()))
		if address in addresses:
			addresses.remove(address)
		self.standard_header(json.dumps({ "result": addresses }))
		
	def ping(self):
		address = self.client_address[0]
		print "address =", address
		self.add_address(address)
		self.standard_header("")
		
	def file_list(self):
		self.standard_header(json.dumps({ "result": self.server.files }))
		
	def search(self):
		keyword = self.path.replace("/search/", "")
		found = []
		for file in self.server.files:
			if keyword in file:
				found.append([file, self.server.files[file][0], self.server.files[file][2]])
		self.standard_header(json.dumps({ "result": found }))						
		
	def download(self):
		try:		
			fileitem = self.path.replace("/download/", "")
			#print self.server.files
			filename = os.path.join(self.server.files[fileitem][0], fileitem)
			self.download_header(filename)
		except:
			self.wfile.flush()
			self.error_header("File does not exist")
			
	def ajax(self):
		try:
			f = open("index.html", "r")
			self.standard_header(f.read())
			f.close()
		except:
			self.err_header("Ajax interface not available")
			
	def ajaxbrowse(self):
		try:
			url = urllib2.urlopen("http://%s:8080/file_list" % self.path.replace("/ajaxbrowse/", ""), timeout=5)
			self.standard_header(url.read())
			url.close()
		except:
			self.error_header("Server not available.")
	
	def ajaxsearch(self):
		queue = Queue.Queue(0)
		
		for address in self.server.addresses:
			queue.put(address)
		
		consumer_list = []
		results = []
		
		for i in range(10):
			consumer_list.append(search_consumer(queue, self.path.replace("/ajaxsearch/", ""), results))
			
		for consumer_thread in consumer_list:
			consumer_thread.start()	
		
		for consumer_thread in consumer_list:
			consumer_thread.join()
			
		self.standard_header(json.dumps({"result": results}))
	
	# Bugzilla
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
		
class server(threading.Thread):
	def __init__(self):
		self.server = httpserver((socket.gethostbyname(socket.gethostname()), 8080), fileserver)
		threading.Thread.__init__(self)
	
	def run(self):
		try:
			self.server.serve_forever()
		except Exception:
			pass
			
class search_consumer(threading.Thread):
	def __init__(self, queue, filename, results):
		threading.Thread.__init__(self)
		self.queue = queue
		self.filename = filename
		self.results = results

	def run(self):
		while not self.queue.empty():
			address = self.queue.get()
			request = None
			try:
				request = urllib2.urlopen("http://%s:8080/search/%s" % (address, self.filename), timeout=5)
				self.results += json.loads(request.read())["result"]
			except:
				print "Searching %s failed" % address
				pass
					
class client(threading.Thread):
	def __init__(self):
		self.actions = {
			"address_list": self.address_list,
			"browse": self.browse,
			"search": self.search,
			"download": self.download,
			"help": self.help,
			"exit": self.exit
		}
		
		self.running = True
		
		self.server_thread = server()
		self.server_thread.start()
		
		threading.Thread.__init__(self)
		
	def run(self):
		action = ""
		while action != "exit":
			input = raw_input().split(" ")
			action = input[0]
			if action in self.actions:
				self.actions[action](input[1:])
			else:
				print "Try 'help' for more information."
				
	def address_list(self, args):
		print "Address list:"
		for address in self.server_thread.server.addresses:
			print address

	def browse(self, args):
		try:
			url = urllib2.urlopen("http://%s:8080/file_list" % args[0], timeout=5)
			result = json.loads(url.read())["result"]
			for key in result:
				print key, result[key][0], result[key][2]
		except:
			print "Invalid server address"
	
	def search(self, args):
		queue = Queue.Queue(0)
		
		for address in self.server_thread.server.addresses:
			queue.put(address)
		
		consumer_list = []
		results = []
		
		for i in range(10):
			consumer_list.append(search_consumer(queue, args[0], results))
			
		for consumer_thread in consumer_list:
			consumer_thread.start()	
		
		for consumer_thread in consumer_list:
			consumer_thread.join()
			
		print results
	
	def download(self, args):
		try:
			get_file = urllib2.urlopen("http://%s:8080/download/%s" % (args[0], args[1]), timeout=5)
			new_file = open(args[1], "w")
			new_file.flush()
			new_file.write(get_file.read())
			new_file.close()
		except:
			print 'Error during download.\n', 'Please check that the server address and file name are correct.'
			

	def help(self, args):
		print """
Actions:
	
USAGE: address_list
Display the list of known server addresses.

USAGE: browse [server_address]
Display the file list for the specified server.
EXAMPLE: browse 127.0.0.1

USAGE: search [keyword] [server_address]
Search for a specified keyword. If no server_address is given all known servers will be searched.
EXAMPLE: search cats
EXAMPLE: search cats 127.0.0.1

USAGE: download [server_address] [filename]
Download a file from the specified server.
EXAMPLE: download 127.0.0.1 cats.jpg
"""

	def exit(self, args):
		print "server stopped"
		self.server_thread.server.server_close()
		self.server_thread.join()
	
def main():
	client_thread = client()
	client_thread.start()
	client_thread.join()
				
if __name__ == "__main__":
	sys.exit(main())