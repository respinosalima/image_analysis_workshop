"""Compare the automatic threshold methods of scikit-image on the DAPI channel.

Run it from the top folder of the workshop repository with:

    uv run src/compare_auto_thresholds.py

What it does:
  1. Reads the DAPI channel of the 3-channel image.
  2. Lets each automatic method in scikit-image pick a threshold, and prints
     the threshold, the % of pixels above it, and the number of objects.
  3. Shows the intensity histogram with every threshold drawn as a line
     (matplotlib window).
  4. After you close the plot, opens napari with the DAPI image and one mask
     per method, so you can switch the masks on and off and compare them.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import napari
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

# --- 2. Let every method choose a threshold ----------------------------------
# Each of these functions looks only at the pixel values (the histogram)
# and returns one number: the threshold.
methods = {
    "Otsu": filters.threshold_otsu,
    "Li": filters.threshold_li,
    "Yen": filters.threshold_yen,
    "Isodata": filters.threshold_isodata,
    "Triangle": filters.threshold_triangle,
    "Mean": filters.threshold_mean,
    "Minimum": filters.threshold_minimum,
}

thresholds = {"Manual (2500)": 2500}
for name, method in methods.items():
    try:
        thresholds[name] = float(method(dapi))
    except RuntimeError as error:
        # "Minimum" fails when the histogram does not have two clear peaks.
        print(f"{name:>14}: failed ({error})")

print(f"\n{'method':>14}  {'threshold':>9}  {'% nucleus':>9}  {'objects':>7}")
masks = {}
for name, value in thresholds.items():
    mask = dapi > value
    masks[name] = mask
    n_objects = measure.label(mask).max()
    print(f"{name:>14}  {value:9.0f}  {mask.mean() * 100:8.1f}%  {n_objects:7d}")

# Multi-Otsu splits the image into 3 classes (background, dim, bright),
# so it returns 2 thresholds instead of 1.
multi = filters.threshold_multiotsu(dapi, classes=3)
print(f"\nMulti-Otsu (3 classes) thresholds: {multi.round(0)}")

# --- 3. Histogram with all thresholds ----------------------------------------
fig, ax = plt.subplots(figsize=(9, 5))
upper = np.percentile(dapi, 99.9)  # ignore the very brightest pixels
ax.hist(dapi.ravel(), bins=256, range=(dapi.min(), upper), color="gray")
ax.set_yscale("log")  # background pixels vastly outnumber nucleus pixels
colors = plt.cm.tab10.colors
for (name, value), color in zip(thresholds.items(), colors):
    ax.axvline(value, color=color, label=f"{name}: {value:.0f}")
ax.set_xlabel("DAPI intensity")
ax.set_ylabel("number of pixels (log scale)")
ax.set_title("DAPI histogram and automatic thresholds")
ax.legend()
plt.tight_layout()
plt.show()  # close this window to continue to napari

# --- 4. Compare the masks in napari ------------------------------------------
viewer = napari.Viewer(title="Automatic thresholds")
scale = (pixel_size, pixel_size)
units = ("µm", "µm")
viewer.add_image(dapi, name="DAPI", scale=scale, units=units,
                 contrast_limits=(dapi.min(), upper))
for name, mask in masks.items():
    viewer.add_labels(mask.astype(np.uint8), name=name, opacity=0.4,
                      scale=scale, units=units, visible=False)
viewer.layers[-1].visible = True  # show one mask to start with
viewer.scale_bar.visible = True
napari.run()
