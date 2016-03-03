from graphics import Ellipse, Rectangle, View, Shape, RootView, Label
from time import time
import asyncio
from http_server import start_application
from detection import Detector, CameraStream, image_callback
from threading import Thread


class Timer:
	def __init__(self):
		self.v = Label("", loc=(0,0), color=(1,1,1), font_size=200)
		self.children = [self.v]
		self.time = 0
		self.start()
		self.value = 0

	def update(self):
		if self.is_counting:
			self.value = time() - self.time
			self.v.text = "{:.1f}".format(self.value)

	def start(self):
		self.time = time()
		self.is_counting = True

	def stop(self):
		self.is_counting = False


class Game:
	def __init__(self, root):
		self.root = root
		self.dots = [Ellipse(color=(1,1,1), loc=(root.width - (x + 1) * root.width / 11, ((x/5 - 1) ** 2) * root.height * .75), size=(40,40)) for x in range(11)]
		self.detectors = [Detector(d, self.detector_fired) for d in self.dots]
		self.timer = Timer()
		root.children = self.dots + [self.timer]
		self.camera = CameraStream(0)
		self.state = 0

	def detector_fired(self, detector):
		print("Detector Fired: ", self.detectors.index(detector))

	async def callback(self, data):
		if data['cmd'] == 'save_images':
			image_callback.save_images = data['arg']
		if data['cmd'] == 'start':
			self.root.io_loop.create_task(self.main())
		if data['cmd'] == 'stop':
			await self.stop()
		if data['cmd'] == 'train':
			await self.train()

	async def main(self):
		self.timer.start()
		self.state = 1
		while self.state == 1:
			for detector in self.detectors:
				detector.detect(self.camera)
			await asyncio.sleep(0.01)

	async def stop(self):
		self.state = 0
		self.timer.stop()

	async def train(self):
		self.state = 2
		for child in self.root.children:
			child.hidden = True

		try:
			for detector in self.detectors:
				await detector.train(self.root, self.camera)
		finally:
			for child in self.root.children:
				child.hidden = False

if __name__ == '__main__':
	root = RootView()
	g = Game(root)
	Thread(target=g.camera.run).start()

	root.io_loop.call_soon(root.master_loop)
	start_application(g.callback, image_callback)










