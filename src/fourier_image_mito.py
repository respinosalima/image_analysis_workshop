"""Calculate the Fourier image of Mito_Cropped.tif and show it next to the image.

Run it from the top folder of the workshop repository with:

    uv run src/fourier_image_mito.py

Napari opens with two images side by side: on the left the original, and on the
right the logarithm of the amplitudes of its Fourier image.  Close the Napari
window to end the script.
"""

from pathlib import Path

import napari
import numpy as np
import tifffile

# Where the image lives.  Path(__file__) is this script, ".parent.parent" walks
# up two folders to the top of the workshop repository.
REPO = Path(__file__).resolve().parent.parent
INPUT = REPO / "testImages" / "Mito_Cropped.tif"

with tifffile.TiffFile(INPUT) as tif:
    image = tif.asarray().astype(float)
    # The pixel size is stored as "pixels per micron" in the XResolution tag.
    numerator, denominator = tif.pages[0].tags["XResolution"].value
pixel_size = denominator / numerator  # microns per pixel

rows, cols = image.shape
print(f"Read {INPUT.name}: {rows} x {cols} pixels, {pixel_size:.4f} µm per pixel")

# The Fourier transform describes the image as a sum of 2D waves (stripes).
# Each pixel of the Fourier image is one wave: its position tells the
# direction and how fine the stripes are, and its value tells how strong
# (amplitude) and how shifted (phase) the wave is.
# fftshift moves the slowest wave (the average brightness) to the center, so
# coarse structures are near the middle and fine details further out.
fourier = np.fft.fftshift(np.fft.fft2(image))

# The values are complex numbers: abs() gives the amplitude of each wave.
# The center is many thousands of times brighter than the rest, so take the
# logarithm to see the weaker waves too.  log1p(x) = log(1 + x), so 0 stays 0.
log_amplitude = np.log1p(np.abs(fourier))

# One pixel step in the Fourier image is a change in frequency of
# 1 / (image width in microns): the finest wave (at the edge) has stripes
# 2 pixels apart.
print(f"Fourier image: one pixel = {1 / (cols * pixel_size):.4f} waves per µm "
      f"(left-right), {1 / (rows * pixel_size):.4f} waves per µm (up-down)")
print(f"Finest stripes (at the edge): {2 * pixel_size:.3f} µm apart")

# The two images have different units (microns versus waves per micron), so
# show both in pixels; otherwise Napari would draw one of them tiny.
viewer = napari.Viewer(title="Image and its Fourier image")
viewer.add_image(image, name="Mito_Cropped", colormap="gray")
viewer.add_image(log_amplitude, name="Fourier image (log of amplitudes)",
                 colormap="gray")

# Show the layers side by side in a grid instead of on top of each other.
viewer.grid.enabled = True
napari.run()
