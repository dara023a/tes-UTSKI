@extends('layouts.app')

@section('title', 'Extraction — Spectra Watermarking')

@section('footer_code', '03 · EXTRACTION')

@section('content')
<section class="pagehead">
  <div class="wrap">
    <div class="breadcrumb"><a href="{{ route('index') }}">Beranda</a> / Extraction</div>
    <h1>Ekstraksi watermark secara blind</h1>
    <p class="lead">Sistem hanya membutuhkan citra dan secret key — tanpa citra asli — untuk mencoba memulihkan kembali watermark yang tersisip.</p>
    <div class="stepnav">
      <a href="{{ route('embedding.index') }}">01 Embedding</a><span class="arrow">→</span>
      <a href="{{ route('attack.index') }}">02 Attack</a><span class="arrow">→</span>
      <a class="here">03 Extraction</a><span class="arrow">→</span>
      <a href="{{ route('evaluation.index') }}">04 Evaluation</a>
    </div>
  </div>
</section>

<section style="padding-top:56px">
  <div class="wrap">
    <div class="wsbox">
      <div class="wshead"><span><span class="dot on"></span>WORKSPACE.EXTRACT</span><span id="vStatus">{{ ($run && !empty($run['extracted_image'])) ? 'Selesai' : (($run && !empty($run['attacked_image'])) ? 'Citra siap diekstraksi' : 'Menunggu citra') }}</span></div>
      <div class="wsgrid">
        <div class="wscol">

          @if ($run && !empty($run['attacked_image']))
            <div class="assetcard" id="attackAssetCard">
              <img class="thumb" id="attackThumb" src="{{ route('artifacts.show', ['kind' => 'attacked']) }}" alt="Citra hasil attack">
              <div class="info">
                <div class="t">Gunakan hasil Attack terakhir</div>
                <div class="d" id="attackInfo">Attack: {{ str_replace('_', ' ', $run['attack_type'] ?? 'none') }} · Parameter: {{ $run['parameter'] ?? '—' }}</div>
              </div>
              <a class="btn btn-outline btn-sm" href="{{ route('artifacts.show', ['kind' => 'attacked']) }}" download="attacked.png">Unduh</a>
            </div>
          @else
            <div class="assetcard empty" id="attackAssetEmpty">
              Belum ada hasil dari halaman Attack di browser ini. Unggah citra secara manual atau <a href="{{ route('attack.index') }}">jalankan attack dulu</a>.
            </div>
          @endif

          <form method="POST" action="{{ route('extraction.run') }}">
            @csrf
            <div class="field" style="margin-top:16px">
              <label>Secret Key</label>
              <input type="password" name="secret_key" id="vKey" placeholder="Kunci rahasia" autocomplete="new-password" required>
            </div>

            <div class="field">
              <label>Strategi bila ukuran citra berubah</label>
              <select name="on_size_mismatch" required>
                <option value="raise" {{ old('on_size_mismatch', $defaultMismatch) === 'raise' ? 'selected' : '' }}>raise — tanpa sinkronisasi ukuran</option>
                <option value="resize" {{ old('on_size_mismatch', $defaultMismatch) === 'resize' ? 'selected' : '' }}>resize — untuk resize murni</option>
                <option value="centered_crop" {{ old('on_size_mismatch', $defaultMismatch) === 'centered_crop' ? 'selected' : '' }}>centered_crop — mengasumsikan crop simetris</option>
              </select>
            </div>

            <button class="btn btn-dark" style="margin-top:18px;width:100%" id="verifyBtn" type="submit" {{ (!$run || empty($run['attacked_image'])) ? 'disabled' : '' }}>Ekstrak Watermark</button>
          </form>
        </div>

        <div class="wscol">
          <p style="font-size:13.5px;margin-bottom:10px">Hasil ekstraksi akan tampil di sini setelah proses selesai.</p>

          @if (!$run || empty($run['extracted_image']))
            <div id="vResultEmpty" style="border:1px dashed var(--line);padding:28px;text-align:center;font-size:13px;color:#8A93A2">Belum ada citra diproses</div>
          @else
            @php($metricsList = session('watermark_metrics', []))
            @php($latestMetric = end($metricsList))
            <div id="vResult">
              <div class="resultbanner ok" id="vBanner">✓ Watermark terdeteksi &amp; diekstraksi</div>
              
              <div style="margin: 16px 0; text-align: center;">
                <img src="{{ route('artifacts.show', ['kind' => 'extracted']) }}" alt="Extracted Watermark" style="max-height: 140px; border: 1px solid var(--line); border-radius: 4px; padding: 4px; background: #fff;">
                <p style="font-size: 12px; color: var(--slate); margin-top: 4px;">Visual Citra Watermark Hasil Ekstraksi</p>
              </div>

              @if ($latestMetric)
                <div class="metricrow">
                  <div class="metric"><div class="num" id="vNc">{{ number_format((float) $latestMetric['ncc'], 3) }}</div><div class="lbl2">NC</div></div>
                  <div class="metric"><div class="num" id="vBer">{{ number_format((float) $latestMetric['ber'] * 100, 1) }}%</div><div class="lbl2">BER</div></div>
                  <div class="metric"><div class="num" id="vId">Terdeteksi</div><div class="lbl2">Status</div></div>
                </div>
              @endif

              <div class="banner-info" id="nextBanner" style="margin-top:18px;display:flex">
                Tersimpan. Lihat semua hasil pengujian di <a href="{{ route('evaluation.index') }}" style="color:var(--blue-dim);font-weight:600">halaman Evaluation →</a>
              </div>
            </div>
          @endif
        </div>
      </div>
    </div>
  </div>
</section>
@endsection
