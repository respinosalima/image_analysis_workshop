"""Open one or more images from the testImages folder in napari.

Run it from the top folder of the workshop repository with:

    uv run src/open_in_napari.py

This opens Nucleus_cropped_noise_lowpass.tif and
Nucleus_cropped_noise_fourier_circle.tif.  To open other images, put their
names after the command, for example:

    uv run src/open_in_napari.py Nucleus_cropped_noise.tif Nucleus_cropped_noise_lowpass.tif

Each image opens in its own napari window.  Close all windows to end the script.
"""

import sys
from pathlib import Path

import napari
import tifffile

REPO = Path(__file__).resolve().parent.parent
IMAGE_DIR = REPO / "testImages"

DEFAULT_IMAGES = [
    "Nucleus_cropped_noise_lowpass.tif",
    "Nucleus_cropped_noise_fourier_circle.tif",
]

names = sys.argv[1:] or DEFAULT_IMAGES


def read_image(path):
    """Read the pixels and the pixel size (micrometer per pixel, or None).
    The pixel size is stored as "pixels per micrometer" in the XResolution
    tag, as a fraction (numerator, denominator)."""
    with tifffile.TiffFile(path) as tif:
        pixels = tif.asarray()
        numerator, denominator = tif.pages[0].tags["XResolution"].value
        unit = (tif.imagej_metadata or {}).get("unit", "")
    if unit in ("micron", "um", "µm") and numerator:
        return pixels, denominator / numerator
    return pixels, None  # no pixel size in micrometers stored


for name in names:
    path = IMAGE_DIR / name
    if not path.exists():
        sys.exit(f"Cannot find {path}")

    pixels, pixel_size = read_image(path)

    print(f"{name}")
    print(f"  size       : {pixels.shape[0]} x {pixels.shape[1]} pixels, {pixels.dtype}")
    print(f"  value range: {pixels.min():.4g} - {pixels.max():.4g}")

    viewer = napari.Viewer(title=name)
    # Fourier images have no pixel size in micrometers: their pixels are
    # frequencies (waves), not places in the sample.  Show those in pixels,
    # without a scale bar.
    if pixel_size:
        print(f"  pixel size : {pixel_size:.4g} micrometer")
        viewer.add_image(pixels, name=path.stem,
                         scale=(pixel_size, pixel_size), units=("µm", "µm"))
        viewer.scale_bar.visible = True
    else:
        print("  pixel size : none stored (a Fourier image?) - shown in pixels")
        viewer.add_image(pixels, name=path.stem)

# Start napari and wait until all windows are closed.
napari.run()
