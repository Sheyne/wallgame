import numpy as np
import cairocffi as cairo
from cairotft import linuxfb

def rect_inset(rect, amt):
    rect = np.array(rect)
    rect[0] += amt
    rect[1] -= 2 * amt
    return rect

def rect_corners(rect):
    x,y = rect[0,]
    w,h = rect[1,]
    return [(x,y), (x+w,y), (x, y+h), (x+w,y+h)]


class Display:
    def __init__(self, interface='/dev/fb0', cairo_format=cairo.FORMAT_RGB16_565):
        if hasattr(interface, "memory"):
            self.memory = linuxfb.memory_buffer(interface.memory.fix_info.smem_len)
            self.surface = linuxfb.cairo_surface_from_fbmem(interface.memory, self.memory, cairo_format)
        else:
            self.memory = linuxfb.open_fbmem(interface)
            self.surface = linuxfb.cairo_surface_from_fbmem(self.memory, self.memory.mmap, cairo_format)

        self.width, self.height = self.surface.get_width(), self.surface.get_height()
        self.context = cairo.Context(self.surface)

    def draw_display(self, display):
        self.context.set_source_surface(display.surface)
        self.context.paint()

    def draw_point(self, point, color=(1,1,1)):
        ctx = self.context
        ctx.set_source_rgb(*color)
        ctx.arc(*point, 15, 0, 2 * pi)
        ctx.fill()

    def draw_points(self, pts, color=(1,1,1)):
        for pt in pts:
            self.draw_point(pt, color)


    def blank(self):
        self.context.set_source_rgb(0,0,0)
        self.context.rectangle(0, 0, self.width, self.height)
        self.context.fill()