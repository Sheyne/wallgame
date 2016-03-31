from getchy import get_key
import cv2
import numpy as np
import random

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
    random.shuffle(points)
    real_locations = cv2.perspectiveTransform(np.array([points], dtype=np.float32), trans)[0]

    masks = [(slice(y-6, y+6), slice(x-6, x+6)) for x, y in real_locations]

    hit = set()
    candidates = set()
    get_an_image()
    get_an_image()
    get_an_image()
    get_an_image()
    explode_frame = {}
    last_dot_touched = None
    last_dot_touched = -1
    prev = get_an_image()
    import time
    last_time = time.time()
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
                if last_dot_touched == None:
                    hit.add(idx)
                    explode_frame[idx] = 0
                else: 
                    if last_dot_touched + 1 == idx:
                        hit.add(idx)
                        explode_frame[idx] = 0
                        last_dot_touched += 1
            if score > 3:
                candidates.add(idx)

        buff.blank()
        buff.context.move_to(5, 150)
        buff.context.set_font_size(120)
        buff.context.set_source_rgb(1,1,1)
        buff.context.show_text("{:.2f}".format(time.time() - last_time))

        for idx, point in enumerate(points):
            color = (1,1,1) if idx in hit else (0.2,0.2,0.3)
            if last_dot_touched + 1 == idx:
                color = (0,0,1)
            buff.draw_point(point, color)
            if last_dot_touched != None:
                buff.context.move_to(point[0] - 10, point[1] + 12)
                buff.context.set_font_size(30)
                buff.context.set_source_rgb(*((0,0,0) if idx in hit else (1,1,1)))
                buff.context.show_text(str(idx))

        display.draw_display(buff)

        if len(hit) == len(points):
            time.sleep(1.5)
            break
