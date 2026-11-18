"""Craftsman episode: upscale to 1080x1920, burn telops (same style as compose.py), add end card,
replace audio with the voice-removed SFX track.

Usage: python3 compose_craftsman.py SRC_VIDEO SFX_WAV FONTS_DIR ENDCARD_PNG WORK_DIR OUT_MP4
"""
import subprocess, sys
from pathlib import Path

SRC, SFX, FONTS, ENDCARD, WORK, OUT = sys.argv[1:7]
WORK = Path(WORK)
FPS = 30
X_END = 0.6
END_LEN = 4.5


def dur(p):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).strip())


main = dur(SRC)
end_start = main - X_END
total = end_start + END_LEN

T = [
    (0.6, 4.6, ["この道、40年。"]),
    (5.0, 9.2, ["腕には、自信があった。"]),
    (9.6, 14.6, ["でも、「AIに仕事を", "取られる」と聞いて…"]),
    (15.6, 20.0, ["若いのが持ってきた、", "一台のタブレット。"]),
    (20.5, 24.8, ["図面も、段取りも、", "ぜんぶここに。"]),
    (25.3, 29.8, ["…なんだ、", "俺の腕が、まだ要るのか。"]),
    (30.6, 35.2, ["AIは、ただの道具だった。"]),
    (35.8, 39.3, ["俺の40年を、", "若い手に渡すための。"]),
    (39.8, 42.4, ["AIに仕事を、", "取られると思ってた。"]),
    (42.8, min(45.2, end_start), ["…逆だった。"]),
]


def ts(sec):
    cs = int(round(sec * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


ass = [
    "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "",
    "[V4+ Styles]",
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
    "Style: T,Zen Kaku Gothic New Black,90,&H00FFFFFF,&H00FFFFFF,&H002B2015,&H96000000,0,0,0,0,100,100,2,0,1,8,4,2,110,110,0,1",
    "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
]
for a, b, lines in T:
    ass.append(f"Dialogue: 0,{ts(a)},{ts(b)},T,,0,0,0,,{{\\an2\\pos(540,1340)}}{{\\fad(200,200)}}{r'\N'.join(lines)}")
ass_path = WORK / "craft_telops.ass"
ass_path.write_text("\n".join(ass) + "\n", encoding="utf-8")

n_end = int(round(END_LEN * FPS))
f = [
    f"[0:v]scale=1080:1920:flags=lanczos,fps={FPS},settb=1/{FPS},setpts=PTS-STARTPTS,format=yuv420p,setsar=1,"
    f"ass={ass_path}:fontsdir={FONTS}[v0]",
    f"[1:v]scale=2160:3840,zoompan=z='1+0.025*on/{n_end}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps={FPS},"
    f"trim=duration={END_LEN},settb=1/{FPS},setpts=PTS-STARTPTS,format=yuv420p,setsar=1[v1]",
    f"[v0][v1]xfade=transition=fade:duration={X_END}:offset={end_start:.3f}[vout]",
    f"[2:a]aresample=48000,afade=t=out:st={end_start - 0.5:.3f}:d=1.0,apad,atrim=duration={total:.3f}[aout]",
]
args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", SRC,
        "-loop", "1", "-framerate", str(FPS), "-t", f"{END_LEN}", "-i", ENDCARD, "-i", SFX,
        "-filter_complex", ";".join(f), "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-t", f"{total:.3f}", OUT]
print(f"main {main:.2f}s, end card at {end_start:.2f}s, total {total:.2f}s")
subprocess.run(args, check=True)
print("wrote", OUT)
