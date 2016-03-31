import numpy as np
from new_detect import find_locations, dist, get_projector_transform
import cv2
from time import time, sleep
from multiprocessing import Process, sharedctypes
from graphics import *
import ctypes
from collections import namedtuple
import numpy as np
from random import randint
import importlib
import traceback

camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
camera.set(cv2.CAP_PROP_FPS, 10)
camera.set(cv2.CAP_PROP_CONTRAST, 1)
camera.set(cv2.CAP_PROP_BRIGHTNESS, 0)
camera.set(cv2.CAP_PROP_SATURATION, 1)


display = Display()
buff = Display(display)

buff.blank()

points = [[randint(200, 500), randint(200, 500)] for _ in range(10)]

trans = get_projector_transform(display, camera, scale=1, invert=True)

import reloadable
while True:
	importlib.reload(reloadable)
	print("launching")
	try:
		reloadable.magic_function(points, trans, buff, display, camera, g=globals())
	except:
		traceback.print_exc()


