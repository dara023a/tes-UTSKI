Ini audit menyeluruh terhadap proyek Robust Blind Watermarking DCT

(engine Python + integrasi Laravel) yang sudah kita bangun. Baca ulang

"Konteks Proyek Digital Watermarking untuk AI.md" dan "algoritma.md"

sebagai acuan kebenaran, lalu periksa SELURUH kode (app/\*.py, main.py,

attack\_simulation.py, web\_bridge.py, PythonWatermarkEngine.php, semua

Controller, route, dan view Blade) terhadap checklist di bawah.

ATURAN AUDIT

\- Untuk tiap poin, jawab: STATUS (✅ sesuai / ⚠️ sebagian / ❌ tidak

sesuai / 🚫 tidak bisa diverifikasi), BUKTI (path file + baris, atau

potongan kode/output test yang relevan), dan REKOMENDASI kalau ada

masalah.

\- Kalau kamu tidak yakin atau tidak bisa memverifikasi sesuatu (mis.

karena server belum jalan), tulis 🚫 dan jelaskan kenapa — JANGAN

menandai ✅ hanya karena "seharusnya begitu".

\- Jangan perbaiki apapun dulu di audit ini. Laporkan dulu semua temuan

dalam satu tabel, baru tunggu saya putuskan mana yang perlu di-patch.

A. KEBENARAN ALGORITMA (vs algoritma.md)

1\. Blok DCT benar-benar 8x8, dan posisi koefisien medium-frequency yang

dipakai persis sesuai algoritma.md (bukan koordinat lain yang

"kelihatannya mirip").

2\. Parameter alpha/redundancy yang dipakai default di Laravel/UI sama

dengan yang sudah divalidasi di README.md Fase 2 (alpha vs BER) —

bukan angka baru yang dikarang saat wiring UI.

3\. Proses embedding benar-benar memodifikasi koefisien DCT piksel

(IDCT dipanggil), BUKAN overlay teks/logo di atas gambar di layer

manapun (termasuk cek ulang tidak ada sisa kode canvas-overlay dari

prototipe HTML lama).

B. BLIND EXTRACTION

4\. Alur extraction (dari route sampai ke app/watermark.py) TIDAK pernah

membaca/membutuhkan original image. Telusuri controller/service:

pastikan tidak ada parameter atau file original yang diam-diam

dikirim ke fungsi extract.

5\. Original image tidak dihapus/ditimpa oleh proses attack di

manapun (baik di storage Laravel maupun folder kerja Python).

C. METRIK (PSNR vs NC vs BER)

6\. PSNR dihitung HANYA dari original vs watermarked image, NC & BER

HANYA dari original watermark vs extracted watermark — cek tidak

ada tempat di kode (termasuk sisa JS lama) yang mencampur ketiganya

atau memberi label yang salah.

7\. Tidak ada satupun path di frontend/backend yang masih menghasilkan

metrik lewat random/hardcode/dummy (audit khusus semua file .js di

bawah public/assets yang tersisa dari spectra-watermark-ui — pastikan

Math.random() untuk metrik sudah 100% hilang, bukan cuma tidak

dipanggil).

8\. Nilai metrik yang tampil di halaman evaluation benar-benar

round-trip dari app/metrics.py lewat web\_bridge.py→

PythonWatermarkEngine.php, bukan hasil hardcode di controller/view

untuk keperluan demo.

D. ATTACK MODULE

9\. Attack yang dipicu dari attack.html/attack.blade.php memanggil

fungsi single-image (attack\_jpeg, attack\_resize, attack\_pure\_crop,

attack\_crop\_resize\_back), BUKAN attack\_simulation.py (yang untuk

batch eksperimen).

10\. JPEG quality 90/70/50 tersedia dan benar-benar mengubah kompresi

(verifikasi ukuran file/kualitas berubah, bukan cuma label UI).

E. SECRET KEY & KEAMANAN

11\. Secret key tidak pernah hardcode di source code, tidak masuk ke

git history/commit, tidak di-log ke console/file log, dan tidak

dikirim balik ke response JSON/HTML ke browser.

12\. Kalau key disimpan sementara (mis. session/file temp untuk

dijembatani ke Python), pastikan dibersihkan setelah request

selesai dan tidak bisa diakses lewat URL publik.

F. ERROR HANDLING & ROBUSTNESS

13\. Exception dari Python (ImageLoadError, MetadataError,

CapacityError, PipelineError) benar-benar ditangkap di sisi

Laravel dan ditampilkan sebagai pesan yang jelas, bukan crash 500

polos atau stack trace mentah ke user.

14\. Upload gambar dengan ukuran bukan kelipatan 8 ditangani sesuai

aturan (di-crop ke kelipatan 8 terbesar), bukan error tak jelas.

G. INTEGRITAS PENGUJIAN

15\. Jalankan ulang seluruh test suite Python (unittest discover) dan

laporkan jumlah test + status PASS/FAIL apa adanya, bukan diambil

dari ingatan hasil run sebelumnya.

16\. Konfirmasi tidak ada klaim "robust" atau angka NC/BER di

laporan/README yang belum benar-benar berasal dari eksperimen

(cross-check terhadap CSV hasil pengujian kalau ada).

H. KELENGKAPAN ARSITEKTUR (vs diagram 5 tahap)

17\. Petakan tiap kotak diagram (Preprocessing&DCT, Embedding, Attack

Simulator, Blind Extraction, Metrics Engine) ke file/route yang

mengimplementasikannya, dan tandai kalau ada kotak yang belum

punya implementasi nyata (masih placeholder/UI kosong).

OUTPUT

Rangkum semua temuan dalam SATU tabel markdown: No | Item | Status |

Bukti | Rekomendasi. Di akhir, beri ringkasan: berapa ✅, berapa ⚠️/❌

yang perlu diperbaiki sebelum demo/submit, dan urutkan prioritas

perbaikannya.