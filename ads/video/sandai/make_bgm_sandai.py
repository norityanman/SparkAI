"""Original synthesized piano BGM for the 3-generation episode (48.8s). Usage: make_bgm_sandai.py OUT.wav

Timeline (matches refast_sandai_final.mp4):
  0.0–14.6  Sunday night, 3-way split  : quiet, a little melancholic (Am F C G)
  14.6      same ad stops their fingers: soft chime, music starts to lift
  14.6–29.3 team learns AI together    : warmer, arpeggios grow
  29.3–43.8 each person's success      : brightest, bass + melody
  43.8–48.8 end card                    : resolve on C and fade out
"""
import sys, wave
import numpy as np

SR, TOTAL, BAR = 48000, 48.8, 3.0
BEAT = BAR / 4
rng = np.random.default_rng(23)
L = np.zeros(int(SR * (TOTAL + 3))); R = np.zeros_like(L)
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def hz(n): return 440.0 * 2 ** ((NOTE[n[:-1]] + 12 * (int(n[-1]) + 1) - 69) / 12)
def tt(d): return np.arange(int(SR * d)) / SR


def add(sig, t0, pan=0.0):
    i = int(t0 * SR); j = min(i + len(sig), len(L)); s = sig[: j - i]
    L[i:j] += s * np.sqrt((1 - pan) / 2); R[i:j] += s * np.sqrt((1 + pan) / 2)


def piano(f, d=2.5, v=1.0):
    t = tt(d); s = np.zeros_like(t)
    for k in range(1, 8):
        if f * k > 16000: break
        s += np.sin(2 * np.pi * f * k * t * (1 + .0004 * k * k)) * np.exp(-(2.2 + 1.1 * k) * t) / k ** 1.6
    return s * np.minimum(1, t / .004) * (.75 + .25 * np.exp(-12 * t)) * v * .32


def pad(fs, d, v=1.0):
    t = tt(d); s = np.zeros_like(t)
    for f in fs:
        for det in (-.003, 0, .003):
            ph = rng.uniform(0, 6.28); s += np.sin(2 * np.pi * f * (1 + det) * t + ph) + .25 * np.sin(4 * np.pi * f * (1 + det) * t + ph)
    a, r = min(1.2, d / 3), min(1.0, d / 3)
    return s * np.clip(np.minimum(t / a, (d - t) / r), 0, 1) * v * .03 / max(1, len(fs))


def bell(f, d=2.0, v=1.0):
    t = tt(d)
    return (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-4 * t)) * np.exp(-2.5 * t) * np.minimum(1, t / .002) * v * .1


def bass(f, d, v=1.0):
    t = tt(d)
    return (np.sin(2 * np.pi * f * t) + .3 * np.sin(4 * np.pi * f * t)) * np.minimum(1, t / .02) * np.exp(-.9 * t) * np.clip((d - t) / .2, 0, 1) * v * .22


CH = {"Am": ["A2", "E3", "A3", "C4", "E4"], "F": ["F2", "C3", "F3", "A3", "C4"], "C": ["C3", "G3", "C4", "E4", "G4"],
      "G": ["G2", "D3", "G3", "B3", "D4"], "Dm": ["D3", "A3", "D4", "F4", "A4"], "Em": ["E2", "B2", "E3", "G3", "B3"]}


def sparse(ch, t0, v=1.0):
    tn = CH[ch]; add(pad([hz(n) for n in tn[1:4]], BAR + .6, .9 * v), t0); add(piano(hz(tn[0]), 3, .6 * v), t0, -.2)
    for k, n in enumerate(tn[2:5]): add(piano(hz(n), 2.5, .45 * v), t0 + BEAT * (1 + k), .15 * (k - 1))


def full(ch, t0, v=1.0, b=True):
    tn = CH[ch]; add(pad([hz(n) for n in tn[1:5]], BAR + .6, 1.2 * v), t0)
    if b: add(bass(hz(tn[0]), BAR, v), t0)
    for k, idx in enumerate([1, 2, 3, 4, 3, 2, 3, 4]):
        add(piano(hz(tn[idx]), 2.0, (.46 + (.1 if k % 2 == 0 else 0)) * v), t0 + k * BEAT / 2, .25 * np.sin(k))


# section A: Sunday night (0–15)
for i, ch in enumerate(["Am", "F", "C", "G", "Am"]): sparse(ch, i * BAR, .85)
for t0, n in [(1.5, "E5"), (4.5, "C5"), (7.5, "G4"), (10.5, "B4"), (13.5, "A4")]: add(piano(hz(n), 3, .4), t0, .3)
# lift at 14.6: the same ad
for k, n in enumerate(["E6", "G6", "C7"]): add(bell(hz(n), 2.2, .7 - .12 * k), 14.65 + .09 * k, .3 * (k - 1))
# section B: learning together (15–30)
for i, ch in enumerate(["F", "C"]): sparse(ch, 15 + i * BAR, 1.0)
for i, ch in enumerate(["Dm", "G", "C"]): full(ch, 21 + i * BAR, .75, b=False)
for t0, n in [(21, "F5"), (22.5, "E5"), (24, "D5"), (25.5, "B4"), (27, "C5"), (28.5, "E5")]: add(piano(hz(n), 3, .6), t0, -.1)
# section C: success (30–45)
for i, ch in enumerate(["F", "G", "Em", "Am", "F"]): full(ch, 30 + i * BAR, 1.05)
mel = [(30, "A5"), (31.5, "G5"), (32.25, "F5"), (33, "G5"), (34.5, "D5"), (36, "E5"), (37.5, "G5"), (39, "C6"),
       (40.5, "B5"), (41.25, "A5"), (42, "A5"), (43.5, "G5")]
for t0, n in mel: add(piano(hz(n), 3, .7), t0, -.1)
# section D: end card, resolve (45–48.8)
add(pad([hz(n) for n in ["C3", "G3", "C4", "E4", "G4"]], 4.0, 1.3), 45.0); add(bass(hz("C2"), 3.8, 1.0), 45.0)
for k, n in enumerate(["C4", "E4", "G4", "C5", "E5"]): add(piano(hz(n), 3.8, .55), 45.0 + .07 * k, -.3 + .15 * k)


def reverb(x, sec=2.2, mix=.26):
    n = int(SR * sec); t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-3.2 * t); ir[: int(.012 * SR)] = 0; ir /= np.sqrt(np.sum(ir ** 2))
    size = 1 << int(np.ceil(np.log2(len(x) + n)))
    return x * (1 - mix) + np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)] * mix


L, R = reverb(L), reverb(R)
n = int(SR * TOTAL); L, R = L[:n], R[:n]; t = np.arange(n) / SR
fade = np.clip(np.minimum(t / .8, (TOTAL - t) / 2.5), 0, 1); L, R = L * fade, R * fade
pk = max(np.abs(L).max(), np.abs(R).max()); L, R = L / pk * .6, R / pk * .6
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([L, R], 1) * 32767).astype("<i2").tobytes())
print("wrote", sys.argv[1])
