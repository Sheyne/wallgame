import cairocffi as cairo
from cairotft import linuxfb
from random import randint
import numpy as np
from math import pi
from new_detect import find_locations, dist
import cv2

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

    def blank(self):
        self.context.set_source_rgb(0,0,0)
        self.context.rectangle(0, 0, self.width, self.height)
        self.context.fill()
        self.dump_buffer()


display = Display()
display.blank()

camera = cv2.VideoCapture(0)


points = [(randint(15, display.width - 15),randint(500, display.height - 15)) for _ in range(3)]
real_locations = find_locations(display, camera, points)

masks = {}

scale_factor = 0.4

def get_an_image():
    _, img = camera.read()
    img = cv2.resize(img, (int(img.shape[1] * scale_factor), int(img.shape[0] * scale_factor)))
    img = img.astype(np.int16)
    return img

an_img = get_an_image()


for point, ((x, y), size) in real_locations.items():
    x *= scale_factor
    y *= scale_factor
    size *= scale_factor
    masks[point] = np.fromfunction(lambda i,j, _: dist((y, x), (i,j)) < (size/2)**2, an_img.shape)

cv2.imwrite("an_img.png", an_img)
for point, mask in masks.items():
    cv2.imwrite("{}-{}-mask.png".format(*point), mask.astype(np.uint8) * 0xff)

while True:
    for x,y in points:
        display.draw_point(x,y)

    display.dump_buffer()


    noises = {}
    prev_frame = None
    idx = 0

    hits = set()
    while len(hits) < len(points):
        img = get_an_image()
        if prev_frame is not None:
            diff = np.abs(img - prev_frame)

            for point, mask in masks.items():
                volume = diff[mask].sum()
                if idx > 0:
                    if idx > 10 and volume > noises[point] * 1.5:
                        display.draw_point(*point, (1,0,0))
                        display.dump_buffer()
                        hits.add(point)

                    noises[point] = noises[point] * .75 + volume * .25
                else:
                    noises[point] = volume

            idx += 1

        prev_frame = img

