import cv2
import numpy as np

img = cv2.imread('src/agv/maps/my_new_map.pgm', cv2.IMREAD_GRAYSCALE)
h, w = img.shape
origin_x = -7.41
origin_y = -6.71
res = 0.05

obstacles = np.where(img < 50)
x_coords = obstacles[1] * res + origin_x
y_coords = (h - 1 - obstacles[0]) * res + origin_y

print(f"Min X: {np.min(x_coords):.2f}, Max X: {np.max(x_coords):.2f}")
print(f"Min Y: {np.min(y_coords):.2f}, Max Y: {np.max(y_coords):.2f}")
