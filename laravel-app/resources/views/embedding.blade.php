@extends('layouts.app')

@section('title', 'Embedding — Spectra Watermarking')

@section('footer_code', '01 · EMBEDDING')

@section('content')
<section class="pagehead">
  <div class="wrap">
    <div class="breadcrumb"><a href="{{ route('index') }}">Beranda</a> / Embedding</div>
    <h1>Sisipkan watermark ke dalam karya Anda</h1>
    <p class="lead">Unggah citra, tentukan watermark dan secret key, lalu proses embedding dijalankan langsung di alur ini. Hasilnya bisa dilanjutkan ke halaman Attack.</p>
    <div class="stepnav">
      <a class="here">01 Embedding</a><span class="arrow">→</span>
      <a href="{{ route('attack.index') }}">02 Attack</a><span class="arrow">→</span>
      <a href="{{ route('extraction.index') }}">03 Extraction</a><span class="arrow">→</span>
      <a href="{{ route('evaluation.index') }}">04 Evaluation</a>
    </div>
  </div>
</section>

<section style="padding-top:56px">
  <div class="wrap">
    <div class="wsbox">
      <div class="wshead"><span><span class="dot on"></span>WORKSPACE.EMBED</span><span id="wsStatus">Menunggu citra</span></div>
      <form method="POST" action="{{ route('embedding.store') }}" enctype="multipart/form-data">
        @csrf
        <div class="wsgrid">
          <div class="wscol">
            <div class="drop" id="dropZone">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 16V4M12 4l-4 4M12 4l4 4M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2"/></svg>
              <p>Tarik &amp; letakkan citra, atau klik untuk memilih</p>
              <p class="sub">PNG / JPG, maksimum 10MB</p>
            </div>
            <input type="file" name="original_image" id="fileInput" accept="image/*" style="display:none" required>

            <div class="field">
              <label>Watermark (Citra Watermark)</label>
              <input type="file" name="watermark_image" accept="image/*" required>
            </div>

            <div class="field">
              <label>Secret Key</label>
              <input type="password" name="secret_key" id="wmKey" placeholder="Kunci rahasia" autocomplete="new-password" required>
            </div>

            <div class="field">
              <label>Alpha (Kekuatan Watermark)</label>
              <input type="number" name="alpha" step="any" min="0" value="{{ old('alpha') }}" placeholder="cth: 0.1 atau 5" required>
              <small style="color:var(--slate);font-size:12px;display:block;margin-top:2px">Masukkan nilai alpha yang ditentukan untuk eksperimen.</small>
            </div>

            <div class="field">
              <label>Redundancy</label>
              <input type="number" name="redundancy" min="1" value="{{ old('redundancy', 1) }}">
              <small style="color:var(--slate);font-size:12px;display:block;margin-top:2px">Default engine: 1.</small>
            </div>

            <div class="field">
              <label>Threshold Binarisasi</label>
              <input type="number" name="threshold" min="0" max="255" value="{{ old('threshold', 127) }}">
              <small style="color:var(--slate);font-size:12px;display:block;margin-top:2px">Default engine: 127.</small>
            </div>

            <label class="field" style="display:flex;align-items:center;gap:10px;padding-top:8px;">
              <input type="checkbox" name="preserve_color" value="1" {{ old('preserve_color') ? 'checked' : '' }}>
              <span style="font-size:13.5px">Preserve color (proses luminance Y)</span>
            </label>

            <div class="meta" id="metaBox" style="display:none">
              <div><span class="k">DIMENSI</span><span class="v" id="mDim">—</span></div>
              <div><span class="k">FORMAT</span><span class="v" id="mFmt">—</span></div>
              <div><span class="k">UKURAN FILE</span><span class="v" id="mSize">—</span></div>
              <div><span class="k">BLOK 8×8</span><span class="v" id="mBlocks">—</span></div>
            </div>

            <button class="btn btn-dark" style="margin-top:18px;width:100%" type="submit" id="processBtn">Proses Embedding</button>
          </div>

          <div class="wscol">
            <div class="stagelist" id="stageList">
              <div class="stage" data-s="1">Membaca citra &amp; validasi format</div>
              <div class="stage" data-s="2">Transformasi DCT per blok</div>
              <div class="stage" data-s="3">Menyisipkan watermark di frekuensi menengah</div>
              <div class="stage" data-s="4">Inverse DCT &amp; rekonstruksi citra</div>
              <div class="stage" data-s="5">Menghitung PSNR &amp; SSIM</div>
            </div>

            @if ($hasRun)
              <div class="banner-info" id="nextBanner" style="margin-top:20px;display:flex">
                Citra ter-watermark tersimpan privat di server. Lanjutkan ke <a href="{{ route('attack.index') }}" style="color:var(--blue-dim);font-weight:600">halaman Attack →</a> untuk mengujinya, atau langsung ke <a href="{{ route('extraction.index') }}" style="color:var(--blue-dim);font-weight:600">Extraction</a> tanpa serangan.
              </div>
            @endif
          </div>
        </div>
      </form>
    </div>
  </div>
</section>
@endsection

@push('scripts')
<script>
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const metaBox = document.getElementById('metaBox');
    const wsStatus = document.getElementById('wsStatus');

    function updateFileMeta(file) {
        if (!file) return;
        dropZone.querySelector('p').textContent = file.name;
        if (wsStatus) wsStatus.textContent = 'Citra siap diproses';
        const img = new Image();
        img.onload = function() {
            if (metaBox) {
                metaBox.style.display = 'grid';
                document.getElementById('mDim').textContent = img.width + ' × ' + img.height + ' px';
                document.getElementById('mFmt').textContent = (file.type.split('/')[1] || '?').toUpperCase();
                document.getElementById('mSize').textContent = (file.size / 1024).toFixed(0) + ' KB';
                document.getElementById('mBlocks').textContent = (Math.ceil(img.width / 8) * Math.ceil(img.height / 8)).toLocaleString('id-ID');
            }
        };
        img.src = URL.createObjectURL(file);
    }

    if (dropZone && fileInput) {
        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag'); });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag'));
        dropZone.addEventListener('drop', e => {
            e.preventDefault();
            dropZone.classList.remove('drag');
            const f = e.dataTransfer.files && e.dataTransfer.files[0];
            if (f) {
                fileInput.files = e.dataTransfer.files;
                updateFileMeta(f);
            }
        });
        fileInput.addEventListener('change', e => {
            const f = e.target.files && e.target.files[0];
            if (f) updateFileMeta(f);
        });
    }
</script>
@endpush
