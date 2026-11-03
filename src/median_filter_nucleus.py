"""Remove the noise from Nucleus_cropped_noise.tif with median filters of three
different shapes, save the results, and show them next to the noisy image.

Run it from the top folder of the workshop repository with:

    uv run src/median_filter_nucleus.py

The filtered images are saved next to the original in testImages/, e.g.
Nucleus_cropped_noise_median_3x3.tif.  Napari then opens with the noisy image
and the three filtered versions.  Close the Napari window to end the script.
"""

from pathlib import Path

import napari
import numpy as np
import tifffile
from scipy import ndimage

# Where the image lives.  Path(__file__) is this script, ".parent.parent" walks
# up two folders to the top of the workshop repository.
REPO = Path(__file__).resolve().parent.parent
INPUT = REPO / "testImages" / "Nucleus_cropped_noise.tif"

# The shapes of the median filters ("structuring elements").  A 1 means the
# pixel at that spot takes part, a 0 means it is left out.  The middle of each
# shape is the pixel being replaced.
KERNELS = {
    # 3 x 3 with the 4 corners left out: a plus sign of 5 pixels.
    "plus": np.array([
        [0, 1, 0],
        [1, 1, 1],
        [0, 1, 0],
    ]),
    # The full 3 x 3 square: 9 pixels.
    "3x3": np.ones((3, 3)),
    # The full 5 x 5 square: 25 pixels.
    "5x5": np.ones((5, 5)),
}

with tifffile.TiffFile(INPUT) as tif:
    noisy = tif.asarray()
    # The pixel size is stored in the file as "pixels per micron" in the
    # XResolution and YResolution tags.  Keep it, so that the filtered images
    # have the same size in microns as the original.
    page = tif.pages[0]
    resolution = (page.tags["XResolution"].value, page.tags["YResolution"].value)
    unit = tif.imagej_metadata.get("unit", "micron")

# Pixel size in microns, for Napari: one divided by "pixels per micron".
numerator, denominator = resolution[0]
pixel_size = denominator / numerator

viewer = napari.Viewer(title="Median filters")
scale = (pixel_size, pixel_size)
viewer.add_image(noisy, name="noisy original", scale=scale,
                 units=("µm", "µm"))

for name, kernel in KERNELS.items():
    # The median filter slides the shape over the image.  At every position it
    # sorts the pixel values under the shape and keeps the middle one.  A
    # single very bright or very dark noise pixel ends up at one end of that
    # sorted list, so it never becomes the middle value and disappears.
    filtered = ndimage.median_filter(noisy, footprint=kernel)

    output = INPUT.with_name(f"{INPUT.stem}_median_{name}.tif")
    tifffile.imwrite(output, filtered, imagej=True, resolution=resolution,
                     metadata={"unit": unit})
    print(f"{name:>5} ({int(kernel.sum()):>2} pixels): saved {output.name}")

    viewer.add_image(filtered, name=f"median {name}", scale=scale,
                     units=("µm", "µm"))

# Show the layers side by side in a grid instead of on top of each other.
viewer.grid.enabled = True
viewer.scale_bar.visible = True
napari.run()
