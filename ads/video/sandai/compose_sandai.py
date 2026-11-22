"""3世代編「日曜の夜が、怖くなくなった。」: rearrange 3 generated clips into story order, crossfade,
telops, sound effects only (voices removed with Demucs), SparkAI / ReFast logo end card.

Usage: compose_sandai.py CLIP_A CLIP_B CLIP_C SPARKAI_LOGO REFAST_LOGO FONTS_DIR WORK_DIR OUT_MP4
  CLIP_A = 7.43 (45s full draft), CLIP_B = 7.44 (night office / team learning), CLIP_C = 7.54 (success)
"""
import subprocess, sys, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

A, B, C, SPARK, REFAST, FONTS, WORK, OUT = sys.argv[1:9]
WORK = Path(WORK); WORK.mkdir(parents=True, exist_ok=True)
FPS, X, X_END, END_LEN = 30, 0.5, 0.6, 5.0
W, H = 1080, 1920
SRC = {"A": A, "B": B, "C": C}

# Story order (source, start, end). A's last part (30.2–45.3) repeats C's success scenes, so it is not used.
SEGS = [  # animation only: A 15.1–30.2 is live-action style and A 30.2–45.3 repeats C, so neither is used
    ("A", 0.0, 15.13),    # 悩み: Sunday night, 3-way split
    ("B", 0.0, 15.136),   # 知る → 相談・学ぶ: same ad at night, learning AI together
    ("C", 0.0, 15.136),   # 成功体験 → 未来
]


def run(*a):
    subprocess.run(a, check=True)


# telops relative to each segment start (segment index, start, end, lines, style)
T = [
    (0, 0.5, 4.5, ["日曜の夜が、", "怖い。"], "T"),
    (0, 4.8, 7.6, ["「私、成長してるのかな」"], "T"), (0, 4.8, 7.6, ["葵・24歳"], "N"),
    (0, 7.9, 10.7, ["「娘と、話せてない」"], "T"), (0, 7.9, 10.7, ["拓海・33歳"], "N"),
    (0, 11.0, 14.6, ["「私のやり方、", "もう古いのかな」"], "T"), (0, 11.0, 14.6, ["真由美・44歳"], "N"),
    (1, 0.4, 3.1, ["3人とも、同じ広告で", "指が止まった。"], "T"),
    (1, 3.3, 5.9, ["「一緒に、", "聞いてみない？」"], "T"),
    (1, 6.5, 10.3, ["相談したら、", "“本音”から聞いてくれた。"], "T"),
    (1, 10.6, 14.6, ["若さも、経験も、", "全部、武器になった。"], "T"),
    (2, 0.4, 4.1, ["葵は、", "頼られる人に。"], "T"),
    (2, 4.5, 8.1, ["拓海は、18時に帰って", "娘と絵本を読む人に。"], "T"),
    (2, 8.5, 11.5, ["真由美の経験は、", "チームの財産に。"], "T"),
    (2, 11.9, 99, ["日曜の夜が、", "怖くなくなった。"], "T"),
]

# ---------- 1) voices removed per source, then cut segments (video + SFX audio) ----------
sfx_src = {}
for k, p in SRC.items():
    wav = WORK / f"src{k}.wav"
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", p, "-vn", "-ac", "2", "-ar", "44100", str(wav))
    run(sys.executable, "-m", "demucs", "-n", "htdemucs", "--two-stems=vocals", "-d", "cpu", "-o", str(WORK / "sep"), str(wav))
    sfx_src[k] = WORK / "sep" / "htdemucs" / f"src{k}" / "no_vocals.wav"

lengths = [b - a for _, a, b in SEGS]
starts = [0.0]
for L in lengths[:-1]:
    starts.append(starts[-1] + L - X)
main_len = starts[-1] + lengths[-1]
end_start = main_len - X_END
total = end_start + END_LEN


def ts(s):
    cs = int(round(s * 100)); return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: T,Zen Kaku Gothic New Black,90,&H00FFFFFF,&H00FFFFFF,&H002B2015,&H96000000,0,0,0,0,100,100,2,0,1,8,4,2,110,110,0,1",
       "Style: N,Zen Kaku Gothic New Bold,46,&H00FFFFFF,&H00FFFFFF,&H002B2015,&H96000000,0,0,0,0,100,100,2,0,1,5,3,2,110,110,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for si, a, b, lines, st in T:
    s0, s1 = starts[si] + a, min(starts[si] + b, end_start + .1)
    y = 1340 if st == "T" else 1420
    ass.append(f"Dialogue: 0,{ts(s0)},{ts(s1)},{st},,0,0,0,,{{\\an2\\pos(540,{y})}}{{\\fad(200,200)}}{r'\N'.join(lines)}")
ap = WORK / "sandai.ass"; ap.write_text("\n".join(ass) + "\n", encoding="utf-8")

# ---------- 2) end card ----------
BLACK, BOLD = f"{FONTS}/ZenKakuGothicNew-Black.ttf", f"{FONTS}/ZenKakuGothicNew-Bold.ttf"
NAVY, ORANGE, GRAY = (31, 43, 61), (240, 110, 40), (110, 118, 130)


def knock_white(path, width):
    im = Image.open(path).convert("RGB"); im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    a = np.asarray(im).astype(np.int16); out = im.convert("RGBA")
    out.putalpha(Image.fromarray(np.clip((255 - a.min(axis=2)) * 6, 0, 255).astype(np.uint8))); return out


def ct(d, y, s, size, fill, path):
    f = ImageFont.truetype(path, size); d.text(((W - d.textlength(s, font=f)) / 2, y), s, font=f, fill=fill)


bg = Image.new("RGB", (W, H), (255, 255, 255))
glow = Image.new("L", (W, H), 0); ImageDraw.Draw(glow).ellipse([140, 120, 940, 920], fill=60)
bg = Image.composite(Image.new("RGB", (W, H), (255, 236, 214)), bg, glow.filter(ImageFilter.GaussianBlur(120))); bg.save(WORK / "end_bg.png")
sp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sp.alpha_composite(knock_white(SPARK, 660), ((W - 660) // 2, 170)); sp.save(WORK / "end_spark.png")
tx = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(tx)
ct(d, 880, "何歳でも、どこからでも、", 78, NAVY, BLACK); ct(d, 985, "人は伸びる。", 78, NAVY, BLACK)
ct(d, 1110, "人が足りないなら、人を伸ばせばいい。", 40, GRAY, BOLD)
pw, ph, py = 720, 124, 1210
d.rounded_rectangle([(W - pw) / 2, py, (W + pw) / 2, py + ph], radius=ph // 2, fill=ORANGE)
ct(d, py + 28, "無料相談 30分", 60, (255, 255, 255), BLACK); ct(d, py + ph + 30, "プロフィールのリンクから", 40, NAVY, BOLD)
tx.save(WORK / "end_text.png")
rf = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rl = knock_white(REFAST, 300)
rf.alpha_composite(rl, ((W - 300) // 2, 1500)); ct(ImageDraw.Draw(rf), 1500 + rl.height + 18, "株式会社ReFast", 40, NAVY, BOLD); rf.save(WORK / "end_refast.png")

SR = 48000; logo_t = end_start + X_END + 0.15; n = int(SR * total); sig = np.zeros(n)
for k, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):
    t = np.arange(int(SR * 2.0)) / SR
    s = (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-4 * t)) * np.exp(-2.8 * t) * np.minimum(1, t / .002) * (.12 - .02 * k)
    i = int((logo_t + .08 * k) * SR); sig[i:i + len(s)] += s[: max(0, n - i)]
with wave.open(str(WORK / "sparkle.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((sig * 32767).astype("<i2").tobytes())

# ---------- 3) assemble ----------
args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
idx = {}
for k in "ABC":
    idx[k] = len(idx); args += ["-i", SRC[k]]
aidx = {}
for k in "ABC":
    aidx[k] = 3 + len(aidx); args += ["-i", str(sfx_src[k])]
for p in ["end_bg.png", "end_spark.png", "end_text.png", "end_refast.png"]:
    args += ["-loop", "1", "-framerate", str(FPS), "-t", str(END_LEN), "-i", str(WORK / p)]
args += ["-i", str(WORK / "sparkle.wav")]
f = []
uses = {k: sum(1 for s in SEGS if s[0] == k) for k in "ABC"}
vsplit = {k: [f"v{k}{j}" for j in range(uses[k])] for k in "ABC"}
asplit = {k: [f"a{k}{j}" for j in range(uses[k])] for k in "ABC"}
for k in "ABC":
    f.append(f"[{idx[k]}:v]scale={W}:{H},fps={FPS},settb=1/{FPS},format=yuv420p,setsar=1,split={uses[k]}" + "".join(f"[{x}]" for x in vsplit[k]))
    f.append(f"[{aidx[k]}:a]aresample=48000,aformat=channel_layouts=stereo,asplit={uses[k]}" + "".join(f"[{x}]" for x in asplit[k]))
used = {k: 0 for k in "ABC"}
for i, (k, a, b) in enumerate(SEGS):
    j = used[k]; used[k] += 1
    f.append(f"[{vsplit[k][j]}]trim={a}:{b},setpts=PTS-STARTPTS[s{i}]")
    f.append(f"[{asplit[k][j]}]atrim={a}:{b},asetpts=PTS-STARTPTS[t{i}]")
prev, aprev = "s0", "t0"
for i in range(1, len(SEGS)):
    f.append(f"[{prev}][s{i}]xfade=transition=fade:duration={X}:offset={starts[i]:.3f}[x{i}]"); prev = f"x{i}"
    f.append(f"[{aprev}][t{i}]acrossfade=d={X}[y{i}]"); aprev = f"y{i}"
e0 = 6
f.append(f"[{prev}]fade=t=in:st=0:d=0.4,ass={ap}:fontsdir={FONTS}[main]")
f.append(f"[{e0}:v]format=yuv420p,setsar=1,settb=1/{FPS}[ebg]")
f.append(f"[{e0 + 1}:v]format=rgba,fade=t=in:st=0.5:d=0.7:alpha=1[esp]")
f.append(f"[{e0 + 2}:v]format=rgba,fade=t=in:st=1.2:d=0.6:alpha=1[etx]")
f.append(f"[{e0 + 3}:v]format=rgba,fade=t=in:st=1.8:d=0.6:alpha=1[erf]")
f.append(f"[ebg][esp]overlay=format=auto[e1];[e1][etx]overlay=format=auto[e2];[e2][erf]overlay=format=auto,format=yuv420p,settb=1/{FPS},setpts=PTS-STARTPTS[end]")
f.append(f"[main][end]xfade=transition=fade:duration={X_END}:offset={end_start:.3f}[vout]")
f.append(f"[{aprev}]afade=t=out:st={end_start:.3f}:d=1.2,apad,atrim=duration={total:.3f}[sfx]")
f.append(f"[{e0 + 4}:a]aformat=channel_layouts=stereo[spk]")
f.append("[sfx][spk]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.7:attack=1:level=false[aout]")
args += ["-filter_complex", ";".join(f), "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-t", f"{total:.3f}", OUT]
run(*args)
print(f"segment starts {[round(s, 2) for s in starts]}, end card at {end_start:.2f}s, total {total:.2f}s -> {OUT}")
