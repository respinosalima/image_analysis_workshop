"""Show why a thin fiber appears twice in the gradient magnitude image.

Run it from the top folder of the workshop repository with:

    uv run src/sobel_double_edge.py

Run src/sobel_actin.py first: this script reads the images it saved.

A plot opens that follows one row of pixels straight across a fiber, and draws
the brightness of the original image and of the gradient magnitude along that
row.  It is also saved as Pictures/sobel_double_edge.png.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import tifffile

# Where the images live.  Path(__file__) is this script, ".parent.parent" walks
# up two folders to the top of the workshop repository.
REPO = Path(__file__).resolve().parent.parent
IMAGES = REPO / "testImages"
OUTPUT = REPO / "Pictures" / "sobel_double_edge.png"

# How many pixels to show on each side of the fiber.
HALF_WIDTH = 12

original = tifffile.imread(IMAGES / "Actin_cropped.tif")
sobel_x = tifffile.imread(IMAGES / "Actin_cropped_sobel_x.tif")
magnitude = tifffile.imread(IMAGES / "Actin_cropped_gradient_magnitude.tif")

# Find a fiber that runs up and down, so a row of pixels crosses it.  The
# strongest Sobel x value marks the steep left edge of such a fiber.
row, edge = np.unravel_index(np.argmax(sobel_x), sobel_x.shape)

# The middle of the fiber is its brightest point just right of that edge.
right = original[row, edge:edge + HALF_WIDTH]
center = edge + int(np.argmax(right))
start, stop = center - HALF_WIDTH, center + HALF_WIDTH + 1
columns = np.arange(start, stop)

fig, ax_image = plt.subplots(figsize=(8, 4.5))
ax_image.plot(columns, original[row, start:stop], "o-", color="black",
              label="original brightness")
ax_image.set_xlabel(f"column (along row {row})")
ax_image.set_ylabel("original brightness")

# The magnitude has much larger numbers, so it gets its own axis on the right.
ax_magnitude = ax_image.twinx()
ax_magnitude.plot(columns, magnitude[row, start:stop], "s-", color="#d62728",
                  label="gradient magnitude")
ax_magnitude.set_ylabel("gradient magnitude", color="#d62728")

# Mark the middle of the fiber.
ax_image.axvline(center, color="gray", linestyle="--")
ax_image.text(center, ax_image.get_ylim()[1], " middle of fiber",
              va="top", color="gray")

ax_image.set_title("One fiber in the original gives two peaks in the "
                   "gradient magnitude")
fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.85))
fig.tight_layout()

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUTPUT, dpi=100)
print(f"Row {row}, fiber middle at column {center}.  Saved {OUTPUT}")
plt.show()
