import cv2
from math import pi
import numpy as np
from itertools import *
import collections
from statistics import median
from math import ceil
from collections import defaultdict
from functools import partial

params = cv2.SimpleBlobDetector_Params()
params.minThreshold = 20
params.maxThreshold = 255
params.filterByArea = True
params.filterByCircularity = True
params.minCircularity = 0.4
params.filterByColor = True
params.blobColor = 0xFF
params.minArea = 50
params.maxArea = 500
detector = cv2.SimpleBlobDetector_create(params)


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

def dist(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

def keypoint_distance(points):
    return sum(dist(a.pt, b.pt) + abs(a.size - b.size) for a, b in pairwise(points))

def bucketize(a, set_lengths=3, required_sets=3):
    return ([b] for b in chain.from_iterable(repeat(a, required_sets)))

def find_locations(display, camera, points, repeats=3):
    display.ctx_main.set_source_rgb(0,0,0)
    display.ctx_main.rectangle(0, 0, display.width, display.height)
    display.ctx_main.fill()
    # get camera in a good state
    for x in range(15):
        ret, img = camera.read()

    keypoints = collections.defaultdict(set)

    point_is_on = defaultdict(lambda: False)
    ret, prev_img = camera.read()
    all_imgs = [prev_img]
    def add_keypoints(a, b):
        diff = cv2.absdiff(a, b)
        kp = detector.detect(diff)
        if len(kp) >= len(point_set):
            for point in point_set:
                keypoints[point].add(tuple(kp))

    job = None
    for point_set in bucketize(points, required_sets=repeats):
        for x,y in point_set:
            display.draw_point(x,y, color=(0,0,0) if point_is_on[x,y] else (1,1,1), immediately=True)
            point_is_on[x,y] = not point_is_on[x,y]
        
        if job:
            job()
        else:
            camera.read()
            camera.read()
        camera.read()
        camera.read()
        camera.read()
        camera.read()
        camera.read()
        camera.read()
        camera.read()
        camera.read()
        ret, img = camera.read()
        all_imgs.append(img)
        job = partial(add_keypoints, img, prev_img)
        prev_img = img
    job()
    for idx, img in enumerate(all_imgs):
        cv2.imwrite("basic-test-{}.png".format(idx), img)

    real_locations = {}
    for pt, potential_keypoints in keypoints.items():
        # idx used as tie breaker
        *_, kpts = min((keypoint_distance(points), idx, points) for idx, points in enumerate(product(*potential_keypoints)))
        print([(int(k.pt[0]), int(k.pt[1])) for k in kpts])
        x = median(p.pt[0] for p in kpts)
        y = median(p.pt[1] for p in kpts)
        size = median(p.size for p in kpts)
        real_locations[pt] = ((x,y),size)
    return real_locations







