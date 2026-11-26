# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Marketing material for **株式会社ReFast** and its service **SparkAI** (DX support, system building, AI training for small and mid-sized companies). There is no application to build or test. The repo holds:

- `ads/*.md`: ad story concepts, written in Japanese. Each one follows the same arc: 悩み → SNSで知る → クリック → 相談 → 学ぶ → 成功体験 → 輝かしい未来. Each has a 60s scene table with telops, a 15s cut, and notes.
- `ads/storyboard.html`: a storyboard page that was published as an Artifact.
- `ads/video/`: scripts that turn AI-generated anime clips (supplied by the user) into finished vertical SNS ads, plus the rendered `.mp4` outputs.

Main copy: 「人が足りないなら、人を伸ばせばいい。」. Always use the brand names exactly as written: 株式会社ReFast and SparkAI.

## Video pipeline (ads/video)

Each episode has its own `compose_*.py` (for example `riku/compose_final.py`, `megumi/compose_megumi.py`, `sandai/compose_sandai.py`, `hinano/compose_hinano.py`). They are standalone Python scripts with the same shape:

1. **Audio, sound effects only.** Demucs (`python3 -m demucs -n htdemucs`) separates the clip's audio.
   - Use `--two-stems=vocals` and keep `no_vocals.wav` when only voices must go.
   - When the generated clip also contains music, run the 4-stem mode and keep only `drums.wav`, which holds the short sound effects (see `SFX_STEM` in `sandai/compose_sandai.py`).
2. **Telops.** A Python list `T` of `(start, end, lines, style)` is written to an ASS file and burned in with ffmpeg's `ass` filter.
   - Times are relative to the clip, or to the segment when several clips are joined.
3. **End card.** PIL draws transparent layers that fade in one after another, in this order:
   - the SparkAI logo
   - the copy
   - an orange 「無料相談 30分」 pill and 「プロフィールのリンクから」
   - the ReFast logo with 「株式会社ReFast」
   
   A small synthesized "sparkle" chime plays when the logo appears.
4. **One ffmpeg `filter_complex`** does all of this:
   - trim and reorder segments
   - join them with `xfade` and `acrossfade`
   - overlay the telops
   - add the end card
   - mix the audio, then `loudnorm` and `alimiter`

Run a script like this:
```bash
python3 ads/video/<episode>/compose_<episode>.py <clips...> <sparkai_logo.jpg> ads/video/video_src/refast_logo.png <fonts_dir> <work_dir> ads/video/<output>.mp4
```
Each script's docstring gives its exact argument order.

Other scripts:
- `young/` and `riku/`: animations drawn in code, used when no generated clips exist. `scenes.html` draws each frame on a canvas, `render.js` uses Playwright to grab frames and pipe them to ffmpeg, `make_audio.py` synthesizes BGM and sound effects with numpy, and `compose_*.py` adds telops and the end card.
- `make_bgm*.py`: original piano BGM synthesized with numpy, timed to each video's scenes. Use these only when BGM is requested.
- `video_src/`: assets from an earlier, separate pipeline (Noto Sans telop `.ass` files, `bgm*.py`, `refast_logo.png`).

### Environment requirements
- `ffmpeg` with libass, numpy, and Pillow are needed. Node Playwright is preinstalled.
- Fonts: Zen Kaku Gothic New Black/Bold TTFs, downloaded from `raw.githubusercontent.com/google/fonts/main/ofl/zenkakugothicnew/` into a scratch fonts dir. They are not committed.
- Demucs: install with `pip install demucs`. PyTorch from PyPI works. The first run downloads the model from `dl.fbaipublicfiles.com`, which must be allowed by the environment's network settings.
- The SparkAI logo (`2e733742-image.jpg`) comes from the user's uploads and is passed in as an argument. The user declined copying it into the repo, so do not commit it.

### House style for videos
- Output is vertical 1080×1920, 30fps, H.264 CRF 18, AAC 192k, `+faststart`.
- 16:9 clips go on a blurred background with the telops below the picture (see `megumi/compose_megumi.py`).
- Telop ASS style: Zen Kaku Gothic New Black, size about 84–90 at PlayRes 1080×1920, white text with a navy outline (`&H002B2015`), outline 8, shadow 4, `\an2\pos(540,1340)`. At most 2 lines and about 13 characters per line, with a 0.15–0.2s fade. Use a small `N` style for notes such as 「※イメージです」, which must accompany any illustrative number.
- Audio:
  - Voices and generated BGM are removed and sound effects kept, unless the user asks for BGM.
  - Use `loudnorm=I=-16:TP=-1.5` followed by `alimiter=limit=0.7`. A limit of 0.84 still clipped after AAC encoding.
- Keep only anime-looking footage. Cut live-action-looking shots, and also cut shots that repeat scenes from another clip. If shots must stay, unify them with the `ANIME` filter in `hinano/compose_hinano.py`: three `bilateral` passes, then multiply-blended edge lines in `gbrp`, then a shared grade.

### Pitfalls seen when editing the filter graphs
- Find real cut points with timestamped contact sheets (`fps=2,drawtext=...%{pts},tile=`). Scene-detection timestamps alone have placed telops on the wrong shot.
- `xfade` needs matching timebases. Add `settb=1/30` after `concat` or `overlay`.
- Filter labels must be unique across the whole graph. Shot-processing labels once collided with the end card's `[e1]`.
- `blend` on mixed pixel formats turns the image green. Convert both inputs to `gbrp` first.
- AI-generated clips can contain glitches, such as a phone floating with no hand. Remove them by trimming the clip and dissolving over the gap (`CUTS` in `riku/compose_final.py`), then shift the telops to match.

### Checking a render
- Contact sheet: `ffmpeg -i out.mp4 -vf "fps=1/2,scale=150:267,tile=13x2" -frames:v 1 sheet.png`, then view the image.
- Duration and streams: `ffprobe`. Peak level: `volumedetect` (should be below 0 dB).
- Claude cannot listen to audio. Tell the user to check the result by ear, and name the time ranges where voices or music were removed.

## Working with this user

- The user writes in Japanese. Reply in Japanese.
- When the user asks for a story (「ストーリー考えて」), reply with text only. Do not make a video, and do not save or commit the story unless asked. The user once declined a commit of a story file.
- When the user uploads clips, deliver the edited video with `SendUserFile` and commit it to the working branch.
- Do not use paid services or sites.
- The user cannot share Instagram links usefully: instagram.com is not reachable from this environment and needs a login anyway. Ask for screen recordings and screenshots instead.
