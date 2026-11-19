"""Original synthesized BGM + sound effects for the young-employee episode (60.0s). Usage: make_audio.py OUT.wav

Timeline (matches scenes.html + end card):
  0–13  night office / train : sparse, melancholic (Am F C G)   + fax, train rumble
  15.7  ad stops in the feed  : sparkle
  22.1  tap "無料で相談する"    : click + sparkle
  24–41 consultation / study  : warm (F C G Am), fuller from 33
  41–53 success / handover    : brightest section, applause at 45.2, whoosh at 50
  53.5– sunrise + end card    : resolve on C, sparkle at 55.6, fade out
"""
import sys, wave
import numpy as np

SR, TOTAL = 48000, 60.0
BAR = 3.0
BEAT = BAR / 4
rng = np.random.default_rng(11)
L = np.zeros(int(SR * (TOTAL + 3)))
R = np.zeros_like(L)
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def hz(n):
    return 440.0 * 2 ** ((NOTE[n[:-1]] + 12 * (int(n[-1]) + 1) - 69) / 12)


def add(sig, t0, pan=0.0, gain=1.0, bus=None):
    i = int(t0 * SR); j = min(i + len(sig), len(L)); s = sig[: j - i] * gain
    L[i:j] += s * np.sqrt((1 - pan) / 2); R[i:j] += s * np.sqrt((1 + pan) / 2)


def tt(d):
    return np.arange(int(SR * d)) / SR


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
    att, rel = min(1.2, d / 3), min(1.0, d / 3)
    return s * np.clip(np.minimum(t / att, (d - t) / rel), 0, 1) * v * .03 / max(1, len(fs))


def bell(f, d=2.0, v=1.0):
    t = tt(d)
    s = np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-4 * t) + .3 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-7 * t)
    return s * np.exp(-2.5 * t) * np.minimum(1, t / .002) * v * .12


def bass(f, d, v=1.0):
    t = tt(d)
    return (np.sin(2 * np.pi * f * t) + .3 * np.sin(4 * np.pi * f * t)) * np.minimum(1, t / .02) * np.exp(-.9 * t) * np.clip((d - t) / .2, 0, 1) * v * .22


def smooth(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


CH = {"Am": ["A2", "E3", "A3", "C4", "E4"], "F": ["F2", "C3", "F3", "A3", "C4"],
      "C": ["C3", "G3", "C4", "E4", "G4"], "G": ["G2", "D3", "G3", "B3", "D4"], "Em": ["E2", "B2", "E3", "G3", "B3"]}


def sparse_bar(ch, t0, v=1.0):
    tn = CH[ch]
    add(pad([hz(n) for n in tn[1:4]], BAR + .6, .9 * v), t0)
    add(piano(hz(tn[0]), 3, .65 * v), t0, -.2)
    for k, n in enumerate(tn[2:5]): add(piano(hz(n), 2.5, .5 * v), t0 + BEAT * (1 + k), .15 * (k - 1))


def full_bar(ch, t0, v=1.0, with_bass=True):
    tn = CH[ch]
    add(pad([hz(n) for n in tn[1:5]], BAR + .6, 1.2 * v), t0)
    if with_bass: add(bass(hz(tn[0]), BAR, v), t0)
    for k, idx in enumerate([1, 2, 3, 4, 3, 2, 3, 4]):
        add(piano(hz(tn[idx]), 2.0, (.48 + (.1 if k % 2 == 0 else 0)) * v), t0 + k * BEAT / 2, .25 * np.sin(k))


# ---- music ----
for b, ch in enumerate(["Am", "F", "C", "G", "Am"]): sparse_bar(ch, b * BAR, .9)          # 0–15
sparse_bar("F", 15, 1.0); sparse_bar("G", 18, 1.0)                                          # 15–21 (light lifts)
sparse_bar("C", 21, 1.0)                                                                     # 21–24
for b, ch in enumerate(["F", "C", "G"]): full_bar(ch, 24 + b * BAR, .75, with_bass=False)   # 24–33 consultation
for b, ch in enumerate(["Am", "F", "G"]): full_bar(ch, 33 + b * BAR, .9)                    # 33–42 learning
for b, ch in enumerate(["C", "G", "Am", "F"]): full_bar(ch, 42 + b * BAR, 1.1)              # 42–54 success / handover
mel = [(24.0, "C5"), (25.5, "E5"), (27, "G5"), (28.5, "E5"), (30, "D5"), (31.5, "B4"),
       (33, "C5"), (34.5, "E5"), (36, "A5"), (37.5, "G5"), (39, "F5"), (40.5, "D5"),
       (42, "E5"), (43.5, "G5"), (44.25, "E5"), (45, "D5"), (46.5, "B4"), (48, "C5"), (49.5, "E5"),
       (51, "F5"), (52.5, "E5"), (53.25, "D5")]
for t0, n in mel: add(piano(hz(n), 3.0, .7), t0, -.1)
add(pad([hz(n) for n in ["C3", "G3", "C4", "E4", "G4"]], 6.6, 1.3), 54.0)
add(bass(hz("C2"), 5.5, 1.1), 54.0)
for k, n in enumerate(["C4", "E4", "G4", "C5", "E5"]): add(piano(hz(n), 5, .55), 54.0 + .07 * k, -.3 + .15 * k)
for t0, ns in [(15.7, ["E6", "G6", "C7"]), (22.1, ["G5", "B5", "D6", "G6"]), (55.6, ["C6", "E6", "G6"])]:
    for k, n in enumerate(ns): add(bell(hz(n), 2.2, .7 - .1 * k), t0 + .09 * k, .35 * (k - 1))


# ---- sound effects ----
def fax(t0):
    t = tt(2.4); s = np.zeros_like(t)
    for k in range(6):
        a, b = int(k * .32 * SR), int((k * .32 + .2) * SR)
        s[a:b] += np.sin(2 * np.pi * (1100 if k % 2 else 2100) * t[a:b]) * .05
    whir = smooth(rng.standard_normal(len(t)), 8) * .05 * np.clip((t - 1.0) / .2, 0, 1)
    add(s + whir, t0, .4)


def train(t0, d):
    t = tt(d); n = smooth(smooth(rng.standard_normal(len(t)), 60), 60) * 2.2
    env = np.clip(np.minimum(t / .6, (d - t) / .6), 0, 1)
    sig = n * env * .25
    for k in np.arange(.4, d, 1.15):
        for dt in (0, .14):
            i = int((k + dt) * SR); c = tt(.12)[: max(0, len(sig) - i)]
            sig[i:i + len(c)] += np.sin(2 * np.pi * 90 * c) * np.exp(-35 * c) * .35 * env[min(i, len(env) - 1)]
    add(sig, t0, 0)


def click(t0, v=.4):
    c = tt(.05); add((np.sin(2 * np.pi * 1800 * c) + rng.standard_normal(len(c)) * .3) * np.exp(-90 * c) * v, t0)


def applause(t0, d):
    for k in range(int(d * 28)):
        tk = t0 + rng.uniform(0, d); c = tt(.06)
        env = min(1, (tk - t0) / .4) * min(1, (t0 + d - tk) / .8)
        add(smooth(rng.standard_normal(len(c)), 3) * np.exp(-60 * c) * .18 * env, tk, rng.uniform(-.7, .7))


def whoosh(t0, d=.9):
    t = tt(d); n = rng.standard_normal(len(t)); k = int(4 + 30 * 0)
    sig = smooth(n, 12) * np.sin(np.pi * t / d) ** 2 * .12
    add(sig, t0, .2)


fax(1.8); train(7.0, 6.2); click(22.1, .5); applause(45.2, 3.2); whoosh(49.4)


# ---- reverb, fades, normalize ----
def reverb(x, sec=2.2, mix=.26):
    n = int(SR * sec); t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-3.2 * t); ir[: int(.012 * SR)] = 0; ir /= np.sqrt(np.sum(ir ** 2))
    size = 1 << int(np.ceil(np.log2(len(x) + n)))
    return x * (1 - mix) + np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)] * mix


L, R = reverb(L), reverb(R)
n = int(SR * TOTAL); L, R = L[:n], R[:n]
t = np.arange(n) / SR
fade = np.clip(np.minimum(t / .6, (TOTAL - t) / 2.5), 0, 1)
L, R = L * fade, R * fade
peak = max(np.abs(L).max(), np.abs(R).max()); L, R = L / peak * .6, R / peak * .6
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.stack([L, R], 1) * 32767).astype("<i2").tobytes())
print("wrote", sys.argv[1])
