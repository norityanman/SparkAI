"""Megumi (career-gap) episode: 16:9 animation -> vertical 1080x1920 (blurred background), telops under the
picture, sound effects only (voices removed with Demucs), SparkAI / ReFast logo end card.

Usage: compose_megumi.py CLIP SPARKAI_LOGO REFAST_LOGO FONTS_DIR WORK_DIR OUT_MP4
"""
import subprocess, sys, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CLIP, SPARK, REFAST, FONTS, WORK, OUT = sys.argv[1:7]
WORK = Path(WORK); WORK.mkdir(parents=True, exist_ok=True)
FPS, X_END, END_LEN = 30, 0.6, 5.0
W, H = 1080, 1920
VIDEO_Y = 416          # top of the 1080x608 picture inside the vertical frame
TELOP_Y = 1340         # bottom edge of telops (below the picture)


def run(*a):
    subprocess.run(a, check=True)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).strip())


main_len = dur(CLIP)
end_start = main_len - X_END
total = end_start + END_LEN

# ---------- 1) sound effects only ----------
wav = WORK / "megumi.wav"
run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", CLIP, "-vn", "-ac", "2", "-ar", "44100", str(wav))
run(sys.executable, "-m", "demucs", "-n", "htdemucs", "--two-stems=vocals", "-d", "cpu", "-o", str(WORK / "sep"), str(wav))
sfx = WORK / "sep" / "htdemucs" / "megumi" / "no_vocals.wav"

# ---------- 2) telops ----------
T = [
    (0.4, 5.2, ["「お母さんの仕事なんて、", "書くことないよ」"], "T"),
    (5.8, 10.0, ["若い人たちの会話に、", "ついていけない。"], "T"),
    (10.3, 14.9, ["10年のブランク。", "私だけ、置いていかれてる。"], "T"),
    (15.3, 18.0, ["…私でも、", "まだ間に合う？"], "T"),
    (18.4, 20.8, ["「私も、子育てで", "8年ブランクがありました」"], "T"),
    (21.0, 23.2, ["10年の子育ても、", "“経験”だと言ってくれた。"], "T"),
    (23.6, 26.8, ["娘と並んで、", "私も“宿題”。"], "T"),
    (27.0, 30.0, ["できることから、", "ひとつずつ。"], "T"),
    (30.4, 32.1, ["「これ、恵さんが", "作ったの？」"], "T"),
    (32.4, 34.3, ["みんなが、", "集まってきた。"], "T"),
    (34.6, 37.8, ["会社で、", "“頼られる人”になった。"], "T"),
    (38.2, 42.0, ["「私のお母さんは、会社の", "みんなを助ける人です」"], "T"),
    (42.4, 99, ["娘の作文に、", "私の仕事が書かれていた。"], "T"),
]


def ts(s):
    cs = int(round(s * 100)); return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: T,Zen Kaku Gothic New Black,90,&H00FFFFFF,&H00FFFFFF,&H002B2015,&H96000000,0,0,0,0,100,100,2,0,1,8,4,2,110,110,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for a, b, lines, st in T:
    ass.append(f"Dialogue: 0,{ts(a)},{ts(min(b, end_start + .1))},{st},,0,0,0,,{{\\an2\\pos(540,{TELOP_Y})}}{{\\fad(200,200)}}{r'\N'.join(lines)}")
ap = WORK / "megumi.ass"; ap.write_text("\n".join(ass) + "\n", encoding="utf-8")

# ---------- 3) end card layers ----------
BLACK, BOLD = f"{FONTS}/ZenKakuGothicNew-Black.ttf", f"{FONTS}/ZenKakuGothicNew-Bold.ttf"
NAVY, ORANGE, GRAY = (31, 43, 61), (240, 110, 40), (110, 118, 130)


def knock_white(path, width):
    im = Image.open(path).convert("RGB")
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    a = np.asarray(im).astype(np.int16)
    out = im.convert("RGBA"); out.putalpha(Image.fromarray(np.clip((255 - a.min(axis=2)) * 6, 0, 255).astype(np.uint8))); return out


def ct(d, y, s, size, fill, path):
    f = ImageFont.truetype(path, size); d.text(((W - d.textlength(s, font=f)) / 2, y), s, font=f, fill=fill)


bg = Image.new("RGB", (W, H), (255, 255, 255))
glow = Image.new("L", (W, H), 0); ImageDraw.Draw(glow).ellipse([140, 120, 940, 920], fill=60)
bg = Image.composite(Image.new("RGB", (W, H), (255, 236, 214)), bg, glow.filter(ImageFilter.GaussianBlur(120))); bg.save(WORK / "end_bg.png")
spark = Image.new("RGBA", (W, H), (0, 0, 0, 0)); spark.alpha_composite(knock_white(SPARK, 660), ((W - 660) // 2, 170)); spark.save(WORK / "end_spark.png")
txt = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(txt)
ct(d, 880, "何歳からでも、", 88, NAVY, BLACK); ct(d, 995, "人は伸びる。", 88, NAVY, BLACK)
ct(d, 1125, "人が足りないなら、人を伸ばせばいい。", 40, GRAY, BOLD)
pw, ph, py = 720, 124, 1210
d.rounded_rectangle([(W - pw) / 2, py, (W + pw) / 2, py + ph], radius=ph // 2, fill=ORANGE)
ct(d, py + 28, "無料相談 30分", 60, (255, 255, 255), BLACK); ct(d, py + ph + 30, "プロフィールのリンクから", 40, NAVY, BOLD)
txt.save(WORK / "end_text.png")
ref = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rl = knock_white(REFAST, 300)
ref.alpha_composite(rl, ((W - 300) // 2, 1500)); ct(ImageDraw.Draw(ref), 1500 + rl.height + 18, "株式会社ReFast", 40, NAVY, BOLD); ref.save(WORK / "end_refast.png")

# ---------- 4) sparkle SFX at the logo reveal ----------
SR = 48000; logo_t = end_start + X_END + 0.15
n = int(SR * total); sig = np.zeros(n)
for k, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):
    t = np.arange(int(SR * 2.0)) / SR
    s = (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-4 * t)) * np.exp(-2.8 * t) * np.minimum(1, t / .002) * (.12 - .02 * k)
    i = int((logo_t + .08 * k) * SR); sig[i:i + len(s)] += s[: max(0, n - i)]
with wave.open(str(WORK / "sparkle.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((sig * 32767).astype("<i2").tobytes())

# ---------- 5) assemble ----------
args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", CLIP]
for p in ["end_bg.png", "end_spark.png", "end_text.png", "end_refast.png"]:
    args += ["-loop", "1", "-framerate", str(FPS), "-t", str(END_LEN), "-i", str(WORK / p)]
args += ["-i", str(sfx), "-i", str(WORK / "sparkle.wav")]
f = [
    f"[0:v]fps={FPS},settb=1/{FPS},setpts=PTS-STARTPTS,split[s0][s1]",
    f"[s0]scale=-2:{H},crop={W}:{H},boxblur=30:3,eq=brightness=-0.06[blur]",
    f"[s1]scale={W}:-2[fg]",
    f"[blur][fg]overlay=0:{VIDEO_Y},format=yuv420p,setsar=1,fade=t=in:st=0:d=0.4,ass={ap}:fontsdir={FONTS}[main]",
    f"[1:v]format=yuv420p,setsar=1,settb=1/{FPS}[ebg]",
    "[2:v]format=rgba,fade=t=in:st=0.5:d=0.7:alpha=1[esp]",
    "[3:v]format=rgba,fade=t=in:st=1.2:d=0.6:alpha=1[etx]",
    "[4:v]format=rgba,fade=t=in:st=1.8:d=0.6:alpha=1[erf]",
    f"[ebg][esp]overlay=format=auto[e1];[e1][etx]overlay=format=auto[e2];[e2][erf]overlay=format=auto,format=yuv420p,settb=1/{FPS},setpts=PTS-STARTPTS[end]",
    f"[main][end]xfade=transition=fade:duration={X_END}:offset={end_start:.3f}[vout]",
    f"[5:a]aresample=48000,aformat=channel_layouts=stereo,afade=t=out:st={end_start:.3f}:d=1.2,apad,atrim=duration={total:.3f}[sfx]",
    "[6:a]aformat=channel_layouts=stereo[spk]",
    "[sfx][spk]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.7:attack=1:level=false[aout]",
]
args += ["-filter_complex", ";".join(f), "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-t", f"{total:.3f}", OUT]
run(*args)
print(f"end card at {end_start:.2f}s, total {total:.2f}s -> {OUT}")
