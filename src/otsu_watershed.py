"""Segment the DAPI channel with Otsu + fill holes + watershed, and show the
result in napari.

Run it from the top folder of the workshop repository with:

    uv run src/otsu_watershed.py

Optionally give a different MIN_DISTANCE (in pixels), for example:

    uv run src/otsu_watershed.py 15

What it does:
  1. Reads the DAPI channel of the 3-channel image.
  2. Thresholds it with Otsu and fills the holes -> mask of the nuclei.
  3. Distance transform: every nucleus pixel gets a value equal to its
     distance to the nearest background pixel.  The centre of a round
     nucleus is far from the edge (high value); two touching nuclei look
     like two "hills" with a lower "saddle" where they touch.
  4. Finds the top of every hill (a local maximum of the distance) and uses
     each one as a seed ("marker") for one nucleus.
  5. Watershed: imagine turning the hills upside down into valleys and
     filling them with water, starting at the seeds.  Where water from two
     seeds meets, a dividing line is drawn.  This splits touching nuclei.
  6. Saves the label image (pixel size copied) and opens napari with the
     DAPI image, the labels before watershed and the labels after watershed.
"""

import sys
from pathlib import Path

import napari
import numpy as np
import tifffile
from bioio import BioImage
from scipy import ndimage
from skimage import feature, filters, measure, segmentation

REPO = Path(__file__).resolve().parent.parent
IMAGE_DIR = REPO / "testImages" / "3Channel_FF_Corrected_1"
IMAGE_PATH = IMAGE_DIR / "3Channel_FF_Corrected_1_MMStack_Pos0.ome.tif"
OUTPUT_PATH = IMAGE_DIR / "3Channel_FF_Corrected_1_DAPI_watershed_labels.tif"

# Two seeds must be at least this many pixels apart.  Smaller -> more
# splitting (risk: one nucleus cut in pieces); larger -> less splitting
# (risk: touching nuclei stay merged).  A typical nucleus here is ~45 px wide.
MIN_DISTANCE = int(sys.argv[1]) if len(sys.argv) > 1 else 10

# --- 1. Read the DAPI channel ------------------------------------------------
image = BioImage(IMAGE_PATH)
dapi_index = list(image.channel_names).index("DAPI")
dapi = image.get_image_data("YX", T=0, C=dapi_index, Z=0)
pixel_size = image.physical_pixel_sizes.X  # micrometer per pixel

# --- 2. Otsu threshold + fill holes ------------------------------------------
threshold = filters.threshold_otsu(dapi)
mask = ndimage.binary_fill_holes(dapi > threshold)
labels_before = measure.label(mask)
print(f"Otsu threshold: {threshold:.0f}")
print(f"Objects before watershed: {labels_before.max()}")

# --- 3. Distance transform ---------------------------------------------------
distance = ndimage.distance_transform_edt(mask)
# A little smoothing removes tiny bumps on the edges that would otherwise
# create extra hills (and cut a nucleus into pieces).
distance = filters.gaussian(distance, sigma=2)

# --- 4. One seed at the top of every hill ------------------------------------
peaks = feature.peak_local_max(distance, min_distance=MIN_DISTANCE,
                              labels=labels_before, exclude_border=False)
markers = np.zeros_like(labels_before)
markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)

# --- 5. Watershed ------------------------------------------------------------
# The minus sign turns the hills into valleys; mask= keeps the water
# inside the nuclei; connectivity=2 lets it also spread diagonally (the
# same rule measure.label uses), so no edge pixel is left unlabeled.
labels = segmentation.watershed(-distance, markers, mask=mask, connectivity=2)
print(f"Objects after watershed (min_distance={MIN_DISTANCE}): {labels.max()}")

# --- 6. Save, copying the pixel size -----------------------------------------
tifffile.imwrite(
    OUTPUT_PATH,
    labels.astype(np.uint16),
    imagej=True,
    resolution=(1 / pixel_size, 1 / pixel_size),
    metadata={"unit": "um", "axes": "YX"},
)
print(f"Saved {OUTPUT_PATH}")

# --- 7. Show in napari -------------------------------------------------------
viewer = napari.Viewer(title="DAPI watershed")
scale = (pixel_size, pixel_size)
units = ("µm", "µm")
viewer.add_image(dapi, name="DAPI", scale=scale, units=units,
                 contrast_limits=(dapi.min(), np.percentile(dapi, 99.9)))
viewer.add_image(distance, name="distance transform", colormap="magma",
                 scale=scale, units=units, visible=False)
viewer.add_labels(labels_before, name="before watershed", opacity=0.5,
                  scale=scale, units=units, visible=False)
viewer.add_labels(labels, name="watershed", opacity=0.5,
                  scale=scale, units=units)
viewer.add_points(peaks, name="seeds", size=6, face_color="white",
                  scale=scale, units=units)
viewer.scale_bar.visible = True
napari.run()
