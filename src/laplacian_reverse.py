"""Can we get the original image back from its Laplacian?

Run it from the top folder of the workshop repository with:

    uv run src/laplacian_reverse.py

The script tries three things with Actin_cropped.tif and prints the results:

1. It adds 1000 to every pixel and shows that the Laplacian does not change:
   the overall brightness is lost and can never be recovered.
2. It undoes the Laplacian with the Fourier transform.  Apart from that lost
   brightness, this gives the original back almost perfectly.
3. It adds a tiny bit of noise to the Laplacian before undoing it, and shows
   that the result is then far off.

Napari then opens with the results side by side.  Close it to end the script.
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

# The same Laplacian kernel as in src/laplacian_actin.py.
LAPLACIAN = np.array([
    [0,  1, 0],
    [1, -4, 1],
    [0,  1, 0],
])

# How much noise to add to the Laplacian in step 3, as a fraction of how much
# the Laplacian itself varies (0.01 = 1 percent).
NOISE_FRACTION = 0.01

with tifffile.TiffFile(INPUT) as tif:
    original = tif.asarray().astype(np.float64)
    numerator, denominator = tif.pages[0].tags["XResolution"].value
    pixel_size = denominator / numerator  # microns per pixel


def laplacian_of(image):
    # mode="wrap" treats the image as if its left edge continues at its right
    # edge (and top at bottom).  The Fourier transform works the same way, so
    # this keeps step 2 exact.
    return ndimage.correlate(image, LAPLACIAN, mode="wrap")


def undo_laplacian(lap):
    """Undo the Laplacian with the Fourier transform.

    In Fourier space, applying a kernel means multiplying every frequency by a
    fixed number: the kernel's own Fourier transform.  So undoing it means
    dividing by that number.  For the Laplacian that number is 0 for the
    lowest frequency (the overall brightness): that frequency was multiplied
    by 0, so it is gone, and dividing by 0 is impossible.  We set it to 0.
    """
    # Place the kernel in an image-sized array, with its center at the top
    # left corner (pixel 0, 0), where the Fourier transform expects it.
    kernel = np.zeros(lap.shape)
    kernel[:3, :3] = LAPLACIAN
    kernel = np.roll(kernel, shift=(-1, -1), axis=(0, 1))
    kernel_fourier = np.fft.fft2(kernel)

    lap_fourier = np.fft.fft2(lap)
    result_fourier = np.zeros_like(lap_fourier)
    nonzero = np.abs(kernel_fourier) > 1e-12
    result_fourier[nonzero] = lap_fourier[nonzero] / kernel_fourier[nonzero]
    return np.fft.ifft2(result_fourier).real


def error(image):
    """Average difference from the original, in pixel values."""
    return np.abs(image - original).mean()


# 1. A brighter copy of the image has exactly the same Laplacian.
lap = laplacian_of(original)
lap_brighter = laplacian_of(original + 1000)
print("1. Largest difference between the Laplacian of the original and of "
      f"the original + 1000: {np.abs(lap - lap_brighter).max():.6f}")

# 2. Undo the Laplacian.  The result has lost its overall brightness (its
#    average is 0), so we have to borrow the average from the original.
recovered = undo_laplacian(lap)
print(f"2. Recovered from the Laplacian: average {recovered.mean():.1f} "
      f"(the original's is {original.mean():.1f})")
recovered += original.mean()
print(f"   After adding the original's average back: average error "
      f"{error(recovered):.4f}")

# 3. The same, but with a tiny bit of noise added to the Laplacian first, as
#    would happen with any real measurement or rounding.
rng = np.random.default_rng(seed=1)
noise = rng.normal(scale=NOISE_FRACTION * lap.std(), size=lap.shape)
recovered_noisy = undo_laplacian(lap + noise) + original.mean()
print(f"3. With {NOISE_FRACTION:.0%} noise added to the Laplacian: average "
      f"error {error(recovered_noisy):.1f}")

scale = (pixel_size, pixel_size)
units = ("µm", "µm")
contrast = (float(original.min()), float(original.max()))
viewer = napari.Viewer(title="Reversing the Laplacian")
viewer.add_image(original, name="original", scale=scale, units=units,
                 contrast_limits=contrast)
viewer.add_image(recovered, name="recovered from Laplacian", scale=scale,
                 units=units, contrast_limits=contrast)
viewer.add_image(recovered_noisy, name=f"recovered, {NOISE_FRACTION:.0%} noise",
                 scale=scale, units=units, contrast_limits=contrast)
viewer.add_image(recovered_noisy - original, name="error with noise",
                 scale=scale, units=units, colormap="bwr",
                 contrast_limits=(-1000, 1000))
viewer.grid.enabled = True
viewer.scale_bar.visible = True
napari.run()
