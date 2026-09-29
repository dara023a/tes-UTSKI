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

            <!-- 1. Metabox dipindahkan ke bawah drop zone gambar -->
            <div class="meta" id="metaBox" style="display:none; margin-top:14px; padding:12px; border:1px solid var(--line); border-radius:4px; background:#f8fafc;">
              <div style="grid-column: span 2; font-weight:600; font-size:11.5px; color:var(--slate); text-transform:uppercase; letter-spacing:0.04em; margin-bottom:4px;">Detail Citra Input</div>
              <div><span class="k">DIMENSI</span><span class="v" id="mDim">—</span></div>
              <div><span class="k">FORMAT</span><span class="v" id="mFmt">—</span></div>
              <div><span class="k">UKURAN FILE</span><span class="v" id="mSize">—</span></div>
              <div><span class="k">BLOK 8×8</span><span class="v" id="mBlocks">—</span></div>
            </div>

            <div class="field" style="margin-top:16px">
              <label>Watermark (Citra Watermark)</label>
              <input type="file" name="watermark_image" accept="image/*" required>
            </div>

            <!-- 4. Secret Key dengan ikon mata toggle password & Tooltip -->
            <div class="field">
              <div class="label-with-tooltip">
                <label for="wmKey" style="margin-bottom:0">Secret Key</label>
                <div class="tooltip-trigger" tabindex="0" aria-label="Penjelasan Secret Key">?
                  <div class="tooltip-content">Secret key: kunci untuk menentukan blok mana yang dipakai menanam bit. Key yang sama wajib dipakai saat extraction, kalau berbeda watermark akan gagal terbaca.</div>
                </div>
              </div>
              <div class="input-password-wrapper" style="margin-top:6px">
                <input type="password" name="secret_key" id="wmKey" placeholder="Kunci rahasia" autocomplete="new-password" required>
                <button type="button" class="toggle-password-btn" title="Tampilkan/Sembunyikan Key" onclick="togglePasswordVisibility('wmKey', this)">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                </button>
              </div>
            </div>

            <!-- 2. Alpha dengan Tooltip -->
            <div class="field">
              <div class="label-with-tooltip">
                <label style="margin-bottom:0">Alpha (α) — Kekuatan Watermark</label>
                <div class="tooltip-trigger" tabindex="0" aria-label="Penjelasan Alpha">?
                  <div class="tooltip-content">Alpha (α): margin pemisah antara dua koefisien DCT. Makin besar, watermark makin tahan serangan tapi kualitas gambar (PSNR) makin turun.</div>
                </div>
              </div>
              <input type="number" name="alpha" step="any" min="0" value="{{ old('alpha', config('watermark.default_params.alpha')) }}" placeholder="cth: 0.1 atau 5" style="margin-top:6px" required>
              <small style="color:var(--slate);font-size:12px;display:block;margin-top:4px">Masukkan nilai alpha yang ditentukan untuk eksperimen.</small>
            </div>

            <!-- 2. Redundancy (rentang 3-15) dengan Tooltip -->
            <div class="field">
              <div class="label-with-tooltip">
                <label style="margin-bottom:0">Redundancy (Rentang 3–15)</label>
                <div class="tooltip-trigger" tabindex="0" aria-label="Penjelasan Redundancy">?
                  <div class="tooltip-content">Redundancy: berapa kali tiap bit watermark ditanam (minimal 3). Makin tinggi, makin tahan serangan, tapi kapasitas gambar yang dibutuhkan makin besar.</div>
                </div>
              </div>
              <input type="number" name="redundancy" min="3" max="15" value="{{ old('redundancy', config('watermark.default_params.redundancy')) }}" style="margin-top:6px">
              <small style="color:var(--slate);font-size:12px;display:block;margin-top:4px">Default engine: 3 (rentang 3-15).</small>
            </div>

            <!-- 2. Threshold Binarisasi (0-255) dengan Tooltip -->
            <div class="field">
              <div class="label-with-tooltip">
                <label style="margin-bottom:0">Threshold Binarisasi (0–255)</label>
                <div class="tooltip-trigger" tabindex="0" aria-label="Penjelasan Threshold Binarisasi">?
                  <div class="tooltip-content">Threshold binarisasi: batas nilai piksel (0-255) untuk mengubah logo watermark menjadi hitam-putih sebelum ditanam.</div>
                </div>
              </div>
              <input type="number" name="threshold" min="0" max="255" value="{{ old('threshold', 127) }}" style="margin-top:6px">
              <small style="color:var(--slate);font-size:12px;display:block;margin-top:4px">Default engine: 127 (rentang 0-255).</small>
            </div>

            <!-- 3. Preserve Color Switch Card dengan Tooltip -->
            <div class="toggle-card">
              <div class="toggle-info">
                <div class="toggle-title">
                  <span>Preserve Color</span>
                  <div class="tooltip-trigger" tabindex="0" aria-label="Penjelasan Preserve Color">?
                    <div class="tooltip-content">Preserve color: jika dicentang, watermark ditanam di kanal luminansi saja sehingga warna asli gambar tetap dipertahankan.</div>
                  </div>
                </div>
                <span class="toggle-desc">Proses pada kanal luminansi Y (mempertahankan warna asli citra)</span>
              </div>
              <label class="switch">
                <input type="checkbox" name="preserve_color" id="preserveColor" value="1" {{ old('preserve_color') ? 'checked' : '' }}>
                <span class="switch-slider"></span>
              </label>
            </div>

            <button class="btn btn-dark" style="margin-top:20px;width:100%" type="submit" id="processBtn">Proses Embedding</button>
          </div>

          <div class="wscol">
            <div class="stagelist" id="stageList">
              <div class="stage" data-s="1">Membaca citra &amp; validasi format</div>
              <div class="stage" data-s="2">Transformasi DCT per blok</div>
              <div class="stage" data-s="3">Menyisipkan watermark di frekuensi menengah</div>
              <div class="stage" data-s="4">Inverse DCT &amp; rekonstruksi citra</div>
              <div class="stage" data-s="5">Menghitung PSNR &amp; SSIM</div>
            </div>

            <!-- 6. Banner pilihan lanjut ke tahap berikutnya -->
            @if ($hasRun)
              <div class="next-steps-container" id="nextBanner">
                <div class="next-steps-title">Pilih Langkah Selanjutnya</div>
                <div class="next-steps-desc">Citra ter-watermark tersimpan privat di server. Anda dapat menguji ketahanan citra dengan serangan atau langsung mengekstraksi watermark.</div>
                <div class="next-steps-grid">
                  <a href="{{ route('attack.index') }}" class="next-step-card primary">
                    <div>
                      <div class="card-head">
                        <span class="badge">TAHAP 02</span>
                        <h4>Uji Ketahanan (Attack)</h4>
                      </div>
                      <p>Simulasikan kompresi JPEG, resize, cropping, noise, brightness/contrast pada citra.</p>
                    </div>
                    <div class="action-link">Lanjut ke Attack →</div>
                  </a>
                  <a href="{{ route('extraction.index') }}" class="next-step-card">
                    <div>
                      <div class="card-head">
                        <span class="badge">TAHAP 03</span>
                        <h4>Ekstraksi Langsung</h4>
                      </div>
                      <p>Langsung verifikasi &amp; pulihkan watermark dari citra tanpa melakukan attack.</p>
                    </div>
                    <div class="action-link">Langsung ke Extraction →</div>
                  </a>
                </div>
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
