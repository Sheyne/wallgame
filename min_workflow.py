import numpy as np
from math import pi
from new_detect import find_locations, dist
import cv2
from time import time, sleep
from multiprocessing import Process, sharedctypes
from graphics import *
import ctypes
from collections import namedtuple

frame_buffer = Display()
display = Display(frame_buffer)

frame_buffer.blank()
display.blank()

camera = cv2.VideoCapture(1)

frame = [(0,0), (display.width, display.height)]
points = rect_corners(rect_inset(frame, 15))

real_locations = find_locations(frame_buffer, camera, points, 4)

# sc = 0.2
# height = int(display.height * sc)
# width = int(display.width * sc)

# raw_image = sharedctypes.RawArray(ctypes.c_ubyte, height * width * 4)
# drawing = np.frombuffer(raw_image, dtype=np.uint8)
# drawing.shape = (height, width, 4)
# surf = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height, raw_image)

# drawing[:,:] = (0, 0, 0xff,0)
# display.ctx_main.scale(1/sc)

# def draw_drawing():
#     while True:
#         display.ctx_main.set_source_surface(surf)
#         display.ctx_main.paint()

# Process(target=draw_drawing).start()

# def get_an_image():
#     _, img = camera.read()
#     return cv2.flip(img, 0)

# camera_space = np.array([real_locations[point][0] for point in points],np.float32)

# projector_space = np.array(points,np.float32)
# projector_space *= sc

# trans = cv2.getPerspectiveTransform(camera_space, projector_space)

# for _ in range(10):
#     get_an_image()
# an_img = get_an_image()

# prev_image = cv2.warpPerspective(get_an_image(), trans, (int(display.width * sc), int(display.height * sc)))
# while True:
#     img = get_an_image()
#     img =  cv2.warpPerspective(img, trans, (int(display.width * sc), int(display.height * sc)))
#     diffs = (cv2.absdiff(img, prev_image).sum(-1).astype(np.uint16) / 3).astype(np.uint8)
    
#     drawing[diffs > 30] = (0, 0, 0, 0)

#     prev_image = img




