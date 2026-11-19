"""End card for the young-employee episode (SparkAI service / 株式会社ReFast). Usage: make_endcard.py FONTS_DIR OUT.png"""
import sys
from PIL import Image, ImageDraw, ImageFont

FONTS, OUT = sys.argv[1], sys.argv[2]
BLACK, BOLD = f"{FONTS}/ZenKakuGothicNew-Black.ttf", f"{FONTS}/ZenKakuGothicNew-Bold.ttf"
W, H = 1080, 1920
NAVY, AMBER, WHITE, SOFT = (21, 32, 43), (224, 160, 74), (255, 255, 255), (178, 190, 202)
img = Image.new("RGB", (W, H), NAVY)
d = ImageDraw.Draw(img)


def ct(y, s, size, fill, path=BLACK):
    f = ImageFont.truetype(path, size)
    d.text(((W - d.textlength(s, font=f)) / 2, y), s, font=f, fill=fill)


cx, cy, r = W // 2, 500, 70
d.polygon([(cx, cy - r), (cx + r * .28, cy - r * .28), (cx + r, cy), (cx + r * .28, cy + r * .28),
           (cx, cy + r), (cx - r * .28, cy + r * .28), (cx - r, cy), (cx - r * .28, cy - r * .28)], fill=AMBER)
ct(680, "人が足りないなら、", 92, WHITE)
ct(810, "人を伸ばせばいい。", 92, WHITE)
ct(990, "DX支援・システム構築・AI人材教育", 44, SOFT, BOLD)
ct(1090, "SparkAI", 130, AMBER)
pw, ph, py = 760, 130, 1380
d.rounded_rectangle([(W - pw) / 2, py, (W + pw) / 2, py + ph], radius=ph // 2, fill=AMBER)
ct(py + 30, "無料相談 30分", 62, NAVY)
ct(py + ph + 40, "プロフィールのリンクから", 44, WHITE, BOLD)
ct(1760, "株式会社ReFast", 36, SOFT, BOLD)
img.save(OUT)
print("wrote", OUT)
