"""Clean up an Otsu mask of the DAPI channel with erosion + dilation,
then count the objects and plot their sizes.

Run it from the top folder of the workshop repository with:

    uv run src/otsu_erode_dilate_sizes.py

What it does:
  1. Reads the DAPI channel of the 3-channel image.
  2. Thresholds it with the Otsu method -> mask (True = object).
  3. Erodes the mask twice: every round peels one pixel off the edge of
     every object.  Objects that are only a few pixels wide disappear
     completely, and thin bridges between touching objects break.
  4. Dilates the mask twice: every round adds one pixel back around the
     edge.  The surviving objects grow back to roughly their old size, but
     whatever vanished during erosion cannot come back.
     (Erosion followed by the same amount of dilation is called "opening".)
  5. Counts the objects and shows a histogram of their sizes (in pixels),
     before and after the clean-up.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from bioio import BioImage
from skimage import filters, measure, morphology

REPO = Path(__file__).resolve().parent.parent
IMAGE_PATH = (REPO / "testImages" / "3Channel_FF_Corrected_1"
              / "3Channel_FF_Corrected_1_MMStack_Pos0.ome.tif")
ROUNDS = 2  # number of erosions, followed by the same number of dilations

# --- 1. Read the DAPI channel ------------------------------------------------
image = BioImage(IMAGE_PATH)
dapi_index = list(image.channel_names).index("DAPI")
dapi = image.get_image_data("YX", T=0, C=dapi_index, Z=0)

# --- 2. Otsu threshold -------------------------------------------------------
threshold = filters.threshold_otsu(dapi)
mask = dapi > threshold
print(f"Otsu threshold: {threshold:.0f}")

# --- 3 + 4. Erode twice, then dilate twice -----------------------------------
# By default each round looks at the pixel and its 4 direct neighbours
# (up, down, left, right).
cleaned = mask.copy()
for _ in range(ROUNDS):
    cleaned = morphology.erosion(cleaned)
for _ in range(ROUNDS):
    cleaned = morphology.dilation(cleaned)


# --- 5. Count objects and measure their sizes --------------------------------
def object_sizes(binary_mask):
    """Label the objects and return the size (in pixels) of each one."""
    labels = measure.label(binary_mask)
    return np.bincount(labels.ravel())[1:]  # [1:] drops the background (0)


sizes_before = object_sizes(mask)
sizes_after = object_sizes(cleaned)

for name, sizes in [("Before", sizes_before), ("After ", sizes_after)]:
    print(f"{name}: {len(sizes)} objects, smallest {sizes.min()} px, "
          f"largest {sizes.max()} px, median {np.median(sizes):.0f} px")

# Same bins for both histograms, so they can be compared directly.
bins = np.linspace(0, max(sizes_before.max(), sizes_after.max()), 51)
fig, axes = plt.subplots(2, 1, figsize=(8, 7), sharex=True, sharey=True)
axes[0].hist(sizes_before, bins=bins, color="gray", edgecolor="black")
axes[0].set_title(f"Otsu only: {len(sizes_before)} objects")
axes[1].hist(sizes_after, bins=bins, color="steelblue", edgecolor="black")
axes[1].set_title(f"After {ROUNDS}x erosion + {ROUNDS}x dilation: "
                  f"{len(sizes_after)} objects")
axes[1].set_xlabel("object size (number of pixels)")
for ax in axes:
    ax.set_ylabel("number of objects")
plt.tight_layout()
plt.show()
