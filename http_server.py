from aiohttp import web
import json
import urllib

async def handle_main(request):
    return web.Response(body=b"""<html>
	<script>
	function send_message(o){
		var xmlhttp = new XMLHttpRequest();
		xmlhttp.open("GET", '/message/'+encodeURI(JSON.stringify(o)), true);
		xmlhttp.send();
	}
	</script>

	<input type="button" onclick="send_message({cmd:'start'})" value="Start"/><br />
	<input type="button" onclick="send_message({cmd:'stop'})" value="Stop"/><br />
	<input type="button" onclick="send_message({cmd:'train'})" value="Train"/><br />
	<input type="button" onclick="send_message({cmd:'save_images', arg: false})" value="Dont"/>
	<input type="button" onclick="send_message({cmd:'save_images', arg: true})" value="Save Images"/><br />

	</html>""")

async def handle_image(request):
	image = request.match_info.get('image', "baseline")
	return web.Response(content_type="image/png",body=request.app.image_callback(image))

async def handle_images(request):
	return web.Response(body=b"""<html>
				<img src="image/baseline" />
				<img src="image/red" />
				<img src="image/green" />
				<img src="image/blue" />
	</html>""")

async def handle_message(request):
	message = request.match_info.get('message')
	data = json.loads(urllib.parse.unquote(message))
	await request.app.callback(data)
	return web.Response(body=b'success')

app = web.Application()
app.router.add_route('GET', '/', handle_main)
app.router.add_route('GET', '/images', handle_images)
app.router.add_route('GET', '/image/{image}', handle_image)
app.router.add_route('GET', '/message/{message}', handle_message)

def start_application(callback, image_callback):
	app.callback = callback
	app.image_callback = image_callback
	web.run_app(app, port=8000)
