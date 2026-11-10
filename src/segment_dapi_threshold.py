"""Segment the nuclei (DAPI channel) with a simple, fixed threshold.

Run it from the top folder of the workshop repository with:

    uv run src/segment_dapi_threshold.py

Optionally give a different threshold, for example:

    uv run src/segment_dapi_threshold.py 3000

What it does:
  1. Reads the 3-channel image and picks out the DAPI channel.
  2. Every pixel brighter than the threshold (default 2500) becomes "nucleus",
     everything else becomes "background".  This gives a mask (True/False).
  3. Touching "nucleus" pixels are grouped into objects, and each object gets
     its own number (1, 2, 3, ...).  This is called a label image.
  4. Saves the label image as a TIFF (with the pixel size copied over) and
     shows the DAPI image plus the segmentation in napari.
"""

import sys
from pathlib import Path

import napari
import numpy as np
import tifffile
from bioio import BioImage
from skimage import measure

REPO = Path(__file__).resolve().parent.parent
IMAGE_DIR = REPO / "testImages" / "3Channel_FF_Corrected_1"
IMAGE_PATH = IMAGE_DIR / "3Channel_FF_Corrected_1_MMStack_Pos0.ome.tif"
OUTPUT_PATH = IMAGE_DIR / "3Channel_FF_Corrected_1_DAPI_labels.tif"

threshold = float(sys.argv[1]) if len(sys.argv) > 1 else 2500

# --- 1. Read the image and select the DAPI channel ---------------------------
image = BioImage(IMAGE_PATH)
print(f"Channels in the file: {list(image.channel_names)}")
dapi_index = list(image.channel_names).index("DAPI")
dapi = image.get_image_data("YX", T=0, C=dapi_index, Z=0)
pixel_size = image.physical_pixel_sizes.X  # micrometer per pixel
print(f"DAPI image: {dapi.shape[1]} x {dapi.shape[0]} pixels, {dapi.dtype}, "
      f"values {dapi.min()} - {dapi.max()}, pixel size {pixel_size} µm")

# --- 2. Threshold: brighter than the threshold = nucleus ---------------------
mask = dapi > threshold
print(f"Threshold {threshold:g}: {mask.mean() * 100:.1f}% of pixels are 'nucleus'")

# --- 3. Give every separate object its own number ----------------------------
labels = measure.label(mask)
print(f"Found {labels.max()} objects")

# --- 4. Save the labels, copying the pixel size ------------------------------
# TIFF stores resolution as "pixels per unit", so we use 1 / pixel size.
tifffile.imwrite(
    OUTPUT_PATH,
    labels.astype(np.uint16),
    imagej=True,
    resolution=(1 / pixel_size, 1 / pixel_size),
    metadata={"unit": "um", "axes": "YX"},
)
print(f"Saved label image to {OUTPUT_PATH}")

# --- 5. Show the result in napari --------------------------------------------
viewer = napari.Viewer(title="DAPI segmentation")
scale = (pixel_size, pixel_size)
viewer.add_image(dapi, name="DAPI", colormap="blue", blending="additive",
                 scale=scale, units=("µm", "µm"))
viewer.add_labels(labels, name=f"nuclei (threshold {threshold:g})",
                  opacity=0.4, scale=scale, units=("µm", "µm"))
viewer.scale_bar.visible = True
napari.run()
