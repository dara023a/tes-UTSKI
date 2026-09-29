Tugas: perbaiki tampilan (UI/UX) aplikasi Laravel watermarking DCT ini.

FOKUS HANYA TAMPILAN. Jangan ubah logika, alur, backend, route, controller,

maupun script Python.

ATURAN WAJIB

\- Jangan ubah atribut name, id, action, method form, dan @csrf.

\- Jangan rename variabel Blade yang dikirim controller.

\- Jangan tambah dependency baru tanpa konfirmasi (CDN Chart.js boleh,

tanyakan dulu).

\- Tampilan harus responsif dan konsisten di semua halaman.

\- Setelah selesai, uji ulang alur: embed → attack → extract → evaluation,

termasuk pastikan tombol "Lanjut ke \[tahap\]" di tiap halaman tidak rusak

(jangan ubah href/route-nya).

DAFTAR PERUBAHAN

1\. Metabox \[ISI: jelaskan isinya, misal info ukuran/dimensi gambar\]:

pindahkan ke bawah drop zone gambar.

2\. Field input watermark, alpha, redundancy (rentang 3-15), threshold

binarisasi (0-255): redesain agar modern dan rapi. Tambahkan ikon tanda

tanya (?) yang menampilkan penjelasan saat hover/klik/fokus (teks

tooltip terlampir di bawah).

3\. Preserve color: fitur ini TERPAKAI (bukan dekoratif), perbaiki

tampilannya saja — checkbox/toggle yang lebih jelas, tidak perlu

dihapus.

4\. Secret key: tambahkan tombol ikon mata untuk tampil/sembunyi isi field.

5\. Banner info sukses: jadikan notifikasi pop-up (toast) yang hilang otomatis

beberapa detik. Pesan error dan hasil penting (PSNR, NC, BER, SSIM)

TIDAK boleh hilang otomatis — tetap tampil di halaman.

6\. Banner "lanjut ke tahap berikutnya": buat lebih menarik dan beraturan.

Halaman sekarang punya 2 tombol pilihan ("Lanjut ke Attack" / "Langsung

ke Extraction") — desain agar user jelas melihat keduanya sebagai

pilihan, bukan satu alur paksa.

7\. Field jenis attack: perbaiki tampilan (misalnya card atau segmented

select).

8\. Field on\_size\_mismatch: dropdown/radio dengan 3 opsi jelas —

"Tolak (raise)", "Sesuaikan ukuran (resize)", "Potong di tengah

(centered crop)" — beri deskripsi singkat tiap opsi.

9\. Halaman evaluation: rapikan banner info, buat lebih informatif.

Tampilkan juga pesan yang rapi kalau belum ada hasil sama sekali di

sesi ini (sudah ada teksnya dari backend, tinggal styling).

10\. Halaman evaluation: tambahkan grafik NC, BER, PSNR, SSIM. Data SUDAH

tersedia semua di session/variabel yang dikirim controller — pastikan

ambil dari situ, jangan hardcode angka.

TEKS TOOLTIP

\- Alpha (α): margin pemisah antara dua koefisien DCT. Makin besar, watermark

makin tahan serangan tapi kualitas gambar (PSNR) makin turun.

\- Redundancy: berapa kali tiap bit watermark ditanam (minimal 3). Makin

tinggi, makin tahan serangan, tapi kapasitas gambar yang dibutuhkan

makin besar.

\- Threshold binarisasi: batas nilai piksel (0-255) untuk mengubah logo

watermark menjadi hitam-putih sebelum ditanam.

\- Secret key: kunci untuk menentukan blok mana yang dipakai menanam bit.

Key yang sama wajib dipakai saat extraction, kalau berbeda watermark

akan gagal terbaca.

\- Preserve color: jika dicentang, watermark ditanam di kanal luminansi

saja sehingga warna asli gambar tetap dipertahankan.

OUTPUT YANG DIHARAPKAN

\- Ringkasan file yang diubah.