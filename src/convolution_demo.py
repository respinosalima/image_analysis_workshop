"""Draw step-by-step pictures that show how a local filter calculates its output.

Run it from the top folder of the workshop repository with:

    uv run src/convolution_demo.py

The pictures are saved in Pictures/convolution/:

    step_1.png ... step_9.png   one picture per position of the structuring element
    convolution.gif             all steps as a short animation
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw into files only, no window on screen
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "Pictures" / "convolution"

# The 5 x 5 input "image": a small bright spot in a darker background.
IMAGE = np.array(
    [
        [1, 2, 1, 0, 1],
        [2, 5, 6, 4, 1],
        [1, 6, 9, 5, 2],
        [0, 4, 5, 3, 1],
        [1, 1, 2, 1, 0],
    ]
)

# The 3 x 3 structuring element.  The numbers are the weights each pixel is
# multiplied with; the output is the average of those products (their sum
# divided by the number of pixels under the structuring element).  The 4 corners are switched off ("None"), so the shape is a
# plus sign rather than a square.  Try changing the weights and run again.
KERNEL = [
    [None, -1, None],
    [-1, 4, -1],
    [None, -1, None],
]

INPUT_COLOR = "#dbe9f6"
KERNEL_COLOR = "#f9c784"
CENTER_COLOR = "#f08a24"
OUTPUT_COLOR = "#b9e4c9"
NEW_COLOR = "#3fae6a"
EDGE_COLOR = "#e6e6e6"


def kernel_cells(row, col):
    """Image pixels covered by the structuring element centered at (row, col),
    with the weight of each one."""
    cells = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            weight = KERNEL[dr + 1][dc + 1]
            if weight is not None:
                cells.append((row + dr, col + dc, weight))
    return cells


def draw_grid(ax, values, colors, title):
    """Draw a 5 x 5 grid of numbers.  Row 0 is at the top, like in an image."""
    n = len(values)
    for r in range(n):
        for c in range(n):
            ax.add_patch(
                Rectangle((c, r), 1, 1, facecolor=colors[r][c], edgecolor="#555", lw=1)
            )
            if values[r][c] != "":
                ax.text(c + 0.5, r + 0.5, str(values[r][c]),
                        ha="center", va="center", fontsize=18)
    ax.set_xlim(-0.1, n + 0.1)
    ax.set_ylim(n + 0.1, -0.5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=14)


def plus_outline(row, col):
    """Corner points of the plus-shaped outline around center pixel (row, col)."""
    x, y = col, row
    return [
        (x, y - 1), (x + 1, y - 1), (x + 1, y), (x + 2, y), (x + 2, y + 1),
        (x + 1, y + 1), (x + 1, y + 2), (x, y + 2), (x, y + 1), (x - 1, y + 1),
        (x - 1, y), (x, y),
    ]


def draw_step(fig, step, centers, output):
    """Draw one picture: input with the structuring element, the average, the
    output."""
    fig.clear()
    ax_in, ax_calc, ax_out = fig.subplots(1, 3, gridspec_kw={"width_ratios": [5, 4, 5]})
    row, col = centers[step]
    cells = kernel_cells(row, col)

    # Input image, with the pixels under the structuring element colored.
    colors = [[INPUT_COLOR] * 5 for _ in range(5)]
    for r, c, _ in cells:
        colors[r][c] = KERNEL_COLOR
    colors[row][col] = CENTER_COLOR
    draw_grid(ax_in, IMAGE, colors, "Input image")
    ax_in.add_patch(Polygon(plus_outline(row, col), closed=True,
                            fill=False, edgecolor="#c0392b", lw=3.5))
    # The weights, written small in the corner of each covered pixel.
    for r, c, w in cells:
        ax_in.text(c + 0.92, r + 0.88, f"×{w}", ha="right", va="bottom",
                   fontsize=9, color="#c0392b")

    # An arrow showing where the structuring element goes next.
    if step + 1 < len(centers):
        nr, nc = centers[step + 1]
        ax_in.add_patch(FancyArrowPatch((col + 0.5, row + 0.5), (nc + 0.5, nr + 0.5),
                                        arrowstyle="-|>", mutation_scale=22,
                                        color="#c0392b", lw=2, ls="--", shrinkA=14, shrinkB=22,
                                        connectionstyle="arc3,rad=-0.3"))

    # The calculation, written out: add up weight x pixel for every covered
    # pixel, then divide by how many pixels there are to get the average.
    terms = [f"{w}×{IMAGE[r][c]}" for r, c, w in cells]
    total = sum(w * IMAGE[r][c] for r, c, w in cells)
    result = round(total / len(cells), 2)
    output[row][col] = result
    lines = [" + ".join(terms[i:i + 3]) for i in range(0, len(terms), 3)]
    text = ("(" + "\n+ ".join(lines) + f")\n/ {len(cells)}"
            f"\n\n= {total} / {len(cells)} = {result:g}")
    ax_calc.axis("off")
    ax_calc.text(0.5, 0.62, text, ha="center", va="center", fontsize=15,
                 family="monospace")
    ax_calc.text(0.5, 0.2, f"Step {step + 1} of {len(centers)}\n"
                 f"center pixel: row {row}, column {col}",
                 ha="center", va="center", fontsize=12, color="#555")
    ax_calc.annotate("", xy=(1.0, 0.62), xytext=(0.85, 0.62),
                     xycoords="axes fraction",
                     arrowprops=dict(arrowstyle="-|>", color="#333", lw=2))

    # Output image: edge pixels (no full neighborhood) gray, done pixels green.
    out_colors = [[EDGE_COLOR] * 5 for _ in range(5)]
    out_values = [["?"] * 5 for _ in range(5)]
    for r, c in centers:
        out_colors[r][c] = "white"
        out_values[r][c] = ""
    for r, c in centers[: step + 1]:
        out_colors[r][c] = OUTPUT_COLOR
        out_values[r][c] = f"{output[r][c]:g}"
    out_colors[row][col] = NEW_COLOR
    draw_grid(ax_out, out_values, out_colors, "Output image")
    fig.tight_layout()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # The structuring element only fits completely at the 3 x 3 inner pixels.
    # Visit them row by row, left to right, starting near the origin (top left).
    centers = [(r, c) for r in range(1, 4) for c in range(1, 4)]
    # float, not whole numbers, because an average can have decimals.
    output = np.zeros(IMAGE.shape, dtype=float)

    fig = plt.figure(figsize=(13, 4.6))
    for step in range(len(centers)):
        draw_step(fig, step, centers, output)
        fig.savefig(OUT_DIR / f"step_{step + 1}.png", dpi=100)

    anim = FuncAnimation(fig, lambda s: draw_step(fig, s, centers, output),
                         frames=len(centers))
    anim.save(OUT_DIR / "convolution.gif", writer=PillowWriter(fps=0.7), dpi=80)
    print(f"Saved pictures to {OUT_DIR}")


if __name__ == "__main__":
    main()
