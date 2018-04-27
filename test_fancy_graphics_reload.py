from graphics import *
from time import time
from random import shuffle, choice
import numpy as np

def r(k):
	w = Window(k['d'])

	buttons = []

	for x in range(100, 1000, 100):
		e = Dot((x, abs(x - 600) + 100))
		buttons.append(e)
		w.helpers.add(e)

	w.draw()

	shuffle(buttons)

	for b in buttons:
		b.hit()
		for x in range(20):
			w.draw()
		choice(buttons).reset()
