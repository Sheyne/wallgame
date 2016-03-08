import cairocffi as cairo
from cairotft import linuxfb
from random import randint
import numpy as np
from math import pi
from new_detect import find_locations, dist
import cv2
import worst_http_ever
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


q = {}
while True:

    def sider():
        if 'location' not in q:
            return
        locs = q['location']
        points = [(int(loc[0] * display.width), int(loc[1] * display.height)) for k, loc in locs.items()]
        display.blank(False)
        for x,y in points:
            display.draw_point(x,y)

        display.dump_buffer()

    worst_http_ever.http_waiter(q, sider)
    
    locs = q['location']
    points = [(loc[0] * display.width, loc[1] * display.height) for k, loc in locs.items()]

    display.blank()
    if 'redo' in q:
        real_locations = find_locations(display, camera, points)

    masks = {}

    scale_factor = 0.6

    def get_an_image():
        _, img = camera.read()
        img = cv2.resize(img, (int(img.shape[1] * scale_factor), int(img.shape[0] * scale_factor)))
        img = img.astype(np.int16)
        return img

    an_img = get_an_image()

    for point, ((x, y), size) in real_locations.items():
        x *= scale_factor
        y *= scale_factor
        size *= scale_factor / 2
        area = (slice(y-size,y+size), slice(x-size, x+size))

        masks[point] = area

    for x,y in points:
        display.draw_point(x,y)

    display.dump_buffer()

    while 1:
        noises = {}
        prev_frame = None
        idx = 0
        t = time()
        hits = set()
        while True:
            display.blank(False)
            with display.context:
                display.context.set_source_rgb(1,1,1)
                display.context.move_to(10, 110)
                display.context.set_font_size(100)
                display.context.show_text("{:.2f}".format(time()-t))
            draw_points(points)
            draw_points(hits, color=(0,0,1))
            display.dump_buffer()
            if len(hits) == len(points):
                sleep(2)
                break
            img = get_an_image()
            if prev_frame is not None:
                diff = np.abs(img - prev_frame)

                for point, mask in masks.items():
                    volume = diff[mask].sum()
                    if idx > 0:
                        if idx > 20 and volume > noises[point] * 2.4:
                            hits.add(point)

                        noises[point] = noises[point] * .75 + volume * .25
                    else:
                        noises[point] = volume

                idx += 1
            prev_frame = img
