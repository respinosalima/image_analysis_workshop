"""Rotate Actin_cropped.tif by 45 degrees and compare the Fourier images of the
original and the rotated image.

Run it from the top folder of the workshop repository with:

    uv run src/fourier_rotate_actin.py

The rotated image is saved next to the original in testImages/ as
Actin_cropped_rotated_45.tif (same pixel size).  Napari then opens with four
images: the original and rotated image, and below them their Fourier images
(logarithm of the amplitudes).  Close the Napari window to end the script.
"""

from pathlib import Path

import napari
import numpy as np
import tifffile
from scipy import ndimage

REPO = Path(__file__).resolve().parent.parent
INPUT = REPO / "testImages" / "Actin_cropped.tif"
ANGLE = 45  # degrees, counter-clockwise

# Fade the image to black towards its edges before the Fourier transform?
# The Fourier transform treats the image as if it repeats like floor tiles; the
# jump between one edge and the opposite edge adds a bright "+" through the
# center of the Fourier image.  That "+" does NOT rotate with the image (the
# image edges stay horizontal and vertical), which hides what we want to see.
# Set to False to see the "+" appear.
FADE_EDGES = True

with tifffile.TiffFile(INPUT) as tif:
    image = tif.asarray().astype(float)
    # Keep the pixel size: rotating does not change the size of a pixel.
    page = tif.pages[0]
    resolution = (page.tags["XResolution"].value, page.tags["YResolution"].value)
    unit = tif.imagej_metadata.get("unit", "micron")

# Rotate.  reshape=False keeps the image size; the corners that turn in from
# outside the image are filled with 0 (black).  order=1 means each new pixel
# is calculated from its 4 nearest neighbors (linear interpolation).
rotated = ndimage.rotate(image, ANGLE, reshape=False, order=1, mode="constant",
                         cval=0)

output = INPUT.with_name(f"{INPUT.stem}_rotated_{ANGLE}.tif")
tifffile.imwrite(output, np.clip(rotated, 0, 65535).astype(np.uint16),
                 imagej=True, resolution=resolution, metadata={"unit": unit})
print(f"Saved {output.name}")

# Cut out the largest square in the middle that has no black corners in the
# rotated image, and the same square from the original.  Otherwise the edges
# of the black corners would add their own (fake) waves to the Fourier image.
rows, cols = image.shape
side = int(min(rows, cols) / np.sqrt(2)) - 2  # -2: stay clear of the corners
top, left = (rows - side) // 2, (cols - side) // 2
original_square = image[top:top + side, left:left + side]
rotated_square = rotated[top:top + side, left:left + side]
print(f"Compare the middle {side} x {side} pixels of both images")


def log_fourier_amplitude(data):
    """The logarithm of the amplitudes of the Fourier image, center = 0 Hz."""
    if FADE_EDGES:
        # A "Hann window": 1 in the middle, smoothly going to 0 at the edges.
        fade = np.outer(np.hanning(data.shape[0]), np.hanning(data.shape[1]))
        data = (data - data.mean()) * fade
    return np.log1p(np.abs(np.fft.fftshift(np.fft.fft2(data))))


fourier_original = log_fourier_amplitude(original_square)
fourier_rotated = log_fourier_amplitude(rotated_square)

# Show all four in pixels, so they line up in a 2 x 2 grid.  Use the same
# contrast for both Fourier images, so their brightness can be compared.
viewer = napari.Viewer(title=f"Rotating by {ANGLE} degrees")
contrast = (fourier_original.min(), fourier_original.max())
viewer.add_image(fourier_rotated, name=f"Fourier image, rotated {ANGLE}°",
                 contrast_limits=contrast)
viewer.add_image(fourier_original, name="Fourier image, original",
                 contrast_limits=contrast)
viewer.add_image(rotated_square, name=f"rotated {ANGLE}°")
viewer.add_image(original_square, name="original")

# Show the layers side by side in a grid instead of on top of each other.
# Napari puts the last added layer top-left: original | rotated on top,
# their Fourier images below.
viewer.grid.enabled = True
viewer.grid.shape = (2, 2)
napari.run()
