"""Cross-correlate Mito_Cropped.tif with Mito_template.tif, without any
normalization, and report where the result is highest.

Run it from the top folder of the workshop repository with:

    uv run src/cross_correlate_mito.py

The result is saved as testImages/Mito_Cropped_xcorr.tif, and the position of
its highest value is printed in the terminal.
"""

from pathlib import Path

import numpy as np
import tifffile
from scipy import ndimage

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
