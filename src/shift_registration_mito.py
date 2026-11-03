"""Shift Mito_Cropped.tif by a known number of pixels, then use
cross-correlation to measure how far it moved.

Run it from the top folder of the workshop repository with:

    uv run src/shift_registration_mito.py

The shifted copy is saved as testImages/Mito_Cropped_shifted.tif.  The terminal
shows the real shift and the shift found by cross-correlation.  Napari then
opens with the original (magenta), the shifted copy (green), the
cross-correlation, and the shifted copy moved back.  Where magenta and green
overlap they look white.  Close Napari to end the script.
"""

from pathlib import Path

import napari
import numpy as np
import tifffile
from scipy import ndimage, signal

# Where the images live.  Path(__file__) is this script, ".parent.parent" walks
# up two folders to the top of the workshop repository.
REPO = Path(__file__).resolve().parent.parent
IMAGE = REPO / "testImages" / "Mito_Cropped.tif"
OUTPUT = REPO / "testImages" / "Mito_Cropped_shifted.tif"

# How far to move the image, in pixels.  Positive = down / to the right.
SHIFT_DOWN = 7
SHIFT_RIGHT = 4

with tifffile.TiffFile(IMAGE) as tif:
    original = tif.asarray()
    # The pixel size is stored as "pixels per micron" in the XResolution and
    # YResolution tags.  Keep it, so the shifted copy has the same pixel size.
    page = tif.pages[0]
    resolution = (page.tags["XResolution"].value, page.tags["YResolution"].value)
    unit = tif.imagej_metadata.get("unit", "micron")

# Make the shifted copy.  The pixels that move out at the bottom and right are
# lost, and the empty strip that appears at the top and left is filled with 0,
# like a camera that moved over the sample.
shifted = ndimage.shift(original, shift=(SHIFT_DOWN, SHIFT_RIGHT), order=0,
                        cval=0)
tifffile.imwrite(OUTPUT, shifted, imagej=True, resolution=resolution,
                 metadata={"unit": unit})
print(f"Saved {OUTPUT}")

# Cross-correlation of the two whole images.  Imagine sliding the shifted image
# over the original, one pixel at a time, in every direction.  At every offset,
# multiply the overlapping pixels and add up.  The offset where the two images
# line up best gives the highest value.
#
# First subtract each image's average brightness.  Otherwise every offset with
# a large overlap scores high simply because the images are bright, and the
# peak is pulled toward "no shift".
a = shifted.astype(np.float64) - shifted.mean()
b = original.astype(np.float64) - original.mean()

# method="fft" uses the Fourier transform to do this quickly: sliding a whole
# image over another one pixel at a time would take millions of steps.
# mode="full" tries every offset where the images overlap at all.
xcorr = signal.correlate(a, b, mode="full", method="fft")

# The result has one value per offset.  Its center (index rows - 1,
# columns - 1) is offset 0, so subtract that to get the shift in pixels.
peak_row, peak_column = np.unravel_index(np.argmax(xcorr), xcorr.shape)
found_down = peak_row - (original.shape[0] - 1)
found_right = peak_column - (original.shape[1] - 1)

numerator, denominator = resolution[0]
pixel_size = denominator / numerator  # microns per pixel

print(f"\nReal shift:  {SHIFT_DOWN} pixels down, {SHIFT_RIGHT} pixels right")
print(f"Found shift: {found_down} pixels down, {found_right} pixels right")
print(f"           = {found_down * pixel_size:.2f} um down, "
      f"{found_right * pixel_size:.2f} um right")

# Use the shift we found to move the shifted image back, as you would to line
# up the frames of a drifting time-lapse.
moved_back = ndimage.shift(shifted, shift=(-found_down, -found_right), order=0,
                           cval=0)

scale = (pixel_size, pixel_size)
units = ("µm", "µm")
viewer = napari.Viewer(title="Measuring a shift with cross-correlation")
viewer.add_image(original, name="original", scale=scale, units=units,
                 colormap="magenta", blending="additive")
viewer.add_image(shifted, name="shifted", scale=scale, units=units,
                 colormap="green", blending="additive")
viewer.add_image(moved_back, name="shifted, moved back", scale=scale,
                 units=units, colormap="green", blending="additive",
                 visible=False)
# The cross-correlation is larger than the image (every offset), so it is
# placed with its center (offset 0) over the image's top-left corner.
viewer.add_image(xcorr, name="cross-correlation", scale=scale, units=units,
                 colormap="magma", visible=False,
                 translate=(-(original.shape[0] - 1) * pixel_size,
                            -(original.shape[1] - 1) * pixel_size))
viewer.scale_bar.visible = True
napari.run()
