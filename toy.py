import cv2
import numpy
import itertools

baseline = cv2.imread("Training Data/1-baseline.png").astype(numpy.int16)
red = cv2.imread("Training Data/1-red.png").astype(numpy.int16)
green = cv2.imread("Training Data/1-green.png").astype(numpy.int16)
blue = cv2.imread("Training Data/1-blue.png").astype(numpy.int16)

baseline = baseline.transpose(2,0,1)
red = red.transpose(2,0,1)
green = green.transpose(2,0,1)
blue = blue.transpose(2,0,1)

keypoints = []

for idx, img in enumerate((blue, green, red)):
	diff = numpy.abs(img[idx] - baseline[idx]).astype(numpy.uint8)
	diff = numpy.full_like(diff, 255) - diff

	params = cv2.SimpleBlobDetector_Params()
	params.minThreshold = 100;
	params.maxThreshold = 255;
	params.filterByArea = True
	params.minArea = 300
	params.maxArea = 1000
	 
	detector = cv2.SimpleBlobDetector_create(params)
	 
	# Detect blobs.
	keypoints.append(detector.detect(diff))

def dist(a, b):
	return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

unlikeness, keypoint = min( # find the set of three keypoints (one red, one green, one blue)
						    # which are most like each other. (Distance between centers and 
						    # approximate sizes are closest)
				            (dist(a.pt, b.pt) + dist(b.pt, c.pt) + 2*b.size - a.size - c.size, a)
				              for a, b, c in itertools.product(*keypoints)
			            )

if unlikeness > 4:
	raise ValueError("probably a bad calibration run")

print(keypoint.pt, keypoint.size)
mask = numpy.fromfunction(lambda x,y: dist(keypoint.pt, (y, x)) < (keypoint.size/2)**2, diff.shape)
diff[mask == 0] = 0
 

# # Draw detected blobs as red circles.
# # cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS ensures the size of the circle corresponds to the size of blob
# im_with_keypoints = cv2.drawKeypoints(diff, keypoints, numpy.array([]), (0,0,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
 
# Show keypoints
cv2.imshow("Keypoints", diff)
cv2.waitKey(0)