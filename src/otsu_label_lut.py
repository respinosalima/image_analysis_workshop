"""Segment the DAPI channel (Otsu + fill holes), label the nuclei and save the
label image with a colour lookup table (LUT) so every object gets its own colour.

Run it from the top folder of the workshop repository with:

    uv run src/otsu_label_lut.py

What it does:
  1. Reads the DAPI channel of the 3-channel image.
  2. Thresholds it with the Otsu method -> mask (True = nucleus).
  3. Fills holes: dark spots that are completely surrounded by nucleus pixels
     become part of the nucleus.
  4. Labels the objects: every separate object gets its own number
     (1, 2, 3, ...); the background stays 0.
  5. Saves the label image as an ImageJ TIFF with a LUT in which every number
     has a clearly different colour (background = black).  The pixel size is
     copied from the original image.  Open the result in Fiji/ImageJ to see
     the colours (napari ignores the stored LUT, but colours labels itself).
"""

import colorsys
from pathlib import Path

import numpy as np
import tifffile
from bioio import BioImage
from scipy import ndimage
from skimage import filters, measure

REPO = Path(__file__).resolve().parent.parent
IMAGE_DIR = REPO / "testImages" / "3Channel_FF_Corrected_1"
IMAGE_PATH = IMAGE_DIR / "3Channel_FF_Corrected_1_MMStack_Pos0.ome.tif"
OUTPUT_PATH = IMAGE_DIR / "3Channel_FF_Corrected_1_DAPI_otsu_labels_LUT.tif"

# --- 1. Read the DAPI channel ------------------------------------------------
image = BioImage(IMAGE_PATH)
dapi_index = list(image.channel_names).index("DAPI")
dapi = image.get_image_data("YX", T=0, C=dapi_index, Z=0)
pixel_size = image.physical_pixel_sizes.X  # micrometer per pixel

# --- 2. Otsu threshold -------------------------------------------------------
threshold = filters.threshold_otsu(dapi)
mask = dapi > threshold
print(f"Otsu threshold: {threshold:.0f}")

# --- 3. Fill holes -----------------------------------------------------------
filled = ndimage.binary_fill_holes(mask)
print(f"Filling holes added {filled.sum() - mask.sum()} pixels")

# --- 4. Label the objects ----------------------------------------------------
labels = measure.label(filled)
n_objects = labels.max()
print(f"Number of objects: {n_objects}")

# --- 5. Build a LUT with distinct colours ------------------------------------
# A LUT is a table of 256 colours: pixel value 0 is shown in colour 0,
# value 1 in colour 1, and so on.  We step around the colour wheel by the
# "golden angle" (about 0.618 of a turn) so that neighbouring numbers get
# very different colours, and vary the brightness a little as well.
lut = np.zeros((3, 256), dtype=np.uint8)  # rows = red, green, blue
golden = 0.618033988749895
for value in range(1, 256):
    hue = (value * golden) % 1.0
    brightness = 1.0 if value % 2 else 0.75
    r, g, b = colorsys.hsv_to_rgb(hue, 0.9, brightness)
    lut[:, value] = (round(r * 255), round(g * 255), round(b * 255))
# value 0 (background) stays black

# A LUT has 256 entries, so the labels must fit in 8 bits (0-255).
if n_objects > 255:
    raise SystemExit(f"{n_objects} objects do not fit in a 256-colour LUT")

# --- 6. Save as ImageJ TIFF with LUT and pixel size --------------------------
# TIFF stores resolution as "pixels per unit", so we use 1 / pixel size.
tifffile.imwrite(
    OUTPUT_PATH,
    labels.astype(np.uint8),
    imagej=True,
    resolution=(1 / pixel_size, 1 / pixel_size),
    metadata={"unit": "um", "axes": "YX", "LUTs": [lut],
              "Ranges": (0.0, 255.0)},
)
print(f"Saved {OUTPUT_PATH}")
