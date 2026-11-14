import numpy as np, wave, sys

SR = 48000
DUR = 43.94
BPM = 84
BEAT = 60 / BPM
BAR = BEAT * 4
N = int(SR * (DUR + 0.5))
rng = np.random.default_rng(11)

L = np.zeros(N); R = np.zeros(N)

def midi(n): return 440 * 2 ** ((n - 69) / 12)

def add(sig, start, pan=0.0, gain=1.0):
    i = int(start * SR)
    if i >= N: return
    sig = sig[: N - i] * gain
    L[i:i+len(sig)] += sig * np.sqrt((1 - pan) / 2)
    R[i:i+len(sig)] += sig * np.sqrt((1 + pan) / 2)

def piano(note, length=2.5, vel=1.0):
    t = np.arange(int(SR * length)) / SR
    f = midi(note)
    s = np.zeros_like(t)
    for h, a in [(1, 1), (2, .45), (3, .2), (4, .1), (5, .05)]:
        s += a * np.sin(2*np.pi*f*h*t) * np.exp(-t * (1.6 + h*0.9))
    env = np.minimum(t / 0.004, 1)
    s *= env * np.exp(-t * 0.6)
    tail = np.minimum(1, (length - t) / 0.08)
    return s * tail * vel * 0.22

def pad(notes, length):
    t = np.arange(int(SR * length)) / SR
    s = np.zeros_like(t)
    for n in notes:
        for d in (-0.08, 0.08):
            f = midi(n) * 2 ** (d / 12)
            s += np.sin(2*np.pi*f*t) + 0.25*np.sin(2*np.pi*2*f*t)
    att = np.minimum(t / 0.9, 1); rel = np.minimum(1, (length - t) / 0.9)
    return s * att * rel * 0.018

def bass(note, length):
    t = np.arange(int(SR * length)) / SR
    f = midi(note)
    s = np.sin(2*np.pi*f*t) + 0.15*np.sin(2*np.pi*2*f*t)
    env = np.minimum(t/0.01, 1) * np.exp(-t*0.8) * np.minimum(1, (length-t)/0.05)
    return s * env * 0.16

def kick():
    t = np.arange(int(SR*0.35))/SR
    f = 50 + 70*np.exp(-t*30)
    ph = 2*np.pi*np.cumsum(f)/SR
    return np.sin(ph) * np.exp(-t*12) * 0.28

def shaker():
    n = rng.standard_normal(int(SR*0.08))
    n = np.diff(n, prepend=0)  # high-pass-ish
    t = np.arange(len(n))/SR
    return n * np.exp(-t*60) * 0.025

# chord: (root for bass, chord tones)
A, F, C, G, E, B = 57, 53, 48, 55, 52, 59
chords = {
    'Am': (45, [57, 60, 64]), 'F': (41, [53, 57, 60]), 'C': (48, [55, 60, 64]),
    'G': (43, [55, 59, 62]), 'G/B': (47, [55, 59, 62]), 'Em': (40, [55, 59, 64]),
}
prog = ['Am','F','C','G','G',  'C','G/B','Am','F','C',  'F','G','Am','G','C']
# bars 0-4 intro (quiet), 5-10 build, 11-15 lift, 16 ending (truncated by length)

for bar, name in enumerate(prog):
    t0 = bar * BAR
    if t0 > DUR: break
    root, tones = chords[name]
    last = (bar == len(prog) - 1) or (t0 + BAR > DUR - 1.5)
    section = 0 if bar < 5 else (1 if bar < 10 else 2)
    plen = (DUR + 0.5 - t0) if last else BAR + 0.6
    add(pad([n - 12 for n in tones] + ([tones[0]] if section else []), plen), t0,
        gain=0.8 if section == 0 else 1.0)
    if last:
        for k, n in enumerate([tones[0]-12] + tones + [tones[1]+12]):
            add(piano(n, DUR + 0.5 - t0 - k*0.06, 0.9), t0 + k*0.06, pan=-0.3 + k*0.15)
        add(bass(root, DUR + 0.5 - t0), t0)
        continue
    if section == 0:
        # sparse quarter-note arpeggio
        pat = [tones[0], tones[1], tones[2], tones[1]+12 if bar % 2 else tones[2]+12]
        for k, n in enumerate(pat):
            add(piano(n, 2.4, 0.6 + 0.1*(k == 0)), t0 + k*BEAT, pan=-0.2 + 0.13*k)
    else:
        up = [tones[0], tones[1], tones[2], tones[0]+12, tones[2], tones[1]+12, tones[2]+12, tones[1]+12]
        for k, n in enumerate(up):
            add(piano(n, 1.8, 0.62 + 0.15*(k % 4 == 0)), t0 + k*BEAT/2, pan=-0.35 + 0.1*k)
        if section == 2:  # melody on top
            mel = [tones[2]+12, tones[1]+12, tones[2]+12, tones[0]+24]
            for k, n in enumerate(mel):
                add(piano(n, 2.2, 0.45), t0 + k*BEAT + BEAT/2*(k % 2), pan=0.25)
        add(bass(root, BEAT*2), t0); add(bass(root, BEAT*1.5), t0 + BEAT*2.5)
        for k in range(4):
            if section == 2 or k in (0, 2):
                add(kick(), t0 + k*BEAT, gain=0.8 if section == 1 else 1.0)
        for k in range(8):
            if section == 2 or k % 2:
                add(shaker(), t0 + k*BEAT/2 + 0.01, pan=0.4 if k % 2 else -0.4)

# simple stereo reverb by FFT convolution
def reverb(x, seed):
    r = np.random.default_rng(seed)
    t = np.arange(int(SR*2.2))/SR
    ir = r.standard_normal(len(t)) * np.exp(-t*3.2)
    ir[:int(SR*0.02)] = 0; ir[0] = 0
    n = len(x) + len(ir)
    y = np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(ir, n), n)[:len(x)]
    return y / np.max(np.abs(ir)) * 0.012
Lw, Rw = L + reverb(L, 1), R + reverb(R, 2)

# master: fade in/out, normalize
n = int(DUR*SR)
Lw, Rw = Lw[:n], Rw[:n]
t = np.arange(n)/SR
env = np.minimum(t/1.0, 1) * np.clip((DUR - t)/1.6, 0, 1)
Lw *= env; Rw *= env
peak = max(np.max(np.abs(Lw)), np.max(np.abs(Rw)))
Lw, Rw = Lw/peak*0.89, Rw/peak*0.89
st = (np.stack([Lw, Rw], 1) * 32767).astype(np.int16)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
print('ok', n/SR)
