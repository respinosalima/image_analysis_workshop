"""Find mitochondria that look like Mito_template.tif in Mito_Cropped.tif with
normalized cross-correlation, and mark them with circles in Napari.

Run it from the top folder of the workshop repository with:

    uv run src/match_template_mito.py

The normalized cross-correlation is saved as testImages/Mito_Cropped_ncc.tif,
and the peaks found are printed in the terminal.  Napari then opens with the
image, the peaks as circles, and the cross-correlation image (hidden at
first: click its eye icon to see it).  Close Napari to end the script.
"""

from pathlib import Path

import napari
import numpy as np
import tifffile
from skimage.feature import match_template, peak_local_max

# Where the images live.  Path(__file__) is this script, ".parent.parent" walks
# up two folders to the top of the workshop repository.
REPO = Path(__file__).resolve().parent.parent
IMAGE = REPO / "testImages" / "Mito_Cropped.tif"
TEMPLATE = REPO / "testImages" / "Mito_template.tif"
OUTPUT = REPO / "testImages" / "Mito_Cropped_ncc.tif"

# Only keep peaks at least this good.  1 is a perfect match.
THRESHOLD = 0.9

# Peaks closer together than this (in pixels) count as one: only the highest
# of them is kept.
MIN_DISTANCE = 4

with tifffile.TiffFile(IMAGE) as tif:
    image = tif.asarray()
    # The pixel size is stored as "pixels per micron" in the XResolution and
    # YResolution tags.  Keep it, so the result has the same size in microns.
    page = tif.pages[0]
    resolution = (page.tags["XResolution"].value, page.tags["YResolution"].value)
    unit = tif.imagej_metadata.get("unit", "micron")

template = tifffile.imread(TEMPLATE)

# Normalized cross-correlation.  At every position, both the template and the
# piece of image under it are first made comparable: their average is
# subtracted and they are divided by how much they vary.  Then they are
# multiplied and added up, as in the plain cross-correlation.  Brightness no
# longer matters, only shape: the result runs from -1 (exact opposite) through
# 0 (no resemblance) to 1 (perfect match).
#
# pad_input=True makes the result as large as the image, with each value at
# the position of the template's center, so peaks line up with the image.
ncc = match_template(image.astype(np.float32), template.astype(np.float32),
                     pad_input=True)

tifffile.imwrite(OUTPUT, ncc.astype(np.float32), imagej=True,
                 resolution=resolution, metadata={"unit": unit})
print(f"Saved {OUTPUT}")

# A peak is a pixel higher than all pixels around it.  peak_local_max gives
# their (row, column) positions, best first.
peaks = peak_local_max(ncc, min_distance=MIN_DISTANCE, threshold_abs=THRESHOLD)

print(f"\nFound {len(peaks)} peaks above {THRESHOLD}, "
      f"at least {MIN_DISTANCE} pixels apart:")
print(f"{'row':>5} {'column':>7} {'value':>7}")
for row, column in peaks:
    print(f"{row:>5} {column:>7} {ncc[row, column]:>7.3f}")

numerator, denominator = resolution[0]
pixel_size = denominator / numerator  # microns per pixel
scale = (pixel_size, pixel_size)
units = ("µm", "µm")

viewer = napari.Viewer(title="Template matching")
viewer.add_image(image, name="Mito_Cropped", scale=scale, units=units)
viewer.add_image(ncc, name="normalized cross-correlation", scale=scale,
                 units=units, colormap="magma", contrast_limits=(-1, 1),
                 visible=False)
# The peaks as rings the size of the template.  The Points layer gets the same
# scale as the image, so its (row, column) positions land on the right pixels.
viewer.add_points(peaks, name=f"peaks > {THRESHOLD}", scale=scale,
                  units=units, symbol="ring", size=template.shape[0],
                  face_color="yellow", border_width=0)
viewer.scale_bar.visible = True
napari.run()
