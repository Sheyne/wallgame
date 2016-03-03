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
		self.images = deque(maxlen=10)
		self.idx = 0

	def run(self):
		while True:
			self.idx += 1
			retval, image = self.camera.read()
			self.images.append(image)

	def latest(self):
		return self.images[-1]

def dist(a, b):
	return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

import io

master_images = {}
def image_callback(arg):
	return master_images[arg]

def set_master_image(name, image):
	buff = io.BytesIO()
	if len(image.shape) == 3:
		b,g,r = image.transpose(2,0,1)
		image = numpy.array([r,g,b]).transpose(1,2,0)
	i = Image.fromarray(image)
	i.save(buff, format="PNG")
	master_images[name] = buff.getvalue()

def generate_mask(baseline, red, green, blue):
	# set_master_image('baseline', baseline)
	# set_master_image('red', red)
	# set_master_image('green', green)
	# set_master_image('blue', blue)
	baseline = baseline.astype(numpy.int16).transpose(2,0,1)

	params = cv2.SimpleBlobDetector_Params()
	params.minThreshold = 100;
	params.maxThreshold = 255;
	params.filterByArea = True
	params.minArea = 100
	params.maxArea = 1000
	detector = cv2.SimpleBlobDetector_create(params)

	keypoints = []
	for idx, img in enumerate((blue, green, red)):
		img = img.astype(numpy.int16).transpose(2,0,1)
		diff = numpy.abs(img[idx] - baseline[idx]).astype(numpy.uint8)
		diff = numpy.full_like(diff, 255) - diff
		
		kp = detector.detect(diff)
		keypoints.append(kp)

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

	return numpy.fromfunction(lambda x,y: dist(keypoint.pt, (y, x)) < (keypoint.size/2)**2, diff.shape)


class Detector:
	def __init__(self, target, action):
		self.target = target
		self.action = action

	async def train(self, root, camera):
		async def refresh():
			root.draw_interface()		
			await asyncio.sleep(0.3)
		
		await refresh()
		baseline = camera.latest()
		
		self.target.hidden = False
		old_color = self.target.color

		self.target.color = (1, 0, 0)
		
		await refresh()
		red = camera.latest()
		self.target.color = (0, 1, 0)
		root.draw_interface()		

		await refresh()
		green = camera.latest()
		self.target.color = (0, 0, 1)
		root.draw_interface()		

		await refresh()
		blue = camera.latest()

		self.target.hidden = True
		self.target.color = old_color
		root.draw_interface()		

		self.mask = generate_mask(baseline, red, green, blue)

	def clear(self):
		self.is_fired = False

	def feed(self, image_stream):
			def compute_diff(i, j):
				diff = j[self.mask] - i[self.mask]
				max_diff = numpy.abs(diff).astype(numpy.uint8)
				return max_diff.sum()
			first, *rest, last = images
			average_diff = sum(compute_diff(first, image) for image in rest) / len(rest)
			diff = compute_diff(first, last)
			hit = diff > average_diff * 3
			if hit:
				self.action(self)





















