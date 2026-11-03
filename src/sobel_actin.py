"""Find edges in Actin_cropped.tif with the Sobel x and Sobel y kernels, and
combine both into the gradient magnitude.

Run it from the top folder of the workshop repository with:

    uv run src/sobel_actin.py

Three images are saved next to the original in testImages/:

    Actin_cropped_sobel_x.tif           change in brightness from left to right
    Actin_cropped_sobel_y.tif           change in brightness from top to bottom
    Actin_cropped_gradient_magnitude.tif  strength of the change, any direction

Napari then opens with the original and these three images side by side.
Close the Napari window to end the script.
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

# The Sobel x kernel: right column minus left column.  The result is positive
# where the image gets brighter from left to right, negative where it gets
# darker, and 0 where it stays the same.  The middle row counts twice, which
# smooths the result a little, so noise has less effect.
SOBEL_X = np.array([
    [-1, 0, 1],
    [-2, 0, 2],
    [-1, 0, 1],
])

# The Sobel y kernel is the same kernel turned on its side: bottom row minus
# top row.  Positive where the image gets brighter from top to bottom.
SOBEL_Y = np.array([
    [-1, -2, -1],
    [ 0,  0,  0],
    [ 1,  2,  1],
])

with tifffile.TiffFile(INPUT) as tif:
    original = tif.asarray()
    # The pixel size is stored as "pixels per micron" in the XResolution and
    # YResolution tags.  Keep it, so the new images have the same size in
    # microns as the original.
    page = tif.pages[0]
    resolution = (page.tags["XResolution"].value, page.tags["YResolution"].value)
    unit = tif.imagej_metadata.get("unit", "micron")

# Slide each kernel over the image, multiply each pixel by its weight and add
# up.  ndimage.correlate uses the kernel exactly as written above.  Calculate
# in decimals (float32), because the results can be negative.
image = original.astype(np.float32)
sobel_x = ndimage.correlate(image, SOBEL_X)
sobel_y = ndimage.correlate(image, SOBEL_Y)

# The gradient magnitude combines both directions, like the long side of a
# right triangle (Pythagoras): sqrt(x^2 + y^2).  It is large on every edge,
# whatever its direction, and always positive.
magnitude = np.sqrt(sobel_x**2 + sobel_y**2)

for result, name in [(sobel_x, "sobel_x"), (sobel_y, "sobel_y"),
                     (magnitude, "gradient_magnitude")]:
    output = INPUT.with_name(f"{INPUT.stem}_{name}.tif")
    tifffile.imwrite(output, result, imagej=True, resolution=resolution,
                     metadata={"unit": unit})
    print(f"Saved {output.name}: values {result.min():.0f} to {result.max():.0f}")

numerator, denominator = resolution[0]
pixel_size = denominator / numerator  # microns per pixel
scale = (pixel_size, pixel_size)

# Sobel x and y share the same color range, centered on 0: red where the
# image gets brighter (in the kernel's direction), blue where it gets darker.
largest = float(max(np.abs(sobel_x).max(), np.abs(sobel_y).max()))

viewer = napari.Viewer(title="Sobel edges")
viewer.add_image(original, name="original", scale=scale, units=("µm", "µm"))
viewer.add_image(sobel_x, name="Sobel x (red: brighter to the right)",
                 scale=scale, units=("µm", "µm"), colormap="bwr",
                 contrast_limits=(-largest, largest))
viewer.add_image(sobel_y, name="Sobel y (red: brighter downward)",
                 scale=scale, units=("µm", "µm"), colormap="bwr",
                 contrast_limits=(-largest, largest))
viewer.add_image(magnitude, name="gradient magnitude", scale=scale,
                 units=("µm", "µm"))
viewer.grid.enabled = True
viewer.scale_bar.visible = True
napari.run()
