import BaseHTTPServer, sqlite3, os, json

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
		addresses = ""
		try:
			addresses = '{ "result": %s }' % json.dumps(get_address_list())
		except:
			addresses = '{ "error": { "code": 100, "message": "Address list not found."} }'	
		self.standard_header()
		self.wfile.write(addresses)

	def file_list(self):
		files = ""
		try:
			files = '{ "result": %s }' % json.dumps(get_file_list())
		except:
			files = '{ "error": { "code": 200, "message": "File list not found."} }'
		self.standard_header()			
		self.wfile.write(files)

	def search(self):
		keyword = "%" + self.path.replace("/search/", "") + "%"	
		connection = sqlite3.connect("database")
		cursor = connection.cursor()		
		files = dict()
		for row in cursor.execute("SELECT * FROM files WHERE filename LIKE ?", (keyword,)):
			files[row[0]] = row[1]
		connection.close()
		self.standard_header()		
		self.wfile.write('{ "result": %s }' % json.dumps(files))

	def download(self):
		filename = self.path.replace("/download/", "")
		try:
			f = open(filename, "r")
			self.download_header(filename)
			self.wfile.write(f.read())
			f.close()
		except:
			self.wfile.flush()
			self.standard_header()
			self.wfile.write('{ "error": { "code": 300, "message": "File not found."} }')	

	def error(self):
		self.standard_header()		
		self.wfile.write('{ "error": { "code": 400, "message": "Malformed URL." } }')

def get_address_list():
	connection = sqlite3.connect("database")
	cursor = connection.cursor()
	addresses = []
	for row in cursor.execute("SELECT * FROM addresses"):
		addresses.append(row[0])
	connection.close()
	return addresses
	
def add_address(address):
	connection = sqlite3.connect("database")
	cursor = connection.cursor()
	cursor.execute("INSERT INTO addresses VALUES (?)", (address,))
	connection.commit()
	connection.close()
	
def get_file_list():
	connection = sqlite3.connect("database")
	cursor = connection.cursor()
	files = dict()
	for row in cursor.execute("SELECT * FROM files"):
		files[row[0]] = row[1]
	connection.close()
	return files	
	
def add_files():
	connection = sqlite3.connect("database")
	cursor = connection.cursor()	
	
	for item in os.walk("."):
		for filename in item[2]:
			path = os.path.join(item[0], filename)
			cursor.execute("INSERT INTO files VALUES (?, ?)", (filename, path.replace("./", "")))
			
	connection.commit()
	connection.close()

def main():
	try:
		open("database", "r")
	except:
		connection = sqlite3.connect("database")
		cursor = connection.cursor()
		cursor.execute("CREATE TABLE addresses (address TEXT)")
		cursor.execute("CREATE TABLE files (filename TEXT, path TEXT)")
		connection.commit()
		connection.close()
		add_files()
	
	server = BaseHTTPServer.HTTPServer(("localhost", 8080), FileServer)
	
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass
		
	print
	
	server.server_close()

if __name__ == "__main__":
	main()