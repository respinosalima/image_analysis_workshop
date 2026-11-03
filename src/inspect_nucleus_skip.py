"""Print every third pixel of an image, show its number type, then show it.

Run it from the top folder of the workshop repository with:

    uv run src/inspect_nucleus_skip.py

The numbers are printed in the terminal, then Napari opens in its own window.
Close that window to end the script.
"""

from pathlib import Path

import napari
import numpy as np
import tifffile

# Where the image lives.  Path(__file__) is this script, ".parent.parent" walks
# up two folders to the top of the workshop repository.
REPO = Path(__file__).resolve().parent.parent
IMAGE = REPO / "testImages" / "nucleus_cropped_1.tif"

# Take one row (or column), then skip 2, so we move 3 steps each time.
# Change this number to 2 if you want to keep every other pixel instead.
STEP = 3

# tifffile reads the TIFF file and hands back the pixels as a NumPy array: a
# grid of numbers, one number per pixel.
with tifffile.TiffFile(IMAGE) as tif:
    pixels = tif.asarray()

    # ImageJ stores the pixel size as a "resolution": how many pixels fit in
    # one micrometer.  The pixel size is one divided by that.
    numerator, denominator = tif.pages[0].tags["XResolution"].value
    pixel_size = denominator / numerator  # micrometers per pixel

# pixels[start:stop:step] picks values from start up to (not including) stop,
# jumping "step" places each time.  "::STEP" means "from the beginning, every
# STEP-th one", so this keeps rows 0, 3, 6, ... and columns 0, 3, 6, ...
# The final [:10, :10] keeps the first 10 of those rows and columns.
every_third = pixels[::STEP, ::STEP]
corner = every_third[:10, :10]

row_numbers = list(range(0, pixels.shape[0], STEP))[:10]
print(f"Rows and columns {row_numbers} of {IMAGE.name}:\n")
with np.printoptions(linewidth=200):
    print(corner)

# .dtype is the kind of number stored in each pixel.  "uint16" means unsigned
# (no negative values) 16-bit integers, so each pixel can be 0 - 65535.
print(f"\nNumber type: {pixels.dtype}  (values can be "
      f"{np.iinfo(pixels.dtype).min} - {np.iinfo(pixels.dtype).max})")

# Show the full image in Napari, plus the "every third pixel" version as a
# second layer.  Each pixel in that smaller image stands for 3 x 3 original
# pixels, so its pixel size is 3 times larger; with the right "scale" both
# layers line up and cover the same area.  Click the eye icon next to a layer
# to hide or show it and compare the two.
viewer = napari.Viewer()
viewer.add_image(pixels, name="original", scale=(pixel_size, pixel_size),
                 units=("um", "um"))
viewer.add_image(every_third, name=f"subsampled (step {STEP})",
                 scale=(pixel_size * STEP, pixel_size * STEP),
                 units=("um", "um"), visible=False)
viewer.scale_bar.visible = True

napari.run()
