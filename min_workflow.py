import cairocffi as cairo
from cairotft import linuxfb
from random import randint
import numpy as np
from math import pi
from new_detect import find_locations, dist
import cv2
from time import time, sleep
from multiprocessing import Process, sharedctypes
import ctypes

class Display:
    def __init__(self, interface='/dev/fb0', cairo_format=cairo.FORMAT_RGB16_565):
        fbmem = linuxfb.open_fbmem(interface)
        self.surf = linuxfb.cairo_surface_from_fbmem(fbmem,fbmem.mmap,cairo_format)

        self.width, self.height = self.surf.get_width(), self.surf.get_height()

        buffermem = linuxfb.memory_buffer(fbmem.fix_info.smem_len)
        self.buffer_surf = linuxfb.cairo_surface_from_fbmem(fbmem, buffermem, cairo_format)
        
        self.ctx_main = cairo.Context(self.surf)
        self.context = cairo.Context(self.buffer_surf)

    def dump_buffer(self):
        self.ctx_main.set_source_surface(self.buffer_surf)
        self.ctx_main.paint()

    def draw_point(self, x, y, color=(1,1,1), immediately=False):
        ctx = self.ctx_main if immediately else self.context
        ctx.set_source_rgb(*color)
        ctx.arc(x,y, 15, 0, 2 * pi)
        ctx.fill()

    def blank(self, dump=True):
        self.context.set_source_rgb(0,0,0)
        self.context.rectangle(0, 0, self.width, self.height)
        self.context.fill()
        if dump:
            self.dump_buffer()


display = Display()
display.blank()

camera = cv2.VideoCapture(1)

def draw_points(pts, color=(1,1,1)):
    for x,y in pts:
        display.draw_point(x,y, color)



display.blank()

inset = 15

points = [(inset, inset), (display.width-inset, inset), (inset, display.height-inset), (display.width-inset, display.height-inset)]

real_locations = find_locations(display, camera, points, 4)

real_locations[points[1]], real_locations[points[3]] = real_locations[points[3]], real_locations[points[1]]

print(real_locations)

sc = 0.2
height = int(display.height * sc)
width = int(display.width * sc)

raw_image = sharedctypes.RawArray(ctypes.c_ubyte, height * width * 4)
drawing = np.frombuffer(raw_image, dtype=np.uint8)
drawing.shape = (height, width, 4)
surf = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height, raw_image)

drawing[:,:] = (0, 0, 0xff,0)
display.ctx_main.scale(1/sc)

def draw_drawing():
    while True:
        display.ctx_main.set_source_surface(surf)
        display.ctx_main.paint()

Process(target=draw_drawing).start()

def get_an_image():
    _, img = camera.read()
    return cv2.flip(img, 0)

camera_space = np.array([real_locations[point][0] for point in points],np.float32)

projector_space = np.array(points,np.float32)
projector_space *= sc

trans = cv2.getPerspectiveTransform(camera_space, projector_space)

for _ in range(10):
    get_an_image()
an_img = get_an_image()

prev_image = cv2.warpPerspective(get_an_image(), trans, (int(display.width * sc), int(display.height * sc)))
while True:
    img = get_an_image()
    img =  cv2.warpPerspective(img, trans, (int(display.width * sc), int(display.height * sc)))
    diffs = (cv2.absdiff(img, prev_image).sum(-1).astype(np.uint16) / 3).astype(np.uint8)
    
    drawing[diffs > 30] = (0, 0, 0, 0)

    prev_image = img




