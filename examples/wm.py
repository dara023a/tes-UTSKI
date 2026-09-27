from PIL import Image, ImageDraw, ImageFont

# 1. Buat kanvas biner (mode '1' = 1-bit/biner) ukuran 156x156 px, latar belakang hitam (0)
width, height = 156, 156
image = Image.new('1', (width, height), 0)
draw = ImageDraw.Draw(image)

text = "3238"

# 2. Muat font bawaan sistem atau buat teks dengan ukuran presisi
try:
    # Menggunakan font Arial jika tersedia di sistem
    font = ImageFont.truetype("arial.ttf", 48)
except IOError:
    # Fallback ke font standar jika arial.ttf tidak ditemukan
    font = ImageFont.load_default()

# 3. Hitung posisi koordinat agar teks tepat berada di tengah (center)
bbox = draw.textbbox((0, 0), text, font=font)
text_w = bbox[2] - bbox[0]
text_h = bbox[3] - bbox[1]

x = (width - text_w) // 2
y = (height - text_h) // 2 - bbox[1]

# 4. Gambar angka "3238" dengan warna putih (1)
draw.text((x, y), text, fill=1, font=font)

# 5. Simpan gambar watermark
image.save("watermark_3238.png")
print("Watermark biner 156x156 px 'watermark_3238.png' berhasil dibuat!")