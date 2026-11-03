"""Filter Nucleus_cropped_noise.tif with three averaging (convolution) kernels,
and compare the results with the median-filtered images.

Run it from the top folder of the workshop repository with:

    uv run src/mean_vs_median_nucleus.py

Run src/median_filter_nucleus.py first: this script reads the median-filtered
images that script saved.

The averaged images are saved next to the original in testImages/, e.g.
Nucleus_cropped_noise_mean_3x3.tif.  The terminal shows, for every filter, how
far its result is from the clean nucleus image (before noise was added).
Napari then opens with all images side by side.  Close it to end the script.
"""

from pathlib import Path

import napari
import numpy as np
import tifffile
from scipy import ndimage

# Where the images live.  Path(__file__) is this script, ".parent.parent" walks
# up two folders to the top of the workshop repository.
REPO = Path(__file__).resolve().parent.parent
INPUT = REPO / "testImages" / "Nucleus_cropped_noise.tif"

# The noisy image was made from the DAPI channel (index 2) of Cell_cropped.tif
# by src/make_noisy_nucleus.py.  That clean image tells us what a perfect
# filter would give back.
CLEAN = REPO / "testImages" / "Cell_cropped.tif"
DAPI_INDEX = 2

# The averaging kernels.  Each number is the weight its pixel gets.
KERNELS = {
    "3x3": np.ones((3, 3)),
    "3x3 center 4": np.array([
        [1, 1, 1],
        [1, 4, 1],
        [1, 1, 1],
    ]),
    "7x7": np.ones((7, 7)),
}

# The median-filtered images saved by src/median_filter_nucleus.py.
MEDIAN_NAMES = ["plus", "3x3", "5x5"]

with tifffile.TiffFile(INPUT) as tif:
    noisy = tif.asarray()
    # The pixel size is stored as "pixels per micron" in the XResolution and
    # YResolution tags.  Keep it, so that the filtered images have the same
    # size in microns as the original.
    page = tif.pages[0]
    resolution = (page.tags["XResolution"].value, page.tags["YResolution"].value)
    unit = tif.imagej_metadata.get("unit", "micron")

clean = tifffile.imread(CLEAN)[DAPI_INDEX]


def error(image):
    """Average distance between an image and the clean one, in pixel values.
    0 would be a perfect result.  int32 allows negative differences."""
    return np.abs(image.astype(np.int32) - clean.astype(np.int32)).mean()


# Every result goes into this dictionary: name -> image.
results = {}

for name, kernel in KERNELS.items():
    # Normalize: divide every weight by the sum of all weights, so the weights
    # add up to 1.  The output is then a weighted average, and the image keeps
    # its brightness (a sum of 9 pixels would be about 9 times too bright).
    kernel = kernel / kernel.sum()

    # Convolution: slide the kernel over the image, and at every position
    # multiply each pixel by its weight and add the results up.  Calculate in
    # decimals (float), then round back to whole numbers like the original.
    averaged = ndimage.convolve(noisy.astype(float), kernel)
    averaged = np.round(averaged).astype(noisy.dtype)
    results[f"mean {name}"] = averaged

    file_name = name.replace(" ", "_")
    output = INPUT.with_name(f"{INPUT.stem}_mean_{file_name}.tif")
    tifffile.imwrite(output, averaged, imagej=True, resolution=resolution,
                     metadata={"unit": unit})
    print(f"Saved {output.name}")

for name in MEDIAN_NAMES:
    median_file = INPUT.with_name(f"{INPUT.stem}_median_{name}.tif")
    if not median_file.exists():
        raise SystemExit(f"{median_file.name} not found: "
                         "run  uv run src/median_filter_nucleus.py  first.")
    results[f"median {name}"] = tifffile.imread(median_file)

# The comparison: lower is better.
print(f"\nAverage difference from the clean nucleus (lower is better):")
print(f"  {'noisy original':<20} {error(noisy):8.1f}")
for name, image in results.items():
    print(f"  {name:<20} {error(image):8.1f}")

# Show everything side by side, all with the same contrast so that brightness
# can be compared fairly.
numerator, denominator = resolution[0]
pixel_size = denominator / numerator  # microns per pixel
scale = (pixel_size, pixel_size)
limits = (int(clean.min()), int(clean.max()))

viewer = napari.Viewer(title="Mean vs median filters")
viewer.add_image(clean, name="clean (no noise)", scale=scale,
                 units=("µm", "µm"), contrast_limits=limits)
viewer.add_image(noisy, name="noisy original", scale=scale,
                 units=("µm", "µm"), contrast_limits=limits)
for name, image in results.items():
    viewer.add_image(image, name=name, scale=scale, units=("µm", "µm"),
                     contrast_limits=limits)
viewer.grid.enabled = True
viewer.scale_bar.visible = True
napari.run()
