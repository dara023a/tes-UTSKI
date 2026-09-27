Saya sedang mengerjakan proyek mata kuliah Keamanan Informasi dengan topik **Digital Watermarking**. Tolong pahami konteks proyek ini terlebih dahulu sebelum memberikan saran, kode, atau rancangan implementasi.

## 1. Gambaran Umum Proyek

Judul proyek:

**“Robust Watermarking Blind Berbasis DCT Frekuensi Menengah untuk Melindungi Karya Ilustrasi Digital dari Pencurian di Media Sosial: Analisis Ketahanan terhadap Kompresi JPEG, Resize, dan Cropping”**

Tujuan utama proyek adalah membuat aplikasi yang dapat menyisipkan watermark kepemilikan ke dalam sebuah gambar secara **tidak terlihat (invisible)**, kemudian watermark tersebut tetap dapat dideteksi/diekstraksi setelah gambar mengalami berbagai manipulasi.

Contoh kasus:
- Seorang ilustrator memiliki gambar asli.
- Pemilik menyisipkan watermark berupa logo atau identitas pemilik.
- Gambar kemudian diunggah ke media sosial.
- Media sosial dapat melakukan kompresi atau perubahan ukuran gambar.
- Gambar juga dapat mengalami cropping atau manipulasi lainnya.
- Sistem kemudian menerima gambar hasil manipulasi tersebut.
- Sistem mencoba mengambil kembali watermark tanpa membutuhkan gambar asli.
- Sistem menghitung seberapa baik watermark masih dapat dikenali menggunakan NC dan BER.

Aplikasi yang dibuat akan berbasis web.

Teknologi yang direncanakan:
- **Laravel** → bagian web interface, upload, routing, hasil, dan integrasi aplikasi.
- **Python** → bagian inti pengolahan citra dan algoritma watermarking.
- **DCT** → metode transformasi yang digunakan untuk watermarking.
- Laravel akan menjalankan/menghubungkan proses Python untuk melakukan embedding, extraction, attack, dan perhitungan metrik.

## 2. Apa yang Dimaksud Digital Watermarking?

Digital watermarking adalah teknik menyisipkan informasi tertentu ke dalam media digital, misalnya gambar, sehingga informasi tersebut dapat digunakan untuk menunjukkan kepemilikan, autentikasi, atau tujuan tertentu.

Dalam proyek ini, watermark berupa:
- logo sederhana dalam bentuk binary image, atau
- identitas pemilik seperti NPM/nama.

Watermark harus dibuat **invisible**, sehingga secara visual gambar hasil watermarking tetap terlihat seperti gambar asli.

Yang penting: watermark bukan sekadar ditempel sebagai teks/logo di atas gambar. Watermark benar-benar disisipkan ke dalam data piksel melalui proses transformasi DCT.

## 3. Apa Itu Robust Watermarking?

**Robust watermarking** adalah watermarking yang dirancang agar watermark tetap dapat dideteksi setelah gambar mengalami perubahan atau serangan tertentu.

Dalam proyek ini, robustness akan diuji dengan beberapa attack/manipulasi:

1. JPEG compression quality 90
2. JPEG compression quality 70
3. JPEG compression quality 50
4. Resize
5. Cropping
6. Gaussian noise
7. Brightness adjustment
8. Contrast adjustment

Tidak semua attack harus digabungkan sekaligus. Sistem akan menguji gambar hasil watermarking terhadap masing-masing attack dan kemudian melihat apakah watermark masih dapat diekstraksi.

JPEG quality 90, 70, dan 50 merupakan pengujian yang secara eksplisit diwajibkan dalam tugas.

## 4. Apa Itu Blind Watermarking?

**Blind watermarking** berarti proses extraction/detection watermark tidak membutuhkan gambar asli.

Dalam proyek ini, sistem hanya membutuhkan:
- gambar yang sudah diberi watermark dan mungkin sudah mengalami attack;
- secret key;
- informasi yang diperlukan untuk proses ekstraksi.

Tidak boleh bergantung pada original image untuk mengambil watermark.

Perbedaannya:

### Non-blind
Original image + attacked watermarked image → extraction

### Blind
Attacked watermarked image + secret key → extraction

Proyek ini menggunakan pendekatan **blind watermarking**.

Hal ini penting karena dalam kasus nyata, pihak yang ingin memverifikasi kepemilikan belum tentu memiliki akses ke gambar yang benar-benar identik dengan gambar sebelum watermarking.

## 5. Apa Itu DCT?

**DCT (Discrete Cosine Transform)** adalah transformasi yang mengubah representasi gambar dari domain spasial menjadi domain frekuensi.

Secara sederhana:

Gambar normal:
**pixel → spatial domain**

Setelah DCT:
**pixel → frequency coefficients**

Koefisien DCT menunjukkan komponen frekuensi yang terdapat dalam gambar.

Dalam implementasi watermarking citra, gambar umumnya dibagi menjadi blok, misalnya **8×8 piksel**, kemudian DCT diterapkan pada setiap blok.

Setelah watermark dimasukkan ke koefisien DCT, dilakukan **Inverse DCT (IDCT)** untuk mengubahnya kembali menjadi gambar.

Alur sederhananya:

**Image → Split 8×8 blocks → DCT → Modify coefficients → IDCT → Watermarked Image**

Ukuran blok dan metode pemilihan koefisien harus mengikuti algoritma/paper utama yang digunakan dalam penelitian. Jangan mengarang posisi koefisien jika belum ditentukan.

## 6. Apa Itu Low, Medium, dan High Frequency?

Dalam domain DCT, koefisien dapat dipahami secara sederhana sebagai:

- **Low frequency** → perubahan/intensitas gambar yang relatif besar dan halus.
- **Medium/intermediate frequency** → frekuensi menengah.
- **High frequency** → detail kecil atau perubahan cepat pada gambar.

Proyek ini menggunakan **medium-frequency coefficients**.

Alasannya secara umum adalah mencari kompromi antara:

**Imperceptibility ↔ Robustness**

Jika watermark terlalu banyak memengaruhi komponen yang sensitif, kualitas visual gambar dapat turun.

Jika watermark hanya diletakkan pada komponen yang sangat mudah hilang akibat kompresi, watermark dapat menjadi tidak robust.

Karena itu penelitian ini berfokus pada frekuensi menengah.

Namun, posisi koefisien medium-frequency yang digunakan dalam implementasi harus ditentukan berdasarkan paper/algoritma yang dipilih, bukan asal memilih koordinat.

## 7. Apa Itu Embedding?

**Embedding** adalah proses memasukkan watermark ke dalam gambar.

Input:

- Original image
- Watermark
- Secret key

Proses:

1. Baca gambar.
2. Ubah gambar ke format yang sesuai untuk DCT.
3. Bagi gambar menjadi blok.
4. Lakukan DCT.
5. Tentukan medium-frequency coefficients.
6. Gunakan secret key untuk menentukan posisi/blok/urutan tertentu jika algoritmanya menggunakan key.
7. Modifikasi koefisien berdasarkan bit watermark.
8. Lakukan IDCT.
9. Gabungkan kembali blok.
10. Hasilkan watermarked image.

Secara konseptual:

**Original Image + Watermark + Secret Key**
→ DCT
→ Medium Frequency Coefficients
→ Embedding
→ IDCT
→ **Watermarked Image**

## 8. Apa Itu Extraction?

**Extraction** adalah proses mengambil kembali watermark dari gambar yang telah diberi watermark.

Karena proyek menggunakan blind watermarking, extraction tidak menggunakan original image.

Input:

- Attacked watermarked image
- Secret key

Proses:

1. Baca gambar hasil attack.
2. Bagi menjadi blok.
3. DCT setiap blok.
4. Ambil medium-frequency coefficients yang digunakan saat embedding.
5. Gunakan secret key jika diperlukan.
6. Analisis koefisien untuk menentukan kembali bit watermark.
7. Susun bit menjadi watermark.
8. Hasilkan extracted watermark.

Secara konseptual:

**Attacked Watermarked Image + Secret Key**
→ DCT
→ Medium Frequency Coefficients
→ Extraction
→ **Extracted Watermark**

## 9. Apa Itu Secret Key?

Secret key digunakan untuk menambahkan aspek keamanan pada watermarking.

Key dapat digunakan untuk menentukan:
- blok mana yang digunakan;
- posisi koefisien;
- urutan pemilihan;
- pseudo-random sequence;
- atau mekanisme lain sesuai algoritma yang digunakan.

Tujuannya agar proses extraction tidak bisa dilakukan secara sembarangan tanpa mengetahui key.

Secret key **tidak boleh di-hardcode di source code atau di-upload ke GitHub**.

Jika menggunakan random sequence, gunakan random generator yang sesuai dan dokumentasikan mekanismenya.

## 10. Apa Itu Attack?

Attack dalam konteks proyek ini bukan berarti menyerang sistem komputer.

Attack berarti **manipulasi terhadap gambar watermarked** untuk menguji ketahanan watermark.

Contoh:

### JPEG Compression

Gambar dikompresi dengan kualitas:
- 90
- 70
- 50

Tujuannya melihat apakah watermark tetap dapat dideteksi ketika kualitas JPEG semakin turun.

### Resize

Ukuran gambar diubah.

Contohnya:
Original:
1920×1080

menjadi ukuran tertentu yang telah ditentukan dalam eksperimen.

Parameter resize harus didokumentasikan dan digunakan secara konsisten.

### Cropping

Sebagian area gambar dipotong.

Tujuannya menguji apakah watermark masih dapat dideteksi ketika sebagian informasi gambar hilang.

### Gaussian Noise

Noise ditambahkan ke gambar untuk menguji ketahanan watermark terhadap gangguan acak.

### Brightness

Kecerahan gambar diubah.

### Contrast

Kontras gambar diubah.

Parameter untuk resize, cropping, Gaussian noise, brightness, dan contrast harus ditentukan secara jelas dalam eksperimen. Jika memungkinkan, gunakan parameter yang memiliki dasar dari literatur atau jelaskan bahwa parameter tersebut merupakan rancangan eksperimen.

## 11. Apa Itu PSNR?

**PSNR (Peak Signal-to-Noise Ratio)** digunakan untuk mengukur kualitas gambar hasil watermarking dibandingkan dengan gambar asli.

Perbandingan:

**Original Image vs Watermarked Image**

PSNR digunakan untuk mengetahui seberapa besar perubahan kualitas gambar akibat proses embedding.

Secara umum:

**PSNR semakin tinggi → perbedaan antara original dan watermarked semakin kecil.**

PSNR terutama digunakan untuk menilai **imperceptibility/kualitas visual**, bukan langsung untuk menilai apakah watermark berhasil diekstraksi setelah attack.

Jadi:

**PSNR → kualitas gambar setelah embedding**

## 12. Apa Itu NC?

**NC (Normalized Correlation)** digunakan untuk mengukur kemiripan antara watermark asli dengan watermark hasil extraction.

Perbandingan:

**Original Watermark vs Extracted Watermark**

Semakin dekat nilai NC ke 1, semakin mirip watermark hasil extraction dengan watermark asli.

NC digunakan untuk melihat tingkat keberhasilan watermark setelah mengalami attack.

## 13. Apa Itu BER?

**BER (Bit Error Rate)** mengukur berapa banyak bit watermark yang salah setelah extraction.

Perbandingan:

**Original Watermark bits vs Extracted Watermark bits**

Secara sederhana:

**BER = jumlah bit yang salah / jumlah seluruh bit**

Semakin kecil BER berarti semakin sedikit kesalahan bit pada watermark hasil extraction.

Jadi:

- NC → mengukur kemiripan watermark.
- BER → mengukur kesalahan bit watermark.

Keduanya digunakan bersama untuk mengevaluasi robustness.

## 14. Perbedaan PSNR, NC, dan BER

Jangan menganggap ketiganya mengukur hal yang sama.

| Metrik | Membandingkan | Tujuan |
|---|---|---|
| PSNR | Original image vs Watermarked image | Mengukur kualitas/imperceptibility |
| NC | Original watermark vs Extracted watermark | Mengukur kemiripan watermark |
| BER | Original watermark vs Extracted watermark | Mengukur kesalahan bit |

Alur evaluasinya:

**Original Image**
↓
Embedding
↓
**Watermarked Image**
↓
PSNR
↓
Attack
↓
**Attacked Image**
↓
Blind Extraction
↓
**Extracted Watermark**
↓
NC + BER

## 15. Apa yang Sebenarnya Akan Diimplementasikan?

Aplikasi yang dibuat harus memiliki setidaknya beberapa fungsi utama berikut.

### A. Watermark Embedding

User:
1. Upload gambar.
2. Upload watermark.
3. Memasukkan secret key.
4. Klik proses embedding.

Sistem:
- melakukan DCT;
- memilih medium-frequency coefficients;
- memasukkan watermark;
- melakukan IDCT;
- menghasilkan watermarked image;
- menghitung PSNR.

Output:
- original image;
- watermarked image;
- PSNR.

### B. Attack/Manipulation

User memilih jenis attack.

Contoh:
- JPEG Q90
- JPEG Q70
- JPEG Q50
- Resize
- Crop
- Gaussian Noise
- Brightness
- Contrast

Sistem menghasilkan attacked image tanpa mengubah file original.

### C. Blind Watermark Extraction

User memasukkan:
- attacked watermarked image;
- secret key.

Sistem:
- melakukan DCT;
- mengambil koefisien yang relevan;
- melakukan extraction;
- menghasilkan extracted watermark.

Original image tidak digunakan.

### D. Evaluation

Sistem menghitung:
- NC;
- BER.

Hasil dapat ditampilkan dalam bentuk tabel.

Contoh:

| Attack | Parameter | NC | BER |
|---|---:|---:|---:|
| JPEG | 90 | ... | ... |
| JPEG | 70 | ... | ... |
| JPEG | 50 | ... | ... |
| Resize | ... | ... | ... |
| Crop | ... | ... | ... |

Nilai harus berasal dari eksperimen nyata, bukan dibuat-buat.

### E. Analysis

Aplikasi/report dapat menampilkan grafik seperti:

- JPEG quality vs NC
- JPEG quality vs BER
- Attack type vs NC
- Attack type vs BER
- PSNR antar gambar

Tujuan analisis adalah melihat bagaimana perubahan/serangan memengaruhi keberhasilan watermark.

## 16. Arsitektur Teknologi

Arsitektur yang direncanakan:

**User**
↓
**Laravel Web Interface**
↓
Upload / Input Key / Pilih Attack
↓
**Python Watermarking Engine**
↓
DCT / Embedding / Extraction / Attack / Metrics
↓
Hasil dikembalikan ke Laravel
↓
**Web Result**

Laravel tidak perlu melakukan perhitungan DCT secara langsung jika Python digunakan sebagai processing engine.

Python bertanggung jawab terhadap:
- DCT;
- IDCT;
- watermark embedding;
- watermark extraction;
- secret-key mechanism;
- attack;
- PSNR;
- NC;
- BER.

Laravel bertanggung jawab terhadap:
- UI;
- upload;
- validasi;
- routing;
- penyimpanan file;
- pemanggilan Python;
- menampilkan hasil;
- tabel/grafik hasil eksperimen.

## 17. Fungsi Python yang Kemungkinan Dibutuhkan

Struktur awal dapat berupa:

```text
dct2()
idct2()

select_coefficients()

generate_key_sequence()

embed_watermark()

extract_watermark()

apply_jpeg_attack()
apply_resize_attack()
apply_crop_attack()
apply_gaussian_noise()
apply_brightness_attack()
apply_contrast_attack()

calculate_psnr()
calculate_nc()
calculate_ber()
```

Nama fungsi masih dapat disesuaikan dengan implementasi final.

Yang penting, algoritma inti harus ditulis dan dipahami oleh anggota kelompok, bukan hanya memanggil library yang sudah menyediakan seluruh watermarking algorithm.

Library boleh digunakan untuk operasi standar seperti membaca gambar, DCT dasar, resize, JPEG compression, dan sebagainya, tetapi logika utama:
- pemilihan koefisien;
- embedding;
- extraction;
- penggunaan key;
- dan evaluasi

harus jelas dan dapat dijelaskan saat presentasi.

## 18. Urutan Pengembangan yang Diinginkan

Jangan langsung membuat UI Laravel terlebih dahulu.

Urutan yang lebih aman:

### Tahap 1 — Research
Cari paper mengenai:
- robust image watermarking;
- blind watermarking;
- DCT watermarking;
- medium/intermediate frequency;
- JPEG attack;
- cropping;
- resize;
- PSNR;
- NC;
- BER.

Minimal gunakan 10 referensi untuk laporan sesuai ketentuan tugas.

Pilih satu paper utama yang paling dekat dengan metode proyek sebagai dasar algoritma.

### Tahap 2 — Algorithm Design

Tentukan berdasarkan paper:
- ukuran blok DCT;
- koefisien medium-frequency;
- cara embedding;
- cara extraction;
- mekanisme secret key;
- bentuk watermark;
- ukuran watermark;
- threshold/parameter jika ada.

Jangan mengarang parameter yang belum ditentukan.

### Tahap 3 — Python Prototype

Sebelum Laravel dibuat, pastikan:

**Original Image**
→ Embedding
→ Watermarked Image
→ Extraction
→ Extracted Watermark

sudah berhasil.

Kemudian uji:

**Watermarked Image**
→ JPEG/Crop/Resize/etc.
→ Attacked Image
→ Blind Extraction
→ Extracted Watermark
→ NC + BER

### Tahap 4 — Attack Module

Implementasikan attack satu per satu.

Pastikan setiap hasil attack disimpan sebagai file terpisah.

### Tahap 5 — Evaluation

Hitung:
- PSNR;
- NC;
- BER.

Simpan hasil eksperimen ke dataset/tabel.

### Tahap 6 — Laravel Integration

Setelah algoritma Python stabil, baru buat interface Laravel.

### Tahap 7 — Experiment

Gunakan beberapa gambar uji dan lakukan semua pengujian yang diwajibkan.

### Tahap 8 — Report & Demo

Masukkan:
- teori;
- algoritma;
- flowchart;
- arsitektur;
- implementasi;
- hasil pengujian;
- tabel;
- grafik;
- analisis;
- kesimpulan.

## 19. Hal yang Jangan Dilakukan

Jangan:
- membuat watermark hanya dengan menempelkan teks/logo menggunakan overlay;
- menggunakan original image saat blind extraction;
- mengarang nilai PSNR/NC/BER;
- mengklaim watermark robust sebelum dilakukan pengujian;
- memilih koefisien medium-frequency secara asal tanpa dasar;
- hanya membuat UI tanpa implementasi algoritma;
- hanya menggunakan library yang sudah menyediakan watermarking tanpa memahami implementasinya;
- menyimpan secret key di source code/GitHub;
- menghapus original image ketika melakukan attack.

## 20. Fokus Utama Proyek

Jika harus diringkas menjadi satu alur:

**Gambar asli + watermark + secret key**
→ **DCT**
→ **medium-frequency coefficients**
→ **embedding**
→ **IDCT**
→ **watermarked image**
→ **attack/manipulation**
→ **attacked image**
→ **blind extraction menggunakan secret key**
→ **extracted watermark**
→ **NC + BER**

Sementara:

**Original image vs Watermarked image**
→ **PSNR**

Jadi proyek ini sebenarnya menguji dua hal utama:

1. **Imperceptibility**
   - Apakah watermark dapat disisipkan tanpa merusak kualitas gambar secara signifikan?
   - Diukur menggunakan PSNR.

2. **Robustness**
   - Apakah watermark masih dapat diperoleh setelah gambar dimanipulasi?
   - Diukur menggunakan NC dan BER.

Saat membantu saya mengembangkan proyek ini, selalu bedakan ketiga hal tersebut dan jangan mencampur PSNR, NC, dan BER.

Jika ada parameter algoritma yang belum ditentukan, jangan langsung mengarang. Jelaskan bahwa parameter tersebut harus ditentukan berdasarkan paper utama atau rancangan eksperimen, lalu bantu saya memilih dan menjelaskan alasannya.