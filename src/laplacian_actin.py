"""Apply the Laplacian kernel to Actin_cropped.tif, and compare it with the
unsharp masks and unsharp-mask sharpened images.

Run it from the top folder of the workshop repository with:

    uv run src/laplacian_actin.py

Run src/gaussian_unsharp_actin.py first: this script reads the images it saved.

Saved next to the original in testImages/:

    Actin_cropped_laplacian.tif             the Laplacian
    Actin_cropped_laplacian_sharpened.tif   original minus the Laplacian

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
INPUT = REPO / "testImages" / "Actin_cropped.tif"

# The Laplacian kernel: the 4 neighbors minus 4 times the center pixel.  It
# measures how much a pixel differs from the pixels around it:
#   0 where the image is flat or changes evenly (a straight slope),
#   negative where a pixel is brighter than its neighbors (on a fiber),
#   positive where it is darker than its neighbors (right next to a fiber).
# The weights add up to 0, so flat areas give 0.
LAPLACIAN = np.array([
    [0,  1, 0],
    [1, -4, 1],
    [0,  1, 0],
])

# The unsharp mask sizes made by src/gaussian_unsharp_actin.py.
MASK_SIZES = ["5x5", "21x21"]

with tifffile.TiffFile(INPUT) as tif:
    original = tif.asarray()
    # The pixel size is stored as "pixels per micron" in the XResolution and
    # YResolution tags.  Keep it, so the new images have the same size in
    # microns as the original.
    page = tif.pages[0]
    resolution = (page.tags["XResolution"].value, page.tags["YResolution"].value)
    unit = tif.imagej_metadata.get("unit", "micron")


def save(image, name):
    """Save an image next to the original, with the original pixel size."""
    output = INPUT.with_name(f"{INPUT.stem}_{name}.tif")
    tifffile.imwrite(output, image, imagej=True, resolution=resolution,
                     metadata={"unit": unit})
    print(f"Saved {output.name}")


def read(name):
    """Read an image saved by src/gaussian_unsharp_actin.py."""
    path = INPUT.with_name(f"{INPUT.stem}_{name}.tif")
    if not path.exists():
        raise SystemExit(f"{path.name} not found: "
                         "run  uv run src/gaussian_unsharp_actin.py  first.")
    return tifffile.imread(path)


# Slide the kernel over the image, multiply and add.  Decimals (float32),
# because the result can be negative.
laplacian = ndimage.correlate(original.astype(np.float32), LAPLACIAN)
save(laplacian, "laplacian")

# Sharpening with the Laplacian: subtract it from the original.  On a fiber
# the Laplacian is negative, so subtracting it makes the fiber brighter; next
# to a fiber it is positive, so that becomes darker.  Store as whole numbers
# from 0 to 65535 like the original: clip, then round.
limits = np.iinfo(original.dtype)
sharpened = np.clip(original - laplacian, limits.min, limits.max)
sharpened = np.round(sharpened).astype(original.dtype)
save(sharpened, "laplacian_sharpened")

# How alike are the images?  The correlation is +1 when two images go up and
# down together everywhere, 0 when they have nothing to do with each other,
# and -1 when one is the exact opposite of the other.
print("\nCorrelation between the Laplacian and each unsharp mask:")
for size in MASK_SIZES:
    mask = read(f"unsharp_{size}")
    r = np.corrcoef(laplacian.ravel(), mask.ravel())[0, 1]
    print(f"  Laplacian vs mask {size:<6} {r:+.2f}")

print("\nCorrelation between the Laplacian-sharpened image and each "
      "unsharp-mask sharpened image:")
for size in MASK_SIZES:
    unsharp_sharpened = read(f"unsharp_sharpened_{size}")
    r = np.corrcoef(sharpened.ravel(), unsharp_sharpened.ravel())[0, 1]
    print(f"  vs unsharp-mask sharpened {size:<6} {r:+.2f}")

numerator, denominator = resolution[0]
pixel_size = denominator / numerator  # microns per pixel
scale = (pixel_size, pixel_size)
units = ("µm", "µm")

viewer = napari.Viewer(title="Laplacian vs unsharp mask")
contrast = (int(original.min()), int(original.max()))
viewer.add_image(original, name="original", scale=scale, units=units,
                 contrast_limits=contrast)

# Laplacian and masks: red positive, blue negative, white 0.  Each gets its own
# color range, because their numbers are of different sizes; the pattern is
# what matters.  The Laplacian is shown with its sign flipped (-Laplacian), so
# that red means "brighter than the surroundings", as in the masks.
for image, name in [(-laplacian, "-Laplacian"),
                    (read("unsharp_5x5"), "unsharp mask 5x5"),
                    (read("unsharp_21x21"), "unsharp mask 21x21")]:
    largest = float(np.percentile(np.abs(image), 99.5))
    viewer.add_image(image, name=name, scale=scale, units=units,
                     colormap="bwr", contrast_limits=(-largest, largest))

# The sharpened images, all with the contrast of the original.
viewer.add_image(sharpened, name="Laplacian sharpened", scale=scale,
                 units=units, contrast_limits=contrast)
for size in MASK_SIZES:
    viewer.add_image(read(f"unsharp_sharpened_{size}"),
                     name=f"unsharp-mask sharpened {size}", scale=scale,
                     units=units, contrast_limits=contrast)

viewer.grid.enabled = True
viewer.scale_bar.visible = True
napari.run()
