"""Show that convolution in real space is multiplication in Fourier space.

Run it from the top folder of the workshop repository with:

    uv run src/fourier_convolution_demo.py

The noisy nucleus image is smoothed with the 7 x 7 "Smooth" kernel (all ones,
divided by 49) in two ways: by convolution, and by multiplying the Fourier
images and transforming back.  The script prints how much the two results
differ, and saves a picture in Pictures/fourier2d/convolution_theorem.png.
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
OUTPUT = REPO / "Pictures" / "fourier2d" / "convolution_theorem.png"

KERNEL = np.ones((7, 7)) / 49  # a larger version of the Smooth kernel from Session 3


def fourier(image):
    """2D Fourier transform, with the zero frequency moved to the center."""
    return np.fft.fftshift(np.fft.fft2(image))


def kernel_as_image(kernel, shape):
    """Put the small kernel in an image of the given size (zeros elsewhere),
    with the kernel's center pixel at position (0, 0).  The Fourier transform
    needs the kernel to be the same size as the image to multiply them."""
    padded = np.zeros(shape)
    rows, cols = kernel.shape
    padded[:rows, :cols] = kernel
    # Move the center of the kernel to the top left corner.  Pixels that move
    # "off" the top or left edge come back in at the bottom or right edge.
    return np.roll(padded, (-(rows // 2), -(cols // 2)), axis=(0, 1))


image = tifffile.imread(INPUT).astype(float)
kernel_image = kernel_as_image(KERNEL, image.shape)

# Way 1: convolution in real space.  mode="wrap" treats the image as repeating
# like tiles, which is what the Fourier transform does too (see the README).
smoothed = ndimage.convolve(image, KERNEL, mode="wrap")

# Way 2: multiply the Fourier images, pixel by pixel, and transform back.
image_f = np.fft.fft2(image)
kernel_f = np.fft.fft2(kernel_image)
smoothed_via_fourier = np.real(np.fft.ifft2(image_f * kernel_f))

difference = np.abs(smoothed - smoothed_via_fourier).max()
print(f"Pixel values of the smoothed image: {smoothed.min():.0f} - {smoothed.max():.0f}")
print(f"Largest difference between the two ways: {difference:.2g}")

# --- The picture --------------------------------------------------------------

image_amp = np.log1p(np.abs(fourier(image)))
smoothed_amp = np.log1p(np.abs(fourier(smoothed)))
kernel_amp = np.abs(fourier(kernel_image))  # between 0 and 1: no log needed
# Same brightness scale for both images, and for both Fourier images, so that
# you can compare them directly.
img_range = dict(vmin=image.min(), vmax=image.max())
amp_range = dict(vmin=smoothed_amp.min(), vmax=image_amp.max())

# Show the kernel enlarged: a small area around the center of the kernel image.
zoom = 5
kernel_zoom = np.fft.fftshift(kernel_image)
center_row, center_col = kernel_zoom.shape[0] // 2, kernel_zoom.shape[1] // 2
kernel_zoom = kernel_zoom[center_row - zoom:center_row + zoom + 1,
                          center_col - zoom:center_col + zoom + 1]

fig, axes = plt.subplots(2, 3, figsize=(13, 9))
panels = [
    (axes[0, 0], image, "noisy image", img_range),
    (axes[0, 1], kernel_zoom, f"{KERNEL.shape[0]} x {KERNEL.shape[1]} Smooth kernel (enlarged)", {}),
    (axes[0, 2], smoothed, "smoothed image", img_range),
    (axes[1, 0], image_amp, "Fourier image (amplitudes, log)", amp_range),
    (axes[1, 1], kernel_amp, "Fourier image of the kernel\n(amplitudes, not log)",
     dict(vmin=0, vmax=1)),
    (axes[1, 2], smoothed_amp, "Fourier image (amplitudes, log)", amp_range),
]
for ax, data, title, brightness in panels:
    ax.imshow(data, cmap="gray", interpolation="nearest", **brightness)
    ax.set_title(title, fontsize=11)
    ax.set_xticks([])
    ax.set_yticks([])

# The "equation" signs between the panels, placed in figure coordinates.
for x, y, sign in [(0.355, 0.73, "⊛"), (0.672, 0.73, "="),
                   (0.355, 0.27, "×"), (0.672, 0.27, "=")]:
    fig.text(x, y, sign, fontsize=30, ha="center", va="center")
fig.text(0.015, 0.73, "real space", rotation=90, fontsize=13, va="center")
fig.text(0.015, 0.27, "Fourier space", rotation=90, fontsize=13, va="center")
fig.suptitle("Convolution in real space = multiplication in Fourier space",
             fontsize=14)
fig.subplots_adjust(left=0.04, right=0.99, bottom=0.03, top=0.9,
                    wspace=0.25, hspace=0.2)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUTPUT, dpi=100)
print(f"Saved {OUTPUT}")
