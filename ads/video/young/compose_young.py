"""Young-employee episode: animation (or generated clips, same timing) + telops + end card + audio.
Usage: compose_young.py ANIM_MP4 AUDIO_WAV ENDCARD_PNG FONTS_DIR WORK_DIR OUT_MP4
"""
import subprocess, sys
from pathlib import Path

ANIM, AUDIO, ENDCARD, FONTS, WORK, OUT = sys.argv[1:7]
WORK = Path(WORK); FPS = 30; X_END = .6; END_LEN = 4.5


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).strip())


end_start = dur(ANIM) - X_END
total = end_start + END_LEN

T = [  # (start, end, lines, style)
    (0.6, 6.5, ["入社2年目。", "覚えることは、雑用ばかり。"], "T"),
    (7.6, 12.6, ["このままで、いいのかな。"], "T"),
    (15.8, 18.7, ["…この人も、最初は", "パソコンが苦手だった？"], "T"),
    (19.4, 23.8, ["無料相談、30分だけ。"], "T"),
    (24.6, 28.6, ["「何に困ってるか」を、", "先に聞いてくれた。"], "T"),
    (29.0, 32.7, ["売り込みじゃなく、", "相談に乗ってくれた。"], "T"),
    (33.6, 40.5, ["昼休みの20分が、", "楽しみになった。"], "T"),
    (42.0, 48.1, ["3時間かかってた発注が、", "15分に。"], "T"),
    (42.0, 48.1, ["※イメージです"], "N"),
    (48.9, 53.2, ["次は、源さんの「技」を、", "未来に残したい。"], "T"),
    (53.7, end_start + .1, ["翔太、24歳。", "あのタブレットを渡すまで。"], "T"),
]


def ts(s):
    cs = int(round(s * 100)); return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: T,Zen Kaku Gothic New Black,90,&H00FFFFFF,&H00FFFFFF,&H002B2015,&H96000000,0,0,0,0,100,100,2,0,1,8,4,2,110,110,0,1",
       "Style: N,Zen Kaku Gothic New Bold,42,&H00FFFFFF,&H00FFFFFF,&H002B2015,&H96000000,0,0,0,0,100,100,1,0,1,4,2,2,110,110,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for a, b, lines, st in T:
    y = 1340 if st == "T" else 1410
    ass.append(f"Dialogue: 0,{ts(a)},{ts(b)},{st},,0,0,0,,{{\\an2\\pos(540,{y})}}{{\\fad(200,200)}}{r'\N'.join(lines)}")
ap = WORK / "young_telops.ass"; ap.write_text("\n".join(ass) + "\n", encoding="utf-8")

n_end = int(round(END_LEN * FPS))
f = [f"[0:v]scale=1080:1920,fps={FPS},settb=1/{FPS},setpts=PTS-STARTPTS,format=yuv420p,setsar=1,ass={ap}:fontsdir={FONTS}[v0]",
     f"[1:v]scale=2160:3840,zoompan=z='1+0.025*on/{n_end}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps={FPS},trim=duration={END_LEN},settb=1/{FPS},setpts=PTS-STARTPTS,format=yuv420p,setsar=1[v1]",
     f"[v0][v1]xfade=transition=fade:duration={X_END}:offset={end_start:.3f}[vout]",
     f"[2:a]aresample=48000,apad,atrim=duration={total:.3f},loudnorm=I=-16:TP=-1.5:LRA=11[aout]"]
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", ANIM, "-loop", "1", "-framerate", str(FPS), "-t", str(END_LEN), "-i", ENDCARD, "-i", AUDIO,
                "-filter_complex", ";".join(f), "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-t", f"{total:.3f}", OUT], check=True)
print(f"wrote {OUT} ({total:.2f}s)")
