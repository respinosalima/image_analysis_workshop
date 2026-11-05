"""Make two 64 x 64 pixel images with vertical stripes (30 and 40 stripes from
left to right), and show them next to their Fourier images.

Run it from the top folder of the workshop repository with:

    uv run src/fourier_stripes.py

Napari opens with the two stripe images on top and their Fourier images
(logarithm of the amplitudes) below.  Close the Napari window to end the script.
"""

import napari
import numpy as np

SIZE = 64  # pixels, width and height
STRIPE_COUNTS = [30, 40]  # number of bright stripes from left to right


def stripes(n_stripes):
    """Smooth vertical stripes: brightness goes up and down n_stripes times
    from the left to the right edge (a cosine wave, values 0 to 1)."""
    x = np.arange(SIZE)
    one_row = 0.5 + 0.5 * np.cos(2 * np.pi * n_stripes * x / SIZE)
    return np.tile(one_row, (SIZE, 1))  # repeat the row for every image row


def log_fourier_amplitude(image):
    """Logarithm of the amplitudes of the Fourier image, 0 Hz in the center."""
    return np.log1p(np.abs(np.fft.fftshift(np.fft.fft2(image))))


viewer = napari.Viewer(title="Stripes and their Fourier images")
layers = []
for n in STRIPE_COUNTS:
    image = stripes(n)
    fourier = log_fourier_amplitude(image)

    # Find the two bright spots that are not the center (the center is the
    # average brightness).  Their distance from the center, in pixels, is the
    # number of stripes the Fourier transform "sees".
    center = SIZE // 2
    fourier_no_center = fourier.copy()
    fourier_no_center[center, center] = 0
    spot_cols = np.flatnonzero(fourier_no_center[center] >
                               0.5 * fourier_no_center.max())
    print(f"{n} stripes ({SIZE / n:.2f} pixels per stripe): spots at "
          f"{(spot_cols - center).tolist()} pixels from the center")

    layers.append((image, f"{n} stripes", (0, 1)))
    layers.append((fourier, f"Fourier image, {n} stripes", None))

# Napari puts the last added layer top-left, so add them in reverse order:
# stripe images on top, their Fourier images below.
for data, name, contrast in [layers[3], layers[1], layers[2], layers[0]]:
    viewer.add_image(data, name=name, contrast_limits=contrast,
                     interpolation2d="nearest")  # show the real pixels

viewer.grid.enabled = True
viewer.grid.shape = (2, 2)
napari.run()
