import cv2
from math import pi
import numpy as np
import itertools
import collections
from statistics import median

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
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

def dist(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

def keypoint_distance(points):
    return sum(dist(a.pt, b.pt) + abs(a.size - b.size) for a, b in pairwise(points))


def find_locations(display, camera, points):
    # get camera in a good state
    for x in range(10):
        ret, img = camera.read()

    keypoints = collections.defaultdict(set)

    for point_set in itertools.combinations(points, 2):
        imgs = []
        for color in [(1,1,1), (0,0,0)]:
            for x,y in point_set:
                display.draw_point(x,y, color=color, immediately=True)

            camera.read()
            camera.read()
            camera.read()
            ret, img = camera.read()
            imgs.append(img)
        base, dots = imgs
        diff = dots.astype(np.int16) - base.astype(np.int16)
        diff[diff < 0] = 0
        kp = detector.detect(diff.astype(np.uint8))
        if len(kp) >= 2:
            for point in point_set:
                keypoints[point].add(tuple(kp))

    real_locations = {}
    for pt, potential_keypoints in keypoints.items():
        # idx used as tie breaker
        *_, kpts = min((keypoint_distance(points), idx, points) for idx, points in enumerate(itertools.product(*potential_keypoints)))
        x = median(p.pt[0] for p in kpts)
        y = median(p.pt[1] for p in kpts)
        size = median(p.size for p in kpts)
        real_locations[pt] = ((x,y),size)
    return real_locations







