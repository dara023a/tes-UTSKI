@extends('layouts.app')

@section('title', 'Evaluation — Spectra Watermarking')

@section('footer_code', '04 · EVALUATION')

@section('content')
<section class="pagehead">
  <div class="wrap">
    <div class="breadcrumb"><a href="{{ route('index') }}">Beranda</a> / Evaluation</div>
    <h1>Hasil pengujian robustness</h1>
    <p class="lead">NC dan BER mengukur pemulihan watermark setelah attack. PSNR dan SSIM mengukur imperceptibility citra watermarked sebelum attack; hasil berasal dari fungsi metrik Python.</p>
    <div class="stepnav">
      <a href="{{ route('embedding.index') }}">01 Embedding</a><span class="arrow">→</span>
      <a href="{{ route('attack.index') }}">02 Attack</a><span class="arrow">→</span>
      <a href="{{ route('extraction.index') }}">03 Extraction</a><span class="arrow">→</span>
      <a class="here">04 Evaluation</a>
    </div>
  </div>
</section>

<section style="padding-top:56px">
  <div class="wrap">

    <div class="banner-info" style="margin-bottom:28px">
      Data pada halaman ini dihitung secara presisi oleh engine pemrosesan citra Python. Hasil evaluasi mencakup nilai kualitas visual (<strong>PSNR, SSIM</strong>) dan ketahanan watermark (<strong>NC, BER</strong>) dari pengujian dalam sesi ini.
    </div>

    @if (!$rows)
      <div class="empty-state" id="emptyState">
        Belum ada hasil evaluasi dalam sesi ini. Jalankan
        <a href="{{ route('embedding.index') }}">Embedding</a> → 
        <a href="{{ route('attack.index') }}">Attack</a> → 
        <a href="{{ route('extraction.index') }}">Extraction</a> terlebih dahulu.
      </div>
    @else
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
            @foreach ($rows as $row)
              <tr>
                <td>{{ \Illuminate\Support\Carbon::parse($row['created_at'])->format('d M Y H:i:s') }}</td>
                <td>{{ strtoupper(str_replace('_', ' ', $row['attack_type'])) }}</td>
                <td>{{ $row['parameter'] }}</td>
                <td>{{ $row['psnr'] === 'inf' ? '∞' : number_format((float) $row['psnr'], 2) . ' dB' }}</td>
                <td>{{ number_format((float) $row['ssim'], 4) }}</td>
                <td>{{ number_format((float) $row['ncc'], 4) }}</td>
                <td>{{ number_format((float) $row['ber'] * 100, 2) }}%</td>
                <td>
                  <span class="status-pill {{ $row['status_class'] ?? 'err' }}">
                    {{ $row['status'] ?? 'Gagal' }}
                  </span>
                </td>
              </tr>
            @endforeach
          </tbody>
        </table>
      </div>

      @php($latest = end($rows))
      <div class="shead" style="margin:42px 0 20px">
        <span class="tag">Imperceptibility &amp; Robustness</span>
        <h2 style="font-size:22px">Ringkasan Metrik Pengujian Terakhir</h2>
        <p>PSNR dan SSIM dihitung dari citra asli dan citra watermarked sebelum attack. NC dan BER dihitung setelah ekstraksi watermark dari citra attacked.</p>
      </div>

      <div class="metricrow">
        <div class="metric">
          <div class="num">{{ $latest['psnr'] === 'inf' ? '∞' : number_format((float) $latest['psnr'], 2) }}</div>
          <div class="lbl2">PSNR (dB)</div>
        </div>
        <div class="metric">
          <div class="num">{{ number_format((float) $latest['ssim'], 4) }}</div>
          <div class="lbl2">SSIM</div>
        </div>
        <div class="metric">
          <div class="num">{{ number_format((float) $latest['ncc'], 4) }}</div>
          <div class="lbl2">NC</div>
        </div>
        <div class="metric">
          <div class="num">{{ number_format((float) $latest['ber'] * 100, 2) }}%</div>
          <div class="lbl2">BER</div>
        </div>
      </div>

      @if ($run && !empty($run['extracted_image']))
        <div style="display:flex;gap:12px;margin-top:24px;flex-wrap:wrap">
          <a class="btn btn-outline btn-sm" href="{{ route('artifacts.show', ['kind' => 'attacked']) }}" download="attacked.png">Unduh Attacked Image</a>
          <a class="btn btn-outline btn-sm" href="{{ route('artifacts.show', ['kind' => 'extracted']) }}" download="extracted-watermark.png">Unduh Extracted Watermark</a>
          <a class="btn btn-primary btn-sm" href="{{ route('attack.index') }}">Uji Attack Lain</a>
        </div>
      @endif
    @endif

  </div>
</section>
@endsection
