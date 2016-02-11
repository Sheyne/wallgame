from PIL import Image as PillowImage, ImageTk
import numpy
from math import ceil
import cv2
import asyncio
from itertools import combinations
from collections import namedtuple
from math import sqrt

def ceil_range(a, pad=10):
	return int(ceil(a/pad) * pad)

def pad(a, pad=10):
	l = len(a)
	nl = ceil_range(l, pad)
	return numpy.append(a, numpy.zeros(nl - l, dtype=numpy.int))

def intervals(l):
    for length in range(1, l+1):
        for idx in range(0, l-length+1):
            yield slice(idx, idx+length)

def bucketize(a, bucket_size):
	a = pad(a, bucket_size)
	return a.reshape((len(a)/bucket_size, bucket_size)).sum(axis=-1)

def offset_slice(sl, offset):
	return slice(sl.start + offset, sl.stop + offset)

def expand_slice(sl, fraction):
	o = sl.stop - sl.start
	d = int((o/fraction - o)/2)
	return slice(max(sl.start - d, 0), sl.stop + 2 * d)

def find_range(a, most, bucket_size):
	buckets = bucketize(a, bucket_size)
	for i in intervals(len(buckets)):
		if buckets[i].sum() > most:
			return slice(i.start * bucket_size, i.stop * bucket_size)
	return False

def find_box(a, bucket_size=None, mosts=[0.5, 0.7, 0.95, 0.99, 0.99, 0.99, 0.99, 0.99], depth=0):
	most = numpy.sum(a) * mosts[depth]
	if bucket_size == None:
		bucket_size = int(min(*a.shape)/5)
	s1 = find_range(numpy.sum(a, axis=1), most=most, bucket_size=bucket_size)
	s2 = find_range(numpy.sum(a, axis=0), most=most, bucket_size=bucket_size)
	s1 = expand_slice(s1, mosts[depth])
	s2 = expand_slice(s2, mosts[depth])
	if bucket_size > 10:
		s1b, s2b = find_box(a[s1,s2], int(bucket_size / 2), depth=depth+1)
		return offset_slice(s1b, s1.start), offset_slice(s2b, s2.start)
	return s1, s2

def compute_mask(diff):
	box = find_box(diff)
	i, j = box
	rx = (i.stop - i.start)/ 2
	ry = (j.stop - j.start)/ 2
	h = i.start + rx
	k = j.start + ry
	return numpy.fromfunction(lambda i, j: (i-h)**2/rx**2 + (j-k)**2/ry**2 <= 1, diff.shape[:2], dtype=numpy.int)

def multi_masks(baseline, red, green, blue):	
	baseline = baseline.transpose(2,0,1).astype(numpy.int16)

	for channel, color in enumerate((blue, green, red)):
		color = color.astype(numpy.int16)
		diff = color.transpose(2,0,1)[channel] - baseline[channel]
		diff[diff < 20] = 0
		yield compute_mask(diff.astype(numpy.uint8))

def async(func):
	asyncio.get_event_loop().run_in_executor(None, func)

class AsyncCamera():
	def __init__(self, *args, **kwd):
		self.camera = cv2.VideoCapture(*args, **kwd)

	async def read(self, *args, **kwd):
		return await asyncio.get_event_loop().run_in_executor(None, self.camera.read,*args, **kwd)

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

			if clock % 15 == 0:
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
		retval, baseline = await self.camera.read()
		button.train("#FF0000")
		await asyncio.sleep(0.3)
		retval, red = await self.camera.read()
		button.train("#00FF00")
		await asyncio.sleep(0.3)
		retval, green = await self.camera.read()
		button.train("#0000FF")
		await asyncio.sleep(0.3)
		retval, blue = await self.camera.read()
		button.update()

		def cpu_bound():
			a,b,c = (a & b for (a,b) in combinations(multi_masks(baseline, red, green, blue), 2))
			button.presser.mask = a | b | c

		await asyncio.get_event_loop().run_in_executor(None, cpu_bound)

	async def take_image(self):
		retval, image = await self.camera.read()
		image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		# image = cv2.Canny(image, 170, 200)
		self.images.append(image.astype(numpy.int16))
		if len(self.images) > self.image_backlog_size:
			del self.images[0]

	async def get_images(self):
		while len(self.images) < self.image_backlog_size:
			await self.take_image()

start = False
clock = 0

def key_pressed(e):
	global start
	start = True

def dist(a, b):
	return sqrt(((b-a)**2).sum())

def v(a):
	try:
		return numpy.array((a.x, a.y))
	except:
		return numpy.array(a)

dragging = False
def mouse_down(game, e):
	global dragging
	e = v(e)
	for button in game.buttons:
		b = v(button.coords)
		if dist(b, e) < 30:
			dragging = (button, e-b)
			break

def mouse_move(g, e):
	if dragging:
		e = v(e)
		b, diff = dragging
		b.coords = e - diff
		b.update()

def mouse_up(g, e):
	global dragging
	dragging = False

async def startgame(game):
	global clock
	for button in game.buttons:
		button.set_state(CameraButton.OFF)

	while not start:
		await asyncio.sleep(0.1)
	print("Starting training in ")
	for x in range(5, 0, -1):
		print(x)
		await asyncio.sleep(1)

	for button in game.buttons:
		button.set_state(CameraButton.INVISIBLE)

	for button in game.buttons:
		await game.train(button)

	for button in game.buttons:
		button.set_state(CameraButton.OFF)

	await game.get_images()

	while True:
		out = game.images[-1].astype(numpy.uint8)
		for button in game.buttons:
			out[button.presser.mask] = 200
		cv2.imshow("Stream", out)
		
		if clock % 15 == 0:
			print(chr(27) + "[2J")
		for button in game.buttons:
			button.presser.check(game.images)

		await asyncio.sleep(0.05)
		await game.take_image()
		clock += 1


from tkinter import *
from functools import partial

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



master = Tk()
canvas_width = 1500
canvas_height = 940
w = Canvas(master, 
           width=canvas_width,
           height=canvas_height)
w.config(background='black')
w.pack()
game = Game(w)
asyncio.ensure_future(startgame(game))
master.bind("<Key>", key_pressed)
master.bind("<Button-1>", partial(mouse_down, game))
master.bind("<B1-Motion>", partial(mouse_move, game))
master.bind("<ButtonRelease-1>", partial(mouse_up, game))
async_tkinter_runloop(master)




