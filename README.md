# Contour

A Python script to output a low-resolution corner contour of an image.

I wrote it to generate hitboxes of sprites in a game I was working on.

The output can be downscaled as necessary, and can be output as a list of
coordinates for use with Godot, or as an actual .png.

## Usage

There are currently no command-line arguments to change output scaling or format.

```
py contour.py <filename>
```
