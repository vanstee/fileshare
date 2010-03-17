import BaseHTTPServer, sqlite3, traceback, sys

class FileServer(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_GET(self):		
		action = {
			"/address_list": self.address_list,
			"/file_list": self.file_list,
			"/search": self.search,
			"/download": self.download
		}
		
		for key in action:
			if self.path.startswith(key):
				action.get(key)()
				
	def standard_header(self):
		self.send_response(200)
		self.send_header("Content-Type", "text/html")
		self.end_headers()
		
	def download_header(self, filename):
		self.send_response(200)
		self.send_header("Content-Type", "application/octet-stream"); 
		self.send_header("Content-Type", "application/download"); 
		self.send_header("Content-Transfer-Encoding", "binary"); 
		self.send_header("Content-Disposition", "attachment; filename=%s" % filename)

	def address_list(self):
		self.standard_header()
		addresses = ""
		try:
			addresses = '{ "result": [ %s ] }' % get_address_list()
		except:
			addresses = '{ "error": { "code": 100, "message": "Address list not found."} }'	
		self.wfile.write(addresses)

	def file_list(self):
		self.standard_header()
		files = ""
		try:
			f = open("file_list.json", "r")
			files = '{ "result": %s }' % f.read()
			f.close()
		except:
			addresses = '{ "error": { "code": 200, "message": "File list not found."} }'
		self.wfile.write(files)

	def search(self):
		self.standard_header()		
		self.wfile.write('{ "result": { } }')

	def download(self):
		filename = "../" + self.path.replace("/download/", "")
		try:
			f = open(filename, "r")
			self.download_header(filename)
			self.wfile.write(f.read())
			f.close()
		except:
			traceback.print_exc(file=sys.stdout)
			self.standard_header()
			self.wfile.write('{ "error": { "code": 300, "message": "File not found."} }')	

	def error(self):
		self.standard_header()		
		self.wfile.write('{ "error": { "code": 400, "message": "Malformed URL." } }')

def get_address_list():
	connection = sqlite3.connect("database")
	cursor = connection.cursor()
	addresses = ",".join(' "' + str(row[0]) + '"' for row in cursor.execute("SELECT * FROM addresses"))
	connection.close()
	return addresses
	
def add_address(address):
	connection = sqlite3.connect("database")
	cursor = connection.cursor()
	cursor.execute("INSERT INTO addresses VALUES (?)", (address,))
	connection.commit()
	connection.close()

if __name__ == '__main__':
	try:
		open("database", "r")
	except:
		connection = sqlite3.connect("database")
		cursor = connection.cursor()
		cursor.execute("CREATE TABLE addresses (address TEXT)")
		connection.commit()
		connection.close()

	add_address("1.2.3.4")
	add_address("2.3.4.5")
	add_address("3.4.5.6")	
	
	server = BaseHTTPServer.HTTPServer(("localhost", 8080), FileServer)
	
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass
		
	print
	
	server.server_close()