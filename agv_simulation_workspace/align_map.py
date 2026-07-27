import cv2
import numpy as np

# Load original map
img = cv2.imread('src/agv/maps/my_new_map.pgm', cv2.IMREAD_GRAYSCALE)
h, w = img.shape
res = 0.05

# Find walls (black pixels)
obstacles = np.where(img < 50) # row, col

min_row, max_row = np.min(obstacles[0]), np.max(obstacles[0])
min_col, max_col = np.min(obstacles[1]), np.max(obstacles[1])

print(f"Map size: {w}x{h}")
print(f"Walls at rows: {min_row} to {max_row} (Height: {max_row-min_row} pixels = {(max_row-min_row)*res} m)")
print(f"Walls at cols: {min_col} to {max_col} (Width: {max_col-min_col} pixels = {(max_col-min_col)*res} m)")

# Center of the room in pixels
center_row = (min_row + max_row) / 2.0
center_col = (min_col + max_col) / 2.0
print(f"Center of room (pixels): col={center_col}, row={center_row}")

# In Gazebo, center of room is (0,0)
# Map X = (col * res) + origin_x -> We want center_col * res + origin_x = 0
# Map Y = ((h - 1 - row) * res) + origin_y -> We want (h - 1 - center_row) * res + origin_y = 0

origin_x = - (center_col * res)
origin_y = - ((h - 1 - center_row) * res)
print(f"Calculated Origin to align room center to (0,0):")
print(f"origin_x: {origin_x:.3f}")
print(f"origin_y: {origin_y:.3f}")

# Now let's find the boxes!
# Box 1 (Gazebo Blue Box) is at X=2, Y=2.
# Box 2 (Gazebo Red Box) is at X=-2.5, Y=-1.5.

# Let's search for pixels corresponding to the boxes
# Box 1 expected Map X,Y: (2, 2)
expected_col1 = int((2 - origin_x) / res)
expected_row1 = h - 1 - int((2 - origin_y) / res)

print(f"If map is correct, Blue Box should be near col={expected_col1}, row={expected_row1}")

# Let's check a 20x20 region around expected Blue Box
blue_box_region = img[expected_row1-20:expected_row1+20, expected_col1-20:expected_col1+20]
if np.any(blue_box_region < 50):
    print("Blue Box FOUND at Gazebo coordinates!")
else:
    print("Blue Box NOT FOUND at expected coordinates! Map is flipped or rotated.")

# Let's search the whole image for clusters of obstacles inside the room
# We ignore pixels near the walls (margin of 10 pixels)
inner_obstacles = []
for r, c in zip(obstacles[0], obstacles[1]):
    if r > min_row + 10 and r < max_row - 10 and c > min_col + 10 and c < max_col - 10:
        inner_obstacles.append((r, c))

if inner_obstacles:
    in_r, in_c = inner_obstacles[0]
    ob_x = in_c * res + origin_x
    ob_y = (h - 1 - in_r) * res + origin_y
    print(f"Found inner obstacle at Map X={ob_x:.2f}, Y={ob_y:.2f} (col={in_c}, row={in_r})")
