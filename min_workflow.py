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

points = [[randint(50, display.width - 50), randint(50, display.height-50)] for _ in range(10)]

trans = get_projector_transform(display, camera, scale=1, invert=True)
# trans = np.array([[  1.00000000e+00,   1.27675648e-15,  -7.49400542e-15],
#        [  3.77475828e-15,   1.00000000e+00,  -7.16093851e-15],
#        [  2.48412402e-15,   1.02695630e-15,   1.00000000e+00]])

import reloadable
while True:
	importlib.reload(reloadable)
	print("launching")
	try:
		reloadable.magic_function(points, trans, buff, display, camera, g=globals())
	except:
		traceback.print_exc()


