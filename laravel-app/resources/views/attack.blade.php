@extends('layouts.app')

@section('title', 'Attack / Manipulation — Spectra Watermarking')

@section('footer_code', '02 · ATTACK')

@section('content')
<section class="pagehead">
  <div class="wrap">
    <div class="breadcrumb"><a href="{{ route('index') }}">Beranda</a> / Attack</div>
    <h1>Uji ketahanan citra terhadap manipulasi</h1>
    <p class="lead">Pilih citra ter-watermark yang ingin diserang, pilih jenis attack, lalu lihat perubahan visualnya sebelum dan sesudah. Perhitungan NC/BER dilakukan di halaman Extraction.</p>
    <div class="stepnav">
      <a href="{{ route('embedding.index') }}">01 Embedding</a><span class="arrow">→</span>
      <a class="here">02 Attack</a><span class="arrow">→</span>
      <a href="{{ route('extraction.index') }}">03 Extraction</a><span class="arrow">→</span>
      <a href="{{ route('evaluation.index') }}">04 Evaluation</a>
    </div>
  </div>
</section>

<section style="padding-top:56px">
  <div class="wrap">

    <div class="shead" style="margin-bottom:24px"><span class="tag">Langkah 1</span><h2 style="font-size:22px">Pilih citra yang akan diserang</h2></div>

    @if ($run)
      <div class="assetcard" id="embedAssetCard">
        <img class="thumb" id="embedThumb" src="{{ route('artifacts.show', ['kind' => 'watermarked']) }}" alt="Citra watermarked">
        <div class="info">
          <div class="t">Gunakan hasil Embedding terakhir</div>
          <div class="d" id="embedInfo">Citra ter-watermark tersimpan privat di server.</div>
        </div>
        <a class="btn btn-outline btn-sm" href="{{ route('artifacts.show', ['kind' => 'watermarked']) }}" download="watermarked.png">Unduh Citra</a>
      </div>
    @else
      <div class="assetcard empty" id="embedAssetEmpty">
        Belum ada hasil dari halaman Embedding di browser ini. Unggah citra ter-watermark secara manual atau <a href="{{ route('embedding.index') }}">buat satu di halaman Embedding</a>.
      </div>
    @endif

    @if ($run)
      <div id="attackPanel" style="margin-top:32px">
        <div class="shead" style="margin-bottom:24px"><span class="tag">Langkah 2</span><h2 style="font-size:22px">Pilih jenis attack &amp; jalankan</h2></div>
        <div style="border:1px solid var(--line);background:#fff">
          <form method="POST" action="{{ route('attack.run') }}">
            @csrf
            <div style="padding:28px">
              <div class="attackflow">
                <span class="af-node">Citra Ter-watermark</span><span class="af-arrow">→</span>
                <span class="af-node" id="atkNode">Parameter Attack</span><span class="af-arrow">→</span>
                <span class="af-node">Attacked Image</span>
              </div>

              <div class="field">
                <label>Jenis Attack</label>
                <select name="attack_type" id="attackType" required>
                  <option value="" disabled {{ old('attack_type', $run['attack_type'] ?? '') === '' ? 'selected' : '' }}>Pilih jenis attack</option>
                  <option value="jpeg" {{ old('attack_type', $run['attack_type'] ?? '') === 'jpeg' ? 'selected' : '' }}>JPEG compression</option>
                  <option value="resize" {{ old('attack_type', $run['attack_type'] ?? '') === 'resize' ? 'selected' : '' }}>Resize murni</option>
                  <option value="pure_crop" {{ old('attack_type', $run['attack_type'] ?? '') === 'pure_crop' ? 'selected' : '' }}>Pure crop</option>
                  <option value="crop_resize_back" {{ old('attack_type', $run['attack_type'] ?? '') === 'crop_resize_back' ? 'selected' : '' }}>Crop lalu resize balik</option>
                  <option value="gaussian_noise" {{ old('attack_type', $run['attack_type'] ?? '') === 'gaussian_noise' ? 'selected' : '' }}>Gaussian Noise</option>
                  <option value="brightness_contrast" {{ old('attack_type', $run['attack_type'] ?? '') === 'brightness_contrast' ? 'selected' : '' }}>Brightness &amp; Contrast</option>
                </select>
              </div>

              <div class="field attack-param" data-attack="jpeg">
                <label>Kualitas JPEG (1–100)</label>
                <div style="display:flex;gap:12px;margin-bottom:8px">
                  <button type="button" class="btn btn-outline btn-sm preset-btn" onclick="document.getElementById('jpegQ').value=90">Preset 90</button>
                  <button type="button" class="btn btn-outline btn-sm preset-btn" onclick="document.getElementById('jpegQ').value=70">Preset 70</button>
                  <button type="button" class="btn btn-outline btn-sm preset-btn" onclick="document.getElementById('jpegQ').value=50">Preset 50</button>
                </div>
                <input id="jpegQ" type="number" name="quality" min="1" max="100" value="{{ old('quality', ($run['attack_type'] ?? '') === 'jpeg' ? $run['parameter'] : 70) }}" placeholder="cth: 70">
              </div>

              <div class="field attack-param" data-attack="resize">
                <label>Scale Resize (cth: 0.5 untuk 50%)</label>
                <input type="number" name="scale" min="0" step="any" value="{{ old('scale', ($run['attack_type'] ?? '') === 'resize' ? $run['parameter'] : 0.5) }}" placeholder="cth: 0.5">
              </div>

              <div class="field attack-param" data-attack="pure_crop,crop_resize_back">
                <label>Crop dari Setiap Sisi (%)</label>
                <input type="number" name="crop_percent" min="0" max="99.99" step="any" value="{{ old('crop_percent', in_array($run['attack_type'] ?? '', ['pure_crop', 'crop_resize_back']) ? $run['parameter'] : 10) }}" placeholder="cth: 10">
              </div>

              <div class="field attack-param" data-attack="gaussian_noise">
                <label>Sigma (Deviasi Standar, cth: 10)</label>
                <input type="number" name="sigma" min="0" step="any" value="{{ old('sigma', 10) }}">
                <label style="margin-top:12px">Seed (Opsional)</label>
                <input type="number" name="seed" value="{{ old('seed') }}" placeholder="Kosongkan untuk acak">
              </div>

              <div class="field attack-param" data-attack="brightness_contrast">
                <label>Contrast (Alpha, cth: 1.2)</label>
                <input type="number" name="brightness_alpha" step="any" value="{{ old('brightness_alpha', 1.0) }}">
                <label style="margin-top:12px">Brightness (Beta, cth: 30)</label>
                <input type="number" name="brightness_beta" step="any" value="{{ old('brightness_beta', 0) }}">
              </div>

              <button class="btn btn-primary" type="submit" style="margin-top:14px">Terapkan Attack</button>

              @if (!empty($run['attacked_image']))
                <div class="rob-viewer" id="robViewer" style="display:block;margin-top:28px;padding-top:20px;border-top:1px solid var(--line)">
                  <div class="shead" style="margin-bottom:16px"><span class="tag">Hasil Attack</span><h2 style="font-size:18px">Citra Setelah Serangan</h2></div>
                  <div class="cvwrap">
                    <img src="{{ route('artifacts.show', ['kind' => 'attacked']) }}" alt="Citra hasil attack" style="max-width:100%;max-height:400px;border:1px solid var(--line);border-radius:4px;">
                  </div>
                  <div style="display:flex;gap:12px;margin-top:16px;flex-wrap:wrap">
                    <a class="btn btn-outline btn-sm" href="{{ route('artifacts.show', ['kind' => 'attacked']) }}" download="attacked.png">Unduh Citra Hasil Attack</a>
                  </div>
                  <div class="banner-info" id="nextBanner" style="margin-top:16px;display:flex;flex-direction:column;gap:12px;">
                    <div>Citra hasil attack tersimpan di server. Anda bisa melakukan attack ulang dengan parameter berbeda, atau lanjut ke tahap ekstraksi.</div>
                    <div style="display:flex;gap:12px">
                      <a href="{{ route('extraction.index') }}" class="btn btn-primary btn-sm">Lanjut ke Extraction →</a>
                    </div>
                  </div>
                </div>
              @endif
            </div>
          </form>
        </div>
      </div>
    @endif

  </div>
</section>
@endsection

@push('scripts')
<script>
    const attackType = document.getElementById('attackType');
    const atkNode = document.getElementById('atkNode');
    if (attackType) {
        const updateParameters = () => {
            const selected = attackType.value;
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
        attackType.addEventListener('change', updateParameters);
        updateParameters();
    }
</script>
@endpush
