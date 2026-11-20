"""assets/icon.png ve assets/icon.ico dosyalarını üretir (OtoTık'taki yaklaşım).

Simge: yeşil-turkuaz yuvarlatılmış kare üzerinde bir metin imleci ve "genişleyen" üç çizgi.
Kullanım:  py tools/make_icon.py   (depo kökünden)
"""
from PIL import Image, ImageDraw

S = 1024
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
grad = Image.new("RGBA", (S, S))
gd = ImageDraw.Draw(grad)
c1, c2 = (20, 184, 166), (59, 130, 246)
for y in range(S):
    t = y / S
    gd.line([(0, y), (S, y)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)) + (255,))
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle([40, 40, S - 40, S - 40], radius=230, fill=255)
img.paste(grad, (0, 0), mask)

d = ImageDraw.Draw(img)
white = (255, 255, 255, 255)
# ";" — tetikleyici öneki
d.ellipse([230, 330, 330, 430], fill=white)
d.ellipse([230, 560, 330, 660], fill=white)
d.polygon([(250, 650), (330, 640), (270, 780), (215, 770)], fill=white)
# genişleyen metin satırları
for y, w in ((330, 420), (480, 340), (630, 260)):
    d.rounded_rectangle([420, y, 420 + w, y + 70], radius=35, fill=white)
img.save("assets/icon.png")
img.resize((256, 256), Image.LANCZOS).save(
    "assets/icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("icon ok")
