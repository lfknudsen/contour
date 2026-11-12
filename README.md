# Contour

Programme to output a low-resolution corner contour (in the form of a list of
coordinates for use with Godot, but also optionally as an actual image)
based on a 2D image.
Intended to be used as the input for a program which converts the coordinates
into a 3D mesh.

It's essentially a way to make a basic collision box out of a 2D sprite. Hence
the low resolution and disinterest in finding *all* corners, much less keeping
all edges: The resulting convex collision shape would be more computationally
expensive to use than necessary (for my purposes).

## Dependencies

Requires the Pillow library.

## Setup

I recommend just using `uv`, but if you prefer not to, you will need to install pillow with

```
pip install pillow
```

## Usage

```
uv run contour.py [OPTIONS] <filenames>
```

or

```
py contour.py [OPTIONS] <filenames>
```

#### Options:

```
-h, -help, --help       Print this message and exit.

-prefix <string>        Set the prefix of the output filename. Default: ''
                        The output will be <prefix><filename w/o extension><suffix><ext>

-suffix <string>        Set the suffix of the output filename. Default: '_corners'
                        Alias: -postfix
                        
-ext <string>           Set the extension and file format of the output file. Default: '.png'
                        If given an empty string, the output will be a png file, but the file
                        itself won't have an extension.

-scale <number>         Resample the input image before running the algorithm, dividing the
                        width and height of the input by this number. Default: 5.0
                        If set to 1, the scale will be the same.

-ppm <number>           Pixels per meter. This is only relevant for Godot's formats.
                        Default: 0.025

-picture                Save the result as a picture file. On by default.
-no-picture             DO NOT save the result as a picture file.

-packed                 Format the result as a Godot packed array and print it to stdout.

-vector                 Format the result as a Godot vector array and print it to stdout.
```

## Example

Below is seen an example of the programme's output. The input image was resampled to
20% of its original size. In the illustration, the 'after' image has therefore been
scaled up by 500% (nearest neighbour algorithm). The background is made white to make it
easier to see the output.

![Example before and after](example.png)

## How it works

Imagine that for each edge pixel in the image, the algorithm moves inward and stops at the
first non-transparent pixel it encounters. If this pixel is a corner (or the edge of the image),
it is kept in the output.