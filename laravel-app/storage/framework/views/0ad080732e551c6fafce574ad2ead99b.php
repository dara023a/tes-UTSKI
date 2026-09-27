<?php $__env->startSection('title', 'Spectra — Invisible Watermarking untuk Karya Ilustrasi'); ?>

<?php $__env->startSection('footer_code', 'DCT · BLIND · PSNR/SSIM/NC/BER'); ?>

<?php $__env->startSection('content'); ?>
<!-- BERANDA -->
<section class="hero" id="beranda">
  <div class="gridtex"></div>
  <div class="wrap">
    <span class="eyebrow">DCT · FREKUENSI MENENGAH · BLIND WATERMARKING</span>
    <h1>Melindungi karya digital dengan watermark tak terlihat</h1>
    <p class="lead">Spectra menyisipkan identitas kepemilikan ke dalam data piksel citra tanpa mengubah tampilannya, lalu memverifikasinya kembali walau citra sudah dikompresi, diubah ukuran, atau dipotong.</p>
    <div class="hero-ctas">
      <a href="<?php echo e(route('embedding.index')); ?>" class="btn btn-primary">Mulai Watermarking</a>
      <a href="#cara-kerja" class="btn btn-ghost">Pelajari Cara Kerjanya</a>
    </div>
    <div class="pipeline" id="heroPipeline"></div>
  </div>
</section>

<!-- ALUR HALAMAN APLIKASI -->
<section id="alur-halaman">
  <div class="wrap">
    <div class="shead"><span class="tag">Alur Aplikasi</span><h2>Empat langkah, empat halaman</h2><p>Setiap tahap pengujian watermarking punya halaman kerjanya sendiri — ikuti urutan ini dari kiri ke kanan.</p></div>
    <div class="flowmap">
      <a class="fmcard" href="<?php echo e(route('embedding.index')); ?>"><span class="fmn mono">01 · EMBED</span><h3>Embedding</h3><p>Sisipkan watermark ke citra & hitung PSNR.</p></a>
      <span class="fmarrow">→</span>
      <a class="fmcard" href="<?php echo e(route('attack.index')); ?>"><span class="fmn mono">02 · ATTACK</span><h3>Attack</h3><p>Serang citra ter-watermark (JPEG, resize, crop, dst).</p></a>
      <span class="fmarrow">→</span>
      <a class="fmcard" href="<?php echo e(route('extraction.index')); ?>"><span class="fmn mono">03 · EXTRACT</span><h3>Extraction</h3><p>Ekstrak watermark secara blind memakai secret key.</p></a>
      <span class="fmarrow">→</span>
      <a class="fmcard" href="<?php echo e(route('evaluation.index')); ?>"><span class="fmn mono">04 · EVAL</span><h3>Evaluation</h3><p>Lihat tabel & grafik NC/BER dari semua pengujian.</p></a>
    </div>
  </div>
</section>

<!-- CARA KERJA -->
<section id="cara-kerja" style="background:var(--paper2)">
  <div class="wrap">
    <div class="shead"><span class="tag">Proses</span><h2>Dari citra ke domain frekuensi, dan kembali lagi</h2><p>Watermark tidak ditempel di atas gambar — ia disisipkan ke dalam koefisien frekuensi citra melalui transformasi DCT, sehingga tidak kasat mata namun tetap dapat dibaca kembali.</p></div>
    <div class="steps">
      <div class="step"><span class="n mono">01</span><h3>Citra Asli</h3><p>Gambar dibagi menjadi blok 8×8 piksel sebagai satuan pemrosesan.</p></div>
      <div class="step"><span class="n mono">02</span><h3>Transformasi DCT</h3><p>Setiap blok diubah dari domain spasial ke domain frekuensi.</p></div>
      <div class="step"><span class="n mono">03</span><h3>Frekuensi Menengah</h3><p>Koefisien menengah dipilih — titik seimbang antara halus dan tahan lama.</p></div>
      <div class="step"><span class="n mono">04</span><h3>Penyisipan + Key</h3><p>Bit watermark disisipkan memakai secret key sebagai penentu posisi.</p></div>
      <div class="step"><span class="n mono">05</span><h3>Inverse DCT</h3><p>Blok dikembalikan ke domain spasial menjadi citra ter-watermark.</p></div>
    </div>
  </div>
</section>

<!-- MENGAPA -->
<section id="mengapa">
  <div class="wrap">
    <div class="split">
      <div>
        <span class="tag">Masalah</span>
        <h2 style="font-size:28px;color:var(--navy);margin-bottom:16px">Karya ilustrasi mudah berpindah tangan tanpa izin</h2>
        <p style="font-size:15.5px">Begitu sebuah karya diunggah, ia bisa diunduh ulang, dikompresi otomatis oleh media sosial, dipotong, atau diklaim pihak lain. Watermark yang terlihat merusak estetika karya — sementara metadata mudah dihapus.</p>
      </div>
      <div>
        <div class="riskrow"><span class="mono">Disalin</span><p style="font-size:14px">Diunduh dan diunggah ulang tanpa kredit ke pembuat asli.</p></div>
        <div class="riskrow"><span class="mono">Dikompresi</span><p style="font-size:14px">Platform mengompresi citra secara otomatis saat diunggah.</p></div>
        <div class="riskrow"><span class="mono">Dipotong</span><p style="font-size:14px">Bagian citra dipotong untuk thumbnail atau reels.</p></div>
        <div class="riskrow"><span class="mono">Diklaim</span><p style="font-size:14px">Sulit membuktikan kepemilikan tanpa bukti yang melekat pada citra.</p></div>
      </div>
    </div>
  </div>
</section>

<!-- FITUR -->
<section id="fitur" style="background:var(--paper2)">
  <div class="wrap">
    <div class="shead"><span class="tag">Kapabilitas</span><h2>Satu alur, delapan kapabilitas inti</h2></div>
    <div class="featgrid">
      <a class="feat dark link" href="<?php echo e(route('embedding.index')); ?>"><span class="lbl">INTI</span><h3>Invisible Watermarking</h3><p>Watermark tersisip di koefisien DCT, tidak pernah mengubah tampilan citra secara kasat mata.</p></a>
      <a class="feat link" href="<?php echo e(route('extraction.index')); ?>"><span class="lbl">EKSTRAKSI</span><h3>Blind Extraction</h3><p>Verifikasi tanpa membutuhkan citra asli — hanya citra dan secret key.</p></a>
      <div class="feat"><span class="lbl">KEAMANAN</span><h3>Secret Key</h3><p>Menentukan posisi penyisipan; tanpanya, ekstraksi tidak dapat dilakukan.</p></div>
      <div class="feat"><span class="lbl">TRANSFORMASI</span><h3>DCT Frekuensi Menengah</h3><p>Titik seimbang antara imperceptibility dan robustness.</p></div>
      <div class="feat"><span class="lbl">POLA</span><h3>Pseudo-noise Sequence</h3><p>Barisan semu-acak yang menyebarkan bit watermark secara aman.</p></div>
      <a class="feat link" href="<?php echo e(route('evaluation.index')); ?>"><span class="lbl">EVALUASI</span><h3>PSNR, SSIM, NC &amp; BER</h3><p>Mengukur kualitas visual dan keberhasilan watermark secara terpisah.</p></a>
      <a class="feat link" style="grid-column:span 2" href="<?php echo e(route('attack.index')); ?>"><span class="lbl">PENGUJIAN</span><h3>Robustness Testing</h3><p>Simulasikan kompresi JPEG, resize, cropping, noise, brightness, dan contrast — lalu lihat apakah watermark masih terbaca.</p></a>
    </div>
  </div>
</section>

<!-- METRIK -->
<section id="metrik-hasil">
  <div class="wrap">
    <div class="shead"><span class="tag">Metrik</span><h2>Empat ukuran, dua tujuan berbeda</h2><p>PSNR &amp; SSIM menilai kualitas visual citra hasil embedding. NC &amp; BER menilai keberhasilan watermark setelah citra mengalami serangan. Keduanya tidak boleh dicampur.</p></div>
    <div class="metricgrid">
      <div class="mcard">
        <h3>PSNR — Kualitas Visual</h3>
        <p>Mengukur seberapa besar perbedaan antara citra asli dan citra ter-watermark. Semakin tinggi nilainya, semakin kecil perbedaannya secara visual.</p>
        <div class="barrow"><span class="mono">30dB</span><div class="track"><div class="fill" style="width:55%"></div></div><span class="mono">Cukup</span></div>
        <div class="barrow"><span class="mono">40dB</span><div class="track"><div class="fill" style="width:85%"></div></div><span class="mono">Baik</span></div>
        <div class="barrow"><span class="mono">50dB</span><div class="track"><div class="fill" style="width:98%"></div></div><span class="mono">Sangat baik</span></div>
      </div>
      <div class="mcard">
        <h3>SSIM — Kemiripan Struktur</h3>
        <p>Mengukur kemiripan struktur visual dua citra, dengan rentang 0 hingga 1. Nilai mendekati 1 berarti struktur citra hampir identik.</p>
        <div class="barrow"><span class="mono">0.85</span><div class="track"><div class="fill" style="width:85%"></div></div><span class="mono">Baik</span></div>
        <div class="barrow"><span class="mono">0.95</span><div class="track"><div class="fill" style="width:95%"></div></div><span class="mono">Sangat baik</span></div>
        <div class="barrow"><span class="mono">0.99</span><div class="track"><div class="fill" style="width:99%"></div></div><span class="mono">Nyaris identik</span></div>
      </div>
      <div class="mcard">
        <h3>NC — Kemiripan Watermark</h3>
        <p>Normalized Correlation membandingkan watermark asli dengan watermark hasil ekstraksi setelah citra diserang. Berbeda dari PSNR/SSIM, NC mengukur keberhasilan watermark, bukan kualitas gambar.</p>
        <div class="barrow"><span class="mono">0.70</span><div class="track"><div class="fill" style="width:70%"></div></div><span class="mono">Mulai melemah</span></div>
        <div class="barrow"><span class="mono">0.90</span><div class="track"><div class="fill" style="width:90%"></div></div><span class="mono">Masih terbaca</span></div>
        <div class="barrow"><span class="mono">0.99</span><div class="track"><div class="fill" style="width:99%"></div></div><span class="mono">Nyaris sempurna</span></div>
      </div>
      <div class="mcard">
        <h3>BER — Error Bit Watermark</h3>
        <p>Bit Error Rate menghitung persentase bit watermark yang salah dibaca saat ekstraksi. Semakin rendah nilainya, semakin akurat watermark yang berhasil dipulihkan.</p>
        <div class="barrow"><span class="mono">15%</span><div class="track"><div class="fill" style="width:15%"></div></div><span class="mono">Cukup terganggu</span></div>
        <div class="barrow"><span class="mono">5%</span><div class="track"><div class="fill" style="width:5%"></div></div><span class="mono">Baik</span></div>
        <div class="barrow"><span class="mono">0%</span><div class="track"><div class="fill" style="width:1%"></div></div><span class="mono">Sempurna</span></div>
      </div>
    </div>
    <p style="margin-top:20px;font-size:13.5px">Hasil eksperimen nyata (bukan ilustrasi di atas) dapat dilihat di halaman <a href="<?php echo e(route('evaluation.index')); ?>">Evaluation</a> setelah menjalankan Embedding → Attack → Extraction.</p>
  </div>
</section>

<!-- EDUKASI -->
<section id="edukasi" style="background:var(--paper2)">
  <div class="wrap">
    <div class="shead"><span class="tag">Edukasi</span><h2>Istilah teknis, dijelaskan sederhana</h2></div>
    <div id="accWrap"></div>
  </div>
</section>

<!-- TENTANG -->
<section id="tentang">
  <div class="wrap">
    <div class="shead"><span class="tag">Tentang</span><h2>Prototipe riset akademik</h2></div>
    <div class="aboutcard">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" style="flex-shrink:0"><rect x="2" y="2" width="8" height="8" fill="#2F6FEF"/><rect x="14" y="2" width="8" height="8" fill="#0B1526"/><rect x="2" y="14" width="8" height="8" fill="#0B1526"/><rect x="14" y="14" width="8" height="8" fill="#2F6FEF" opacity=".5"/></svg>
      <div>
        <p style="font-size:15px;color:var(--ink)">Spectra adalah prototipe antarmuka untuk proyek penelitian akademik mengenai <em>robust blind watermarking berbasis DCT frekuensi menengah</em>, ditujukan untuk melindungi karya ilustrasi digital dari penyalinan di media sosial.</p>
        <p style="font-size:14px;margin-top:12px">Antarmuka ini dibagi menjadi empat halaman kerja — Embedding, Attack, Extraction, dan Evaluation — mengikuti alur pipeline penelitian yang sesungguhnya.</p>
      </div>
    </div>
  </div>
</section>
<?php $__env->stopSection(); ?>

<?php $__env->startPush('scripts'); ?>
<script src="<?php echo e(asset('assets/js/storage.js')); ?>"></script>
<script src="<?php echo e(asset('assets/js/index.js')); ?>"></script>
<?php $__env->stopPush(); ?>

<?php echo $__env->make('layouts.app', array_diff_key(get_defined_vars(), ['__data' => 1, '__path' => 1]))->render(); ?><?php /**PATH D:\spectra-watermark-ui\laravel-app\resources\views\index.blade.php ENDPATH**/ ?>