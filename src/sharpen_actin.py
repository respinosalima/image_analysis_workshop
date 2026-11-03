"""Sharpen Actin_cropped.tif and show it next to the original.

Run it from the top folder of the workshop repository with:

    uv run src/sharpen_actin.py

The sharpened image is saved as testImages/Actin_cropped_sharpened.tif.
Napari then opens with three panels: the original, the sharpened image, and
what sharpening added.  Close the Napari window to end the script.
"""

from pathlib import Path

import napari
import numpy as np
import tifffile
from scipy import ndimage

# Where the image lives.  Path(__file__) is this script, ".parent.parent" walks
# up two folders to the top of the workshop repository.
REPO = Path(__file__).resolve().parent.parent
INPUT = REPO / "testImages" / "Actin_cropped.tif"
OUTPUT = REPO / "testImages" / "Actin_cropped_sharpened.tif"

# The sharpen kernel, the same one ImageJ/Fiji uses (Process > Sharpen).  The
# center pixel gets a big positive weight and its 8 neighbors a negative one.
# Where a pixel is brighter than its surroundings (an edge or a fiber), this
# makes it brighter still, and the dark side of an edge darker.  Where the
# image is flat, the neighbors cancel the center out and nothing changes.
KERNEL = np.array([
    [-1, -1, -1],
    [-1, 12, -1],
    [-1, -1, -1],
])

# Normalize by the sum (12 - 8 = 4), so that flat areas keep their brightness.
KERNEL = KERNEL / KERNEL.sum()

with tifffile.TiffFile(INPUT) as tif:
    original = tif.asarray()
    # The pixel size is stored as "pixels per micron" in the XResolution and
    # YResolution tags.  Keep it, so the sharpened image has the same size in
    # microns as the original.
    page = tif.pages[0]
    resolution = (page.tags["XResolution"].value, page.tags["YResolution"].value)
    unit = tif.imagej_metadata.get("unit", "micron")

# Convolution: slide the kernel over the image, multiply each pixel by its
# weight and add up.  Calculate in decimals (float), because the negative
# weights can give values below zero.
sharpened = ndimage.convolve(original.astype(float), KERNEL)

# What sharpening added (positive) or took away (negative) at every pixel.
added = sharpened - original

# The original stores whole numbers from 0 to 65535 (uint16).  Values below 0
# or above 65535 cannot be stored, so clip them to that range, then round.
limits = np.iinfo(original.dtype)
sharpened = np.round(np.clip(sharpened, limits.min, limits.max)).astype(original.dtype)

tifffile.imwrite(OUTPUT, sharpened, imagej=True, resolution=resolution,
                 metadata={"unit": unit})
print(f"Saved {OUTPUT}")

# Sharpening increases the contrast between neighboring pixels.  One way to
# measure that is the standard deviation: how spread out the pixel values are.
print(f"Original:  values {original.min()} - {original.max()}, "
      f"spread (std) {original.std():.0f}")
print(f"Sharpened: values {sharpened.min()} - {sharpened.max()}, "
      f"spread (std) {sharpened.std():.0f}")

# Show the images side by side.  Original and sharpened get the same contrast
# limits, so brightness can be compared fairly.
numerator, denominator = resolution[0]
pixel_size = denominator / numerator  # microns per pixel
scale = (pixel_size, pixel_size)
contrast = (int(original.min()), int(original.max()))
largest_change = float(np.abs(added).max())

viewer = napari.Viewer(title="Sharpen")
viewer.add_image(original, name="original", scale=scale, units=("µm", "µm"),
                 contrast_limits=contrast)
viewer.add_image(sharpened, name="sharpened", scale=scale, units=("µm", "µm"),
                 contrast_limits=contrast)
# Red where sharpening made the image brighter, blue where it made it darker,
# white where nothing changed.
viewer.add_image(added, name="added by sharpening (red +, blue -)", scale=scale,
                 units=("µm", "µm"), colormap="bwr",
                 contrast_limits=(-largest_change, largest_change))
viewer.grid.enabled = True
viewer.scale_bar.visible = True
napari.run()
