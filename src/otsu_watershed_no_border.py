"""Segment the DAPI channel with Otsu + fill holes + watershed, remove the
objects that touch the image border, and show the result in napari.

Run it from the top folder of the workshop repository with:

    uv run src/otsu_watershed_no_border.py

Optionally give a different MIN_DISTANCE (in pixels), for example:

    uv run src/otsu_watershed_no_border.py 15

What it does:
  1. Reads the DAPI channel of the 3-channel image.
  2. Thresholds it with Otsu and fills the holes -> mask of the nuclei.
  3. Distance transform: every nucleus pixel gets a value equal to its
     distance to the nearest background pixel (one "hill" per nucleus).
  4. Puts a seed on top of every hill.
  5. Watershed: grows the seeds until they meet -> touching nuclei are split.
  6. NEW: removes every object that touches the edge of the image.  Those
     nuclei are only partly in the picture, so their size, shape and
     intensity would be wrong.  This is done AFTER watershed, so that a
     border nucleus touching an inner nucleus only removes the border one.
     The remaining objects are renumbered 1, 2, 3, ... without gaps.
  7. Saves the label image (pixel size copied) and opens napari.
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
OUTPUT_PATH = (IMAGE_DIR
               / "3Channel_FF_Corrected_1_DAPI_watershed_noborder_labels.tif")

# Two seeds must be at least this many pixels apart (see otsu_watershed.py).
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

# --- 3. Distance transform (slightly smoothed) -------------------------------
distance = ndimage.distance_transform_edt(mask)
distance = filters.gaussian(distance, sigma=2)

# --- 4. One seed at the top of every hill ------------------------------------
peaks = feature.peak_local_max(distance, min_distance=MIN_DISTANCE,
                              labels=labels_before, exclude_border=False)
markers = np.zeros_like(labels_before)
markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)

# --- 5. Watershed ------------------------------------------------------------
labels_ws = segmentation.watershed(-distance, markers, mask=mask,
                                   connectivity=2)
print(f"Objects after watershed (min_distance={MIN_DISTANCE}): "
      f"{len(np.unique(labels_ws)) - 1}")

# --- 6. Remove objects touching the image border -----------------------------
# clear_border sets every object that touches the edge to 0 (background).
labels_cleared = segmentation.clear_border(labels_ws)
# Renumber the remaining objects 1, 2, 3, ... so there are no gaps.
labels, _, _ = segmentation.relabel_sequential(labels_cleared)
# Keep the removed objects too, to show them in napari.
removed = np.where((labels_ws > 0) & (labels_cleared == 0), labels_ws, 0)

n_removed = len(np.unique(removed)) - 1
print(f"Objects touching the border (removed): {n_removed}")
print(f"Objects remaining: {labels.max()}")

# --- 7. Save, copying the pixel size -----------------------------------------
tifffile.imwrite(
    OUTPUT_PATH,
    labels.astype(np.uint16),
    imagej=True,
    resolution=(1 / pixel_size, 1 / pixel_size),
    metadata={"unit": "um", "axes": "YX"},
)
print(f"Saved {OUTPUT_PATH}")

# --- 8. Show in napari -------------------------------------------------------
viewer = napari.Viewer(title="DAPI watershed, border objects removed")
scale = (pixel_size, pixel_size)
units = ("µm", "µm")
viewer.add_image(dapi, name="DAPI", scale=scale, units=units,
                 contrast_limits=(dapi.min(), np.percentile(dapi, 99.9)))
removed_layer = viewer.add_labels(removed, name="removed (touch border)",
                                  opacity=0.6, scale=scale, units=units)
removed_layer.contour = 3  # draw only the outline of removed objects
viewer.add_labels(labels, name="watershed, no border objects", opacity=0.5,
                  scale=scale, units=units)
viewer.scale_bar.visible = True
napari.run()
