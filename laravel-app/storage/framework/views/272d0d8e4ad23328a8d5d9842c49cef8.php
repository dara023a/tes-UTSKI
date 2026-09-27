<?php $__env->startSection('title', 'Evaluation — Spectra Watermarking'); ?>

<?php $__env->startSection('footer_code', '04 · EVALUATION'); ?>

<?php $__env->startSection('content'); ?>
<section class="pagehead">
  <div class="wrap">
    <div class="breadcrumb"><a href="<?php echo e(route('index')); ?>">Beranda</a> / Evaluation</div>
    <h1>Hasil pengujian robustness</h1>
    <p class="lead">NC dan BER mengukur pemulihan watermark setelah attack. PSNR dan SSIM mengukur imperceptibility citra watermarked sebelum attack; hasil berasal dari fungsi metrik Python.</p>
    <div class="stepnav">
      <a href="<?php echo e(route('embedding.index')); ?>">01 Embedding</a><span class="arrow">→</span>
      <a href="<?php echo e(route('attack.index')); ?>">02 Attack</a><span class="arrow">→</span>
      <a href="<?php echo e(route('extraction.index')); ?>">03 Extraction</a><span class="arrow">→</span>
      <a class="here">04 Evaluation</a>
    </div>
  </div>
</section>

<section style="padding-top:56px">
  <div class="wrap">

    <div class="banner-info" style="margin-bottom:28px">
      Data pada halaman ini dihitung secara presisi oleh engine pemrosesan citra Python. Hasil evaluasi mencakup nilai kualitas visual (<strong>PSNR, SSIM</strong>) dan ketahanan watermark (<strong>NC, BER</strong>) dari pengujian dalam sesi ini.
    </div>

    <?php if(!$rows): ?>
      <div class="empty-state" id="emptyState">
        Belum ada hasil evaluasi dalam sesi ini. Jalankan
        <a href="<?php echo e(route('embedding.index')); ?>">Embedding</a> → 
        <a href="<?php echo e(route('attack.index')); ?>">Attack</a> → 
        <a href="<?php echo e(route('extraction.index')); ?>">Extraction</a> terlebih dahulu.
      </div>
    <?php else: ?>
      <div class="table-toolbar" id="tableToolbar" style="display:flex">
        <span class="mono" style="font-size:12.5px;color:var(--slate)">Tabel Hasil Ekstraksi &amp; Evaluasi</span>
      </div>

      <div class="table-wrap" id="tableWrap" style="display:block">
        <table class="evaltable">
          <thead>
            <tr>
              <th>Waktu</th>
              <th>Attack</th>
              <th>Parameter</th>
              <th>PSNR</th>
              <th>SSIM</th>
              <th>NC</th>
              <th>BER</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody id="evalBody">
            <?php $__currentLoopData = $rows; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $row): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
              <tr>
                <td><?php echo e(\Illuminate\Support\Carbon::parse($row['created_at'])->format('d M Y H:i:s')); ?></td>
                <td><?php echo e(strtoupper(str_replace('_', ' ', $row['attack_type']))); ?></td>
                <td><?php echo e($row['parameter']); ?></td>
                <td><?php echo e($row['psnr'] === 'inf' ? '∞' : number_format((float) $row['psnr'], 2) . ' dB'); ?></td>
                <td><?php echo e(number_format((float) $row['ssim'], 4)); ?></td>
                <td><?php echo e(number_format((float) $row['ncc'], 4)); ?></td>
                <td><?php echo e(number_format((float) $row['ber'] * 100, 2)); ?>%</td>
                <td>
                  <span class="status-pill <?php echo e(((float)$row['ncc'] >= 0.75) ? 'ok' : (((float)$row['ncc'] >= 0.5) ? 'warn' : 'err')); ?>">
                    <?php echo e(((float)$row['ncc'] >= 0.75) ? 'Terdeteksi' : (((float)$row['ncc'] >= 0.5) ? 'Melemah' : 'Gagal')); ?>

                  </span>
                </td>
              </tr>
            <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
          </tbody>
        </table>
      </div>

      <?php ($latest = end($rows)); ?>
      <div class="shead" style="margin:42px 0 20px">
        <span class="tag">Imperceptibility &amp; Robustness</span>
        <h2 style="font-size:22px">Ringkasan Metrik Pengujian Terakhir</h2>
        <p>PSNR dan SSIM dihitung dari citra asli dan citra watermarked sebelum attack. NC dan BER dihitung setelah ekstraksi watermark dari citra attacked.</p>
      </div>

      <div class="metricrow">
        <div class="metric">
          <div class="num"><?php echo e($latest['psnr'] === 'inf' ? '∞' : number_format((float) $latest['psnr'], 2)); ?></div>
          <div class="lbl2">PSNR (dB)</div>
        </div>
        <div class="metric">
          <div class="num"><?php echo e(number_format((float) $latest['ssim'], 4)); ?></div>
          <div class="lbl2">SSIM</div>
        </div>
        <div class="metric">
          <div class="num"><?php echo e(number_format((float) $latest['ncc'], 4)); ?></div>
          <div class="lbl2">NC</div>
        </div>
        <div class="metric">
          <div class="num"><?php echo e(number_format((float) $latest['ber'] * 100, 2)); ?>%</div>
          <div class="lbl2">BER</div>
        </div>
      </div>

      <?php if($run && !empty($run['extracted_image'])): ?>
        <div style="display:flex;gap:12px;margin-top:24px;flex-wrap:wrap">
          <a class="btn btn-outline btn-sm" href="<?php echo e(route('artifacts.show', ['kind' => 'attacked'])); ?>" download="attacked.png">Unduh Attacked Image</a>
          <a class="btn btn-outline btn-sm" href="<?php echo e(route('artifacts.show', ['kind' => 'extracted'])); ?>" download="extracted-watermark.png">Unduh Extracted Watermark</a>
          <a class="btn btn-primary btn-sm" href="<?php echo e(route('attack.index')); ?>">Uji Attack Lain</a>
        </div>
      <?php endif; ?>
    <?php endif; ?>

  </div>
</section>
<?php $__env->stopSection(); ?>

<?php echo $__env->make('layouts.app', array_diff_key(get_defined_vars(), ['__data' => 1, '__path' => 1]))->render(); ?><?php /**PATH D:\spectra-watermark-ui\laravel-app\resources\views/evaluation.blade.php ENDPATH**/ ?>