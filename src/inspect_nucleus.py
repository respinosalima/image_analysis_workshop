"""Look inside an image: print its pixel values, size and number type, then show it.

Run it from the top folder of the workshop repository.  Give the name of an
image in the testImages folder after the script name:

    uv run src/inspect_nucleus.py nucleus_cropped_2.tif
    uv run src/inspect_nucleus.py nucleus_cropped_3.tif

Without a name it opens nucleus_cropped_1.tif.  You can also give the full path
to an image somewhere else on your computer.

The numbers are printed in the terminal, then Napari opens in its own window.
Close that window to end the script.
"""

import sys
from pathlib import Path

import napari
import numpy as np
import tifffile

# Where the test images live.  Path(__file__) is this script, ".parent.parent"
# walks up two folders to the top of the workshop repository.
REPO = Path(__file__).resolve().parent.parent
IMAGE_DIR = REPO / "testImages"

# sys.argv is the list of words you typed after "uv run": sys.argv[0] is the
# script itself, sys.argv[1] (if present) is the image name you gave.
if len(sys.argv) > 1:
    IMAGE = Path(sys.argv[1])
else:
    IMAGE = Path("nucleus_cropped_1.tif")

# A bare name like "nucleus_cropped_2.tif" is looked up in testImages.  The
# ".tif" ending may be left out.
if not IMAGE.suffix:
    IMAGE = IMAGE.with_suffix(".tif")
if not IMAGE.exists():
    IMAGE = IMAGE_DIR / IMAGE.name
if not IMAGE.exists():
    sys.exit(f"Cannot find the image {IMAGE}")

# tifffile reads the TIFF file and hands back the pixels as a NumPy array: a
# grid of numbers, one number per pixel.
with tifffile.TiffFile(IMAGE) as tif:
    pixels = tif.asarray()

    # ImageJ stores the pixel size as a "resolution": how many pixels fit in
    # one micrometer.  The pixel size is one divided by that.
    numerator, denominator = tif.pages[0].tags["XResolution"].value
    pixel_size = denominator / numerator  # micrometers per pixel

# An image is just a matrix of numbers.  pixels[:10, :10] means "rows 0 to 9,
# columns 0 to 9": the top-left corner of the image.
print(f"First 10 rows and 10 columns of {IMAGE.name}:\n")
with np.printoptions(linewidth=200, precision=1, suppress=True):
    print(pixels[:10, :10])

# .shape gives the size of the matrix as (rows, columns).
rows, columns = pixels.shape
print(f"\nNumber of rows   : {rows}")
print(f"Number of columns: {columns}")

# .dtype is the kind of number stored in each pixel.  Whole-number types such
# as "uint8" (0 - 255) and "uint16" (0 - 65535) have a fixed range.  "float32"
# stores numbers with a decimal point and has no practical limit.
if np.issubdtype(pixels.dtype, np.integer):
    limits = np.iinfo(pixels.dtype)
    print(f"Number type      : {pixels.dtype}  (whole numbers, "
          f"{limits.min} - {limits.max})")
else:
    print(f"Number type      : {pixels.dtype}  (numbers with a decimal point)")
print(f"Values in image  : {pixels.min()} - {pixels.max()}")
print(f"Pixel size       : {pixel_size:.4f} micrometer")

# Show the image in Napari.  "scale" tells Napari how big each pixel is, so the
# scale bar is in micrometers instead of pixels.
viewer = napari.Viewer()
viewer.add_image(pixels, name=IMAGE.stem, scale=(pixel_size, pixel_size),
                 units=("um", "um"))
viewer.scale_bar.visible = True

napari.run()
