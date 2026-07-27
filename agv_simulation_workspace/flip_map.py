import cv2
import yaml

# Read map image
img = cv2.imread('src/agv/maps/my_new_map.pgm', cv2.IMREAD_UNCHANGED)

# Flip horizontally or vertically?
# We want to invert Y. In OpenCV, row 0 is top, row N is bottom.
# ROS map_server loads row N as Y=0, row 0 as Y=max.
# To invert the Y axis in ROS, we flip the image vertically!
flipped_img = cv2.flip(img, 0) # 0 means flipping around the x-axis (vertical flip)

# Save the flipped image
cv2.imwrite('src/agv/maps/my_new_map_flipped.pgm', flipped_img)

# We also need to fix the origin in the YAML file!
# If we flipped vertically, the new origin Y needs to be shifted.
# Actually, the old Y coordinates were: Y_old = row_ros * res + origin_y
# The new Y coordinates: Y_new = -Y_old.
# If we want the map to align with Gazebo, we don't just want -Y_old.
# Let's just create the flipped image first and see its dimensions.
h, w = img.shape
print(f"Map size: {w}x{h}")
