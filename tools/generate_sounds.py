"""
Sound effect synthesizer for Bubbles game.
Generates WAV files using only Python standard library (wave + math + random).
No external dependencies required.
"""

import math
import random
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 44100
SOUNDS_DIR = Path(__file__).resolve().parents[1] / "assets" / "sounds"
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)


def _normalize(samples, target_peak=0.62):
    """Normalize samples to avoid clipping."""
    peak = max(abs(s) for s in samples)
    if peak == 0:
        return samples
    scale = target_peak / peak
    return [s * scale for s in samples]


def _apply_envelope(samples, attack=0.0, decay=0.0, sustain_level=1.0, sustain=0.0, release=0.1):
    """Apply ADSR envelope to samples."""
    n = len(samples)
    duration = n / SAMPLE_RATE
    total = attack + decay + sustain + release
    if total <= 0:
        total = duration
        release = duration

    env = []
    for i in range(n):
        t = i / SAMPLE_RATE
        if t < attack and attack > 0:
            env.append(t / attack)
        elif t < attack + decay and decay > 0:
            progress = (t - attack) / decay
            env.append(1.0 - (1.0 - sustain_level) * progress)
        elif t < attack + decay + sustain:
            env.append(sustain_level)
        elif release > 0:
            progress = (t - (attack + decay + sustain)) / release
            progress = min(progress, 1.0)
            env.append(sustain_level * (1.0 - progress))
        else:
            env.append(0.0)
    return [s * e for s, e in zip(samples, env)]


def _sine(freq, duration, amplitude=0.5):
    """Generate a sine wave."""
    n = int(SAMPLE_RATE * duration)
    return [amplitude * math.sin(2 * math.pi * freq * i / SAMPLE_RATE) for i in range(n)]


def _sweep_exp(freq_start, freq_end, duration, amplitude=0.5):
    """Exponential frequency sweep."""
    n = int(SAMPLE_RATE * duration)
    if freq_start <= 0:
        freq_start = 1
    if freq_end <= 0:
        freq_end = 1
    ratio = freq_end / freq_start
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = t / duration
        freq = freq_start * (ratio ** progress)
        # Phase integration for exponential sweep
        phase = 2 * math.pi * freq_start * duration * (ratio ** progress - 1) / math.log(ratio)
        samples.append(amplitude * math.sin(phase))
    return samples


def _mix(*tracks):
    """Mix tracks without forcing every sound to the same loudness."""
    if not tracks:
        return []
    length = max(len(t) for t in tracks)
    result = [0.0] * length
    for track in tracks:
        for i, v in enumerate(track):
            result[i] += v
    return result


def _delay(samples, delay_seconds):
    """Prepend silence to samples."""
    n = int(SAMPLE_RATE * delay_seconds)
    return [0.0] * n + samples


def _noise(duration, amplitude=0.3):
    """Generate white noise."""
    n = int(SAMPLE_RATE * duration)
    return [random.uniform(-amplitude, amplitude) for _ in range(n)]


def _lowpass(samples, amount=0.08):
    """Simple one-pole low-pass filter to soften synthetic noise."""
    if not samples:
        return []
    current = samples[0]
    filtered = []
    for sample in samples:
        current += amount * (sample - current)
        filtered.append(current)
    return filtered


def _water_noise(duration, amplitude=0.12):
    """Soft filtered noise with a slow pulse, like distant water movement."""
    samples = _lowpass(_noise(duration, amplitude), amount=0.035)
    return [
        sample * (0.65 + 0.35 * math.sin(2 * math.pi * 2.2 * i / SAMPLE_RATE))
        for i, sample in enumerate(samples)
    ]


def _bubble_sweep(freq_start, freq_end, duration, amplitude=0.3):
    body = _mix(
        _sweep_exp(freq_start, freq_end, duration, amplitude),
        _sine((freq_start + freq_end) * 0.32, duration, amplitude * 0.24),
    )
    return _apply_envelope(body, attack=0.006, decay=duration * 0.25, sustain_level=0.38, release=duration * 0.45)


def _save_wav(filename, samples, target_peak=0.62):
    """Save samples as a 16-bit mono WAV file."""
    samples = _normalize(samples, target_peak=target_peak)
    filepath = SOUNDS_DIR / filename
    with wave.open(str(filepath), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        for s in samples:
            # Clamp to int16 range
            s = max(-1.0, min(1.0, s))
            wf.writeframes(struct.pack("<h", int(s * 32767)))
    print(f"  ✓ {filename}")


# ─── Sound Definitions ───────────────────────────────────────────

def generate_bubble_collect():
    """Soft rising bubble when collecting a free bubble."""
    body = _mix(
        _bubble_sweep(380, 760, 0.13, 0.32),
        _delay(_bubble_sweep(620, 980, 0.08, 0.12), 0.045),
        _water_noise(0.17, 0.035),
    )
    _save_wav("bubble_collect.wav", body, target_peak=0.48)


def generate_seed_collect():
    """Warm life chime when collecting a wild seed."""
    body = _mix(
        _delay(_apply_envelope(_sine(392, 0.26, 0.28), attack=0.018, decay=0.08, sustain_level=0.42, release=0.16), 0.0),
        _delay(_apply_envelope(_sine(523, 0.24, 0.20), attack=0.02, decay=0.08, sustain_level=0.35, release=0.14), 0.045),
        _delay(_bubble_sweep(520, 720, 0.12, 0.10), 0.10),
        _water_noise(0.34, 0.025),
    )
    _save_wav("seed_collect.wav", body, target_peak=0.52)


def generate_bubble_burst():
    """Short muffled pop when a bubble bursts."""
    noise_track = _apply_envelope(_lowpass(_noise(0.09, 0.34), amount=0.12), attack=0.001, decay=0.014, sustain_level=0.12, release=0.07)
    body = _mix(
        noise_track,
        _apply_envelope(_sweep_exp(220, 70, 0.10, 0.32), attack=0.001, decay=0.018, sustain_level=0.20, release=0.08),
        _delay(_bubble_sweep(130, 95, 0.08, 0.12), 0.025),
    )
    _save_wav("bubble_burst.wav", body, target_peak=0.56)


def generate_bubble_split():
    """Hollow bloop when the player splits a bubble."""
    body = _mix(
        _bubble_sweep(520, 190, 0.16, 0.30),
        _delay(_bubble_sweep(260, 410, 0.09, 0.12), 0.075),
        _water_noise(0.21, 0.026),
    )
    _save_wav("bubble_split.wav", body, target_peak=0.50)


def generate_seed_release():
    """Soft submerged drop when releasing a seed."""
    body = _mix(
        _apply_envelope(_sweep_exp(330, 120, 0.22, 0.22), attack=0.012, decay=0.07, sustain_level=0.34, release=0.12),
        _delay(_apply_envelope(_sine(180, 0.18, 0.10), attack=0.02, decay=0.05, sustain_level=0.30, release=0.11), 0.02),
        _water_noise(0.24, 0.022),
    )
    _save_wav("seed_release.wav", body, target_peak=0.44)


def generate_level_complete():
    """Soft life bloom for level completion."""
    bloom = _mix(
        _apply_envelope(_sine(330, 0.52, 0.18), attack=0.045, decay=0.14, sustain_level=0.38, release=0.34),
        _delay(_apply_envelope(_sine(440, 0.44, 0.14), attack=0.04, decay=0.13, sustain_level=0.34, release=0.28), 0.055),
        _delay(_apply_envelope(_sine(550, 0.38, 0.10), attack=0.05, decay=0.12, sustain_level=0.28, release=0.24), 0.12),
        _delay(_bubble_sweep(300, 620, 0.16, 0.08), 0.23),
        _delay(_bubble_sweep(420, 760, 0.13, 0.06), 0.38),
        _water_noise(0.66, 0.018),
    )
    _save_wav("level_complete.wav", bloom, target_peak=0.44)


def generate_player_death():
    """Muffled sinking tone when the player loses."""
    main = _mix(
        _delay(_apply_envelope(_sine(300, 0.28, 0.22), attack=0.02, decay=0.08, sustain_level=0.42, release=0.18), 0.0),
        _delay(_apply_envelope(_sine(230, 0.32, 0.23), attack=0.02, decay=0.09, sustain_level=0.38, release=0.20), 0.13),
        _delay(_apply_envelope(_sine(155, 0.40, 0.25), attack=0.025, decay=0.10, sustain_level=0.34, release=0.26), 0.29),
        _delay(_water_noise(0.42, 0.040), 0.16),
    )
    _save_wav("player_death.wav", main, target_peak=0.54)


def generate_menu_select():
    """Soft water tap for menu confirmation."""
    body = _mix(
        _bubble_sweep(420, 680, 0.070, 0.18),
        _delay(_bubble_sweep(680, 520, 0.045, 0.08), 0.026),
    )
    _save_wav("menu_select.wav", body, target_peak=0.34)


def generate_menu_move():
    """Tiny submerged bubble tick for menu navigation."""
    body = _bubble_sweep(330, 510, 0.045, 0.13)
    _save_wav("menu_move.wav", body, target_peak=0.24)


def generate_bubble_spawn():
    """Gentle rising bubble from a vent."""
    body = _mix(
        _bubble_sweep(240, 620, 0.18, 0.28),
        _delay(_bubble_sweep(360, 760, 0.11, 0.10), 0.06),
        _water_noise(0.23, 0.030),
    )
    _save_wav("bubble_spawn.wav", body, target_peak=0.42)


def generate_leaf_touch():
    """Soft leaf brush through water."""
    noise_track = _apply_envelope(_water_noise(0.22, 0.060), attack=0.02, decay=0.05, sustain_level=0.42, release=0.15)
    tone = _mix(
        _apply_envelope(_sine(360, 0.18, 0.11), attack=0.025, decay=0.06, sustain_level=0.30, release=0.11),
        _delay(_bubble_sweep(470, 620, 0.09, 0.07), 0.04),
    )
    body = _mix(noise_track, tone)
    _save_wav("leaf_touch.wav", body, target_peak=0.36)


def generate_transition():
    """Underwater swell for scene transitions."""
    filtered_noise = _apply_envelope(_water_noise(0.58, 0.080), attack=0.10, decay=0.16, sustain_level=0.44, release=0.30)
    body = _mix(
        _apply_envelope(_sweep_exp(140, 520, 0.56, 0.24), attack=0.08, decay=0.18, sustain_level=0.50, release=0.30),
        _delay(_bubble_sweep(280, 720, 0.20, 0.10), 0.27),
        filtered_noise,
    )
    _save_wav("transition.wav", body, target_peak=0.48)


def generate_pause_in():
    """Pause menu opens with a soft downward water dip."""
    body = _mix(
        _bubble_sweep(520, 220, 0.16, 0.18),
        _water_noise(0.18, 0.024),
    )
    _save_wav("pause_in.wav", body, target_peak=0.34)


def generate_pause_out():
    """Pause menu closes with a small rising bubble."""
    body = _mix(
        _bubble_sweep(240, 560, 0.14, 0.18),
        _delay(_bubble_sweep(440, 700, 0.06, 0.06), 0.05),
    )
    _save_wav("pause_out.wav", body, target_peak=0.32)


def generate_all():
    """Generate all sound effects."""
    random.seed(20260622)
    print("Generating sound effects...\n")
    generate_bubble_collect()
    generate_seed_collect()
    generate_bubble_burst()
    generate_bubble_split()
    generate_seed_release()
    generate_level_complete()
    generate_player_death()
    generate_menu_select()
    generate_menu_move()
    generate_bubble_spawn()
    generate_leaf_touch()
    generate_transition()
    generate_pause_in()
    generate_pause_out()
    print(f"\n✓ All sounds saved to: {SOUNDS_DIR}")


if __name__ == "__main__":
    generate_all()
