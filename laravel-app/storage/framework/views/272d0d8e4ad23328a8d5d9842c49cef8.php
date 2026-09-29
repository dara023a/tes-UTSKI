<?php $__env->startSection('title', 'Evaluation — Spectra Watermarking'); ?>

<?php $__env->startSection('footer_code', '04 · EVALUATION'); ?>

<?php $__env->startSection('content'); ?>
<section class="pagehead">
  <div class="wrap">
    <div class="breadcrumb"><a href="<?php echo e(route('index')); ?>">Beranda</a> / Evaluation</div>
    <h1>Hasil pengujian robustness</h1>
    <p class="lead">NC dan BER mengukur pemulihan watermark setelah attack. PSNR dan SSIM mengukur imperceptibility
      citra watermarked sebelum attack; hasil berasal dari fungsi metrik Python.</p>
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

    <!-- 9. Info banner yang lebih informatif & rapi -->
    <div class="banner-info"
      style="margin-bottom:32px; padding:18px 22px; background:#f0f7ff; border:1px solid #cce3ff; border-radius:6px; color:var(--navy)">
      <div style="display:flex; gap:14px; align-items:flex-start">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          style="color:var(--blue); flex-shrink:0; margin-top:2px">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 16v-4M12 8h.01" />
        </svg>
        <div>
          <h4 style="font-size:15px; margin-bottom:6px; color:var(--navy)">Metrik Evaluasi Watermarking (Engine Python)
          </h4>
          <p style="font-size:13.5px; color:var(--slate); line-height:1.5">
            Setiap pengujian dihitung secara presisi oleh engine pemrosesan citra Python:
            <br>
            • <strong>Imperceptibility (PSNR &amp; SSIM)</strong>: Kualitas visual citra ter-watermark dibanding citra
            asli.
            <br>
            • <strong>Robustness (NC &amp; BER)</strong>: Keberhasilan dan keakuratan watermark yang diekstraksi setelah
            citra diserang.
          </p>
        </div>
      </div>
    </div>

    <!-- 9. Tampilan pesan rapi bila belum ada hasil sama sekali di sesi ini -->
    <?php if(!$rows || count($rows) === 0): ?>
      <div class="empty-state" id="emptyState"
        style="border:2px dashed var(--line); border-radius:8px; padding:48px 24px; text-align:center; background:#fff">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"
          style="color:var(--slate); margin-bottom:12px">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <path d="M3 9h18M9 21V9" />
        </svg>
        <h3 style="font-size:18px; color:var(--navy); margin-bottom:8px">Belum Ada Hasil Evaluasi Dalam Sesi Ini</h3>
        <p style="font-size:14px; color:var(--slate); max-width:520px; margin:0 auto 24px; line-height:1.5">
          Jalankan alur pengujian lengkap mulai dari menyisipkan watermark, menguji serangan (attack), hingga
          mengekstraksi watermark untuk melihat grafik dan tabel evaluasi.
        </p>
        <div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap">
          <a href="<?php echo e(route('embedding.index')); ?>" class="btn btn-primary btn-sm">01 Embedding →</a>
          <a href="<?php echo e(route('attack.index')); ?>" class="btn btn-outline btn-sm">02 Attack →</a>
          <a href="<?php echo e(route('extraction.index')); ?>" class="btn btn-outline btn-sm">03 Extraction →</a>
        </div>
      </div>
    <?php else: ?>

    <!-- 10. Grafik NC, BER, PSNR, SSIM -->
    <div style="margin-bottom:36px">
      <div class="shead" style="margin-bottom:20px">
        <span class="tag">Visualisasi Grafik</span>
        <h2 style="font-size:22px">Grafik Performansi Watermarking</h2>
        <p>Grafik diambil langsung dari data sesi pengujian aktif.</p>
      </div>

      <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px" class="chart-grid">
        <!-- Grafik 1: Robustness (NC & BER) -->
        <div class="chart-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px">
            <h3>Ketahanan Watermark (NC &amp; BER)</h3>
            <span class="mono" style="font-size:11px; color:var(--slate)">NC ↑ (Tinggi) | BER ↓ (Rendah)</span>
          </div>
          <div style="position:relative; height:260px; width:100%">
            <canvas id="robustnessChart"></canvas>
          </div>
        </div>

        <!-- Grafik 2: Imperceptibility (PSNR & SSIM) -->
        <div class="chart-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px">
            <h3>Kualitas Visual (PSNR &amp; SSIM)</h3>
            <span class="mono" style="font-size:11px; color:var(--slate)">PSNR (dB) &amp; SSIM (0–1)</span>
          </div>
          <div style="position:relative; height:260px; width:100%">
            <canvas id="imperceptibilityChart"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- Tabel Hasil -->
    <div class="table-toolbar" id="tableToolbar" style="display:flex">
      <span class="mono" style="font-size:12.5px; color:var(--slate); font-weight:600">Tabel Hasil Ekstraksi &amp;
        Evaluasi (<?php echo e(count($rows)); ?> Pengujian)</span>
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
                <span class="status-pill <?php echo e($row['status_class'] ?? 'err'); ?>">
                  <?php echo e($row['status'] ?? 'Gagal'); ?>

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
      <p>PSNR dan SSIM dihitung dari citra asli dan citra watermarked sebelum attack. NC dan BER dihitung setelah
        ekstraksi watermark dari citra attacked.</p>
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
        <a class="btn btn-outline btn-sm" href="<?php echo e(route('artifacts.show', ['kind' => 'attacked'])); ?>"
          download="attacked.png">Unduh Attacked Image</a>
        <a class="btn btn-outline btn-sm" href="<?php echo e(route('artifacts.show', ['kind' => 'extracted'])); ?>"
          download="extracted-watermark.png">Unduh Extracted Watermark</a>
        <a class="btn btn-primary btn-sm" href="<?php echo e(route('attack.index')); ?>">Uji Attack Lain</a>
      </div>
    <?php endif; ?>
    <?php endif; ?>

  </div>
</section>
<?php $__env->stopSection(); ?>

<?php $__env->startPush('scripts'); ?>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script>
    document.addEventListener('DOMContentLoaded', function () {
      const rows = <?php echo json_encode($rows, 15, 512) ?>;
      if (!rows || rows.length === 0) return;

      const labels = rows.map((r, i) => `${r.attack_type.toUpperCase().replace('_', ' ')} (${r.parameter})`);
      const ncValues = rows.map(r => parseFloat(r.ncc) || 0);
      const berValues = rows.map(r => (parseFloat(r.ber) * 100) || 0);
      const psnrValues = rows.map(r => r.psnr === 'inf' ? 60 : (parseFloat(r.psnr) || 0));
      const ssimValues = rows.map(r => parseFloat(r.ssim) || 0);

      // Chart 1: Robustness (NC & BER)
      const ctxRob = document.getElementById('robustnessChart');
      if (ctxRob) {
        new Chart(ctxRob, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [
              {
                label: 'NC (Normalized Correlation)',
                data: ncValues,
                backgroundColor: 'rgba(47, 111, 239, 0.85)',
                borderColor: '#2F6FEF',
                borderWidth: 1,
                yAxisID: 'yNC'
              },
              {
                label: 'BER (%)',
                data: berValues,
                backgroundColor: 'rgba(239, 68, 68, 0.85)',
                borderColor: '#ef4444',
                borderWidth: 1,
                yAxisID: 'yBER'
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              yNC: {
                type: 'linear',
                position: 'left',
                min: 0,
                max: 1.0,
                title: { display: true, text: 'NC Score (0 - 1.0)' }
              },
              yBER: {
                type: 'linear',
                position: 'right',
                min: 0,
                max: 100,
                grid: { drawOnChartArea: false },
                title: { display: true, text: 'BER (%)' }
              }
            }
          }
        });
      }

      // Chart 2: Imperceptibility (PSNR & SSIM)
      const ctxImp = document.getElementById('imperceptibilityChart');
      if (ctxImp) {
        new Chart(ctxImp, {
          type: 'line',
          data: {
            labels: labels,
            datasets: [
              {
                label: 'PSNR (dB)',
                data: psnrValues,
                borderColor: '#1E7A55',
                backgroundColor: 'rgba(30, 122, 85, 0.15)',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                yAxisID: 'yPSNR'
              },
              {
                label: 'SSIM',
                data: ssimValues,
                borderColor: '#8B5CF6',
                backgroundColor: 'rgba(139, 92, 246, 0.15)',
                borderWidth: 2,
                tension: 0.3,
                yAxisID: 'ySSIM'
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              yPSNR: {
                type: 'linear',
                position: 'left',
                title: { display: true, text: 'PSNR (dB)' }
              },
              ySSIM: {
                type: 'linear',
                position: 'right',
                min: 0,
                max: 1.0,
                grid: { drawOnChartArea: false },
                title: { display: true, text: 'SSIM (0 - 1.0)' }
              }
            }
          }
        });
      }
    });
  </script>
<?php $__env->stopPush(); ?>
<?php echo $__env->make('layouts.app', array_diff_key(get_defined_vars(), ['__data' => 1, '__path' => 1]))->render(); ?><?php /**PATH D:\spectra-watermark-ui\laravel-app\resources\views/evaluation.blade.php ENDPATH**/ ?>