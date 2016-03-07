import cv2
import numpy
import itertools
from collections import deque
from PIL import Image
import asyncio


class CameraStream:
	def __init__(self, *args, **kwd):
		super().__init__()
		self.camera = cv2.VideoCapture(*args, **kwd)
		self.images = deque(maxlen=4)
		self.diffs = deque(maxlen=4)
		self.idx = 0
		self.diff_scale = 0.25

	def run(self):
		while True:
			retval, image = self.camera.read()
			image = image.astype(numpy.int16)
			if self.images:
				diff = numpy.abs(image - self.latest()).astype(numpy.uint8)
				diff = cv2.resize(diff, (int(diff.shape[1] * self.diff_scale), int(diff.shape[0] * self.diff_scale)))
				self.diffs.append(diff)

			self.images.append(image)
			self.idx += 1

	def latest(self):
		return self.images[-1]


def dist(a, b):
	return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

import io

master_images = {}
def image_callback(arg):
	if arg == 'mask':
		if not 'mask' in master_images:
			base = numpy.zeros_like(image_callback.g.clickers[0].detectors[0].mask, dtype=numpy.uint8)
			for d in image_callback.g.clickers[0].detectors:
				base[d.mask] = 255
			set_master_image('mask', base, True)

	return master_images[arg]
image_callback.save_images = False


def set_master_image(name, image, override=False):
	if not image_callback.save_images and not override:
		return
	image = image.astype(numpy.uint8)
	buff = io.BytesIO()
	if len(image.shape) == 3:
		b, g, r = image.transpose(2,0,1)
		image = numpy.array([r,g,b]).transpose(1,2,0)
	i = Image.fromarray(image)
	i.save(buff, format="PNG")
	master_images[name] = buff.getvalue()


def generate_mask(baseline, red, green, blue):
	set_master_image('baseline', baseline)
	set_master_image('red', red)
	set_master_image('green', green)
	set_master_image('blue', blue)
	baseline = baseline.transpose(2,0,1)

	params = cv2.SimpleBlobDetector_Params()
	params.minThreshold = 100
	params.maxThreshold = 255
	params.filterByArea = True
	params.filterByCircularity = True
	params.minCircularity = 0.4
	params.minArea = 60
	params.maxArea = 1000
	detector = cv2.SimpleBlobDetector_create(params)

	keypoints = []
	for idx, img in enumerate((blue, green, red)):
		img = img.transpose(2,0,1)
		diff = numpy.abs(img[idx] - baseline[idx]).astype(numpy.uint8)
		diff = numpy.full_like(diff, 255) - diff
		
		kp = detector.detect(diff)
		keypoints.append(kp)

		if image_callback.save_images:
			im_with_keypoints = cv2.drawKeypoints(diff, kp, numpy.array([]), (0,0,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
			set_master_image('diff{}'.format(idx), im_with_keypoints)

	try:
		unlikeness, keypoint = min( # find the set of three keypoints (one red, one green, one blue)
								    # which are most like each other. (Distance between centers and 
								    # approximate sizes are closest)
						            (dist(a.pt, b.pt) + dist(b.pt, c.pt) + 2*b.size - a.size - c.size, a)
						              for a, b, c in itertools.product(*keypoints)
					            )
	except ValueError:
		raise ValueError("probably a bad calibration run, no dots found")


	if unlikeness > 4:
		raise ValueError("probably a bad calibration run, differing dots found")

	return keypoint


class Clicker:
	def __init__(self, action, target, streams=[]):
		self.detectors = [Detector(stream) for stream in streams]
		self.target = target
		self.action = action

	async def train(self, root):
		self.target.hidden = False
		old_color = self.target.color

		colors = [(0,0,0), (1, 0, 0), (0, 1, 0), (0, 0, 1), None] # none is necessary to trip the last lines of the generators
		for color, *_ in zip(colors, *(d.train() for d in self.detectors)):
			self.target.color = color
			root.draw_interface()
			print("Drawing: ", color)
			await asyncio.sleep(0.5)

		self.target.hidden = True
		self.target.color = old_color
		root.draw_interface()

	def feed(self):
		if all(d.detect() for d in self.detectors):
			self.action(self)

from time import time
class Detector:
	def __init__(self, stream):
		self.stream = stream
		self.mask = None
		self.noise = None
		self.idx = 0

	def train(self):
		print("idx:",self.stream.idx)
		yield # wait for the interface to be ready
		print("idx:",self.stream.idx)
		baseline = self.stream.latest()
		print("idx:",self.stream.idx)
		print("took baseline")
		print("idx:",self.stream.idx)
		yield
		print("idx:",self.stream.idx)
		red = self.stream.latest()
		print("idx:",self.stream.idx)
		print("took red")
		print("idx:",self.stream.idx)
		yield
		print("idx:",self.stream.idx)
		green = self.stream.latest()
		print("idx:",self.stream.idx)
		print("took green")
		print("idx:",self.stream.idx)
		yield
		print("idx:",self.stream.idx)
		blue = self.stream.latest()
		print("idx:",self.stream.idx)
		print("took blue")
		print("idx:",self.stream.idx)
		keypoint = generate_mask(baseline, red, green, blue)
		s = (self.stream.diffs[0].shape[0],self.stream.diffs[0].shape[1])
		self.mask = numpy.fromfunction(lambda x,y: dist(keypoint.pt, (self.stream.diff_scale * y, self.stream.diff_scale * x)) < (self.stream.diff_scale * keypoint.size/2)**2, s)
		print("idx:",self.stream.idx)

	def detect(self):
		myidx = self.idx
		idx = self.stream.idx
		frames = []
		if idx > myidx:
			frames = list(self.stream.diffs)[myidx - idx:]

		hit = False
		for frame in frames:
			diff = frame[self.mask].sum()
			
			if not self.noise:
				self.noise = diff
			
			hit = diff > self.noise * 2
			self.noise = self.noise * .75 + diff * .25

		self.idx = idx
		return hit





















