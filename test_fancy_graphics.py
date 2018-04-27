import graphics
import importlib
import test_fancy_graphics_reload
from time import sleep
import traceback


d = graphics.Display()

while 1:
	try:
		importlib.reload(graphics)
		importlib.reload(test_fancy_graphics_reload)
		test_fancy_graphics_reload.r(locals())
	except:
		traceback.print_exc()
