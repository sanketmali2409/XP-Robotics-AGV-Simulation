import cv2
import numpy as np

img = cv2.imread('src/agv/maps/my_new_map.pgm', cv2.IMREAD_GRAYSCALE)
h, w = img.shape
origin_x = -7.41
origin_y = -6.71
res = 0.05

# Find obstacles (black pixels)
obstacles = np.where(img < 50) # row, col

for r, c in zip(obstacles[0], obstacles[1]):
    x = c * res + origin_x
    # row 0 is top, so y from bottom is (h - 1 - r)
    y = (h - 1 - r) * res + origin_y
    if x > 1 and y > 1:
        print(f"Obstacle top right at: X={x:.2f}, Y={y:.2f}")
        break
for r, c in zip(obstacles[0], obstacles[1]):
    x = c * res + origin_x
    y = (h - 1 - r) * res + origin_y
    if x < -1 and y < -1:
        print(f"Obstacle bottom left at: X={x:.2f}, Y={y:.2f}")
        break
