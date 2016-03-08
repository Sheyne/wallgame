import cairocffi as cairo
from cairotft import linuxfb
from random import randint
import numpy as np
from math import pi
from new_detect import find_locations, dist
import cv2
from time import time, sleep

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

camera = cv2.VideoCapture(0)

def draw_points(pts, color=(1,1,1)):
    for x,y in pts:
        display.draw_point(x,y, color)



display.blank()

inset = 15

points = [(inset, inset), (display.width-inset, inset), (inset, display.height-inset), (display.width-inset, display.height-inset)]

real_locations = find_locations(display, camera, points, 2)

print(real_locations)

display.context.set_source_rgb(1,0.4,0.4)
display.context.set_line_width(3)
display.context.move_to(0,0)
display.context.line_to(display.width,display.height)
display.context.move_to(0,display.height)
display.context.line_to(display.width,0)
display.context.move_to(0,0)
display.context.line_to(display.width,0)
display.context.move_to(0,0)
display.context.line_to(0,display.height)
display.context.move_to(0,display.height)
display.context.line_to(display.width,display.height)
display.context.move_to(display.width,display.height)
display.context.line_to(display.width,0)
display.context.stroke()

display.dump_buffer()

def get_an_image():
    _, img = camera.read()
    return img

camera_space = np.array([real_locations[point][0] for point in points],np.float32)

projector_space = np.array(points,np.float32)
sc = 0.5
projector_space *= sc

trans = cv2.getPerspectiveTransform(camera_space, projector_space)

for _ in range(10):
    get_an_image()
an_img = get_an_image()

t = time()
for x in range(10):
    an_img = get_an_image()
    out = cv2.warpPerspective(an_img, trans, (int(display.width * sc), int(display.height * sc)))
print((time() - t)/10)




