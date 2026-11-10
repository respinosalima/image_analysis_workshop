"""Threshold the DAPI channel with Otsu, count the objects and plot their sizes.

Run it from the top folder of the workshop repository with:

    uv run src/otsu_object_sizes.py

What it does:
  1. Reads the DAPI channel of the 3-channel image.
  2. Lets the Otsu method pick a threshold, and makes a mask
     (pixels brighter than the threshold = object).
  3. Gives every separate object its own number (labeling) and counts them,
     no matter how big or small they are.
  4. Measures the size (number of pixels) of every object and shows a
     histogram of those sizes.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from bioio import BioImage
from skimage import filters, measure

REPO = Path(__file__).resolve().parent.parent
IMAGE_PATH = (REPO / "testImages" / "3Channel_FF_Corrected_1"
              / "3Channel_FF_Corrected_1_MMStack_Pos0.ome.tif")

# --- 1. Read the DAPI channel ------------------------------------------------
image = BioImage(IMAGE_PATH)
dapi_index = list(image.channel_names).index("DAPI")
dapi = image.get_image_data("YX", T=0, C=dapi_index, Z=0)
pixel_size = image.physical_pixel_sizes.X  # micrometer per pixel

# --- 2. Otsu threshold -------------------------------------------------------
threshold = filters.threshold_otsu(dapi)
mask = dapi > threshold
print(f"Otsu threshold: {threshold:.0f}")

# --- 3. Label and count the objects ------------------------------------------
labels = measure.label(mask)
n_objects = labels.max()
print(f"Total number of objects: {n_objects}")

# --- 4. Size of every object (in pixels) -------------------------------------
# np.bincount counts how many pixels carry each label number.
# Label 0 is the background, so we drop it with [1:].
sizes = np.bincount(labels.ravel())[1:]
print(f"Object sizes: smallest {sizes.min()} px, largest {sizes.max()} px, "
      f"median {np.median(sizes):.0f} px")
print(f"(1 pixel = {pixel_size:.4f} x {pixel_size:.4f} µm "
      f"= {pixel_size**2:.4f} µm²)")

fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(sizes, bins=50, color="steelblue", edgecolor="black")
ax.set_xlabel("object size (number of pixels)")
ax.set_ylabel("number of objects")
ax.set_title(f"Object sizes after Otsu threshold ({threshold:.0f}), "
             f"{n_objects} objects")
plt.tight_layout()
plt.show()
