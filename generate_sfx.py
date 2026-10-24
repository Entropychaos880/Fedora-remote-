#!/usr/bin/env python3
"""
generate_sfx.py - Synthesize punchy soundboard effects for the ECOMAX subwoofer.
Uses pure Python standard library (wave, math, struct, random).
"""

import math
import struct
import random
import wave
from pathlib import Path

SFX_DIR = Path(__file__).parent / "static" / "sfx"
SFX_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_RATE = 44100


def write_wav(filename: str, samples: list[float]):
    filepath = SFX_DIR / filename
    with wave.open(str(filepath), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)  # 16-bit
        f.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for s in samples:
            # Clamp to -1.0 to 1.0
            val = max(-1.0, min(1.0, s))
            int_val = int(val * 32767)
            frames.extend(struct.pack("<h", int_val))
        f.writeframes(frames)
    print(f"✓ Generated {filepath.name} ({len(samples)/SAMPLE_RATE:.2f}s)")


def gen_bass_drop():
    """Heavy 808 Sub-Bass Drop (95Hz sliding down to 35Hz with harmonic saturation)."""
    duration = 2.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    phase = 0.0

    for i in range(num_samples):
        t = i / SAMPLE_RATE
        # Exponential frequency decay from 95Hz to 36Hz
        freq = 36 + 59 * math.exp(-2.5 * t)
        phase += 2 * math.pi * freq / SAMPLE_RATE

        # Sine wave + slight 2nd harmonic warmth
        signal = 0.85 * math.sin(phase) + 0.15 * math.sin(phase * 2)
        # Soft overdrive saturation
        signal = math.tanh(signal * 1.4)

        # Amplitude envelope: fast attack (10ms), punch sustain, smooth release
        if t < 0.01:
            env = t / 0.01
        else:
            env = math.exp(-1.1 * (t - 0.01))

        samples.append(signal * env * 0.95)

    write_wav("bassdrop.wav", samples)


def gen_airhorn():
    """Classic Jamaican / DJ Club Reggae Airhorn (3 short rhythmic blasts)."""
    # Airhorn fundamental frequencies (approx Bb4 / D5)
    f1, f2, f3 = 466.16, 587.33, 700.0
    blast_len = 0.16
    gap_len = 0.06
    # 3 blasts
    blasts = [(0.0, blast_len), (blast_len + gap_len, blast_len), (2 * (blast_len + gap_len), blast_len * 1.5)]
    total_len = blasts[-1][0] + blasts[-1][1] + 0.1
    num_samples = int(total_len * SAMPLE_RATE)
    samples = [0.0] * num_samples

    for b_start, b_dur in blasts:
        start_idx = int(b_start * SAMPLE_RATE)
        dur_samples = int(b_dur * SAMPLE_RATE)
        p1, p2, p3 = 0.0, 0.0, 0.0
        for i in range(dur_samples):
            t = i / SAMPLE_RATE
            p1 += 2 * math.pi * f1 / SAMPLE_RATE
            p2 += 2 * math.pi * f2 / SAMPLE_RATE
            p3 += 2 * math.pi * f3 / SAMPLE_RATE

            # Harsh brassy square/saw-like harmonic wave
            tone = (math.sin(p1) + 0.7 * math.sin(p2) + 0.4 * math.sin(p3) + 
                    0.3 * math.sin(p1 * 3) + 0.2 * math.sin(p2 * 2))
            # Clip/distort for that signature punchy airhorn blast
            tone = max(-1.0, min(1.0, tone * 1.8)) * 0.7

            # Attack and release
            if t < 0.015:
                env = t / 0.015
            elif t > b_dur - 0.02:
                env = (b_dur - t) / 0.02
            else:
                env = 1.0

            if start_idx + i < num_samples:
                samples[start_idx + i] += tone * env * 0.85

    write_wav("airhorn.wav", samples)


def gen_impact_boom():
    """Cinematic Subwoofer Impact Boom (deep punch + decaying rumble)."""
    duration = 1.8
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    phase = 0.0

    for i in range(num_samples):
        t = i / SAMPLE_RATE
        # Rapid pitch dive from 150Hz to 40Hz
        freq = 40 + 110 * math.exp(-12.0 * t)
        phase += 2 * math.pi * freq / SAMPLE_RATE

        # Sub sine
        sub = math.sin(phase)
        # Noise transient on impact (first 40ms)
        noise = (random.random() * 2 - 1) * math.exp(-60.0 * t) * 0.6
        raw = sub + noise
        raw = math.tanh(raw * 1.5)

        # Envelope
        env = math.exp(-2.2 * t)
        samples.append(raw * env * 0.95)

    write_wav("boom.wav", samples)


def gen_applause():
    """Crowd cheer & applause burst."""
    duration = 2.0
    num_samples = int(duration * SAMPLE_RATE)
    samples = []

    # Filtered noise bursts simulating clapping
    claps = []
    # Generate random clapping impulses
    for _ in range(120):
        claps.append((random.uniform(0.05, 1.8), random.uniform(0.4, 1.0)))

    for i in range(num_samples):
        t = i / SAMPLE_RATE
        val = 0.0

        # Background crowd murmur
        val += (random.random() * 2 - 1) * 0.15

        # Clap impulses
        for c_time, c_amp in claps:
            dt = t - c_time
            if 0 <= dt <= 0.025:
                val += math.sin(dt * 3000) * math.exp(-dt * 150) * c_amp * 0.4

        # Overall fade in and fade out
        if t < 0.2:
            env = t / 0.2
        elif t > 1.5:
            env = (2.0 - t) / 0.5
        else:
            env = 1.0

        samples.append(max(-1.0, min(1.0, val * env * 0.8)))

    write_wav("applause.wav", samples)


def gen_laser():
    """Retro synth laser sweep."""
    duration = 0.4
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    phase = 0.0

    for i in range(num_samples):
        t = i / SAMPLE_RATE
        # Laser sweep 2200Hz down to 180Hz
        freq = 180 + 2020 * math.exp(-12.0 * t)
        phase += 2 * math.pi * freq / SAMPLE_RATE

        sig = math.sin(phase) + 0.3 * math.sin(phase * 2)
        env = math.exp(-6.0 * t)
        samples.append(sig * env * 0.85)

    write_wav("laser.wav", samples)


if __name__ == "__main__":
    gen_bass_drop()
    gen_airhorn()
    gen_impact_boom()
    gen_applause()
    gen_laser()
