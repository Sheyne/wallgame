from getchy import get_key
import cv2
import numpy as np

def magic_function(points, trans, buff, display, camera, g=None):
	def move(k, point, mul=[5]):
		fast = k.upper() == k
		speed = 5 if fast else 1
		speed *= mul[0]
		k = k.lower()
		if k == "w":
			point[1] -= speed
			return True
		if k == "s":
			point[1] += speed
			return True
		if k == "a":
			point[0] -= speed
			return True
		if k == "d":
			point[0] += speed
			return True
		if k == "=":
			mul[0] *= 2
		if k == "-":
			mul[0] *= 0.5
		return False

	def edit(points):
		who = 0
		poked = False
		while True:
			buff.blank()
			for idx, point in enumerate(points):
				buff.draw_point(point, (1,1,1) if idx != who else (0.8, 0.8, 0.6))
				buff.context.move_to(point[0] - 10, point[1] + 12)
				buff.context.set_font_size(30)
				buff.context.set_source_rgb(0,0,0)
				buff.context.show_text(str(idx))


			display.draw_display(buff)
			
			k = get_key()
			if k == "e":
				break

			if k == "q":
				raise KeyboardInterrupt()

			if k in "1234567890":
				who = int(k)

			if move(k, points[who]):
				poked = True

		return poked
	def get_an_image():
	    _, img = camera.read()
	    return  cv2.blur(img,(10, 10))
	print("e")


	edit(points)
	real_locations = cv2.perspectiveTransform(np.array([points], dtype=np.float32), trans)[0]

	masks = [(slice(y-6, y+6), slice(x-6, x+6)) for x, y in real_locations]

	hit = set()
	candidates = set()
	get_an_image()
	get_an_image()
	get_an_image()
	get_an_image()

	prev = get_an_image()

	while True:
		img = get_an_image()
		diff = cv2.absdiff(img, prev)
		prev = img

		noises = [diff[mask].sum() for mask in masks]
		min_noise = sum(sorted(noises)[:4]) / 4

		old_candidated = candidates
		candidates = set()

		for idx, noise in enumerate(noises):
			score = noise / min_noise
			score += 5 if idx in old_candidated else 0
			if score > 8:
				hit.add(idx)
			if score > 3:
				candidates.add(idx)



		buff.blank()
		for idx, point in enumerate(points):
			buff.draw_point(point, (1,1,1) if idx in hit else (0,0,1))
		display.draw_display(buff)

		if len(hit) == len(points):
			break