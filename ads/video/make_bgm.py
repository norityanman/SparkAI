"""Synthesizes an original, royalty-free piano BGM timed to the ReFast ad (28.87s).

Story beats on the video timeline:
  0.0–10.3  night office / instructor  -> sparse, minor-leaning (Am F C G)
  10.3      "3か月後" calendar         -> sparkle + lift
  12.1–24.4 teaching / park            -> fuller, brighter (C G Am F)
  24.4–     end card                    -> resolve on C, sparkle, fade
Usage: python3 make_bgm.py out.wav
"""
import sys, wave
import numpy as np

SR = 48000
TOTAL = 28.87
BPM = 80
BEAT = 60 / BPM          # 0.75s
BAR = 4 * BEAT           # 3.0s
rng = np.random.default_rng(7)
L = np.zeros(int(SR * (TOTAL + 3)))
R = np.zeros_like(L)

NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def hz(name):
    n, octv = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((NOTE[n] + 12 * (octv + 1) - 69) / 12)


def add(sig, t0, pan=0.0, gain=1.0):
    i = int(t0 * SR)
    j = min(i + len(sig), len(L))
    s = sig[: j - i] * gain
    L[i:j] += s * np.sqrt((1 - pan) / 2)
    R[i:j] += s * np.sqrt((1 + pan) / 2)


def piano(f, dur=2.5, vel=1.0):
    t = np.arange(int(SR * dur)) / SR
    s = np.zeros_like(t)
    for k in range(1, 8):
        if f * k > 16000:
            break
        decay = 2.2 + 1.1 * k
        s += np.sin(2 * np.pi * f * k * t * (1 + 0.0004 * k * k)) * np.exp(-decay * t) / k ** 1.6
    env = np.minimum(1, t / 0.004) * (0.75 + 0.25 * np.exp(-12 * t))
    return s * env * vel * 0.32


def pad(freqs, dur, vel=1.0):
    t = np.arange(int(SR * dur)) / SR
    s = np.zeros_like(t)
    for f in freqs:
        for det in (-0.003, 0.0, 0.003):
            ph = rng.uniform(0, 2 * np.pi)
            s += np.sin(2 * np.pi * f * (1 + det) * t + ph) + 0.25 * np.sin(4 * np.pi * f * (1 + det) * t + ph)
    att, rel = min(1.2, dur / 3), min(1.0, dur / 3)
    env = np.clip(np.minimum(t / att, (dur - t) / rel), 0, 1)
    return s * env * vel * 0.03 / max(1, len(freqs))


def bell(f, dur=2.0, vel=1.0):
    t = np.arange(int(SR * dur)) / SR
    s = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-4 * t) + 0.3 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-7 * t)
    return s * np.exp(-2.5 * t) * np.minimum(1, t / 0.002) * vel * 0.12


def bass(f, dur, vel=1.0):
    t = np.arange(int(SR * dur)) / SR
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
    env = np.minimum(1, t / 0.02) * np.exp(-0.9 * t) * np.clip((dur - t) / 0.2, 0, 1)
    return s * env * vel * 0.22


CH = {  # chord tones (low -> high)
    "Am": ["A2", "E3", "A3", "C4", "E4"],
    "F":  ["F2", "C3", "F3", "A3", "C4"],
    "C":  ["C3", "G3", "C4", "E4", "G4"],
    "G":  ["G2", "D3", "G3", "B3", "D4"],
}

# --- section A: 0–12s, sparse (one bar = 3s) ---
for b, ch in enumerate(["Am", "F", "C", "G"]):
    t0 = b * BAR
    tones = CH[ch]
    add(pad([hz(n) for n in tones[1:4]], BAR + 0.6, vel=0.9), t0)
    add(piano(hz(tones[0]), 3.0, 0.7), t0, -0.2)
    for k, n in enumerate([tones[2], tones[3], tones[4]]):
        add(piano(hz(n), 2.5, 0.55), t0 + BEAT * (1 + k), 0.15 * (k - 1))
# melody hint over A (quiet, high)
for t0, n in [(1.5, "E5"), (4.5, "C5"), (7.5, "G4"), (9.75, "D5"), (10.5, "B4")]:
    add(piano(hz(n), 2.5, 0.45), t0, 0.3)

# --- lift at the calendar (10.3s) ---
for k, n in enumerate(["G5", "B5", "D6", "G6"]):
    add(bell(hz(n), 2.0, 0.8 - 0.12 * k), 10.3 + 0.09 * k, 0.4 - 0.25 * k)

# --- section B: 12–24s, brighter, 8th-note arpeggios + bass ---
for b, ch in enumerate(["C", "G", "Am", "F"]):
    t0 = 12 + b * BAR
    tones = CH[ch]
    add(pad([hz(n) for n in tones[1:5]], BAR + 0.6, vel=1.2), t0)
    add(bass(hz(tones[0]), BAR), t0)
    patt = [1, 2, 3, 4, 3, 2, 3, 4]
    for k, idx in enumerate(patt):
        add(piano(hz(tones[idx]), 2.0, 0.5 + (0.1 if k % 2 == 0 else 0)), t0 + k * BEAT / 2, 0.25 * np.sin(k))
mel = [(12.0, "E5", 1.0), (13.5, "G5", .9), (14.25, "E5", .8), (15.0, "D5", 1.0), (16.5, "B4", .8),
       (18.0, "C5", 1.0), (19.5, "E5", .9), (21.0, "F5", 1.0), (22.5, "E5", .9), (23.25, "D5", .8)]
for t0, n, v in mel:
    add(piano(hz(n), 3.0, 0.75 * v), t0, -0.1)

# --- section C: 24–28.87s, resolve on C with sparkle ---
t0 = 24.0
add(pad([hz(n) for n in ["C3", "G3", "C4", "E4", "G4"]], 4.87, vel=1.3), t0)
add(bass(hz("C2"), 4.5, 1.1), t0)
for k, n in enumerate(["C4", "E4", "G4", "C5"]):
    add(piano(hz(n), 4.5, 0.6), t0 + 0.06 * k, -0.3 + 0.2 * k)
add(piano(hz("E5"), 4.5, 0.8), t0 + 0.4, 0.1)
for k, n in enumerate(["C6", "E6", "G6"]):
    add(bell(hz(n), 2.5, 0.6 - 0.1 * k), 24.5 + 0.1 * k, 0.3 * (k - 1))

# --- simple stereo reverb (FFT convolution with decaying noise) ---
def reverb(x, seconds=2.2, mix=0.28):
    n = int(SR * seconds)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-3.2 * t)
    ir[: int(0.012 * SR)] = 0
    ir /= np.sqrt(np.sum(ir ** 2))
    size = 1 << int(np.ceil(np.log2(len(x) + n)))
    wet = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    return x * (1 - mix) + wet * mix


L, R = reverb(L), reverb(R)
n = int(SR * TOTAL)
L, R = L[:n], R[:n]
t = np.arange(n) / SR
fade = np.clip(np.minimum(t / 0.4, (TOTAL - t) / 2.0), 0, 1)  # fade in 0.4s, out over last 2s
L, R = L * fade, R * fade
peak = max(np.abs(L).max(), np.abs(R).max())
L, R = L / peak * 0.6, R / peak * 0.6   # ~ -4.4 dBFS peak

pcm = (np.stack([L, R], axis=1) * 32767).astype("<i2")
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("wrote", sys.argv[1], f"{TOTAL}s")
