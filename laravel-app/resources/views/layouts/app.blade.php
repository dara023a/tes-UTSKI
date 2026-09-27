<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <title>@yield('title', 'Spectra — Invisible Watermarking untuk Karya Ilustrasi')</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ asset('assets/css/style.css') }}">
    @stack('styles')
</head>
<body>

<header>
<nav>
  <a class="brand" href="{{ route('index') }}"><svg viewBox="0 0 24 24" fill="none"><rect x="2" y="2" width="8" height="8" fill="#2F6FEF" opacity=".9"/><rect x="14" y="2" width="8" height="8" fill="#0B1526"/><rect x="2" y="14" width="8" height="8" fill="#0B1526"/><rect x="14" y="14" width="8" height="8" fill="#2F6FEF" opacity=".5"/></svg>Spectra</a>
  <ul class="navlinks" id="navlinks">
    <li><a href="{{ route('index') }}" class="{{ request()->routeIs('index') ? 'active' : '' }}">Beranda</a></li>
    <li><a href="{{ route('index') }}#cara-kerja">Proses</a></li>
    <li><a href="{{ route('embedding.index') }}" class="{{ request()->routeIs('embedding.index') ? 'active' : '' }}">Embedding</a></li>
    <li><a href="{{ route('attack.index') }}" class="{{ request()->routeIs('attack.index') ? 'active' : '' }}">Attack</a></li>
    <li><a href="{{ route('extraction.index') }}" class="{{ request()->routeIs('extraction.index') ? 'active' : '' }}">Extraction</a></li>
    <li><a href="{{ route('evaluation.index') }}" class="{{ request()->routeIs('evaluation.index') ? 'active' : '' }}">Evaluasi</a></li>
    <li><a href="{{ route('index') }}#edukasi">Edukasi</a></li>
    <li><a href="{{ route('index') }}#tentang">Tentang</a></li>
  </ul>
  <a class="navcta" href="{{ route('embedding.index') }}">Mulai Watermarking</a>
  <button class="burger" id="burgerBtn">☰</button>
</nav>
</header>

@if ($errors->any())
    <section class="wrap" style="padding-top:20px; padding-bottom:0;">
        <div class="banner-info" style="border-color: #f2b4a9; background: #fff5f5; color: #7a1f1f;">
            <ul style="margin: 0; padding-left: 18px;">
                @foreach ($errors->all() as $error)
                    <li>{{ $error }}</li>
                @endforeach
            </ul>
        </div>
    </section>
@endif

@if (session('success'))
    <section class="wrap" style="padding-top:20px; padding-bottom:0;">
        <div class="banner-info" style="border-color: #9ad3b1; background: #eefaf2; color: #1c5c3c;">
            {{ session('success') }}
        </div>
    </section>
@endif

@yield('content')

<footer>
  <div class="wrap">
    <span>© 2026 Spectra — Proyek penelitian Keamanan Informasi</span>
    <span class="mono">@yield('footer_code', 'DCT · BLIND · PSNR/SSIM/NC/BER')</span>
  </div>
</footer>

<script src="{{ asset('assets/js/common.js') }}"></script>
@stack('scripts')
</body>
</html>
