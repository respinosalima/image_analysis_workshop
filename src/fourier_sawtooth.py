"""Build a sawtooth wave (rises steadily, then drops back at once) from sine
waves, and show its "recipe": frequency versus phase, with the brightness of
each spot showing the amplitude of that sine wave.

Run it from the top folder of the workshop repository with:

    uv run src/fourier_sawtooth.py

Two pictures are saved in Pictures/fourier/:

    spectrum_2d_sawtooth.png          the sawtooth wave
    spectrum_2d_sawtooth_shifted.png  the same sawtooth, a quarter second later
"""

import matplotlib

matplotlib.use("Agg")  # draw into files only, no window on screen
import matplotlib.pyplot as plt
import numpy as np

# Re-use the plotting helpers from the square wave scripts (same "src" folder),
# so the pictures look the same and can be compared side by side.
from fourier_2d_spectrum import MAX_FREQ, PHASE_STEP, recipe_image
from fourier_series_demo import (OUT_DIR, PERIOD, SUM_COLOR, TARGET_COLOR, TIME,
                                 sine, style_signal_axes, wrap)

N_WAVES = 20  # one wave for every frequency 1, 2, ... 20 Hz (fills the picture)


def sawtooth_wave(t, shift=0.0):
    """Goes from -1 up to +1 during each period, then jumps back to -1."""
    return 2 * (((t - shift) / PERIOD) % 1) - 1


def sawtooth_recipe(n_waves, shift=0.0):
    """The frequencies, amplitudes and phases of the sine waves in a sawtooth.

    Unlike the square wave, a sawtooth contains ALL multiples (1, 2, 3, ...) of
    its basic frequency, with amplitude 2 / (pi x multiple).  Every wave starts
    "upside down" (phase 180 degrees): together they make the downward jump at
    time 0.  Moving the sawtooth later in time by "shift" changes the phases
    (faster waves change more) but never the amplitudes.
    """
    multiples = np.arange(1, n_waves + 1)
    freqs = multiples / PERIOD
    amps = 2 / (np.pi * multiples)
    phases = wrap(np.pi - 2 * np.pi * freqs * shift)
    return freqs, amps, phases


def draw(shift, title, filename):
    freqs, amps, phases = sawtooth_recipe(N_WAVES, shift)
    fig, (ax_sig, ax_img) = plt.subplots(
        2, 1, figsize=(8, 8), gridspec_kw={"height_ratios": [1, 2.2]})

    # Top: the signal itself (the sum of the waves) and the ideal sawtooth.
    total = sum(sine(TIME, f, a, p) for f, a, p in zip(freqs, amps, phases))
    style_signal_axes(ax_sig, f"Signal: sum of {N_WAVES} sine waves")
    ax_sig.plot(TIME, sawtooth_wave(TIME, shift), color=TARGET_COLOR, lw=1.5,
                ls="--", label="sawtooth wave")
    ax_sig.plot(TIME, total, color=SUM_COLOR, lw=2, label="sum")
    ax_sig.legend(loc="lower right", bbox_to_anchor=(1, 1), ncol=2,
                  frameon=False, fontsize=9)

    # Bottom: the recipe as an image.  "extent" puts the pixel centers at the
    # right frequency and phase on the axes.
    image = recipe_image(freqs, amps, phases)
    half_row = PHASE_STEP / 2
    shown = ax_img.imshow(image, cmap="gray", origin="lower", aspect="auto",
                          interpolation="nearest", vmin=0, vmax=amps.max(),
                          extent=(-0.5, MAX_FREQ + 0.5,
                                  -180 - half_row, 180 + half_row))
    ax_img.set_xlabel("frequency (Hz)")
    ax_img.set_ylabel("phase (degrees)")
    ax_img.set_yticks([-180, -90, 0, 90, 180])
    ax_img.set_xticks(range(0, MAX_FREQ + 1, 2))
    ax_img.set_title("Recipe: one spot per sine wave, brightness = amplitude",
                     loc="left", fontsize=11)
    fig.colorbar(shown, ax=ax_img, label="amplitude", shrink=0.9)

    fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT_DIR / filename, dpi=100)
    plt.close(fig)
    print(f"Saved {filename}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    draw(0.0, "Sawtooth wave", "spectrum_2d_sawtooth.png")
    draw(PERIOD / 4, "The same sawtooth wave, moved 0.25 s later in time",
         "spectrum_2d_sawtooth_shifted.png")


if __name__ == "__main__":
    main()
