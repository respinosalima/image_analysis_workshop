"""Animations that show how a square wave is built from sine waves.

Run it from the top folder of the workshop repository with:

    uv run src/fourier_series_demo.py

The animations (and one still picture of each) are saved in Pictures/fourier/:

    circle_to_wave.gif     a point going around a circle draws a sine wave;
                           the radius is the amplitude, the starting angle the phase
    square_wave_build.gif  adding sine waves one by one approaches a square wave
    epicycles.gif          the same sum, drawn as circles riding on circles
    phase_scramble.gif     same amplitudes, different phases: no more square wave
    phase_shift.gif        moving the square wave in time only changes the phases
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw into files only, no window on screen
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Circle, ConnectionPatch

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "Pictures" / "fourier"

# Colors.  Each sine wave keeps its own color in every picture.
WAVE_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4",
               "#008300", "#6250d6", "#e34948"]
SUM_COLOR = "#2a78d6"
NEW_COLOR = "#eb6834"
TARGET_COLOR = "#555555"
FADED_COLOR = "#c8c8c8"

# The square wave: +1 for half a second, -1 for half a second, repeating.
PERIOD = 1.0  # seconds
TIME = np.linspace(0, 2 * PERIOD, 4000)  # show two repeats (enough points to draw fast waves smoothly)


def square_wave(t, shift=0.0):
    return np.where(((t - shift) / PERIOD) % 1 < 0.5, 1.0, -1.0)


def square_wave_recipe(n_waves, shift=0.0):
    """The frequencies, amplitudes and phases of the sine waves in a square wave.

    A square wave contains only the odd multiples (1, 3, 5, ...) of its basic
    frequency, with amplitude 4 / (pi x multiple): the higher the frequency, the
    smaller the wave.  When the square wave is moved later in time by "shift",
    every wave moves with it, which changes its phase but not its amplitude.
    """
    multiples = 2 * np.arange(n_waves) + 1
    freqs = multiples / PERIOD
    amps = 4 / (np.pi * multiples)
    phases = wrap(-2 * np.pi * freqs * shift)
    return freqs, amps, phases


def wrap(angle):
    """Bring an angle (in radians) into the range -180 to +180 degrees."""
    return (angle + np.pi) % (2 * np.pi) - np.pi


def sine(t, freq, amp, phase):
    """One sine wave: amp x sin(2 pi x freq x t + phase)."""
    return amp * np.sin(2 * np.pi * freq * t + phase)


def style_signal_axes(ax, title, xlabel=True):
    ax.set_xlim(TIME[0], TIME[-1])
    ax.set_ylim(-1.6, 1.6)
    ax.axhline(0, color="#999999", lw=0.8)
    ax.set_title(title, loc="left", fontsize=11)
    if xlabel:
        ax.set_xlabel("time (s)")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def style_circle_axes(ax):
    """Use the same height range as the wave plots (-1.6 to 1.6), so a dashed
    line from a point on a circle to the wave plot runs level.  The width range
    is chosen so circles stay round in this panel."""
    fig_width, fig_height = ax.figure.get_size_inches()
    box = ax.get_position()
    half_width = 1.6 * (box.width * fig_width) / (box.height * fig_height)
    ax.set_xlim(-half_width, half_width)
    ax.set_ylim(-1.6, 1.6)
    ax.axis("off")


def draw_spectrum(ax_amp, ax_phase, freqs, amps, phases, max_freq, colors):
    """Bar-like "stem" plots of amplitude and phase for each frequency."""
    for ax in (ax_amp, ax_phase):
        ax.clear()
        ax.axhline(0, color="#999999", lw=0.8)
        ax.set_xlim(0, max_freq + 1)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    for f, a, p, c in zip(freqs, amps, phases, colors):
        ax_amp.plot([f, f], [0, a], color=c, lw=2)
        ax_amp.plot(f, a, "o", color=c, ms=7)
        ax_phase.plot([f, f], [0, np.degrees(p)], color=c, lw=2)
        ax_phase.plot(f, np.degrees(p), "o", color=c, ms=7)
    ax_amp.set_ylim(0, 1.4)
    ax_amp.set_title("Amplitude of each wave", loc="left", fontsize=11)
    ax_phase.set_ylim(-200, 200)
    ax_phase.set_yticks([-180, -90, 0, 90, 180])
    ax_phase.set_ylabel("degrees")
    ax_phase.set_title("Phase of each wave", loc="left", fontsize=11)
    ax_phase.set_xlabel("frequency (Hz)")


def save(anim, fig, name, fps, still_frame):
    anim.save(OUT_DIR / f"{name}.gif", writer=PillowWriter(fps=fps), dpi=80)
    anim._func(still_frame)  # draw one characteristic frame as a still picture
    fig.savefig(OUT_DIR / f"{name}.png", dpi=100)
    plt.close(fig)
    print(f"Saved {name}.gif and {name}.png")


# --- 1. A point going around a circle draws a sine wave ----------------------

def circle_to_wave():
    """Two points go around their circles at the same speed (1 turn per second).

    The gray one has radius 1 and starts at angle 0.  The blue one has a smaller
    radius (amplitude 0.6) and starts 60 degrees further along (phase 60 degrees).
    The height of each point, drawn against time, is a sine wave.
    """
    waves = [(1.0, 0.0, TARGET_COLOR, "amplitude 1.0, phase 0°"),
             (0.6, np.radians(60), SUM_COLOR, "amplitude 0.6, phase 60°")]
    freq = 1 / PERIOD
    n_frames = 80
    fig, (ax_c, ax_w) = plt.subplots(
        1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1, 2.4]})
    fig.subplots_adjust(left=0.03, right=0.98, bottom=0.14, top=0.86, wspace=0.15)

    def draw(frame):
        # Remove the dashed lines of the previous frame.
        for artist in list(fig.artists):
            artist.remove()
        t_now = TIME[-1] * frame / (n_frames - 1)
        ax_c.clear()
        ax_w.clear()
        style_circle_axes(ax_c)
        ax_c.axhline(0, color="#999999", lw=0.8)
        ax_c.axvline(0, color="#999999", lw=0.8)
        style_signal_axes(ax_w, "Height of each point over time")
        shown = TIME <= t_now
        for amp, phase, color, label in waves:
            angle = 2 * np.pi * freq * t_now + phase
            x, y = amp * np.cos(angle), amp * np.sin(angle)
            ax_c.add_patch(Circle((0, 0), amp, fill=False, color=color, lw=1.5))
            ax_c.plot([0, x], [0, y], color=color, lw=2)
            ax_c.plot(x, y, "o", color=color, ms=8)
            # A short mark at the starting angle (time 0) of each point.
            ax_c.plot([0, amp * np.cos(phase)], [0, amp * np.sin(phase)],
                      color=color, lw=1, ls=":")
            ax_w.plot(TIME[shown], sine(TIME[shown], freq, amp, phase),
                      color=color, lw=2, label=label)
            ax_w.plot(t_now, y, "o", color=color, ms=8)
            fig.add_artist(ConnectionPatch((x, y), (t_now, y), "data", "data",
                                           axesA=ax_c, axesB=ax_w, color=color,
                                           lw=0.8, ls="--"))
        ax_c.set_title("Radius = amplitude\nStarting angle (dotted) = phase",
                       loc="left", fontsize=11)
        ax_w.legend(loc="upper right", frameon=False, fontsize=9)

    anim = FuncAnimation(fig, draw, frames=n_frames)
    save(anim, fig, "circle_to_wave", fps=15, still_frame=int(n_frames * 0.35))


# --- 2. Adding sine waves one by one ------------------------------------------

def square_wave_build(n_waves=50):
    freqs, amps, phases = square_wave_recipe(n_waves)
    target = square_wave(TIME)
    fig = plt.figure(figsize=(12, 6.5))
    grid = fig.add_gridspec(2, 2, width_ratios=[2.2, 1], hspace=0.45, wspace=0.25)
    ax_sum = fig.add_subplot(grid[0, 0])
    ax_parts = fig.add_subplot(grid[1, 0])
    ax_amp = fig.add_subplot(grid[0, 1])
    ax_phase = fig.add_subplot(grid[1, 1])

    # Show each new step for a few frames, and hold the last one a bit longer.
    frames = [n for n in range(1, n_waves + 1) for _ in range(3)] + [n_waves] * 6

    def draw(frame):
        n = frames[frame]
        ax_sum.clear()
        ax_parts.clear()
        total = sum(sine(TIME, f, a, p) for f, a, p in
                    zip(freqs[:n], amps[:n], phases[:n]))
        style_signal_axes(ax_sum, f"Sum of the first {n} sine wave"
                          f"{'s' if n > 1 else ''}", xlabel=False)
        ax_sum.plot(TIME, target, color=TARGET_COLOR, lw=1.5, ls="--",
                    label="square wave")
        ax_sum.plot(TIME, total, color=SUM_COLOR, lw=2, label="sum")
        ax_sum.legend(loc="upper right", frameon=False, fontsize=9)

        style_signal_axes(ax_parts, f"The waves added so far (newest: "
                          f"{freqs[n - 1]:g} Hz, amplitude {amps[n - 1]:.2f})")
        for f, a, p in zip(freqs[:n - 1], amps[:n - 1], phases[:n - 1]):
            ax_parts.plot(TIME, sine(TIME, f, a, p), color=FADED_COLOR, lw=1)
        ax_parts.plot(TIME, sine(TIME, freqs[n - 1], amps[n - 1], phases[n - 1]),
                      color=NEW_COLOR, lw=2)

        colors = [FADED_COLOR] * (n - 1) + [NEW_COLOR]
        draw_spectrum(ax_amp, ax_phase, freqs[:n], amps[:n], phases[:n],
                      freqs[-1], colors)
        fig.suptitle("A square wave = a sum of sine waves, each with its own "
                     "frequency, amplitude and phase", fontsize=12)

    anim = FuncAnimation(fig, draw, frames=len(frames))
    save(anim, fig, "square_wave_build", fps=3, still_frame=frames.index(4))


# --- 3. Circles riding on circles ---------------------------------------------

def epicycles(n_waves=5):
    """Each sine wave is a point going around a circle, as in circle_to_wave.

    Put the center of each circle on the moving point of the previous one: the
    height of the last point is then the sum of all the waves.
    """
    freqs, amps, phases = square_wave_recipe(n_waves)
    target = square_wave(TIME)
    n_frames = 160
    fig, (ax_c, ax_w) = plt.subplots(
        1, 2, figsize=(12, 4.6), gridspec_kw={"width_ratios": [1, 1.9]})
    fig.subplots_adjust(left=0.02, right=0.97, bottom=0.22, top=0.9, wspace=0.12)

    def draw(frame):
        # Remove the dashed line of the previous frame.
        for artist in list(fig.artists):
            artist.remove()
        t_now = TIME[-1] * frame / (n_frames - 1)
        ax_c.clear()
        ax_w.clear()
        style_circle_axes(ax_c)
        x, y = 0.0, 0.0
        for i, (f, a, p) in enumerate(zip(freqs, amps, phases)):
            color = WAVE_COLORS[i]
            angle = 2 * np.pi * f * t_now + p
            new_x, new_y = x + a * np.cos(angle), y + a * np.sin(angle)
            ax_c.add_patch(Circle((x, y), a, fill=False, color=color, lw=1.2,
                                 clip_on=False))  # may poke out of the panel
            ax_c.plot([x, new_x], [y, new_y], color=color, lw=2,
                      label=f"{f:g} Hz, amplitude {a:.2f}")
            x, y = new_x, new_y
        ax_c.plot(x, y, "o", color="black", ms=6)
        ax_c.legend(loc="upper center", bbox_to_anchor=(0.5, 0.0), frameon=False,
                    fontsize=8, ncol=2)

        style_signal_axes(ax_w, f"Height of the last point: the sum of "
                          f"{n_waves} sine waves")
        shown = TIME <= t_now
        total = sum(sine(TIME[shown], f, a, p) for f, a, p in
                    zip(freqs, amps, phases))
        ax_w.plot(TIME, target, color=TARGET_COLOR, lw=1.5, ls="--")
        ax_w.plot(TIME[shown], total, color=SUM_COLOR, lw=2)
        ax_w.plot(t_now, y, "o", color="black", ms=6)
        fig.add_artist(ConnectionPatch((x, y), (t_now, y), "data", "data",
                                       axesA=ax_c, axesB=ax_w, color="black",
                                       lw=0.8, ls="--"))

    anim = FuncAnimation(fig, draw, frames=n_frames)
    save(anim, fig, "epicycles", fps=20, still_frame=int(n_frames * 0.15))


# --- 4. Phase matters ---------------------------------------------------------

def phase_animation(name, title, n_waves, phases_for, n_steps, hold):
    """Animate how changing only the phases changes the sum.

    phases_for(fraction) gives the phases to use, for fraction going 0 -> 1.
    The amplitudes never change.
    """
    freqs, amps, _ = square_wave_recipe(n_waves)
    target = square_wave(TIME)
    fig = plt.figure(figsize=(12, 6.5))
    grid = fig.add_gridspec(2, 2, width_ratios=[2.2, 1], hspace=0.45, wspace=0.25)
    ax_sum = fig.add_subplot(grid[:, 0])
    ax_amp = fig.add_subplot(grid[0, 1])
    ax_phase = fig.add_subplot(grid[1, 1])

    # Go from 0 to 1, wait, go back to 0, wait.
    ramp = list(np.linspace(0, 1, n_steps))
    fractions = ramp + [1.0] * hold + ramp[::-1] + [0.0] * hold

    def draw(frame):
        phases = phases_for(fractions[frame])
        ax_sum.clear()
        total = sum(sine(TIME, f, a, p) for f, a, p in zip(freqs, amps, phases))
        style_signal_axes(ax_sum, f"Sum of {n_waves} sine waves")
        ax_sum.set_ylim(-2.6, 2.6)
        ax_sum.plot(TIME, target, color=TARGET_COLOR, lw=1.5, ls="--",
                    label="original square wave")
        ax_sum.plot(TIME, total, color=SUM_COLOR, lw=2, label="sum")
        ax_sum.legend(loc="upper right", frameon=False, fontsize=9)
        draw_spectrum(ax_amp, ax_phase, freqs, amps, phases, freqs[-1],
                      [SUM_COLOR] * n_waves)
        fig.suptitle(title, fontsize=12)

    anim = FuncAnimation(fig, draw, frames=len(fractions))
    save(anim, fig, name, fps=10, still_frame=n_steps + hold // 2)


def phase_scramble(n_waves=10):
    # Random phases, with a fixed seed so the animation is the same every run.
    random_phases = np.random.default_rng(seed=3).uniform(-np.pi, np.pi, n_waves)
    phase_animation(
        "phase_scramble",
        "Same amplitudes, different phases: the square wave is gone",
        n_waves, lambda fraction: wrap(fraction * random_phases),
        n_steps=30, hold=15)


def phase_shift(n_waves=8):
    # Move the square wave a quarter of a period (0.25 s) later in time.
    max_shift = PERIOD / 4
    phase_animation(
        "phase_shift",
        "Moving the square wave in time changes only the phases "
        "(faster waves change more)",
        n_waves, lambda fraction: square_wave_recipe(n_waves, fraction * max_shift)[2],
        n_steps=40, hold=10)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    circle_to_wave()
    square_wave_build()
    epicycles()
    phase_scramble()
    phase_shift()
    print(f"Saved pictures to {OUT_DIR}")


if __name__ == "__main__":
    main()
