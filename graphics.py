import cairocffi as cairo
from cairotft import tft
from math import pi
import asyncio

class View:
	def __init__(self, loc=(0,0), size=(0,0), color=(0,0,0), hidden=False):
		self.loc = loc
		self.size = size
		self.hidden = hidden
		self.color = color

	def transforms(self, context):
		context.translate(*self.loc)
		context.move_to(0,0)
		context.set_source_rgb(*self.color)

	def draw_wrapper(self, context):
		if not self.hidden:
			with context:
				self.transforms(context)
				self.draw(context)
	def draw(self, context):
		pass

class Label(View):
	def __init__(self, text, font_size=20, *args, **kwdargs):
		super().__init__(*args, **kwdargs)
		self.font_size = font_size
		self.text = text

	def draw(self, context):
		context.move_to(0, self.size[1] if self.size[1] else self.font_size)
		context.set_font_size(self.font_size)
		context.show_text(self.text)


class Shape(View):
	def transforms(self, context):
		super().transforms(context)
		context.scale(*self.size)

class Ellipse(Shape):
	def draw(self, context):
		context.arc(0.5, 0.5, 0.5, 0, 2 * pi)
		context.fill()

class Rectangle(Shape):
	def draw(self, context):
		context.rectangle(0, 0, 1, 1)
		context.fill()

class RootView(tft.TftDisplay):
	def __init__(self, cairo_format=cairo.FORMAT_RGB16_565, *args, **kwdargs):
		super().__init__(cairo_format=cairo_format, *args, **kwdargs)
		self.size = (self.width, self.height)
		self.loc = (0, 0)
		self.hidden = False
		self.color = (0,0,0)

	def draw_interface(self):
		ctx = self.ctx		
		self.blank_screen(ctx=ctx,
						  color=(0, 0, 0, 1),
						  blit=False)
		
		def display_node(node):
			if hasattr(node, 'hidden') and node.hidden:
				return
			if hasattr(node, 'update'):
				node.update()
			if hasattr(node, 'children'):
				for child in node.children:
					display_node(child)
			else:
				node.draw_wrapper(ctx)
		display_node(self)
		self.blit()
		self.io_loop.call_later(0.01, self.draw_interface)


