from graphics import Ellipse, Rectangle, View, Shape, RootView, Label
from time import time
import asyncio
from http_server import Server
from detection import Detector, CameraStream, image_callback
from threading import Thread
class Timer:
	def __init__(self):
		self.v = Label("", loc=(0,0), color=(1,1,1), font_size=200)
		self.children = [self.v]
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

	def detector_fired(self, detector):
		print(self.detectors.find(detector))

	def callback(self, data):
		if data == 'start':
			await self.main()
		if data == 'stop':
			await self.stop()
		if data == 'train':
			await self.train()

	def main(self):
		self.timer.start()

	def stop(self):
		self.timer.stop()

	def train(self):
		for child in self.root.children:
			child.hidden = True
		
		for detector in self.detectors:
			detector.train(self.root, self.camera)

		for child in self.root.children:
			child.hidden = False
		



if __name__ == '__main__':
	disp = RootView()
	g = Game(disp)
	s = Server(disp.io_loop, g.callback, image_callback)
	disp.io_loop.call_soon(s.handle_request)
	Thread(target=g.camera.run).start()
	disp.run()










