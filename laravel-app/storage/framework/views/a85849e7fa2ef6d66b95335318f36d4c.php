<?php $__env->startSection('title', 'Extraction — Spectra Watermarking'); ?>

<?php $__env->startSection('footer_code', '03 · EXTRACTION'); ?>

<?php $__env->startSection('content'); ?>
<section class="pagehead">
  <div class="wrap">
    <div class="breadcrumb"><a href="<?php echo e(route('index')); ?>">Beranda</a> / Extraction</div>
    <h1>Ekstraksi watermark secara blind</h1>
    <p class="lead">Sistem hanya membutuhkan citra dan secret key — tanpa citra asli — untuk mencoba memulihkan kembali watermark yang tersisip.</p>
    <div class="stepnav">
      <a href="<?php echo e(route('embedding.index')); ?>">01 Embedding</a><span class="arrow">→</span>
      <a href="<?php echo e(route('attack.index')); ?>">02 Attack</a><span class="arrow">→</span>
      <a class="here">03 Extraction</a><span class="arrow">→</span>
      <a href="<?php echo e(route('evaluation.index')); ?>">04 Evaluation</a>
    </div>
  </div>
</section>

<section style="padding-top:56px">
  <div class="wrap">
    <div class="wsbox">
      <div class="wshead"><span><span class="dot on"></span>WORKSPACE.EXTRACT</span><span id="vStatus"><?php echo e(($run && !empty($run['extracted_image'])) ? 'Selesai' : (($run && !empty($run['attacked_image'])) ? 'Citra siap diekstraksi' : 'Menunggu citra')); ?></span></div>
      <div class="wsgrid">
        <div class="wscol">

          <?php if($run && !empty($run['attacked_image'])): ?>
            <div class="assetcard" id="attackAssetCard">
              <img class="thumb" id="attackThumb" src="<?php echo e(route('artifacts.show', ['kind' => 'attacked'])); ?>" alt="Citra hasil attack">
              <div class="info">
                <div class="t">Gunakan hasil Attack terakhir</div>
                <div class="d" id="attackInfo">Attack: <?php echo e(str_replace('_', ' ', $run['attack_type'] ?? 'none')); ?> · Parameter: <?php echo e($run['parameter'] ?? '—'); ?></div>
              </div>
              <a class="btn btn-outline btn-sm" href="<?php echo e(route('artifacts.show', ['kind' => 'attacked'])); ?>" download="attacked.png">Unduh</a>
            </div>
          <?php else: ?>
            <div class="assetcard empty" id="attackAssetEmpty">
              Belum ada hasil dari halaman Attack di browser ini. Unggah citra secara manual atau <a href="<?php echo e(route('attack.index')); ?>">jalankan attack dulu</a>.
            </div>
          <?php endif; ?>

          <form method="POST" action="<?php echo e(route('extraction.run')); ?>">
            <?php echo csrf_field(); ?>
            <div class="field" style="margin-top:16px">
              <label>Secret Key</label>
              <input type="password" name="secret_key" id="vKey" placeholder="Kunci rahasia" autocomplete="new-password" required>
            </div>

            <div class="field">
              <label>Strategi bila ukuran citra berubah</label>
              <select name="on_size_mismatch" required>
                <option value="raise" <?php echo e(old('on_size_mismatch', $defaultMismatch) === 'raise' ? 'selected' : ''); ?>>raise — tanpa sinkronisasi ukuran</option>
                <option value="resize" <?php echo e(old('on_size_mismatch', $defaultMismatch) === 'resize' ? 'selected' : ''); ?>>resize — untuk resize murni</option>
                <option value="centered_crop" <?php echo e(old('on_size_mismatch', $defaultMismatch) === 'centered_crop' ? 'selected' : ''); ?>>centered_crop — mengasumsikan crop simetris</option>
              </select>
            </div>

            <button class="btn btn-dark" style="margin-top:18px;width:100%" id="verifyBtn" type="submit" <?php echo e((!$run || empty($run['attacked_image'])) ? 'disabled' : ''); ?>>Ekstrak Watermark</button>
          </form>
        </div>

        <div class="wscol">
          <p style="font-size:13.5px;margin-bottom:10px">Hasil ekstraksi akan tampil di sini setelah proses selesai.</p>

          <?php if(!$run || empty($run['extracted_image'])): ?>
            <div id="vResultEmpty" style="border:1px dashed var(--line);padding:28px;text-align:center;font-size:13px;color:#8A93A2">Belum ada citra diproses</div>
          <?php else: ?>
            <?php ($metricsList = session('watermark_metrics', [])); ?>
            <?php ($latestMetric = end($metricsList)); ?>
            <div id="vResult">
              <div class="resultbanner ok" id="vBanner">✓ Watermark terdeteksi &amp; diekstraksi</div>
              
              <div style="margin: 16px 0; text-align: center;">
                <img src="<?php echo e(route('artifacts.show', ['kind' => 'extracted'])); ?>" alt="Extracted Watermark" style="max-height: 140px; border: 1px solid var(--line); border-radius: 4px; padding: 4px; background: #fff;">
                <p style="font-size: 12px; color: var(--slate); margin-top: 4px;">Visual Citra Watermark Hasil Ekstraksi</p>
              </div>

              <?php if($latestMetric): ?>
                <div class="metricrow">
                  <div class="metric"><div class="num" id="vNc"><?php echo e(number_format((float) $latestMetric['ncc'], 3)); ?></div><div class="lbl2">NC</div></div>
                  <div class="metric"><div class="num" id="vBer"><?php echo e(number_format((float) $latestMetric['ber'] * 100, 1)); ?>%</div><div class="lbl2">BER</div></div>
                  <div class="metric"><div class="num" id="vId">Terdeteksi</div><div class="lbl2">Status</div></div>
                </div>
              <?php endif; ?>

              <div class="banner-info" id="nextBanner" style="margin-top:18px;display:flex">
                Tersimpan. Lihat semua hasil pengujian di <a href="<?php echo e(route('evaluation.index')); ?>" style="color:var(--blue-dim);font-weight:600">halaman Evaluation →</a>
              </div>
            </div>
          <?php endif; ?>
        </div>
      </div>
    </div>
  </div>
</section>
<?php $__env->stopSection(); ?>

<?php echo $__env->make('layouts.app', array_diff_key(get_defined_vars(), ['__data' => 1, '__path' => 1]))->render(); ?><?php /**PATH D:\spectra-watermark-ui\laravel-app\resources\views/extraction.blade.php ENDPATH**/ ?>