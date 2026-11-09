"""Undo smoothing by dividing in Fourier space ("inverse filtering").

Run it from the top folder of the workshop repository with:

    uv run src/fourier_deconvolution_demo.py

Smoothing (convolution) is multiplication in Fourier space, so - in theory -
dividing the Fourier image of the smoothed image by the Fourier image of the
kernel, and transforming back, gives you the original image again.

The script smooths the noisy nucleus image with the 3 x 3 Smooth kernel (all
ones, divided by 9), and then tries to undo that in three ways:

  1. Plain division.
  2. Division, but skipping the waves where the kernel's Fourier image is 0.
  3. Like 2, but first rounding the smoothed image to whole numbers, as
     happens when you save it as a normal (16-bit) image file.

It prints how well each attempt worked, and saves a picture in
Pictures/fourier2d/deconvolution_smooth3x3.png.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw into files only, no window on screen
import matplotlib.pyplot as plt
import numpy as np
import tifffile
from scipy import ndimage

REPO = Path(__file__).resolve().parent.parent
INPUT = REPO / "testImages" / "Nucleus_cropped_noise.tif"
OUTPUT = REPO / "Pictures" / "fourier2d" / "deconvolution_smooth3x3.png"

KERNEL = np.ones((3, 3)) / 9  # the 3 x 3 Smooth kernel from Session 3

# Fourier values smaller than this count as "zero".  (Computers calculate with
# a limited number of decimals, so a 0 often comes out as 0.0000000000000001.)
TINY = 1e-9


def fourier(image):
    """2D Fourier transform, with the zero frequency moved to the center."""
    return np.fft.fftshift(np.fft.fft2(image))


def kernel_as_image(kernel, shape):
    """Put the small kernel in an image of the given size (zeros elsewhere),
    with the kernel's center pixel at position (0, 0).  The Fourier transform
    needs the kernel to be the same size as the image to divide them."""
    padded = np.zeros(shape)
    rows, cols = kernel.shape
    padded[:rows, :cols] = kernel
    return np.roll(padded, (-(rows // 2), -(cols // 2)), axis=(0, 1))


def undo_smoothing(smoothed, kernel_f):
    """Divide the Fourier image of the smoothed image by the Fourier image of
    the kernel, but only where the kernel is not 0.  Where it is 0, the wave
    was completely removed by the smoothing, and we set it to 0."""
    keep = np.abs(kernel_f) > TINY
    smoothed_f = np.fft.fft2(smoothed)
    # np.where(keep, kernel_f, 1) puts a harmless 1 where the kernel is 0,
    # so the computer never divides by 0.  Those waves are set to 0 anyway.
    result_f = np.where(keep, smoothed_f / np.where(keep, kernel_f, 1), 0)
    return np.real(np.fft.ifft2(result_f))


def mean_error(image):
    """How far, on average, the pixels are from the original image."""
    return np.abs(image - original).mean()


original = tifffile.imread(INPUT).astype(float)
kernel_f = np.fft.fft2(kernel_as_image(KERNEL, original.shape))

# Smooth the image.  mode="wrap" treats the image as repeating like tiles,
# which is what the Fourier transform does too.
smoothed = ndimage.convolve(original, KERNEL, mode="wrap")

print(f"Image size: {original.shape[0]} x {original.shape[1]} pixels, "
      f"average pixel value {original.mean():.0f}")
print(f"Smoothed image:            average error {mean_error(smoothed):6.1f}")

# Attempt 1: plain division.
with np.errstate(divide="ignore", invalid="ignore"):  # silence the warnings
    plain = np.real(np.fft.ifft2(np.fft.fft2(smoothed) / kernel_f))
zeros = int((np.abs(kernel_f) <= TINY).sum())
print(f"1. Plain division:         {np.isnan(plain).mean():.0%} of the pixels are "
      f"'nan' (not a number),\n"
      f"   because the kernel's Fourier image is 0 at {zeros} spots: "
      f"dividing by 0 is impossible.")

# Attempt 2: skip the waves where the kernel is 0.
recovered = undo_smoothing(smoothed, kernel_f)
print(f"2. Skipping the zeros:     average error {mean_error(recovered):6.1f}")

# Attempt 3: the same, from a smoothed image rounded to whole numbers.
recovered_rounded = undo_smoothing(np.round(smoothed), kernel_f)
print(f"3. From rounded smoothed:  average error {mean_error(recovered_rounded):6.1f}")

# --- The picture --------------------------------------------------------------

img_range = dict(vmin=original.min(), vmax=original.max())
kernel_amp = np.abs(fourier(kernel_as_image(KERNEL, original.shape)))
difference = recovered - original
diff_limit = np.abs(difference).max()

fig, axes = plt.subplots(2, 3, figsize=(13, 9))
panels = [
    (axes[0, 0], original, "original (noisy) image", "gray", img_range),
    (axes[0, 1], smoothed, "smoothed with 3 x 3 Smooth kernel\n"
     f"(average error {mean_error(smoothed):.0f})", "gray", img_range),
    (axes[0, 2], recovered, "2. smoothing undone, skipping the zeros\n"
     f"(average error {mean_error(recovered):.0f})", "gray", img_range),
    (axes[1, 0], kernel_amp, "Fourier image of the kernel (amplitudes)\n"
     "red: exactly 0 - these waves are lost", "gray", dict(vmin=0, vmax=1)),
    (axes[1, 1], difference, "2. minus original\n(blue: too dark, red: too bright)",
     "RdBu_r", dict(vmin=-diff_limit, vmax=diff_limit)),
    (axes[1, 2], recovered_rounded, "3. same, from smoothed image rounded\n"
     f"to whole numbers (average error {mean_error(recovered_rounded):.0f})",
     "gray", img_range),
]
for ax, data, title, cmap, brightness in panels:
    ax.imshow(data, cmap=cmap, interpolation="nearest", **brightness)
    ax.set_title(title, fontsize=11)
    ax.set_xticks([])
    ax.set_yticks([])

# Mark the spots where the kernel's Fourier image is 0 in red.
zero_rows, zero_cols = np.nonzero(kernel_amp <= TINY)
axes[1, 0].plot(zero_cols, zero_rows, "r.", markersize=1)

fig.suptitle("Undoing smoothing: divide by the kernel in Fourier space", fontsize=14)
fig.subplots_adjust(left=0.02, right=0.99, bottom=0.03, top=0.9,
                    wspace=0.1, hspace=0.25)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUTPUT, dpi=100)
print(f"Saved {OUTPUT}")
