"""Print the red, green and blue values of a regular sample of pixels, then show
the image.

Run it from the top folder of the workshop repository with:

    uv run src/rgb_pixel_table.py

The table is printed in the terminal, then Napari opens in its own window.
Close that window to end the script.
"""

import math
from pathlib import Path

import napari
import numpy as np
import tifffile

# Where the image lives.  Path(__file__) is this script, ".parent.parent" walks
# up two folders to the top of the workshop repository.
REPO = Path(__file__).resolve().parent.parent
IMAGE = REPO / "testImages" / "Cell_cropped_2.tif"

# Which fraction of the pixels to list: 0.03 means 3 percent.
FRACTION = 0.03

# tifffile reads the TIFF file and hands back the pixels as a NumPy array.  A
# color image has three numbers per pixel, so the array has three dimensions:
# (rows, columns, colors).  Colors are in the order red, green, blue.
with tifffile.TiffFile(IMAGE) as tif:
    pixels = tif.asarray()

    # ImageJ stores the pixel size as a "resolution": how many pixels fit in
    # one micrometer.  The pixel size is one divided by that.
    numerator, denominator = tif.pages[0].tags["XResolution"].value
    pixel_size = denominator / numerator  # micrometers per pixel

rows, columns, colors = pixels.shape

# To keep pixels evenly spread, take every STEP-th row and every STEP-th
# column.  That keeps 1 pixel out of every STEP x STEP square, so to keep 3% we
# need STEP x STEP = 1 / 0.03 = 33, which makes STEP about 6.
STEP = round(math.sqrt(1 / FRACTION))
sample_rows = range(0, rows, STEP)
sample_columns = range(0, columns, STEP)
n_sampled = len(sample_rows) * len(sample_columns)

# Print the table: one line per sampled pixel.  The ":>6" in each {} lines the
# numbers up in columns 6 characters wide.
print(f"{'row':>6} {'column':>6} {'R':>6} {'G':>6} {'B':>6}")
print("-" * 34)
for r in sample_rows:
    for c in sample_columns:
        red, green, blue = pixels[r, c]
        print(f"{r:>6} {c:>6} {red:>6} {green:>6} {blue:>6}")

print(f"\nImage: {IMAGE.name}, {rows} rows x {columns} columns, "
      f"{colors} colors, number type {pixels.dtype}")
print(f"Listed every {STEP}th row and column: {n_sampled} of {rows * columns} "
      f"pixels ({100 * n_sampled / (rows * columns):.1f}%)")

# Show the image in Napari.  "rgb=True" tells Napari that the last dimension
# holds red, green and blue, so it draws one color picture instead of three
# grey slices.  "scale" makes the scale bar show micrometers.
viewer = napari.Viewer()
viewer.add_image(pixels, name=IMAGE.stem, rgb=True,
                 scale=(pixel_size, pixel_size), units=("um", "um"))

# Mark the pixels that were listed in the table with small dots, so you can see
# where the sample came from.  Click the eye icon of this layer to hide it.
grid_r, grid_c = np.meshgrid(sample_rows, sample_columns, indexing="ij")
points = np.column_stack([grid_r.ravel(), grid_c.ravel()])
viewer.add_points(points, name="sampled pixels", size=1, face_color="yellow",
                  scale=(pixel_size, pixel_size), units=("um", "um"))
viewer.scale_bar.visible = True

napari.run()
