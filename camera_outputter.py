import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--camera", help="which camera to use", type=int, default=0)
parser.add_argument("-f", "--fb_path", help="what framebuffer to use", default='/dev/fb0')
parser.add_argument('-v', '--display_info', help="for each image captured, display information about the frame", action='store_true')
parser.add_argument('--imlazy', metavar="VAR_NAME", help="output code to set the given flags")
parser.add_argument('flags', nargs='*', metavar="FLAG", help='send any number of flags to open cv as FLAG:VALUE pairs')

args = parser.parse_args()

from cairotft import linuxfb
import cairocffi as cairo
import cv2
import numpy
import array

fbmem = linuxfb.open_fbmem(args.fb_path)

surf = linuxfb.cairo_surface_from_fbmem(
    fbmem,
    fbmem.mmap,
    cairo.FORMAT_RGB16_565)

width, height = surf.get_width(), surf.get_height()
size_per_pixel = fbmem.fix_info.smem_len / (width * height)
ctx = cairo.Context(surf)

ctx.set_source_rgba(0,0,0,1)
ctx.rectangle(0, 0, width, height)
ctx.fill()


cam = cv2.VideoCapture(args.camera)

for flag in args.flags:
	if flag.startswith("CV_"):
		flag = flag[3:]
	if ":" in flag:
		flag, value = flag.split(":", 2)
		k, v = getattr(cv2, flag), eval(value)
		cam.set(k, v)
		if args.imlazy:
			print("{}.set(cv2.{}, {})".format(args.imlazy, flag,v))
	else:
		print("{}: {}".format(flag, cam.get(getattr(cv2, flag))))

while True:
	ret, img = cam.read()
	width, height, depth = img.shape
	if args.display_info:
		print(width, height, depth)
	img = numpy.append(img.transpose((2,0,1)), numpy.zeros((width,height)).astype(numpy.uint8)).reshape((4, width, height)).transpose(1,2,0)
	img = img.astype(numpy.uint8).flatten()
	a = bytearray(img)

	ctx.set_source_surface(cairo.ImageSurface(cairo.FORMAT_RGB24, height, width, a))
	ctx.paint()