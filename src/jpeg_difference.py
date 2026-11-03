"""Save an image as JPEG, read it back, and show what the JPEG compression
changed.  The image can be re-saved as JPEG many times in a row (each time
starting from the previous JPEG), to see whether the damage keeps growing.

Run it from the top folder of the workshop repository with:

    uv run src/jpeg_difference.py

Napari opens with three layers: the original TIFF, the JPEG copy, and a map of
the differences between them.  Use the eye icons in the layer list to switch
between them.  Close the Napari window to end the script.
"""

from pathlib import Path

import napari
import numpy as np
import imageio.v3 as iio
import tifffile

# Where the image lives.  Path(__file__) is this script, ".parent.parent" walks
# up two folders to the top of the workshop repository.
REPO = Path(__file__).resolve().parent.parent
IMAGE = REPO / "testImages" / "Cell_cropped_2.tif"

# JPEG quality, from 1 (tiny file, very visible damage) to 100 (big file,
# almost no damage).  Try changing it and running the script again.
QUALITY = 75

# How many times in a row to save as JPEG and read it back.  1 means a single
# save.
N_SAVES = 100

# The JPEG goes next to the original, named after it, the quality and the
# number of saves, e.g. Cell_cropped_2_quality75_100saves.jpg.
JPEG = IMAGE.with_name(f"{IMAGE.stem}_quality{QUALITY}_{N_SAVES}saves.jpg")

# Read the original.  It is a color image: an array of (rows, columns, colors)
# with colors in the order red, green, blue.
with tifffile.TiffFile(IMAGE) as tif:
    original = tif.asarray()

    # ImageJ stores the pixel size as a "resolution": how many pixels fit in
    # one micrometer.  The pixel size is one divided by that.
    numerator, denominator = tif.pages[0].tags["XResolution"].value
    pixel_size = denominator / numerator  # micrometers per pixel

# Save as JPEG, then read the JPEG back from disk, so we see exactly what a
# JPEG file contains.  JPEG cannot store the pixel size in micrometers, so we
# keep using the one from the original.  imageio reads and writes common
# picture formats; it comes installed together with scikit-image.
# Each pass saves the image we got back from the previous pass, the way a file
# gets re-saved every time someone edits and saves it again.
jpeg = original
for save in range(1, N_SAVES + 1):
    iio.imwrite(JPEG, jpeg, quality=QUALITY)
    jpeg = iio.imread(JPEG)

    # Report how far the image has drifted from the original after a few of
    # the saves.  (int16 is explained just below.)
    if save in (1, 2, 5, 10, 20, 50, 100, N_SAVES):
        drift = np.abs(original.astype(np.int16) - jpeg.astype(np.int16))
        print(f"After {save:>3} save(s): average change {drift.mean():.2f}, "
              f"largest {drift.max()}")

# The difference, pixel by pixel and color by color.  Pixel values are stored
# as whole numbers from 0 to 255 that cannot go negative, so first convert to
# a type that can (int16); otherwise 3 - 5 would wrap around to 254.
difference = original.astype(np.int16) - jpeg.astype(np.int16)

# For the picture, add up how much red, green and blue changed (ignoring
# whether they went up or down).  0 means the pixel is unchanged.
change = np.abs(difference).sum(axis=2)

print(f"Original: {IMAGE.name}, {IMAGE.stat().st_size / 1000:.0f} kB")
print(f"JPEG (quality {QUALITY}, {N_SAVES} saves): {JPEG.name}, {JPEG.stat().st_size / 1000:.0f} kB")
print(f"Pixels that changed: {100 * np.mean(change > 0):.1f}%")
print(f"Average change per color value: {np.abs(difference).mean():.2f} "
      f"(largest: {np.abs(difference).max()}) on a 0-255 scale")

# Show all three.  scale gives every layer the original pixel size, so the
# scale bar is in micrometers and the layers line up.
scale = (pixel_size, pixel_size)
viewer = napari.Viewer(title="Original vs JPEG")
viewer.add_image(original, name="original (TIFF)", scale=scale,
                 units=("µm", "µm"))
viewer.add_image(jpeg, name=f"JPEG (quality {QUALITY}, {N_SAVES} saves)", scale=scale,
                 units=("µm", "µm"))
viewer.add_image(change, name="changes (bright = more change)", scale=scale,
                 units=("µm", "µm"), colormap="magma")
viewer.scale_bar.visible = True
napari.run()
