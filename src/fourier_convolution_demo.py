"""Show that convolution in real space is multiplication in Fourier space.

Run it from the top folder of the workshop repository with:

    uv run src/fourier_convolution_demo.py            (5 x 5 Gaussian kernel)
    uv run src/fourier_convolution_demo.py sharpen    (3 x 3 Sharpen kernel)

The noisy nucleus image is filtered with a kernel from Session 3 in two ways:
by convolution, and by multiplying the Fourier images and transforming back.
The kernels you can choose:

    gaussian   the 5 x 5 Gaussian kernel (sigma = 2/3 pixel, the same kernel
               as in src/gaussian_unsharp_actin.py)
    sharpen    the 3 x 3 Sharpen kernel from ImageJ, divided by its sum (4)

The script prints how much the two results differ, and saves a picture in
Pictures/fourier2d/convolution_theorem_<kernel>.png.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw into files only, no window on screen
import matplotlib.pyplot as plt
import numpy as np
import tifffile
from scipy import ndimage

REPO = Path(__file__).resolve().parent.parent
INPUT = REPO / "testImages" / "Nucleus_cropped_noise.tif"

def gaussian_kernel(radius, sigma):
    """A 2D Gaussian (bell shaped) kernel of size (2 * radius + 1) squared.
    First make a 1D bell curve, then multiply it with itself to get 2D.
    The weights add up to 1, so the image keeps its overall brightness."""
    x = np.arange(-radius, radius + 1)          # -2, -1, 0, 1, 2
    bell = np.exp(-x**2 / (2 * sigma**2))
    bell = bell / bell.sum()
    return np.outer(bell, bell)


# The 3 x 3 Sharpen kernel from ImageJ (Session 3).  Its weights add up to
# 12 - 8 = 4, so dividing by 4 makes them add up to 1, and the image keeps its
# overall brightness.
SHARPEN = np.array([
    [-1, -1, -1],
    [-1, 12, -1],
    [-1, -1, -1],
]) / 4

# The kernels you can choose from the command line.  The 5 x 5 Gaussian
# kernel reaches 2 pixels out from the center, with sigma = 2 / 3 (the same
# as in src/gaussian_unsharp_actin.py).
KERNELS = {
    "gaussian": ("5 x 5 Gaussian", gaussian_kernel(radius=2, sigma=2 / 3)),
    "sharpen": ("3 x 3 Sharpen", SHARPEN),
}

choice = sys.argv[1].lower() if len(sys.argv) > 1 else "gaussian"
if choice not in KERNELS:
    sys.exit(f"Unknown kernel '{choice}'.  Choose one of: {', '.join(KERNELS)}")
KERNEL_NAME, KERNEL = KERNELS[choice]
OUTPUT = REPO / "Pictures" / "fourier2d" / f"convolution_theorem_{choice}.png"
print(f"Kernel: {KERNEL_NAME}")


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
filtered = ndimage.convolve(image, KERNEL, mode="wrap")

# Way 2: multiply the Fourier images, pixel by pixel, and transform back.
image_f = np.fft.fft2(image)
kernel_f = np.fft.fft2(kernel_image)
filtered_via_fourier = np.real(np.fft.ifft2(image_f * kernel_f))

difference = np.abs(filtered - filtered_via_fourier).max()
print(f"Pixel values of the filtered image: {filtered.min():.0f} - {filtered.max():.0f}")
print(f"Largest difference between the two ways: {difference:.2g}")

# --- The picture --------------------------------------------------------------

image_amp = np.log1p(np.abs(fourier(image)))
filtered_amp = np.log1p(np.abs(fourier(filtered)))
# No log for the kernel: we want to see by what number each wave is
# multiplied.  1 means "keep as is", below 1 "weaken", above 1 "strengthen".
kernel_amp = np.abs(fourier(kernel_image))
# Same brightness scale for both images, and for both Fourier images, so that
# you can compare them directly.  Filtered pixels brighter or darker than the
# input image are shown as white or black.
img_range = dict(vmin=image.min(), vmax=image.max())
amp_range = dict(vmin=min(image_amp.min(), filtered_amp.min()),
                 vmax=max(image_amp.max(), filtered_amp.max()))
print(f"The kernel multiplies the waves by {kernel_amp.min():.2f} (weakest) "
      f"to {kernel_amp.max():.2f} (strongest)")

print("The kernel (weights rounded to 3 decimals):")
print(np.round(KERNEL, 3))

# Show the kernel enlarged: a small area around the center of the kernel image.
zoom = 5
kernel_zoom = np.fft.fftshift(kernel_image)
center_row, center_col = kernel_zoom.shape[0] // 2, kernel_zoom.shape[1] // 2
kernel_zoom = kernel_zoom[center_row - zoom:center_row + zoom + 1,
                          center_col - zoom:center_col + zoom + 1]

fig, axes = plt.subplots(2, 3, figsize=(13, 9))
panels = [
    (axes[0, 0], image, "noisy image", img_range),
    (axes[0, 1], kernel_zoom, f"{KERNEL_NAME} kernel (enlarged)", {}),
    (axes[0, 2], filtered, "filtered image", img_range),
    (axes[1, 0], image_amp, "Fourier image (amplitudes, log)", amp_range),
    (axes[1, 1], kernel_amp, f"Fourier image of the kernel\n(amplitudes 0 - {kernel_amp.max():.1f}, not log)",
     dict(vmin=0, vmax=max(1, kernel_amp.max()))),
    (axes[1, 2], filtered_amp, "Fourier image (amplitudes, log)", amp_range),
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
