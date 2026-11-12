"""Builds the calendar still (old logo replaced) and the end card as 1080x1920 PNGs."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

S = Path(sys.argv[1])
BLACK = str(S / "fonts/ZenKakuGothicNew-Black.ttf")
BOLD = str(S / "fonts/ZenKakuGothicNew-Bold.ttf")
W, H = 1080, 1920


def font(path, size):
    return ImageFont.truetype(path, size)


def center_text(d, y, text, f, fill, **kw):
    w = d.textlength(text, font=f)
    d.text(((W - w) / 2, y), text, font=f, fill=fill, **kw)


# --- calendar still ---
cal = Image.open(S / "cal_full.png").convert("RGB")
d = ImageDraw.Draw(cal)
d.rectangle([0, 0, W, 305], fill=(217, 96, 76))          # repaint red header band
center_text(d, 70, "ReFast", font(BLACK, 170), (255, 255, 255))
d.rectangle([40, 1400, W - 40, 1880], fill=(251, 251, 251))  # cover garbled table
center_text(d, 1440, "か月後", font(BLACK, 230), (58, 134, 200))
cal.save(S / "cal_fixed.png")

# --- end card ---
NAVY, AMBER, WHITE, SOFT = (21, 32, 43), (224, 160, 74), (255, 255, 255), (178, 190, 202)
card = Image.new("RGB", (W, H), NAVY)
d = ImageDraw.Draw(card)
# spark mark
cx, cy, r = W // 2, 520, 70
d.polygon([(cx, cy - r), (cx + r * .28, cy - r * .28), (cx + r, cy), (cx + r * .28, cy + r * .28),
           (cx, cy + r), (cx - r * .28, cy + r * .28), (cx - r, cy), (cx - r * .28, cy - r * .28)], fill=AMBER)
center_text(d, 700, "人が足りないなら、", font(BLACK, 92), WHITE)
center_text(d, 830, "人を伸ばせばいい。", font(BLACK, 92), WHITE)
center_text(d, 1010, "DX支援・システム構築・AI人材教育", font(BOLD, 44), SOFT)
center_text(d, 1110, "ReFast", font(BLACK, 130), AMBER)
# CTA pill
pw, ph, py = 760, 130, 1380
d.rounded_rectangle([(W - pw) / 2, py, (W + pw) / 2, py + ph], radius=ph // 2, fill=AMBER)
center_text(d, py + 30, "無料DX診断 30分", font(BLACK, 62), NAVY)
center_text(d, py + ph + 40, "プロフィールのリンクから", font(BOLD, 44), WHITE)
center_text(d, 1760, "株式会社ReFast", font(BOLD, 36), SOFT)
card.save(S / "endcard.png")
print("ok")
