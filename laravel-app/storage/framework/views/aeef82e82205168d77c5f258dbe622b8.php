<?php $__env->startSection('title', 'Attack / Manipulation — Spectra Watermarking'); ?>

<?php $__env->startSection('footer_code', '02 · ATTACK'); ?>

<?php $__env->startSection('content'); ?>
<section class="pagehead">
  <div class="wrap">
    <div class="breadcrumb"><a href="<?php echo e(route('index')); ?>">Beranda</a> / Attack</div>
    <h1>Uji ketahanan citra terhadap manipulasi</h1>
    <p class="lead">Pilih citra ter-watermark yang ingin diserang, pilih jenis attack, lalu lihat perubahan visualnya sebelum dan sesudah. Perhitungan NC/BER dilakukan di halaman Extraction.</p>
    <div class="stepnav">
      <a href="<?php echo e(route('embedding.index')); ?>">01 Embedding</a><span class="arrow">→</span>
      <a class="here">02 Attack</a><span class="arrow">→</span>
      <a href="<?php echo e(route('extraction.index')); ?>">03 Extraction</a><span class="arrow">→</span>
      <a href="<?php echo e(route('evaluation.index')); ?>">04 Evaluation</a>
    </div>
  </div>
</section>

<section style="padding-top:56px">
  <div class="wrap">

    <div class="shead" style="margin-bottom:24px"><span class="tag">Langkah 1</span><h2 style="font-size:22px">Pilih citra yang akan diserang</h2></div>

    <?php if($run): ?>
      <div class="assetcard" id="embedAssetCard">
        <img class="thumb" id="embedThumb" src="<?php echo e(route('artifacts.show', ['kind' => 'watermarked'])); ?>" alt="Citra watermarked">
        <div class="info">
          <div class="t">Gunakan hasil Embedding terakhir</div>
          <div class="d" id="embedInfo">Citra ter-watermark tersimpan privat di server.</div>
        </div>
        <a class="btn btn-outline btn-sm" href="<?php echo e(route('artifacts.show', ['kind' => 'watermarked'])); ?>" download="watermarked.png">Unduh Citra</a>
      </div>
    <?php else: ?>
      <div class="assetcard empty" id="embedAssetEmpty">
        Belum ada hasil dari halaman Embedding di browser ini. Unggah citra ter-watermark secara manual atau <a href="<?php echo e(route('embedding.index')); ?>">buat satu di halaman Embedding</a>.
      </div>
    <?php endif; ?>

    <?php if($run): ?>
      <div id="attackPanel" style="margin-top:32px">
        <div class="shead" style="margin-bottom:24px"><span class="tag">Langkah 2</span><h2 style="font-size:22px">Pilih jenis attack &amp; jalankan</h2></div>
        <div style="border:1px solid var(--line);background:#fff">
          <form method="POST" action="<?php echo e(route('attack.run')); ?>">
            <?php echo csrf_field(); ?>
            <div style="padding:28px">
              <div class="attackflow">
                <span class="af-node">Citra Ter-watermark</span><span class="af-arrow">→</span>
                <span class="af-node" id="atkNode">Parameter Attack</span><span class="af-arrow">→</span>
                <span class="af-node">Attacked Image</span>
              </div>

              <div class="field">
                <label style="margin-bottom:10px">Jenis Attack (Pilih Serangan)</label>
                
                <div class="attack-cards-grid" id="attackCardGrid">
                  <div class="attack-card-option" data-val="jpeg">
                    <svg class="opt-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18M15 3v18M3 9h18M3 15h18"/></svg>
                    <div class="opt-title">JPEG Compression</div>
                    <div class="opt-desc">Kompresi lossy standar web &amp; medsos.</div>
                  </div>
                  
                  <div class="attack-card-option" data-val="resize">
                    <svg class="opt-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>
                    <div class="opt-title">Resize Murni</div>
                    <div class="opt-desc">Mengubah resolusi/skala dimensi citra.</div>
                  </div>

                  <div class="attack-card-option" data-val="pure_crop">
                    <svg class="opt-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 2v14a2 2 0 002 2h14M18 22V8a2 2 0 00-2-2H2"/></svg>
                    <div class="opt-title">Pure Crop</div>
                    <div class="opt-desc">Memotong tepi citra tanpa meresize kembali.</div>
                  </div>

                  <div class="attack-card-option" data-val="crop_resize_back">
                    <svg class="opt-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 12a9 9 0 00-9-9 9 9 0 00-9 9 9 9 0 009 9c2.3 0 4.4-.8 6-2.1"/><path d="M21 3v9h-9"/></svg>
                    <div class="opt-title">Crop &amp; Resize Balik</div>
                    <div class="opt-desc">Memotong lalu mengembalikan ke ukuran semula.</div>
                  </div>

                  <div class="attack-card-option" data-val="gaussian_noise">
                    <svg class="opt-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="1"/><circle cx="6" cy="8" r="1"/><circle cx="18" cy="16" r="1"/><circle cx="8" cy="16" r="1"/><circle cx="16" cy="8" r="1"/></svg>
                    <div class="opt-title">Gaussian Noise</div>
                    <div class="opt-desc">Menambahkan gangguan acak Gaussian piksel.</div>
                  </div>

                  <div class="attack-card-option" data-val="brightness_contrast">
                    <svg class="opt-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 3v18a9 9 0 000-18z"/></svg>
                    <div class="opt-title">Brightness &amp; Contrast</div>
                    <div class="opt-desc">Mengubah kecerahan dan kontras warna citra.</div>
                  </div>
                </div>

                <select name="attack_type" id="attackType" required style="display:none">
                  <option value="" disabled <?php echo e(old('attack_type', $run['attack_type'] ?? '') === '' ? 'selected' : ''); ?>>Pilih jenis attack</option>
                  <option value="jpeg" <?php echo e(old('attack_type', $run['attack_type'] ?? '') === 'jpeg' ? 'selected' : ''); ?>>JPEG compression</option>
                  <option value="resize" <?php echo e(old('attack_type', $run['attack_type'] ?? '') === 'resize' ? 'selected' : ''); ?>>Resize murni</option>
                  <option value="pure_crop" <?php echo e(old('attack_type', $run['attack_type'] ?? '') === 'pure_crop' ? 'selected' : ''); ?>>Pure crop</option>
                  <option value="crop_resize_back" <?php echo e(old('attack_type', $run['attack_type'] ?? '') === 'crop_resize_back' ? 'selected' : ''); ?>>Crop lalu resize balik</option>
                  <option value="gaussian_noise" <?php echo e(old('attack_type', $run['attack_type'] ?? '') === 'gaussian_noise' ? 'selected' : ''); ?>>Gaussian Noise</option>
                  <option value="brightness_contrast" <?php echo e(old('attack_type', $run['attack_type'] ?? '') === 'brightness_contrast' ? 'selected' : ''); ?>>Brightness &amp; Contrast</option>
                </select>
              </div>

              <div class="field attack-param" data-attack="jpeg">
                <label>Kualitas JPEG (1–100)</label>
                <div style="display:flex;gap:12px;margin-bottom:8px">
                  <button type="button" class="btn btn-outline btn-sm preset-btn" onclick="document.getElementById('jpegQ').value=90">Preset 90</button>
                  <button type="button" class="btn btn-outline btn-sm preset-btn" onclick="document.getElementById('jpegQ').value=70">Preset 70</button>
                  <button type="button" class="btn btn-outline btn-sm preset-btn" onclick="document.getElementById('jpegQ').value=50">Preset 50</button>
                </div>
                <input id="jpegQ" type="number" name="quality" min="1" max="100" value="<?php echo e(old('quality', ($run['attack_type'] ?? '') === 'jpeg' ? $run['parameter'] : 70)); ?>" placeholder="cth: 70">
              </div>

              <div class="field attack-param" data-attack="resize">
                <label>Scale Resize (cth: 0.5 untuk 50%)</label>
                <input type="number" name="scale" min="0" step="any" value="<?php echo e(old('scale', ($run['attack_type'] ?? '') === 'resize' ? $run['parameter'] : 0.5)); ?>" placeholder="cth: 0.5">
              </div>

              <div class="field attack-param" data-attack="pure_crop,crop_resize_back">
                <label>Crop dari Setiap Sisi (%)</label>
                <input type="number" name="crop_percent" min="0" max="99.99" step="any" value="<?php echo e(old('crop_percent', in_array($run['attack_type'] ?? '', ['pure_crop', 'crop_resize_back']) ? $run['parameter'] : 10)); ?>" placeholder="cth: 10">
              </div>

              <div class="field attack-param" data-attack="gaussian_noise">
                <label>Sigma (Deviasi Standar, cth: 10)</label>
                <input type="number" name="sigma" min="0" step="any" value="<?php echo e(old('sigma', 10)); ?>">
                <label style="margin-top:12px">Seed (Opsional)</label>
                <input type="number" name="seed" value="<?php echo e(old('seed')); ?>" placeholder="Kosongkan untuk acak">
              </div>

              <div class="field attack-param" data-attack="brightness_contrast">
                <label>Contrast (Alpha, cth: 1.2)</label>
                <input type="number" name="brightness_alpha" step="any" value="<?php echo e(old('brightness_alpha', 1.0)); ?>">
                <label style="margin-top:12px">Brightness (Beta, cth: 30)</label>
                <input type="number" name="brightness_beta" step="any" value="<?php echo e(old('brightness_beta', 0)); ?>">
              </div>

              <button class="btn btn-primary" type="submit" style="margin-top:18px">Terapkan Attack</button>

              <?php if(!empty($run['attacked_image'])): ?>
                <div class="rob-viewer" id="robViewer" style="display:block;margin-top:28px;padding-top:20px;border-top:1px solid var(--line)">
                  <div class="shead" style="margin-bottom:16px"><span class="tag">Hasil Attack</span><h2 style="font-size:18px">Citra Setelah Serangan</h2></div>
                  <div class="cvwrap">
                    <img src="<?php echo e(route('artifacts.show', ['kind' => 'attacked'])); ?>" alt="Citra hasil attack" style="max-width:100%;max-height:400px;border:1px solid var(--line);border-radius:4px;">
                  </div>
                  <div style="display:flex;gap:12px;margin-top:16px;flex-wrap:wrap">
                    <a class="btn btn-outline btn-sm" href="<?php echo e(route('artifacts.show', ['kind' => 'attacked'])); ?>" download="attacked.png">Unduh Citra Hasil Attack</a>
                  </div>
                  
                  <div class="next-steps-container" id="nextBanner">
                    <div class="next-steps-title">Pilih Langkah Selanjutnya</div>
                    <div class="next-steps-desc">Citra hasil attack tersimpan di server. Anda bisa melakukan attack ulang dengan parameter berbeda, atau lanjut ke tahap ekstraksi.</div>
                    <div style="display:flex;gap:12px">
                      <a href="<?php echo e(route('extraction.index')); ?>" class="btn btn-primary btn-sm">Lanjut ke Extraction →</a>
                    </div>
                  </div>
                </div>
              <?php endif; ?>
            </div>
          </form>
        </div>
      </div>
    <?php endif; ?>

  </div>
</section>
<?php $__env->stopSection(); ?>

<?php $__env->startPush('scripts'); ?>
<script>
    const attackType = document.getElementById('attackType');
    const atkNode = document.getElementById('atkNode');
    const attackCardGrid = document.getElementById('attackCardGrid');

    if (attackType) {
        const updateParameters = () => {
            const selected = attackType.value;
            
            if (attackCardGrid) {
                attackCardGrid.querySelectorAll('.attack-card-option').forEach(card => {
                    card.classList.toggle('selected', card.dataset.val === selected);
                });
            }

            document.querySelectorAll('.attack-param').forEach(field => {
                const activeTypes = field.dataset.attack.split(',');
                const active = activeTypes.includes(selected);
                field.hidden = !active;
                field.querySelector('input').disabled = !active;
            });
            if (atkNode) {
                const labels = {
                    jpeg: 'JPEG Compression',
                    resize: 'Resize Murni',
                    pure_crop: 'Pure Crop',
                    crop_resize_back: 'Crop lalu Resize Balik',
                    gaussian_noise: 'Gaussian Noise',
                    brightness_contrast: 'Brightness & Contrast'
                };
                atkNode.textContent = labels[selected] || 'Parameter Attack';
            }
        };

        if (attackCardGrid) {
            attackCardGrid.querySelectorAll('.attack-card-option').forEach(card => {
                card.addEventListener('click', () => {
                    attackType.value = card.dataset.val;
                    attackType.dispatchEvent(new Event('change'));
                });
            });
        }

        attackType.addEventListener('change', updateParameters);
        updateParameters();
    }
</script>
<?php $__env->stopPush(); ?>

<?php echo $__env->make('layouts.app', array_diff_key(get_defined_vars(), ['__data' => 1, '__path' => 1]))->render(); ?><?php /**PATH D:\spectra-watermark-ui\laravel-app\resources\views/attack.blade.php ENDPATH**/ ?>