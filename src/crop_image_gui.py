"""Pick an image and a rectangle to crop with a small window, then open the
crop in Napari.

Run it from the top folder of the workshop repository with:

    uv run src/crop_image_gui.py

A small window opens first.  Choose the image file, type the x1, x2, y1 and
y2 positions (in pixels), and press "Crop and open in napari".  Napari then
opens with the cropped image, keeping the original pixel size, so the scale
bar and measurements stay correct.  Tick "save crop" to also save the crop as
an OME-TIFF next to the original image, with "_crop" added to its name.
Close the Napari window to end the script.
"""

from pathlib import Path

import napari
import tifffile
from bioio import BioImage
from magicgui import magicgui
from magicgui.widgets import Label

# Where the images live.  Path(__file__) is this script, ".parent.parent" walks
# up two folders to the top of the workshop repository.
REPO = Path(__file__).resolve().parent.parent
IMAGE_FOLDER = REPO / "testImages"

# The choices made in the window end up here, so we can use them after the
# window closes.
choice = {}


# @magicgui turns this function into a window: every argument becomes an input
# field (a file picker for the Path, number boxes for the ints, a tick box for
# the bool), and the function runs when the button is pressed.
@magicgui(
    call_button="Crop and open in napari",
    image_file={"label": "image", "mode": "r",
                "filter": "Images (*.tif *.tiff *.nd2 *.czi)"},
    x1={"label": "x1 (left)", "max": 100_000},
    x2={"label": "x2 (right)", "max": 100_000},
    y1={"label": "y1 (top)", "max": 100_000},
    y2={"label": "y2 (bottom)", "max": 100_000},
    save_crop={"label": "save crop"},
)
def crop_window(image_file: Path = IMAGE_FOLDER, x1: int = 0, x2: int = 0,
                y1: int = 0, y2: int = 0, save_crop: bool = False):
    # Check the numbers before closing the window, so mistakes can be fixed.
    if not image_file.is_file():
        info.value = "Please choose an image file first."
        return
    if x1 >= x2 or y1 >= y2:
        info.value = "x1 must be smaller than x2, and y1 smaller than y2."
        return
    choice.update(image_file=image_file, x1=x1, x2=x2, y1=y1, y2=y2,
                  save_crop=save_crop)
    crop_window.close()


# A line of text at the top of the window that tells you the image size.
info = Label(value="Choose an image to see its size.")
crop_window.insert(0, info)


def on_image_chosen(image_file: Path):
    """When a file is picked, read its size and fill in the whole image."""
    if not image_file.is_file():
        return
    dims = BioImage(image_file).dims  # reads only the size, not the pixels
    info.value = (f"{image_file.name}: {dims.X} pixels wide (x), "
                  f"{dims.Y} pixels tall (y), {dims.C} channel(s)")
    # Positions run from 0 to the width/height.  x2 and y2 are the first
    # column/row that is NOT included, like Python slicing.
    crop_window.x1.max = crop_window.x2.max = dims.X
    crop_window.y1.max = crop_window.y2.max = dims.Y
    crop_window.x1.value, crop_window.x2.value = 0, dims.X
    crop_window.y1.value, crop_window.y2.value = 0, dims.Y


crop_window.image_file.changed.connect(on_image_chosen)

# Show the window and wait until it is closed.
crop_window.show(run=True)

if not choice:
    print("Window closed without cropping.")
    raise SystemExit

# BioImage reads many microscopy formats.  Its .data always has 5 dimensions,
# in the order (time, channel, z, y, x), whatever the file looked like.
image = BioImage(choice["image_file"])
pixels = image.data

# Crop: keep all times, channels and z-slices, but only rows y1..y2 and
# columns x1..x2.
x1, x2, y1, y2 = choice["x1"], choice["x2"], choice["y1"], choice["y2"]
cropped = pixels[:, :, :, y1:y2, x1:x2]

# Pixel size in micrometers.  Cropping does not change it, so we reuse it.
# If the file does not record a size, use 1 (that is, measure in pixels).
sizes = image.physical_pixel_sizes
size_z, size_y, size_x = sizes.Z or 1, sizes.Y or 1, sizes.X or 1
channel_names = [str(name) for name in image.channel_names]

print(f"Cropped {choice['image_file'].name} to x {x1}-{x2}, y {y1}-{y2}: "
      f"{x2 - x1} x {y2 - y1} pixels, pixel size {size_x} x {size_y} um")

if choice["save_crop"]:
    # Name the crop after the original, e.g. cells.ome.tif -> cells_crop.ome.tif
    name = choice["image_file"].name.removesuffix(".tiff").removesuffix(".tif")
    name = name.removesuffix(".ome")
    out_file = choice["image_file"].with_name(f"{name}_crop.ome.tif")
    # OME metadata stores the pixel size and channel names with the pixels.
    metadata = {"axes": "TCZYX", "Channel": {"Name": channel_names},
                "PhysicalSizeX": size_x, "PhysicalSizeXUnit": "µm",
                "PhysicalSizeY": size_y, "PhysicalSizeYUnit": "µm"}
    if sizes.Z:
        metadata.update(PhysicalSizeZ=size_z, PhysicalSizeZUnit="µm")
    tifffile.imwrite(out_file, cropped, ome=True, metadata=metadata)
    print(f"Saved crop to {out_file}")

# channel_axis=1 gives each channel its own layer.  scale tells Napari the
# pixel size of the remaining (time, z, y, x) axes, and units says what that
# size is measured in, so the scale bar is right.
viewer = napari.Viewer(title=f"Crop of {choice['image_file'].name}")
viewer.add_image(cropped, channel_axis=1, name=channel_names,
                 scale=(1, size_z, size_y, size_x),
                 units=("pixel", "µm", "µm", "µm"))
viewer.scale_bar.visible = True
napari.run()
