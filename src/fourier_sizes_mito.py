"""Compare how much memory Mito_Cropped.tif takes before and after the Fourier
transform.

Run it from the top folder of the workshop repository with:

    uv run src/fourier_sizes_mito.py
"""

from pathlib import Path

import numpy as np
import tifffile

REPO = Path(__file__).resolve().parent.parent
INPUT = REPO / "testImages" / "Mito_Cropped.tif"

image = tifffile.imread(INPUT)
fourier = np.fft.fft2(image)  # the full Fourier image: amplitude AND phase
log_amplitude = np.log1p(np.abs(fourier))  # what napari showed: amplitude only
half = np.fft.rfft2(image)  # only the non-redundant half (see below)


def describe(name, data):
    """Print the number of pixels, the bytes per pixel and the total size."""
    print(f"{name:<38} {data.shape[0]:>4} x {data.shape[1]:<4} "
          f"{data.dtype.name:<11} {data.itemsize:>2} bytes/pixel "
          f"{data.nbytes / 1024:>7.0f} KB")


print(f"File on disk: {INPUT.stat().st_size / 1024:.0f} KB\n")
describe("original image", image)
describe("Fourier image (complex numbers)", fourier)
describe("log of amplitudes (shown in napari)", log_amplitude)
describe("half Fourier image (rfft2)", half)

# The Fourier image of a real image is symmetric: the wave at (row, col) and
# the one at (-row, -col) have the same amplitude and opposite phase.  So one
# half already holds all the information; rfft2 keeps only that half.
mirrored = np.conj(np.roll(fourier[::-1, ::-1], 1, axis=(0, 1)))
print(f"\nEvery wave matches its mirror image: {np.allclose(fourier, mirrored)}")

# Going back from the full Fourier image returns the original pixel values.
back = np.real(np.fft.ifft2(fourier))
print(f"Transforming back gives the original image: {np.allclose(back, image)}")
