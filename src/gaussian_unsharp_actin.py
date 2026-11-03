"""Blur Actin_cropped.tif with a small (5 x 5) and a large (21 x 21) Gaussian
kernel, subtract each blurred image from the original to get "unsharp mask"
images, and add those masks back to the original to sharpen it.  The sharpened
images are compared with the original and with the sharpen filter result.

Run it from the top folder of the workshop repository with:

    uv run src/gaussian_unsharp_actin.py

Run src/sharpen_actin.py first: this script reads the image it saved.

Six images are saved next to the original in testImages/:

    Actin_cropped_gauss_5x5.tif           blurred with the 5 x 5 kernel
    Actin_cropped_gauss_21x21.tif         blurred with the 21 x 21 kernel
    Actin_cropped_unsharp_5x5.tif         original minus the 5 x 5 blur (mask)
    Actin_cropped_unsharp_21x21.tif       original minus the 21 x 21 blur (mask)
    Actin_cropped_unsharp_sharpened_5x5.tif     original + AMOUNT x 5 x 5 mask
    Actin_cropped_unsharp_sharpened_21x21.tif   original + AMOUNT x 21 x 21 mask

Napari then opens with all images side by side.  Close the Napari window to
end the script.
"""

from pathlib import Path

import napari
import numpy as np
import tifffile
from scipy import ndimage

# Where the image lives.  Path(__file__) is this script, ".parent.parent" walks
# up two folders to the top of the workshop repository.
REPO = Path(__file__).resolve().parent.parent
INPUT = REPO / "testImages" / "Actin_cropped.tif"

# Kernel sizes, in pixels.  A kernel of size 5 reaches 2 pixels out from the
# center on every side (2 + 1 + 2 = 5); size 21 reaches 10 pixels out.
KERNEL_SIZES = [5, 21]

# How much of the mask is added back to the original when sharpening.  0 means
# no sharpening; 1 adds the full mask.  Try 0.5 or 2 and run again.
AMOUNT = 1.0

# The result of the sharpen filter, saved by src/sharpen_actin.py.
SHARPEN_FILTER = REPO / "testImages" / "Actin_cropped_sharpened.tif"
if not SHARPEN_FILTER.exists():
    raise SystemExit(f"{SHARPEN_FILTER.name} not found: "
                     "run  uv run src/sharpen_actin.py  first.")

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


numerator, denominator = resolution[0]
pixel_size = denominator / numerator  # microns per pixel
scale = (pixel_size, pixel_size)

# Original and all sharpened images get the same contrast limits, so their
# brightness can be compared fairly.
contrast = (int(original.min()), int(original.max()))

# Sharpening makes neighboring pixels more different from each other.  One way
# to measure that is the standard deviation: how spread out the pixel values
# are.  It is printed for every sharpened image at the end.
spreads = {"original": original.std()}

viewer = napari.Viewer(title="Gaussian blur and unsharp mask")
viewer.add_image(original, name="original", scale=scale, units=("µm", "µm"),
                 contrast_limits=contrast)

for size in KERNEL_SIZES:
    # A Gaussian kernel gives the center pixel the most weight, and less and
    # less to pixels further away, following a bell curve.  sigma is the width
    # of that bell.  Nearly the whole bell lies within 3 sigma of the center,
    # so to fill a kernel reaching "radius" pixels out we use
    # sigma = radius / 3, and cut the kernel off at that radius.
    radius = size // 2
    sigma = radius / 3
    # The weights of a Gaussian kernel add up to 1, so the blurred image keeps
    # the brightness of the original.  Calculate in decimals (float32).
    blurred = ndimage.gaussian_filter(original.astype(np.float32), sigma=sigma,
                                      radius=radius)

    # Unsharp mask: the original minus its blurred version.  The blur keeps
    # the slow, smooth changes (background, broad shapes); subtracting it
    # leaves only what the blur removed: the fine details, such as fibers and
    # edges.  The result is positive on bright details and negative next to
    # them, so it stays in decimals (float32) instead of whole numbers.
    unsharp = original.astype(np.float32) - blurred

    print(f"{size} x {size} kernel: sigma = {sigma:.2f} pixels")
    save(blurred, f"gauss_{size}x{size}")
    save(unsharp, f"unsharp_{size}x{size}")

    viewer.add_image(blurred, name=f"Gaussian {size}x{size}", scale=scale,
                     units=("µm", "µm"))
    viewer.add_image(unsharp, name=f"unsharp {size}x{size}", scale=scale,
                     units=("µm", "µm"))

    # Unsharp masking: add the details (the mask) back to the original.  The
    # fine details are then counted twice (with AMOUNT = 1), so they stand
    # out more, while smooth areas, where the mask is about 0, stay the same.
    sharpened = original + AMOUNT * unsharp
    # Store as whole numbers from 0 to 65535 like the original (uint16): clip
    # values that fall outside that range, then round.
    limits = np.iinfo(original.dtype)
    sharpened = np.round(np.clip(sharpened, limits.min, limits.max))
    sharpened = sharpened.astype(original.dtype)

    save(sharpened, f"unsharp_sharpened_{size}x{size}")
    name = f"unsharp-mask sharpened {size}x{size}"
    spreads[name] = sharpened.std()
    viewer.add_image(sharpened, name=name, scale=scale, units=("µm", "µm"),
                     contrast_limits=contrast)

sharpen_filter = tifffile.imread(SHARPEN_FILTER)
spreads["sharpen filter (3x3)"] = sharpen_filter.std()
viewer.add_image(sharpen_filter, name="sharpen filter (3x3)", scale=scale,
                 units=("µm", "µm"), contrast_limits=contrast)

print(f"\nSpread of pixel values (std), higher = more contrast between "
      f"neighbors (AMOUNT = {AMOUNT}):")
for name, spread in spreads.items():
    print(f"  {name:<35} {spread:6.0f}")

viewer.grid.enabled = True
viewer.scale_bar.visible = True
napari.run()
