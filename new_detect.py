import cv2
from math import pi
import numpy as np
from itertools import *
import collections
from statistics import median
from math import ceil
from functools import partial
import time
from graphics import rect_inset, rect_corners
import numpy as np


params = cv2.SimpleBlobDetector_Params()
params.minThreshold = 40
params.filterByArea = True
params.filterByColor = True
params.blobColor = 0xFF
params.minArea = 5
params.filterByConvexity = True
params.minConvexity = 0
params.maxConvexity = 1
params.filterByCircularity = True
params.minCircularity = 0
params.maxCircularity = 1
# params.maxArea = 100
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

def find_locations(display, camera, points, repeats=3):
    display.blank()

    # get camera in a good state
    for x in range(15):
        ret, img = camera.read()

    keypoints = {point:[] for point in points}
    try_index = 0
    ret, prev_img = camera.read()

    while min(len(a) for k, a in keypoints.items()) < 3:    
        if try_index > 6:
            raise ValueError("Cant find point")

        for point in points:
            display.draw_point(point, (1,1,1) if try_index % 2 == 0 else (0,0,0))

            # time.sleep(0.1)
            # delay needed here
            ret, img = camera.read()
            ret, img = camera.read()
            ret, img = camera.read()
            ret, img = camera.read()
            diff = cv2.absdiff(img, prev_img)
            kps = detector.detect(diff)
            if len(kps) >= 1:
                keypoints[point].append(kps)
            prev_img = img

        try_index += 1

    real_locations = {}

    for pt, potential_keypoints in keypoints.items():
        # idx used as tie breaker
        distance, idx, kpts = min((keypoint_distance(points), idx, points) for idx, points in enumerate(product(*potential_keypoints)))
        if distance > 40:
            raise ValueError("point set too scattered")
        x = median(p.pt[0] for p in kpts)
        y = median(p.pt[1] for p in kpts)
        size = median(p.size for p in kpts)
        real_locations[pt] = ((x,y),size)
    return real_locations

def get_projector_transform(display, camera, scale=1, invert=False):
    frame = [(0,0), (display.width, display.height)]

    points = rect_corners(rect_inset(frame, 15))
    real_locations = find_locations(display, camera, points, 4)

    camera_space = np.array([real_locations[point][0] for point in points],np.float32)

    projector_space = np.array(points,np.float32)
    projector_space *= scale

    spaces = camera_space, projector_space
    if invert:
        spaces = reversed(spaces)
    return cv2.getPerspectiveTransform(* spaces)






