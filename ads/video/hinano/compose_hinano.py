"""ひなの編 (Z世代向け 30秒): unify the look of realistic-looking shots with the anime shots, add telops,
keep sound effects only (voices + generated music removed with Demucs), SparkAI / ReFast logo end card.

Usage: compose_hinano.py CLIP SPARKAI_LOGO REFAST_LOGO FONTS_DIR WORK_DIR OUT_MP4
"""
import subprocess, sys, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CLIP, SPARK, REFAST, FONTS, WORK, OUT = sys.argv[1:7]
WORK = Path(WORK); WORK.mkdir(parents=True, exist_ok=True)
FPS, X_END, END_LEN = 30, 0.6, 4.5
W, H = 1080, 1920


def run(*a):
    subprocess.run(a, check=True)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).strip())


main_len = dur(CLIP)
end_start = main_len - X_END
total = end_start + END_LEN

# ---------- look: one common grade for everything; realistic-looking shots also get a painted/anime finish ----------
GRADE = "eq=saturation=1.1:contrast=1.04:brightness=0.01,colorbalance=rs=0.02:bs=-0.02:rm=0.02:bm=-0.01"
ANIME = ("format=gbrp,bilateral=sigmaS=10:sigmaR=0.16,bilateral=sigmaS=8:sigmaR=0.14,bilateral=sigmaS=6:sigmaR=0.12,"
         "split[sb{i}][se{i}];[se{i}]gblur=sigma=0.8,edgedetect=low=0.07:high=0.2:mode=wires,negate,format=gbrp[sl{i}];"
         "[sb{i}][sl{i}]blend=all_mode=multiply:all_opacity=0.42,format=yuv420p")
# (start, end, realistic?) — cut points follow the scene changes of the source
SHOTS = [(0.0, 20.2333, False), (20.2333, 24.2333, True), (24.2333, 25.1333, False),
         (25.1333, 27.0667, True), (27.0667, main_len, False)]

# ---------- audio: voices (0–15s) and generated music (15s–) removed ----------
wav = WORK / "hinano.wav"
run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", CLIP, "-vn", "-ac", "2", "-ar", "44100", str(wav))
run(sys.executable, "-m", "demucs", "-n", "htdemucs", "-d", "cpu", "-o", str(WORK / "sep4"), str(wav))
stems = WORK / "sep4" / "htdemucs" / "hinano"
MUSIC_FROM = 15.13   # before: drums+bass+other (no voice); after: drums only (no music)

# ---------- telops ----------
T = [
    (0.3, 2.9, ["POV：入社1年目。", "配属、“何でも係”だった。"], "T"),
    (3.2, 5.8, ["（このまま、何者にも", "なれないのかな）"], "T"),
    (6.0, 8.8, ["「AIで、“好き”を仕事に」", "……え？"], "T"),
    (9.2, 13.3, ["無料相談で、", "趣味の動画を見せてみた。"], "T"),
    (13.5, 15.0, ["“武器”って、", "言われた。"], "T"),
    (15.3, 17.0, ["AIで、台本と字幕。"], "T"),
    (17.4, 20.0, ["企画も、", "AIと一緒に考える。"], "T"),
    (20.4, 24.0, ["職人さんの手元は、", "本物。"], "T"),
    (24.3, 27.0, ["再生数、うちの会社史上", "いちばん。"], "T"),
    (24.3, 27.0, ["※イメージです"], "N"),
    (27.2, 99, ["“好き”が、", "仕事になった。"], "T"),
]


def ts(s):
    cs = int(round(s * 100)); return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: T,Zen Kaku Gothic New Black,84,&H00FFFFFF,&H00FFFFFF,&H002B2015,&H96000000,0,0,0,0,100,100,2,0,1,8,4,2,90,90,0,1",
       "Style: N,Zen Kaku Gothic New Bold,40,&H00FFFFFF,&H00FFFFFF,&H002B2015,&H96000000,0,0,0,0,100,100,1,0,1,4,2,2,90,90,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for a, b, lines, st in T:
    y = 1340 if st == "T" else 1410
    ass.append(f"Dialogue: 0,{ts(a)},{ts(min(b, end_start + .1))},{st},,0,0,0,,{{\\an2\\pos(540,{y})}}{{\\fad(150,150)}}{r'\N'.join(lines)}")
ap = WORK / "hinano.ass"; ap.write_text("\n".join(ass) + "\n", encoding="utf-8")

# ---------- end card ----------
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
ct(d, 900, "好きなことで、", 86, NAVY, BLACK); ct(d, 1010, "伸びていい。", 86, NAVY, BLACK)
pw, ph, py = 720, 124, 1180
d.rounded_rectangle([(W - pw) / 2, py, (W + pw) / 2, py + ph], radius=ph // 2, fill=ORANGE)
ct(d, py + 28, "無料相談 30分", 60, (255, 255, 255), BLACK); ct(d, py + ph + 30, "プロフィールのリンクから", 40, NAVY, BOLD)
tx.save(WORK / "end_text.png")
rf = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rl = knock_white(REFAST, 300)
rf.alpha_composite(rl, ((W - 300) // 2, 1500)); ct(ImageDraw.Draw(rf), 1500 + rl.height + 18, "株式会社ReFast", 40, NAVY, BOLD); rf.save(WORK / "end_refast.png")

SR = 48000; logo_t = end_start + X_END + 0.15; n = int(SR * total); sig = np.zeros(n)
for k, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):
    t = np.arange(int(SR * 2.0)) / SR
    s = (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-4 * t)) * np.exp(-2.8 * t) * np.minimum(1, t / .002) * (.09 - .015 * k)
    i = int((logo_t + .08 * k) * SR); sig[i:i + len(s)] += s[: max(0, n - i)]
with wave.open(str(WORK / "sparkle.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((sig * 32767).astype("<i2").tobytes())

# ---------- assemble ----------
args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", CLIP]
for p in ["end_bg.png", "end_spark.png", "end_text.png", "end_refast.png"]:
    args += ["-loop", "1", "-framerate", str(FPS), "-t", str(END_LEN), "-i", str(WORK / p)]
for st in ["drums", "bass", "other"]:
    args += ["-i", str(stems / f"{st}.wav")]
args += ["-i", str(WORK / "sparkle.wav")]
f = [f"[0:v]fps={FPS},settb=1/{FPS},setpts=PTS-STARTPTS,format=yuv420p,split={len(SHOTS)}" + "".join(f"[v{i}]" for i in range(len(SHOTS)))]
for i, (a, b, real) in enumerate(SHOTS):
    look = (ANIME.format(i=i) + "," if real else "") + GRADE
    f.append(f"[v{i}]trim={a}:{b},setpts=PTS-STARTPTS,{look},setsar=1[o{i}]")
f.append("".join(f"[o{i}]" for i in range(len(SHOTS))) + f"concat=n={len(SHOTS)}:v=1:a=0,settb=1/{FPS},fade=t=in:st=0:d=0.3,ass={ap}:fontsdir={FONTS}[main]")
f.append(f"[1:v]format=yuv420p,setsar=1,settb=1/{FPS}[ebg]")
f.append("[2:v]format=rgba,fade=t=in:st=0.4:d=0.6:alpha=1[esp]")
f.append("[3:v]format=rgba,fade=t=in:st=1.0:d=0.5:alpha=1[etx]")
f.append("[4:v]format=rgba,fade=t=in:st=1.5:d=0.5:alpha=1[erf]")
f.append(f"[ebg][esp]overlay=format=auto[e1];[e1][etx]overlay=format=auto[e2];[e2][erf]overlay=format=auto,format=yuv420p,settb=1/{FPS},setpts=PTS-STARTPTS[end]")
f.append(f"[main][end]xfade=transition=fade:duration={X_END}:offset={end_start:.3f}[vout]")
f.append(f"[5:a]aresample=48000,asplit=2[d1][d2]")
f.append(f"[6:a]aresample=48000,atrim=0:{MUSIC_FROM},asetpts=PTS-STARTPTS[b1]")
f.append(f"[7:a]aresample=48000,atrim=0:{MUSIC_FROM},asetpts=PTS-STARTPTS[t1]")
f.append(f"[d1]atrim=0:{MUSIC_FROM},asetpts=PTS-STARTPTS[d1a]")
f.append(f"[d1a][b1][t1]amix=inputs=3:normalize=0[first]")
f.append(f"[d2]atrim={MUSIC_FROM},asetpts=PTS-STARTPTS[second]")
f.append(f"[first][second]acrossfade=d=0.2,aformat=channel_layouts=stereo,afade=t=out:st={end_start:.3f}:d=1.0,apad,atrim=duration={total:.3f}[sfx]")
f.append("[8:a]aresample=48000,aformat=channel_layouts=stereo[spk]")
f.append("[sfx][spk]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.7:attack=1:level=false[aout]")
args += ["-filter_complex", ";".join(f), "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-t", f"{total:.3f}", OUT]
run(*args)
print(f"end card at {end_start:.2f}s, total {total:.2f}s -> {OUT}")
