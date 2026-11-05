<<<<<<< HEAD
"""Cross-correlate Mito_Cropped.tif with Mito_template.tif, without any
normalization, and report where the result is highest.
=======
"""Cross-correlate the mitochondria image with a small template cut out of it.
>>>>>>> main

Run it from the top folder of the workshop repository with:

    uv run src/cross_correlate_mito.py

<<<<<<< HEAD
The result is saved as testImages/Mito_Cropped_xcorr.tif, and the position of
its highest value is printed in the terminal.
=======
The result is saved as testImages/Mito_Cropped_xcorr.tif.
>>>>>>> main
"""

from pathlib import Path

import numpy as np
import tifffile
from scipy import ndimage
<<<<<<< HEAD

# Where the images live.  Path(__file__) is this script, ".parent.parent" walks
# up two folders to the top of the workshop repository.
REPO = Path(__file__).resolve().parent.parent
IMAGE = REPO / "testImages" / "Mito_Cropped.tif"
TEMPLATE = REPO / "testImages" / "Mito_template.tif"
OUTPUT = REPO / "testImages" / "Mito_Cropped_xcorr.tif"

with tifffile.TiffFile(IMAGE) as tif:
    image = tif.asarray()
    # The pixel size is stored as "pixels per micron" in the XResolution and
    # YResolution tags.  Keep it, so the result has the same size in microns.
    page = tif.pages[0]
    resolution = (page.tags["XResolution"].value, page.tags["YResolution"].value)
    unit = tif.imagej_metadata.get("unit", "micron")

template = tifffile.imread(TEMPLATE)

# Cross-correlation: slide the template over the image like a kernel.  At
# every position, multiply each template pixel with the image pixel under it
# and add everything up.  The result is stored at the position of the
# template's center.  It is the same calculation as the filters before, with
# the template as the kernel.
#
# Calculate in decimals (float64): the sums of 121 products of numbers up to
# several thousand are far too large for whole numbers of the original type.
# Outside the image, pixels count as 0 (mode="constant").
xcorr = ndimage.correlate(image.astype(np.float64), template.astype(np.float64),
                          mode="constant", cval=0)

tifffile.imwrite(OUTPUT, xcorr.astype(np.float32), imagej=True,
                 resolution=resolution, metadata={"unit": unit})
print(f"Saved {OUTPUT}")

# np.argmax finds the highest value, but counts pixels as if the image were
# one long line.  np.unravel_index turns that back into (row, column).
row, column = np.unravel_index(np.argmax(xcorr), xcorr.shape)

numerator, denominator = resolution[0]
pixel_size = denominator / numerator  # microns per pixel

print(f"Highest value: {xcorr[row, column]:.4g}")
print(f"  at row {row}, column {column} (y = {row}, x = {column} in pixels)")
print(f"  = {row * pixel_size:.2f} um down, {column * pixel_size:.2f} um across")
=======
from skimage.feature import match_template

REPO = Path(__file__).resolve().parent.parent
INPUT = REPO / "testImages" / "Mito_Cropped.tif"
TEMPLATE = REPO / "testImages" / "Mito_template.tif"
OUTPUT = REPO / "testImages" / "Mito_Cropped_xcorr.tif"

with tifffile.TiffFile(INPUT) as tif:
    image = tif.asarray()
    # Keep the pixel size, so the result has the same size in microns.
    page = tif.pages[0]
    resolution = (page.tags["XResolution"].value, page.tags["YResolution"].value)
    unit = tif.imagej_metadata.get("unit", "micron")
template = tifffile.imread(TEMPLATE)

print(f"Image:    {image.shape} pixels, values {image.min()} - {image.max()}")
print(f"Template: {template.shape} pixels, values {template.min()} - {template.max()}")

# Raw cross-correlation: the template is laid over the image with its center on
# each pixel in turn, the overlapping pixels are multiplied, and the products
# are added up.  Problem: a bright patch gives a big sum no matter what shape it
# has, so every bright region "matches".  Shown here only for comparison.
raw = ndimage.correlate(image.astype(float), template.astype(float))
row, col = np.unravel_index(np.argmax(raw), raw.shape)
print(f"\nRaw cross-correlation: highest value at row {row}, column {col}")

# Normalized cross-correlation fixes this.  For every position it
#   1. subtracts the mean, from both the template and the image patch under it,
#      so only the *pattern* (brighter/darker than average) counts, and
#   2. divides by the spread (standard deviation) of both, so a bright patch
#      no longer wins just by being bright.
# The result runs from -1 (opposite pattern) through 0 (unrelated) to
# 1 (identical shape).  pad_input=True keeps the output the same size as the
# image, with each value placed at the template's center.
xcorr = match_template(image.astype(float), template.astype(float), pad_input=True)

# Find the pixel with the highest value.  argmax gives its position counted in
# the flattened image; unravel_index turns that back into (row, column).
row, col = np.unravel_index(np.argmax(xcorr), xcorr.shape)
print(f"\nNormalized cross-correlation values: {xcorr.min():.3g} - {xcorr.max():.3g}")
print(f"Highest value {xcorr[row, col]:.3g} at row {row}, column {col}")

# The template was cut out around row 37, column 144 (Fiji: x=144, y=37; see
# make_mito_template.py), so a perfect find puts its center there.
print("The template was cut out with its center at row 37, column 144")

# Saved as a 32-bit float image, because the values lie between -1 and 1 and
# a 16-bit image can only hold whole numbers.
tifffile.imwrite(OUTPUT, xcorr.astype(np.float32), imagej=True,
                 resolution=resolution, metadata={"unit": unit})
print(f"Saved {OUTPUT}")
>>>>>>> main
