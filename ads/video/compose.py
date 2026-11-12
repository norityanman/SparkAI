"""Composes the ~30s ReFast ad: slowed segments + calendar still + end card, crossfades, telops (ASS), stretched audio."""
import subprocess, sys
from pathlib import Path

S = Path(sys.argv[1])
SRC = sys.argv[2]
OUT = sys.argv[3]
X = 0.4          # crossfade between scenes
X_END = 0.6      # crossfade into end card
FPS = 30


def dur(p):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).strip())


# inputs: (kind, path, hold_seconds or still_duration)
clips = [
    ("video", S / "seg1.mp4", 0.0),
    ("video", S / "seg2.mp4", 0.0),
    ("still", S / "cal_fixed.png", 2.2),
    ("video", S / "seg4.mp4", 1.0),
    ("video", S / "seg5.mp4", 0.8),
    ("still", S / "endcard.png", 4.5),
]
lengths = [(dur(p) + h) if k == "video" else h for k, p, h in clips]

# start time of each clip on the final timeline
starts, t = [], 0.0
for i, L in enumerate(lengths):
    starts.append(t)
    x = X_END if i + 1 == len(lengths) - 1 else X
    t += L - x
total = starts[-1] + lengths[-1]

# telops: (clip index, start, end, lines, kind)
T = [
    (0, 0.4, 3.0, ["この会社、", "私がいないと回らないんです"], "main"),
    (0, 3.3, 5.7, ["…それが、怖かった。"], "main"),
    (1, 0.3, 2.6, ["私なんかに、AIなんて…"], "main"),
    (1, 2.8, 5.0, ["大丈夫。", "難しい言葉は使いません。"], "main"),
    (3, 0.3, 5.9, ["教わる人が、"], "line1"),
    (3, 2.0, 5.9, ["教える人になった。"], "line2"),
    (4, 0.2, 2.2, ["定時に帰れる毎日へ。"], "main"),
    (4, 2.4, 4.6, ["残業 月40時間 → 5時間"], "main"),
    (4, 2.4, 4.6, ["※イメージです"], "note"),
    (4, 4.8, 6.6, ["この歳で、仕事が", "楽しくなるなんて。"], "main"),
]


def ts(sec):
    cs = int(round(sec * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


BOTTOM = 1340   # bottom edge of telop block (~70% of 1920, clear of feed UI)
LINE = 118
ass = [
    "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "",
    "[V4+ Styles]",
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
    "Style: T,Zen Kaku Gothic New Black,90,&H00FFFFFF,&H00FFFFFF,&H002B2015,&H96000000,0,0,0,0,100,100,2,0,1,8,4,2,110,110,0,1",
    "Style: N,Zen Kaku Gothic New Bold,42,&H00FFFFFF,&H00FFFFFF,&H002B2015,&H96000000,0,0,0,0,100,100,1,0,1,4,2,2,110,110,0,1",
    "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
]
for ci, a, b, lines, kind in T:
    st, en = starts[ci] + a, starts[ci] + b
    fad = r"{\fad(200,200)}"
    if kind == "main":
        y, style = BOTTOM, "T"
        text = r"\N".join(lines)
    elif kind == "line1":
        y, style, text = BOTTOM - LINE, "T", lines[0]
    elif kind == "line2":
        y, style, text = BOTTOM, "T", lines[0]
    else:  # note under the main line
        y, style, text = BOTTOM + 70, "N", lines[0]
    ass.append(f"Dialogue: 0,{ts(st)},{ts(en)},{style},,0,0,0,,{{\\an2\\pos(540,{y})}}{fad}{text}")
(S / "telops.ass").write_text("\n".join(ass) + "\n", encoding="utf-8")

# ---- ffmpeg graph ----
args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
for k, p, h in clips:
    if k == "video":
        args += ["-i", str(p)]
    else:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{h:.3f}", "-i", str(p)]
args += ["-i", SRC]
ai = len(clips)

f = []
for i, ((k, p, h), L) in enumerate(zip(clips, lengths)):
    if k == "video":
        pad = f",tpad=stop_mode=clone:stop_duration={h}" if h else ""
        f.append(f"[{i}:v]fps={FPS},settb=1/{FPS},setpts=PTS-STARTPTS{pad},format=yuv420p,setsar=1[v{i}]")
    else:
        n = int(round(h * FPS))
        z = 0.05 if i == 2 else 0.025
        f.append(f"[{i}:v]scale=2160:3840,zoompan=z='1+{z}*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps={FPS},"
                 f"trim=duration={h},settb=1/{FPS},setpts=PTS-STARTPTS,format=yuv420p,setsar=1[v{i}]")
prev = "v0"
for i in range(1, len(clips)):
    x = X_END if i == len(clips) - 1 else X
    off = starts[i]
    f.append(f"[{prev}][v{i}]xfade=transition=fade:duration={x}:offset={off:.3f}[x{i}]")
    prev = f"x{i}"
fontsdir = S / "fonts"
f.append(f"[{prev}]fade=t=in:st=0:d=0.5,ass={S / 'telops.ass'}:fontsdir={fontsdir}[vout]")

# audio: stretch the whole track to end slightly into the end card, then fade and pad
src_a = dur(SRC)
target = starts[-1] + 1.5
tempo = src_a / target
f.append(f"[{ai}:a]aresample=48000,rubberband=tempo={tempo:.5f}:pitchq=quality,"
         f"afade=t=in:st=0:d=0.3,afade=t=out:st={target - 1.5:.3f}:d=1.5,apad,atrim=duration={total:.3f}[aout]")

args += ["-filter_complex", ";".join(f), "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-t", f"{total:.3f}", OUT]
print("lengths", [round(x, 2) for x in lengths], "starts", [round(x, 2) for x in starts], "total", round(total, 2), "tempo", round(tempo, 3))
subprocess.run(args, check=True)
print("wrote", OUT)
