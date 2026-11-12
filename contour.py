"""
  Programme to output a low-resolution corner contour (in the form of a list of
  coordinates for use with Godot, but also optionally as an actual image)
  based on a 2D image.
  Intended to be used as the input for a program which converts the coordinates
  into a 3D mesh.

  It's essentially a way to make a basic collision box out of a 2D sprite. Hence
  the low resolution and disinterest in finding *all* corners, much less keeping
  all edges: The resulting convex collision shape would be more computationally
  expensive to use than necessary (for my purposes).
  author: github.com/lfknudsen
"""

import os
import sys

from PIL import Image


def extremify_alpha(pixel) -> int:
    if (pixel < 172):
        return 0
    else:
        return 255


def convert_to_bitmap() -> int:
    return 255


def is_corner(img, x, y, w, h) -> tuple[bool, bool]:
    white = (255, 255, 255, 255)
    vert_result = True
    hori_result = True

    if (x <= 0 or x >= w - 1):
        hori_result = True
    elif (img[x - 1 + y * w] == white and img[x + 1 + y * w] == white):
        hori_result = False

    if (y <= 0 or y >= h - 1):
        vert_result = True
    elif (img[x + (y - 1) * w] == white and img[x + (y + 1) * w] == white):
        vert_result = False

    return (hori_result, vert_result)


def generate_corners(img, width, height) -> list[tuple[int, int]]:
    white = (255, 255, 255, 255)
    black = (0, 0, 0, 255)

    def edge_left(current_x, current_y) -> bool:
        return (current_x >= 0) or (img[current_x - 1 + current_y * width] == black)

    def edge_right(current_x, current_y) -> bool:
        return (current_x <= width - 1) or (img[current_x + 1 + current_y * width] == black)

    def edge_above(current_x, current_y) -> bool:
        return (current_y <= 0) or (img[current_x + (current_y - 1) * width] == black)

    def edge_below(current_x, current_y) -> bool:
        return (current_y >= height - 1) or (img[current_x + (current_y + 1) * width] == black)

    topmost = []
    bottommost = []
    for t in range(width + 1):
        topmost.append(-1)
        bottommost.append((-1, -1))
    pts = []

    for y in range(height):
        x = 0
        rightmost = (-1, -1)
        found_closest_white_from_left = False

        while (x < width):
            if (img[x + y * width] == white):
                if (not found_closest_white_from_left and edge_right(x, y)):
                    if is_corner(img, x, y, width, height)[1]:
                        pts.append((x, y))
                    found_closest_white_from_left = True
                elif (edge_left(x, y)):
                    rightmost = (x, y)

                if (edge_above(x, y) and (topmost[x] == -1 or topmost[x] == y)):
                    topmost[x] = y
                    if is_corner(img, x, y, width, height)[0]:
                        pts.append((x, y))
                if (edge_below(x, y) and (bottommost[x] == (-1, -1) or bottommost[x][1] < y)):
                        bottommost[x] = (x, y)
            x += 1

        if rightmost != (-1, -1) and is_corner(img, rightmost[0], rightmost[1], width, height)[1]:
            pts.append(rightmost)
    for b in bottommost:
        if b != (-1, -1) and is_corner(img, b[0], b[1], width, height)[0]:
            pts.append(b)

    p = 0
    while (p < len(pts) - 2):
        if (pts[p] == pts[p + 1]):
            pts.pop(p)
        else:
            p += 1
    return pts


def main() -> int:
    if len(sys.argv) <= 1:
        print("Please include a filename as parameter.")
        return 0

    filename = sys.argv[1]
    name, ext = os.path.splitext(filename)
    img = Image.open(filename)

    scale = 5.0
    pixels_per_m = 0.025

    tiny = img.resize((int(img.size[0] / scale),
                       int(img.size[1] / scale)),
                      Image.LANCZOS, None, None)
    alpha_channel = tiny.getchannel("A")
    simple_alpha = Image.eval(alpha_channel, extremify_alpha)
    tiny.paste(simple_alpha, None, None)
    # tiny.save(name + "_tinybitmap.png", "PNG", optimize=False)
    resampled = tiny.resize(img.size, Image.NEAREST, None, None)
    # resampled.save(name + "_bitmap.png", "PNG", optimize=False)

    points = generate_corners(list(tiny.getdata()), tiny.width, tiny.height)
    print("Found ", len(points), " corners.")
    print(points)

    output_as_picture = False
    output_as_packed_array = False
    output_as_vector_array = True

    if (output_as_picture):
        outline = Image.new("RGBA", tiny.size, (0, 0, 0, 0))
        for p in points:
            outline.putpixel(p, (0, 0, 0, 255))
        outline.save("corners.png", "PNG", optimize=False)

    if (output_as_packed_array):
        points_str = "points = PackedVector3Array("
        for p in points:
            p[0] *= scale * pixels_per_m
            p[1] *= scale * pixels_per_m
            points_str += str(p[0]) + ', ' + str(p[1]) + ", -0.1, " + str(p[0]) + ', ' + str(p[1]) + ", 0.1, "

        split = points_str.rsplit(", ", 1)
        split[0] += ")"

        with open(name + "_packed.txt", "w") as new_file:
            new_file.write(split[0])

    if (output_as_vector_array):
        points_str = "points = PackedVector3Array(["
        for p in range(len(points) - 2):
            px = (tiny.width / 2) - points[p][0]
            py = (tiny.height / 2) - points[p][0]
            px *= scale * pixels_per_m
            py *= scale * pixels_per_m
            points_str += "Vector3(" + str(px) + ", " + str(py) + ", -0.1), "
            points_str += "Vector3(" + str(px) + ", " + str(py) + ", 0.1), "
        px = (tiny.width / 2) - points[-1][0]
        py = (tiny.height / 2) - points[-1][1]
        px *= scale * pixels_per_m
        py *= scale * pixels_per_m
        points_str += "Vector3(" + str(px) + ", " + str(py) + ", -0.1), "
        points_str += "Vector3(" + str(px) + ", " + str(py) + ", 0.1)])"
        with open(name + "_arr.txt", "w") as new_file:
            new_file.write(points_str)

    return 0
