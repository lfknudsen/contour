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
import re
import sys
from dataclasses import dataclass, field

from PIL import Image


@dataclass
class args:
    prefix: str = ""
    suffix: str = "_corners"
    ext: str = ".png"
    scale: float = 0.20
    pixels_per_m: float = 0.025
    output_as_picture: bool = True
    output_as_packed_array: bool = False
    output_as_vector_array: bool = False
    files: list[str] = field(default_factory=list)


def error(msg: str):
    print(f"\033[91m{msg}\033[0m", file=sys.stderr)


def printHelp():
    print(
"""Usage: uv run contour.py [OPTIONS] <filenames...>

Options:
-h, -help, --help       Print this message and exit.

-prefix <string>        Set the prefix of the output filename. Default: ''
                        The output will be <prefix><filename without extension><suffix><ext>

-suffix <string>        Set the suffix of the output filename. Default: '_corners'
                        
-ext <string>           Set the extension and file format of the output file. Default: '.png'
                        If given an empty string, the output will be a png file, but the file
                        itself won't have an extension.

-scale <number>         Resample the input image before running the algorithm. Default: 5
                        The width and height of the input will be divided by this number.
                        If set to 1, the scale will be the same.

-ppm <number>           Pixels per m. This is only relevant for Godot's formats.
                        Default: 0.025

-picture                Save the result as a picture file. On by default.
-no-picture             DO NOT save the result as a picture file.

-packed                 Format the result as a Godot packed array and print it to stdout.

-vector                 Format the result as a Godot vector array and print it to stdout.""")


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


def main(state: args) -> int:
    if len(state.files) == 0:
        error("No filenames given.")
        printHelp()
        sys.exit(1)

    filename = sys.argv[1]
    name, _ = os.path.splitext(filename)
    img = Image.open(filename)

    tiny = img.resize((int(img.size[0] / state.scale),
                       int(img.size[1] / state.scale)),
                      Image.Resampling.LANCZOS, None, None)
    alpha_channel = tiny.getchannel("A")
    simple_alpha = Image.eval(alpha_channel, extremify_alpha)
    tiny.paste(simple_alpha, None, None)

    points = generate_corners(list(tiny.getdata()), tiny.width, tiny.height) # type: ignore

    if (state.output_as_picture):
        outline = Image.new("RGBA", tiny.size, (0, 0, 0, 0))
        for p in points:
            outline.putpixel(p, (0, 0, 0, 255))
        format = None
        if (state.ext == ""):
            format = "PNG"
        outline.save(state.prefix + name + state.suffix + state.ext, format, optimize=True)

    if (state.output_as_packed_array):
        points_str = "points = PackedVector3Array("
        for p in points:
            p0 = str(p[0] * state.scale * state.pixels_per_m)
            p1 = str(p[1] * state.scale * state.pixels_per_m)
            points_str += p0 + ', ' + p1 + ", -0.1, " + p0 + ', ' + p1 + ", 0.1, "

        split = points_str.rsplit(", ", 1)
        split[0] += ")"

        with open(name + "_packed.txt", "w") as new_file:
            new_file.write(split[0])

    if (state.output_as_vector_array):
        points_str = "points = PackedVector3Array(["
        for p in range(len(points) - 2):
            px = (tiny.width / 2) - points[p][0]
            py = (tiny.height / 2) - points[p][0]
            px *= state.scale * state.pixels_per_m
            py *= state.scale * state.pixels_per_m
            points_str += "Vector3(" + str(px) + ", " + str(py) + ", -0.1), "
            points_str += "Vector3(" + str(px) + ", " + str(py) + ", 0.1), "
        px = (tiny.width / 2) - points[-1][0]
        py = (tiny.height / 2) - points[-1][1]
        px *= state.scale * state.pixels_per_m
        py *= state.scale * state.pixels_per_m
        points_str += "Vector3(" + str(px) + ", " + str(py) + ", -0.1), "
        points_str += "Vector3(" + str(px) + ", " + str(py) + ", 0.1)])"
        with open(name + "_arr.txt", "w") as new_file:
            new_file.write(points_str)

    return 0


def next() -> str:
    if hasNext():
        return sys.argv.pop(0)
    return ""


def hasNext() -> bool:
    return len(sys.argv) != 0


if __name__ == "__main__":
    next()
    state = args()

    rxFloat = re.compile("^[0-9]*[.]?[0-9]+$")

    while hasNext():
        arg = next()
        if not arg.startswith("-"):
            state.files.append(arg)
            continue
        match arg:
            case "-h", "-help", "--help":
                printHelp()
                sys.exit(0)
            case "-suffix", "-postfix":
                if hasNext():
                    state.suffix = next()
                else:
                    error("Missing string after -suffix")
                    sys.exit(1)
            case "-prefix":
                if hasNext():
                    state.prefix = next()
                else:
                    error("Missing string after -prefix")
                    sys.exit(1)
            case "-ext":
                if hasNext():
                    state.ext = next()
                    if len(state.ext) > 0 and state.ext[0] != ".":
                        state.ext = "." + state.ext
                else:
                    error("Missing string after -ext")
                    sys.exit(1)
            case "-scale":
                if hasNext():
                    scale = next()
                    if rxFloat.fullmatch(scale):
                        state.scale = float(scale)
                    else:
                        error(f"The value after -scale could not be understood as a decimal number: {scale}")
                        sys.exit(1)
                else:
                    error("Missing number after -scale")
                    sys.exit(1)
            case "-ppm":
                if hasNext():
                    ppm = next()
                    if rxFloat.fullmatch(ppm):
                        state.pixels_per_m = float(ppm)
                    else:
                        error(f"The value after -ppm could not be understood as a decimal number: {ppm}")
                        sys.exit(1)
                else:
                    error("Missing number after -ppm")
                    sys.exit(1)
            case "-picture":
                state.output_as_picture = True
            case "-no-picture":
                state.output_as_picture = False
            case "-packed":
                state.output_as_packed_array = True
            case "-vector":
                state.output_as_vector_array = True
    main(state)
