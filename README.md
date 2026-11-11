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

## Example

Below is seen an example of the programme's output. The input image was resampled to
20% of its original size. In the illustration, the 'after' image has therefore been
scaled up by 500% (nearest neighbour algorithm). The background is made white to make it easier to see the output.

![Example before and after](example.png)

## How it works

This description is written years after I wrote the script, but as I recall:\
For each edge pixel in the image, the algorithm moves inward and stops at the first non-transparent pixel it encounters. If this pixel is a corner, it is kept in the output.