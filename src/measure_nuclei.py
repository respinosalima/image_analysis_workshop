"""Measure the segmented nuclei: count, roundness, area, and DAPI intensity.

First make the label image (watershed, border objects removed) with:

    uv run src/otsu_watershed_no_border.py

Then run this script from the top folder of the workshop repository with:

    uv run src/measure_nuclei.py

What it does:
  1. Reads the label image (each nucleus has its own number) and the
     original DAPI channel.
  2. Keeps only objects larger than MIN_SIZE pixels (tiny specks are not
     nuclei).
  3. Measures for every nucleus:
       - area in µm²  (number of pixels x area of one pixel)
       - roundness = long axis / short axis of the best-fitting ellipse
         (1.0 = perfect circle, larger = more elongated)
       - integrated intensity = sum of the DAPI pixel values in the nucleus
       - mean intensity = average DAPI pixel value in the nucleus
  4. Prints a summary (number of nuclei, mean area, standard deviation and
     standard error of the area) and saves the table as a CSV file that you
     can open in Excel.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import tifffile
from bioio import BioImage
from skimage import measure

REPO = Path(__file__).resolve().parent.parent
IMAGE_DIR = REPO / "testImages" / "3Channel_FF_Corrected_1"
IMAGE_PATH = IMAGE_DIR / "3Channel_FF_Corrected_1_MMStack_Pos0.ome.tif"
LABELS_PATH = (IMAGE_DIR
               / "3Channel_FF_Corrected_1_DAPI_watershed_noborder_labels.tif")
CSV_PATH = IMAGE_DIR / "3Channel_FF_Corrected_1_DAPI_nuclei_measurements.csv"

MIN_SIZE = 5  # objects must be LARGER than this many pixels

if not LABELS_PATH.exists():
    raise SystemExit(f"Cannot find {LABELS_PATH}\n"
                     "Run  uv run src/otsu_watershed_no_border.py  first.")

# --- 1. Read the label image and the original DAPI channel -------------------
labels = tifffile.imread(LABELS_PATH)
image = BioImage(IMAGE_PATH)
dapi_index = list(image.channel_names).index("DAPI")
dapi = image.get_image_data("YX", T=0, C=dapi_index, Z=0)
pixel_size = image.physical_pixel_sizes.X  # micrometer per pixel
pixel_area = pixel_size ** 2               # µm² per pixel

# --- 2 + 3. Measure every object ---------------------------------------------
# regionprops_table measures each labelled object.  Giving it the DAPI image
# as intensity_image lets it look at the original pixel values under each
# object.
table = pd.DataFrame(measure.regionprops_table(
    labels,
    intensity_image=dapi,
    properties=["label", "area", "major_axis_length", "minor_axis_length",
                "intensity_mean"],
))

# Keep only objects larger than MIN_SIZE pixels.
n_all = len(table)
table = table[table["area"] > MIN_SIZE].copy()
print(f"Objects in the label image: {n_all}")
print(f"Nuclei larger than {MIN_SIZE} pixels: {len(table)}")

table = table.rename(columns={"area": "area_pixels"})
table["area_um2"] = table["area_pixels"] * pixel_area
table["roundness_long_over_short"] = (table["major_axis_length"]
                                      / table["minor_axis_length"])
# Sum of pixel values = average pixel value x number of pixels.
table["intensity_sum"] = table["intensity_mean"] * table["area_pixels"]

table = table[["label", "area_pixels", "area_um2", "roundness_long_over_short",
               "intensity_sum", "intensity_mean"]]

# --- 4. Summary --------------------------------------------------------------
areas = table["area_um2"]
mean_area = areas.mean()
sd_area = areas.std()                   # spread of the individual nuclei
sem_area = sd_area / np.sqrt(len(areas))  # uncertainty of the mean itself

print(f"\nPixel size: {pixel_size} µm  (1 pixel = {pixel_area:.4f} µm²)")
print(f"Mean area                 : {mean_area:.1f} µm²")
print(f"Standard deviation (SD)   : {sd_area:.1f} µm²")
print(f"Standard error (SEM)      : {sem_area:.1f} µm²")
print(f"Mean roundness (long/short): {table['roundness_long_over_short'].mean():.2f}")
print(f"Mean of the mean intensity : {table['intensity_mean'].mean():.0f}")

print("\nPer nucleus:")
print(table.to_string(index=False, float_format=lambda v: f"{v:.2f}"))

table.to_csv(CSV_PATH, index=False)
print(f"\nSaved table to {CSV_PATH}")
