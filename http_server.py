from aiohttp import web

async def handle_main(request):
    return web.Response(body=b"""<html>
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

async def handle_images(request):
	image = request.match_info.get('image', "baseline")
	return web.Response(content_type="image/png",body=self.server.image_callback(image))

async def handle_image(request):
	return web.Response(body=b"""<html>
				<img src="image/baseline" />
				<img src="image/red" />
				<img src="image/green" />
				<img src="image/blue" />
	</html>""")

async def handle_message(request):
	print(request.match_info.get('message', "no message here"))
	data = json.loads(urllib.parse.unquote(self.path[len(prefix):]))
	asyncio.ensure_future(self.server.callback(data))
	return web.Response(body=b'success')

app = web.Application()
app.router.add_route('GET', '/', handle_main)
app.router.add_route('GET', '/images', handle_images)
app.router.add_route('GET', '/image/{image}', handle_image)
app.router.add_route('GET', '/message/{message}', handle_message)
web.run_app(app, port=8000)
