# Spectra Watermarking

Aplikasi web untuk menyisipkan dan menguji **invisible blind watermark** pada citra digital. Proyek ini menggabungkan antarmuka Laravel dengan mesin pemrosesan citra Python.

## Anggota Kelompok

| Nama | NPM |
|---|---|
| Yahya | 247006111032 |
| Anggi | 247006111038 |
| Dara | 247006111023 |

## Deskripsi

Spectra menyisipkan watermark biner ke dalam citra menggunakan Discrete Cosine Transform (DCT) per blok 8×8. Bit watermark ditanam pada koefisien frekuensi menengah, sedangkan secret key digunakan untuk menentukan urutan blok secara pseudo-acak. Watermark dapat diekstrak kembali tanpa citra asli (blind extraction).

Aplikasi menyediakan alur kerja untuk:

1. **Embedding** — mengunggah citra asli dan citra watermark, lalu menghasilkan citra ter-watermark.
2. **Attack** — menguji ketahanan citra melalui kompresi JPEG, resize, pemotongan (crop), atau crop yang diikuti resize balik.
3. **Extraction** — mencoba memulihkan watermark dari citra hasil serangan menggunakan secret key.
4. **Evaluation** — melihat metrik kualitas visual dan keberhasilan pemulihan watermark.

PSNR dan SSIM mengukur kualitas visual citra ter-watermark dibanding citra asli. NC (Normalized Correlation) dan BER (Bit Error Rate) mengukur kemiripan watermark hasil ekstraksi terhadap watermark awal.

## Teknologi

- **Backend web:** PHP 8.3+, Laravel 13
- **Mesin pemrosesan:** Python 3.10+
- **Antarmuka:** Blade, Vite, dan Tailwind CSS
- **Pustaka Python:** NumPy, SciPy, OpenCV, Pillow, scikit-image, Matplotlib
- **Penyimpanan lokal:** SQLite dan penyimpanan privat Laravel

## Persyaratan

Pastikan perangkat sudah memiliki:

- Python 3.10 atau lebih baru
- PHP 8.3 atau lebih baru dengan Composer
- Node.js dan npm
- Git (jika proyek diambil dari repositori)

## Instalasi

Perintah berikut ditulis untuk Windows PowerShell. Jalankan dari direktori utama proyek.

### 1. Siapkan mesin Python

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Virtual environment `.venv` pada direktori utama akan digunakan Laravel secara otomatis. Jika PowerShell menolak aktivasi environment, jalankan perintah Python dengan path lengkap, misalnya `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.

### 2. Siapkan aplikasi Laravel

```powershell
cd laravel-app
composer install
Copy-Item .env.example .env
New-Item -ItemType File -Force database\database.sqlite
php artisan key:generate
php artisan migrate
npm install --ignore-scripts
npm run build
```

Jika berkas `.env` sudah ada, jangan menimpanya dengan `.env.example`; lanjutkan langsung ke pembuatan database, pembuatan application key (jika belum tersedia), migrasi, dan build aset.

Konfigurasi bawaan mengarah ke `.venv\Scripts\python.exe` dan `web_bridge.py` di direktori utama proyek. Jika Python atau bridge berada di lokasi lain, atur path absolut pada `laravel-app\.env`:

```dotenv
WATERMARK_PYTHON=D:\lokasi\proyek\.venv\Scripts\python.exe
WATERMARK_BRIDGE=D:\lokasi\proyek\web_bridge.py
```

Pastikan akun yang menjalankan PHP dapat menulis ke direktori `laravel-app\storage` dan `laravel-app\database`.

## Menjalankan Aplikasi

Dari direktori `laravel-app`, jalankan server lokal:

```powershell
php artisan serve
```

Buka alamat yang ditampilkan oleh Laravel, biasanya <http://127.0.0.1:8000>. Server ini menjalankan aplikasi web; proses Python dipanggil oleh Laravel saat operasi watermarking dilakukan.

## Contoh Penggunaan

1. Buka halaman **Embedding**.
2. Pilih citra asli dan citra watermark, lalu masukkan secret key dan nilai **Alpha** yang lebih besar dari 0. Sebagai contoh eksperimen, isi alpha dengan `5`; nilai yang sesuai bergantung pada citra dan kebutuhan ketahanan.
3. Biarkan **Redundancy** pada `1` untuk pengujian dasar. Nilai lebih besar menanam lebih banyak salinan setiap bit, dapat membantu pemulihan setelah crop, tetapi membutuhkan kapasitas blok lebih besar dan dapat menambah distorsi. Pastikan citra memuat blok yang cukup untuk ukuran watermark dan redundancy yang dipilih.
4. Biarkan threshold binarisasi pada `127`, atau ubah sesuai kebutuhan eksperimen. Untuk mempertahankan warna citra, aktifkan **Preserve color** agar watermark diproses pada kanal luminance.
5. Setelah embedding, buka **Attack** dan pilih satu jenis pengujian. Contoh: pilih **JPEG compression** dengan kualitas `70`, kemudian terapkan attack. Alternatif yang tersedia adalah resize, pure crop, serta crop lalu resize balik.
6. Buka **Extraction**, masukkan secret key yang sama dengan saat embedding, lalu pilih strategi jika ukuran citra berubah:
   - `raise`: tidak melakukan sinkronisasi ukuran.
   - `resize`: untuk serangan resize murni.
   - `centered_crop`: untuk crop simetris dari tengah; redundancy lebih dari `1` disarankan agar salinan bit yang tersisa dapat membantu pemulihan.
7. Jalankan ekstraksi. Hasil watermark dan metrik akan tersedia di **Evaluation**. PSNR/SSIM berasal dari proses embedding, sementara NC/BER menunjukkan hasil pemulihan setelah attack.

Alpha, redundancy, ukuran citra, dan parameter serangan memengaruhi hasil. Karena itu, catat parameter eksperimen saat membandingkan nilai metrik.

## Batasan dan Catatan

- Berkas citra yang diunggah dibatasi maksimum 10 MB per berkas.
- Secret key yang dipakai untuk ekstraksi harus sama dengan key saat embedding.
- `centered_crop` mengasumsikan pemotongan simetris dari tengah. Hasilnya dapat tidak akurat jika crop tidak mengikuti asumsi tersebut.
- Penanganan resize membantu sinkronisasi ukuran, tetapi interpolasi resize dapat tetap merusak koefisien DCT dan memengaruhi akurasi watermark.
- Berkas input dan hasil disimpan di penyimpanan privat berdasarkan sesi/run, bukan sebagai berkas publik langsung.

## Menjalankan Pengujian

Uji mesin Python dari direktori utama proyek:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Uji aplikasi Laravel dari direktori `laravel-app`:

```powershell
php artisan test
```

## Struktur Proyek

```text
.
├── .gitignore                   # Mengabaikan dependency, cache, dan konfigurasi lokal
├── app/                         # Algoritma dan pipeline watermark Python
│   ├── dct.py                   # Transformasi DCT/IDCT dan operasi blok 8×8
│   ├── key.py                   # Seed dan urutan blok berbasis secret key
│   ├── watermark.py             # Embedding dan extraction
│   ├── metrics.py               # PSNR, SSIM, NC, dan BER
│   └── pipeline.py              # Pipeline citra dan evaluasi
├── tests/                       # Pengujian unit dan bridge Python
├── attack_simulation.py         # Simulasi serangan terhadap citra
├── web_bridge.py                # Penghubung Laravel dengan pipeline Python
├── requirements.txt             # Dependensi Python
├── main.py                      # Antarmuka CLI opsional untuk mesin watermark
├── docs/                        # Catatan algoritma dan dokumentasi proyek
├── examples/                    # Contoh generator dan citra watermark
└── laravel-app/                 # Antarmuka web, route, dan penyimpanan hasil
```


Kalau ada error ini di localhost pas di run "php artisan server"
- A temporary file could not be opened to write the process output: fopen(C:\WINDOWS\sf_proc_00.out.lock): Failed to open stream: Permission denied
pakai command ini
$root = 'pathfoldernya'
New-Item -ItemType Directory -Force "$root\storage\framework\uploads" | Out-Null
New-Item -ItemType Directory -Force "$root\storage\framework\process-tmp" | Out-Null

Set-Location "$root\public"
& "$env:USERPROFILE\.config\herd\bin\php84\php.exe" `
  -d "upload_tmp_dir=$root\storage\framework\uploads" `
  -d "sys_temp_dir=$root\storage\framework\process-tmp" `
  -S 127.0.0.1:8000 `
  "$root\vendor\laravel\framework\src\Illuminate\Foundation\resources\server.php"