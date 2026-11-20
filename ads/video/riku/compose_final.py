"""Riku episode final: join 4 generated clips with crossfades, keep only sound effects (voices removed with
Demucs), burn telops, and finish with an end card showing the SparkAI and ReFast logos.

Usage:
  compose_final.py CLIP1 CLIP2 CLIP3 CLIP4 SPARKAI_LOGO REFAST_LOGO FONTS_DIR WORK_DIR OUT_MP4
"""
import subprocess, sys, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

*CLIPS, SPARK, REFAST, FONTS, WORK, OUT = sys.argv[1:]
assert len(CLIPS) == 4
WORK = Path(WORK); WORK.mkdir(parents=True, exist_ok=True)
FPS, X, X_END, END_LEN = 30, 0.5, 0.6, 5.0
W, H = 1080, 1920


def run(*a):
    subprocess.run(a, check=True)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).strip())


# ---------- 0) cut out broken frames (clip 2: phone floats without a hand while the can is set down) ----------
CUTS = {1: (4.05, 5.8)}   # clip index -> (cut_from, cut_to) in seconds of the source clip
CUT_XF = 0.25
for i, (a, b) in CUTS.items():
    src, fixed = CLIPS[i], WORK / f"clip{i}_cut.mp4"
    off = a - CUT_XF
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-filter_complex",
        f"[0:v]trim=0:{a},setpts=PTS-STARTPTS[va];[0:v]trim={b},setpts=PTS-STARTPTS[vb];"
        f"[va][vb]xfade=transition=fade:duration={CUT_XF}:offset={off}[v];"
        f"[0:a]atrim=0:{a},asetpts=PTS-STARTPTS[aa];[0:a]atrim={b},asetpts=PTS-STARTPTS[ab];"
        f"[aa][ab]acrossfade=d={CUT_XF}[a]",
        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "15", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "256k", str(fixed))
    CLIPS[i] = str(fixed)

D = [dur(c) for c in CLIPS]
starts = [0.0]
for d in D[:-1]:
    starts.append(starts[-1] + d - X)
main_len = starts[-1] + D[-1]
end_start = main_len - X_END
total = end_start + END_LEN

# ---------- 1) sound effects only: remove voices with Demucs ----------
sfx = []
for i, c in enumerate(CLIPS):
    wav = WORK / f"clip{i}.wav"
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", c, "-vn", "-ac", "2", "-ar", "44100", str(wav))
    run(sys.executable, "-m", "demucs", "-n", "htdemucs", "--two-stems=vocals", "-d", "cpu", "-o", str(WORK / "sep"), str(wav))
    sfx.append(WORK / "sep" / "htdemucs" / f"clip{i}" / "no_vocals.wav")

# ---------- 2) telops ----------
T = [  # (clip, start, end, lines, style) — times relative to each clip
    (0, 0.5, 4.4, ["朝5時。電話と、", "ホワイトボードと、僕。"], "T"),
    (0, 4.7, 7.4, ["鳴りやまない電話。", "配車が、組めない。"], "T"),
    (0, 7.7, 9.6, ["「この配車じゃ、", "帰れねぇよ」"], "T"),
    (0, 10.0, 14.6, ["誰も悪くないのに、", "毎日だれかが怒ってる。"], "T"),
    (1, 0.4, 3.7, ["…AIって、", "うちみたいな会社でも？"], "T"),   # clip 2 times are after the cut
    (1, 3.9, 5.6, ["聞くだけなら、タダだし。"], "T"),
    (1, 5.8, 7.6, ["SparkAIの、無料相談。"], "T"),
    (1, 7.8, 10.3, ["怒られる前に、", "“すごい”って言われた。"], "T"),
    (1, 10.6, 12.6, ["「この表、AIと一緒に", "作り直しましょう」"], "T"),
    (2, 0.4, 5.2, ["僕の頭の中を、", "AIに教えていく。"], "T"),
    (2, 5.6, 9.5, ["配車のルールを、", "ひとつずつ言葉に。"], "T"),
    (2, 10.0, 14.6, ["気づけば、仕事が", "楽しくなっていた。"], "T"),
    (3, 0.4, 4.2, ["朝の配車、", "2時間→10分。"], "T"),
    (3, 0.4, 4.2, ["※イメージです"], "N"),
    (3, 4.6, 7.5, ["大城さんが、", "初めて笑った。"], "T"),
    (3, 7.9, 12.5, ["消したホワイトボードに、", "新しい仲間が増えた。"], "T"),
    (3, 12.8, 99, ["陸、25歳。", "ホワイトボードを消した日。"], "T"),
]


def ts(s):
    cs = int(round(s * 100)); return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: T,Zen Kaku Gothic New Black,90,&H00FFFFFF,&H00FFFFFF,&H002B2015,&H96000000,0,0,0,0,100,100,2,0,1,8,4,2,110,110,0,1",
       "Style: N,Zen Kaku Gothic New Bold,42,&H00FFFFFF,&H00FFFFFF,&H002B2015,&H96000000,0,0,0,0,100,100,1,0,1,4,2,2,110,110,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for ci, a, b, lines, st in T:
    s0, s1 = starts[ci] + a, min(starts[ci] + b, end_start + .1)
    y = 1340 if st == "T" else 1410
    ass.append(f"Dialogue: 0,{ts(s0)},{ts(s1)},{st},,0,0,0,,{{\\an2\\pos(540,{y})}}{{\\fad(200,200)}}{r'\N'.join(lines)}")
ap = WORK / "riku_final.ass"; ap.write_text("\n".join(ass) + "\n", encoding="utf-8")

# ---------- 3) end card layers (white background, logos fade in) ----------
BLACK, BOLD = f"{FONTS}/ZenKakuGothicNew-Black.ttf", f"{FONTS}/ZenKakuGothicNew-Bold.ttf"
NAVY, ORANGE, GRAY = (31, 43, 61), (240, 110, 40), (110, 118, 130)


def knock_white(path, width):
    im = Image.open(path).convert("RGB")
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    a = np.asarray(im).astype(np.int16)
    alpha = np.clip((255 - a.min(axis=2)) * 6, 0, 255).astype(np.uint8)
    out = im.convert("RGBA"); out.putalpha(Image.fromarray(alpha)); return out


def ct(d, y, s, size, fill, path):
    f = ImageFont.truetype(path, size); d.text(((W - d.textlength(s, font=f)) / 2, y), s, font=f, fill=fill)


bg = Image.new("RGB", (W, H), (255, 255, 255))
glow = Image.new("L", (W, H), 0); ImageDraw.Draw(glow).ellipse([140, 120, 940, 920], fill=60)
glow = glow.filter(ImageFilter.GaussianBlur(120))
bg = Image.composite(Image.new("RGB", (W, H), (255, 236, 214)), bg, glow); bg.save(WORK / "end_bg.png")

spark = Image.new("RGBA", (W, H), (0, 0, 0, 0)); spark.alpha_composite(knock_white(SPARK, 660), ((W - 660) // 2, 170)); spark.save(WORK / "end_spark.png")

txt = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(txt)
ct(d, 880, "人が足りないなら、", 84, NAVY, BLACK); ct(d, 990, "人を伸ばせばいい。", 84, NAVY, BLACK)
ct(d, 1120, "DX支援・システム構築・AI人材教育", 40, GRAY, BOLD)
pw, ph, py = 720, 124, 1210
d.rounded_rectangle([(W - pw) / 2, py, (W + pw) / 2, py + ph], radius=ph // 2, fill=ORANGE)
ct(d, py + 28, "無料相談 30分", 60, (255, 255, 255), BLACK); ct(d, py + ph + 30, "プロフィールのリンクから", 40, NAVY, BOLD)
txt.save(WORK / "end_text.png")

ref = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rl = knock_white(REFAST, 300)
ref.alpha_composite(rl, ((W - 300) // 2, 1500)); ImageDraw.Draw(ref)
ct(ImageDraw.Draw(ref), 1500 + rl.height + 18, "株式会社ReFast", 40, NAVY, BOLD); ref.save(WORK / "end_refast.png")

# ---------- 4) sparkle SFX for the logo reveal ----------
SR = 48000; logo_t = end_start + X_END + 0.15
n = int(SR * total); sig = np.zeros(n)
for k, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):
    t = np.arange(int(SR * 2.0)) / SR
    s = (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-4 * t)) * np.exp(-2.8 * t) * np.minimum(1, t / .002) * (.12 - .02 * k)
    i = int((logo_t + .08 * k) * SR); sig[i:i + len(s)] += s[: max(0, n - i)]
with wave.open(str(WORK / "sparkle.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((sig * 32767).astype("<i2").tobytes())

# ---------- 5) assemble ----------
args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
for c in CLIPS: args += ["-i", c]
for p in ["end_bg.png", "end_spark.png", "end_text.png", "end_refast.png"]:
    args += ["-loop", "1", "-framerate", str(FPS), "-t", str(END_LEN), "-i", str(WORK / p)]
for s in sfx: args += ["-i", str(s)]
args += ["-i", str(WORK / "sparkle.wav")]
f = []
for i in range(4):
    f.append(f"[{i}:v]scale={W}:{H},fps={FPS},settb=1/{FPS},setpts=PTS-STARTPTS,format=yuv420p,setsar=1[c{i}]")
f.append(f"[4:v]format=yuv420p,setsar=1,settb=1/{FPS}[ebg]")
f.append(f"[5:v]format=rgba,fade=t=in:st=0.5:d=0.7:alpha=1[esp]")
f.append(f"[6:v]format=rgba,fade=t=in:st=1.2:d=0.6:alpha=1[etx]")
f.append(f"[7:v]format=rgba,fade=t=in:st=1.8:d=0.6:alpha=1[erf]")
f.append("[ebg][esp]overlay=format=auto[e1];[e1][etx]overlay=format=auto[e2];[e2][erf]overlay=format=auto,format=yuv420p,settb=1/30,setpts=PTS-STARTPTS[end]")
prev = "c0"
for i in range(1, 4):
    f.append(f"[{prev}][c{i}]xfade=transition=fade:duration={X}:offset={starts[i]:.3f}[x{i}]"); prev = f"x{i}"
f.append(f"[{prev}]fade=t=in:st=0:d=0.4,ass={ap}:fontsdir={FONTS}[main]")
f.append(f"[main][end]xfade=transition=fade:duration={X_END}:offset={end_start:.3f}[vout]")
a0 = 8
for i in range(4): f.append(f"[{a0 + i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}]")
f.append(f"[a0][a1]acrossfade=d={X}[ax1];[ax1][a2]acrossfade=d={X}[ax2];[ax2][a3]acrossfade=d={X}[ax3]")
f.append(f"[ax3]afade=t=out:st={end_start:.3f}:d=1.2,apad,atrim=duration={total:.3f}[sfx]")
f.append(f"[{a0 + 4}:a]aformat=channel_layouts=stereo[spk]")
f.append(f"[sfx][spk]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.7:attack=1:level=false[aout]")
args += ["-filter_complex", ";".join(f), "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-t", f"{total:.3f}", OUT]
run(*args)
print(f"clip starts {[round(s, 2) for s in starts]}, end card at {end_start:.2f}s, total {total:.2f}s -> {OUT}")
