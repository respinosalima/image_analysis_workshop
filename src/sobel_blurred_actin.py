"""Blur Actin_cropped.tif with the 5 x 5 Gaussian kernel before calculating
the Sobel gradient magnitude, and compare with the gradient magnitude of the
unblurred image.

Run it from the top folder of the workshop repository with:

    uv run src/sobel_blurred_actin.py

Saved next to the original in testImages/:

    Actin_cropped_gauss_5x5_gradient_magnitude.tif

and a plot across one fiber, in Pictures/sobel_blurred_profile.png.
Napari then opens with the images side by side.  Close it to end the script.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw the plot into a file only, no extra window
import matplotlib.pyplot as plt
import napari
import numpy as np
import tifffile
from scipy import ndimage

# Where the image lives.  Path(__file__) is this script, ".parent.parent" walks
# up two folders to the top of the workshop repository.
REPO = Path(__file__).resolve().parent.parent
INPUT = REPO / "testImages" / "Actin_cropped.tif"
OUTPUT = INPUT.with_name(f"{INPUT.stem}_gauss_5x5_gradient_magnitude.tif")
PLOT = REPO / "Pictures" / "sobel_blurred_profile.png"

# The same 5 x 5 Gaussian kernel as in src/gaussian_unsharp_actin.py: it
# reaches 2 pixels out from the center, with sigma = 2 / 3.
RADIUS = 2
SIGMA = RADIUS / 3

# The same Sobel kernels as in src/sobel_actin.py.
SOBEL_X = np.array([
    [-1, 0, 1],
    [-2, 0, 2],
    [-1, 0, 1],
])
SOBEL_Y = SOBEL_X.T  # .T turns the kernel on its side (rows become columns)

with tifffile.TiffFile(INPUT) as tif:
    original = tif.asarray()
    # The pixel size is stored as "pixels per micron" in the XResolution and
    # YResolution tags.  Keep it, so the new image has the same size in
    # microns as the original.
    page = tif.pages[0]
    resolution = (page.tags["XResolution"].value, page.tags["YResolution"].value)
    unit = tif.imagej_metadata.get("unit", "micron")


def gradient_magnitude(image):
    """Sobel x and Sobel y, combined with Pythagoras: sqrt(x^2 + y^2)."""
    sobel_x = ndimage.correlate(image, SOBEL_X)
    sobel_y = ndimage.correlate(image, SOBEL_Y)
    return np.sqrt(sobel_x**2 + sobel_y**2)


# Calculate in decimals (float32).
image = original.astype(np.float32)
blurred = ndimage.gaussian_filter(image, sigma=SIGMA, radius=RADIUS)

magnitude_plain = gradient_magnitude(image)
magnitude_blurred = gradient_magnitude(blurred)

tifffile.imwrite(OUTPUT, magnitude_blurred, imagej=True, resolution=resolution,
                 metadata={"unit": unit})
print(f"Saved {OUTPUT.name}")

# Compare the two.  The background between fibers is mostly noise: a quiet
# part of the image there tells us how much noise each version picks up.  We
# call the darkest quarter of the original image "background".
background = original <= np.percentile(original, 25)
for name, magnitude in [("without blur", magnitude_plain),
                        ("with 5x5 blur", magnitude_blurred)]:
    print(f"{name:>14}: largest {magnitude.max():6.0f}, "
          f"average in background {magnitude[background].mean():5.0f}")

# Plot one row across a fiber, the same one as in src/sobel_double_edge.py:
# the place with the strongest Sobel x value, centered on the fiber's peak.
sobel_x = ndimage.correlate(image, SOBEL_X)
row, edge = np.unravel_index(np.argmax(sobel_x), sobel_x.shape)
center = edge + int(np.argmax(original[row, edge:edge + 12]))
columns = np.arange(center - 12, center + 13)

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(columns, magnitude_plain[row, columns], "s-", color="#d62728",
        label="gradient magnitude, without blur")
ax.plot(columns, magnitude_blurred[row, columns], "o-", color="#1f77b4",
        label="gradient magnitude, with 5x5 blur")
ax.axvline(center, color="gray", linestyle="--")
ax.text(center, ax.get_ylim()[1], " middle of fiber", va="top", color="gray")
ax.set_xlabel(f"column (along row {row})")
ax.set_ylabel("gradient magnitude")
ax.set_title("Across one fiber: blurring first smooths the gradient")
ax.legend(loc="upper left")
fig.tight_layout()
PLOT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(PLOT, dpi=100)
print(f"Saved {PLOT}")

numerator, denominator = resolution[0]
pixel_size = denominator / numerator  # microns per pixel
scale = (pixel_size, pixel_size)

# Both magnitudes get the same contrast limits, so they can be compared fairly.
limits = (0, float(magnitude_plain.max()))

viewer = napari.Viewer(title="Gradient magnitude with and without blur")
viewer.add_image(original, name="original", scale=scale, units=("µm", "µm"))
viewer.add_image(blurred, name="blurred 5x5", scale=scale, units=("µm", "µm"))
viewer.add_image(magnitude_plain, name="gradient magnitude, without blur",
                 scale=scale, units=("µm", "µm"), contrast_limits=limits)
viewer.add_image(magnitude_blurred, name="gradient magnitude, with 5x5 blur",
                 scale=scale, units=("µm", "µm"), contrast_limits=limits)
viewer.grid.enabled = True
viewer.scale_bar.visible = True
napari.run()
