import urllib2, json

def main():
	files = urllib2.urlopen("http://localhost:8080/file_list")	
	file_list = json.loads(files.read())["result"]
	count = 0
	for key in file_list.keys():
		print key
	file_selection = raw_input("Select File: ")
	file_selection = file_list[file_selection]
	get_file = urllib2.urlopen("http://localhost:8080/download/%s" % file_selection)
	print get_file.read()

if __name__ == "__main__":
	main()