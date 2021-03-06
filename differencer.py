from PIL import Image as PillowImage, ImageTk
import numpy
from math import ceil
import cv2
import asyncio
import itertools
from collections import namedtuple
from math import sqrt
from time import time


def dist(a, b):
	return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

def generate_mask(baseline, red, green, blue):
	cv2.imwrite("new_training/baseline.png", baseline.astype(numpy.uint8))
	cv2.imwrite("new_training/red.png", red.astype(numpy.uint8))
	cv2.imwrite("new_training/green.png", green.astype(numpy.uint8))
	cv2.imwrite("new_training/blue.png", blue.astype(numpy.uint8))
	baseline = baseline.transpose(2,0,1)

	params = cv2.SimpleBlobDetector_Params()
	params.minThreshold = 50;
	params.maxThreshold = 255;
	params.filterByArea = True
	params.minArea = 300
	params.maxArea = 1000
	detector = cv2.SimpleBlobDetector_create(params)

	keypoints = []
	for idx, img in enumerate((blue, green, red)):
		img = img.transpose(2,0,1)
		diff = numpy.abs(img[idx] - baseline[idx]).astype(numpy.uint8)
		diff = numpy.full_like(diff, 255) - diff
		keypoints.append(detector.detect(diff))
		print(keypoints)

	unlikeness, keypoint = min( # find the set of three keypoints (one red, one green, one blue)
							    # which are most like each other. (Distance between centers and 
							    # approximate sizes are closest)
					            (dist(a.pt, b.pt) + dist(b.pt, c.pt) + 2*b.size - a.size - c.size, a)
					              for a, b, c in itertools.product(*keypoints)
				            )

	if unlikeness > 4:
		raise ValueError("probably a bad calibration run")

	return numpy.fromfunction(lambda x,y: dist(keypoint.pt, (y, x)) < (keypoint.size/2)**2, diff.shape)

def async(func):
	asyncio.get_event_loop().run_in_executor(None, func)

class AsyncCamera():
	def __init__(self, *args, **kwd):
		self.camera = cv2.VideoCapture(*args, **kwd)

	async def read(self, *args, **kwd):
		while True:
			retval, image = await asyncio.get_event_loop().run_in_executor(None, self.camera.read,*args, **kwd)
			if retval:
				return image

	async def release(self, *args, **kwd):
		return await asyncio.get_event_loop().run_in_executor(None, self.camera.release,*args, **kwd)


Style = namedtuple("Style", "size color")
class CameraButton:
	class Presser:
		def __init__(self, parent):
			self.last_change = 0
			self.parent = parent
			self.is_active = False

		def check(self, images):
			def compute_diff(i, j):
				diff = j[self.mask] - i[self.mask]
				max_diff = numpy.abs(diff).astype(numpy.uint8)
				return max_diff.sum()
			first, *rest, last = images
			average_diff = sum(compute_diff(first, image) for image in rest) / len(rest)
			diff = compute_diff(first, last)
			hit = diff > average_diff * 3

			if main_window.clock % 15 == 0:
				print(self.parent.index, "avg:", average_diff, "frame:", diff)
			
			if self.last_change > 7:
				if hit != self.is_active:
					self.is_active = hit
					self.last_change = 0
					self.parent.press(hit)
			
			self.last_change += 1

	ON = "ON"
	OFF = "OFF"
	INVISIBLE = "INVISIBLE"
	def __init__(self, coords, canvas, on=Style(size=(100,100), color="#FF0000"), off=Style(size=(60,60), color="#00FF00")):
		self.coords = coords
		self.on = on
		self.off = off
		self.state = CameraButton.INVISIBLE
		self.canvas = canvas
		self.index = canvas.create_oval(*self.rect(off), fill="")
		self.presser = CameraButton.Presser(self)
		self.last_change = 0

	def rect(self, style):
		x, y = self.coords
		w, h = style.size
		w /= 2
		h /= 2
		return (x-w, y-h, x+w, y+h)

	def update(self):
		style = Style(color="", size=self.off.size)
		if self.state == CameraButton.ON:
			style = self.on
		if self.state == CameraButton.OFF:
			style = self.off
		self.canvas.itemconfig(self.index, fill=style.color)
		self.canvas.coords(self.index, *self.rect(style))

	def set_state(self, state):
		self.state = state
		self.update()

	def press(self, on):
		new_state = CameraButton.ON if on else CameraButton.OFF
		if new_state == CameraButton.OFF:
			return
		if self.state != CameraButton.INVISIBLE:
			self.set_state(new_state)

	def train(self, color):
		self.canvas.itemconfig(self.index, fill=color)

class Game():
	def __init__(self, canvas):
		self.camera = AsyncCamera(0)
		self.training_images = []
		self.canvas = canvas
		self.images = []
		self.image_backlog_size = 4
		self.buttons = []
		for x in range(7):
			xc = x * 150 + 100
			yc = (x-4) * (x-4) * 30 + 100
			self.buttons.append(CameraButton((xc,yc), canvas))


	async def train(self, button):
		await asyncio.sleep(0.3)
		baseline = await self.camera.read()
		button.train("#FF0000")
		await asyncio.sleep(0.3)
		red = await self.camera.read()
		button.train("#00FF00")
		await asyncio.sleep(0.3)
		green = await self.camera.read()
		button.train("#0000FF")
		await asyncio.sleep(0.3)
		blue = await self.camera.read()
		button.update()

		def cpu_bound():
			button.presser.mask = generate_mask(baseline, red, green, blue)

		await asyncio.get_event_loop().run_in_executor(None, cpu_bound)

	async def take_image(self):
		image = await self.camera.read()
		image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		# image = cv2.Canny(image, 170, 200)
		self.images.append(image.astype(numpy.int16))
		if len(self.images) > self.image_backlog_size:
			del self.images[0]

	async def get_images(self):
		while len(self.images) < self.image_backlog_size:
			await self.take_image()


from tkinter import *

def async_tkinter_runloop(root):
	root.should_quit = False
	def quit():
		root.should_quit = True
	root.createcommand('::tk::mac::Quit', quit)

	async def async_runloop(root, interval=0.05):
		try:
			while not root.should_quit:
				root.update()
				await asyncio.sleep(interval)
		except TclError as e:
			if "application has been destroyed" not in e.args[0]:
				raise
	asyncio.get_event_loop().run_until_complete(async_runloop(root))



def dist(a, b):
	return sqrt(((b-a)**2).sum())
def v(a):
	try:
		return numpy.array((a.x, a.y))
	except:
		return numpy.array(a)

class Window(Tk):
	async def startgame(self):
		for button in self.game.buttons:
			button.set_state(CameraButton.OFF)

		self.timer_hide()
		self.display("Press return to start training.")
		await self.wait_key("Return")
		self.display("Starting training in:")
		await asyncio.sleep(1)
		for x in range(3, 0, -1):
			self.display("{}   ".format(x))
			await asyncio.sleep(0.2)
			self.display("{}.  ".format(x))
			await asyncio.sleep(0.2)
			self.display("{}.. ".format(x))
			await asyncio.sleep(0.2)
			self.display("{}...".format(x))
			await asyncio.sleep(0.2)
		self.display("")

		for button in self.game.buttons:
			button.set_state(CameraButton.INVISIBLE)

		for button in self.game.buttons:
			await self.game.train(button)

		for button in self.game.buttons:
			button.set_state(CameraButton.OFF)
		while True:
			self.display("Press return to begin.")
			key = await self.wait_key("Return", "r")
			if key == "r":
				await self.startgame()
				return
			for button in self.game.buttons:
				button.set_state(CameraButton.OFF)
			self.display("")
			await self.game.get_images()
			self.timer_start()

			while True:
				out = self.game.images[-1].astype(numpy.uint8)
				for button in self.game.buttons:
					out[button.presser.mask] = 200
				# cv2.imshow("Stream", out)
				
				if self.clock % 15 == 0:
					print(chr(27) + "[2J")
				for button in self.game.buttons:
					button.presser.check(self.game.images)

				if all(button.state == CameraButton.ON for button in self.game.buttons):
					self.timer_stop()
					break

				await asyncio.sleep(0.05)
				await self.game.take_image()
				self.clock += 1

	def __init__(self):
		super().__init__()
		self.listening_for = set()
		self.dragging = False
		self.clock = 0
		canvas_width = 1500
		canvas_height = 940
		w = Canvas(self, 
		           width=canvas_width,
		           height=canvas_height)
		w.config(background='black')
		w.pack()
		self.message_text = w.create_text(canvas_width/2, canvas_height/2, text="",  font=("Helvetica", 100), fill="white")
		self.timer = w.create_text(canvas_width*0.15, canvas_height * 0.9, text="",  font=("Helvetica", 75), fill="white")
		self.timer_init = time()
		self.timergo = False

		self.game = Game(w)
		asyncio.ensure_future(self.startgame())
		asyncio.ensure_future(self.timer_loop())
		self.bind("<Key>", self.key_pressed)
		self.bind("<Button-1>", self.mouse_down)
		self.bind("<B1-Motion>", self.mouse_move)
		self.bind("<ButtonRelease-1>", self.mouse_up)

	async def wait_key(self, *keys):
		self.listening_for.update(keys)
		while True:
			for key in keys:
				if not key in self.listening_for:
					return key
			await asyncio.sleep(0.1)

	def display(self, message):
		self.game.canvas.itemconfig(self.message_text, text=message)

	def timer_display(self):
		self.game.canvas.itemconfig(self.timer, text="{:02.1f}".format(time() - self.timer_init))

	async def timer_loop(self):
		while True:
			if self.timergo:
				self.timer_display()
			await asyncio.sleep(0.1)


	def timer_start(self):
		self.timergo = True
		self.timer_init = time()

	def timer_stop(self):
		self.timergo = False

	def timer_hide(self):
		self.timergo = False
		self.game.canvas.itemconfig(self.timer, text="")

	def key_pressed(self, e):
		if e.keysym in self.listening_for:
			self.listening_for.remove(e.keysym)

	def mouse_down(self, e):
		e = v(e)
		for button in self.game.buttons:
			b = v(button.coords)
			if dist(b, e) < 30:
				self.dragging = (button, e-b)
				break

	def mouse_move(self, e):
		if self.dragging:
			e = v(e)
			b, diff = self.dragging
			b.coords = e - diff
			b.update()

	def mouse_up(self, e):
		self.dragging = False

main_window = Window()
async_tkinter_runloop(main_window)




