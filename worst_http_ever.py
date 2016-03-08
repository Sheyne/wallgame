import http.server
import socketserver
import json
from urllib.parse import unquote
from multiprocessing import Process, Queue

class Handler (http.server.BaseHTTPRequestHandler):
	def log_message(self, *args): pass

	def do_GET(self):
		job, *json_data = self.path.split("?", 2)
		job = job[1:]
		data = None
		if len(json_data):
			data = json.loads(unquote(json_data[0]))
		q.put((job, data))
		# self.send_header("content-type", "text/plain")
		# self.send_header("Access-Control-Allow-Origin", "*")
		# self.end_headers()
		self.wfile.write(b"")

socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("", 8001), Handler)

q = Queue()
p = Process(target=httpd.serve_forever, args=(q,))
p.start()
while 1:
	print(q.get())