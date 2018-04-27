import numpy as np
import cairocffi as cairo
from cairotft import linuxfb
from math import pi
from time import time

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

def animate(t, keypoints):
    """
    Given a keypoint mapping `keypoints' give the value of the animation at timestep `t'.
    The keypoint mapping maps times to values

    >>> animate(0, {0: 1, 2:5, 3: 6})
    1
    >>> animate(2, {0: 1, 2:5, 3: 6})
    5
    >>> animate(3, {0: 1, 2:5, 3: 6})
    6
    >>> animate(2.5, {0: 1, 2:5, 3: 6})
    5.5
    >>> animate(7, {0: 1, 2:5, 3: 6})
    6
    """
    points = sorted(keypoints)
    prev = None
    for point in points:
        if point >= t:
            if prev == None:
                prev = point
            t1, e1, t2, e2 = prev, keypoints[prev], point, keypoints[point]
            break
        prev = point
    else:
        t1, e1, t2, e2 = prev, keypoints[prev], prev,keypoints[prev]

    if t1 == t2:
        t = 0
    else:
        t = (t - t1) / (t2 - t1)
    return e1 + (e2 - e1) * t

class Window:
    def __init__(self, display, helpers=set()):
        self.raw_display = display
        self.buffer = Display(display)
        self.helpers = set(helpers)

    def render(self, t):
        self.buffer.blank()
        for helper in self.helpers:
            helper.render(self.buffer, t)

    def dump_buffer(self):
        self.raw_display.draw_display(self.buffer)

    def draw(self):
        self.render(time())
        self.dump_buffer()

class Dot:
    def __init__(self, pt, text=""):
        self.pt = pt
        self.start = False
        self.r_animation = {0: 15, 0.12: 15 * 1.7, 0.3: 15 * 0.8}
        self.color_animation = {0: np.array((0,0,1)), 0.1: np.array((1,1,0)), 0.3: np.array((.4,.4,1))}
        self.font_size_animation = {0: 28, 0.12: 28 * 1.7, 0.3: 28 * 0.8}
        self.font_color_animation = {0: 1, 0.3: 0}
        self.label = Label(pt, text=text, center=True)

    def hit(self):
        self.start = True

    def reset(self):
        self.start = False

    def render(self, d, t):
        if self.start is False:
            t = 0
        elif self.start is True:
            self.start = t
        else:
            t -= self.start
        ctx = d.context
        with ctx:
            c = animate(t, self.color_animation)
            r = animate(t, self.r_animation)
            ctx.set_source_rgb(*c)
            ctx.arc(*self.pt, r, 0, 2 * pi)
            ctx.fill()
        self.label.font_size = animate(t, self.font_size_animation)
        c = animate(t, self.font_color_animation)
        self.label.color = c,c,c
        self.label.render(d, t)

class Label:
    def __init__(self, pt, text="", color=(1,1,1), font_size=14, center=False):
        self.pt = pt
        self.color = color
        self.font_size = font_size
        self.text = text
        self.center = center

    def render(self, d, t):
        ctx = d.context
        with ctx:
            ctx.set_font_size(self.font_size)
            ctx.set_source_rgb(*self.color)

            x, y = self.pt
            if self.center:
                xb, yb, w, h, _, _ = ctx.text_extents(self.text)
                ctx.move_to(x - w/2 - xb, y - h/2 - yb)
            else:
                ctx.move_to(x, y)

            ctx.show_text(self.text)







