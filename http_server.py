import http.server
import socketserver
import urllib.parse
import json
import asyncio

class Handler(http.server.BaseHTTPRequestHandler):
	def log_message(self, format, *args):
		return

	def write_html(self, txt):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(txt)

	def do_GET(self):
		if self.path.startswith("/image/"):
			self.send_response(200)
			self.send_header("Content-type", "image/png")
			self.end_headers()
			self.wfile.write(self.server.image_callback(self.path[len("/image/"):]))
			return

		prefix = '/message?'
		if self.path == "/":
			self.write_html(b"""<html>
	<script>
	function send_message(o){
		var xmlhttp = new XMLHttpRequest();
		xmlhttp.open("GET", '/message?'+encodeURI(JSON.stringify(o)), true);
		xmlhttp.send();
	}
	</script>

	<input type="button" onclick="send_message('start')" value="Start"/><br />
	<input type="button" onclick="send_message('stop')" value="Stop"/><br />
	<input type="button" onclick="send_message('train')" value="Train"/><br />

	</html>""")
		elif self.path == "/image":
			self.write_html(b"""<html>
				<img src="image/baseline" />
				<img src="image/red" />
				<img src="image/green" />
				<img src="image/blue" />
	</html>""")

		elif self.path.startswith(prefix):
			self.write_html(b"")
			data = json.loads(urllib.parse.unquote(self.path[len(prefix):]))
			asyncio.ensure_future(self.server.callback(data))

class Server:
	def __init__(self, loop, callback, image_callback):
		socketserver.TCPServer.allow_reuse_address = True
		self.httpd = socketserver.TCPServer(("", 8000), Handler)
		self.httpd.loop = loop
		self.httpd.callback = callback
		self.httpd.image_callback = image_callback
		self.httpd.serve_forever()
	
	async def handle_request(self):
		self.httpd.handle_request()
	
