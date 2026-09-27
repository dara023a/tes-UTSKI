<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <title><?php echo $__env->yieldContent('title', 'Spectra — Invisible Watermarking untuk Karya Ilustrasi'); ?></title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="<?php echo e(asset('assets/css/style.css')); ?>">
    <?php echo $__env->yieldPushContent('styles'); ?>
</head>
<body>

<header>
<nav>
  <a class="brand" href="<?php echo e(route('index')); ?>"><svg viewBox="0 0 24 24" fill="none"><rect x="2" y="2" width="8" height="8" fill="#2F6FEF" opacity=".9"/><rect x="14" y="2" width="8" height="8" fill="#0B1526"/><rect x="2" y="14" width="8" height="8" fill="#0B1526"/><rect x="14" y="14" width="8" height="8" fill="#2F6FEF" opacity=".5"/></svg>Spectra</a>
  <ul class="navlinks" id="navlinks">
    <li><a href="<?php echo e(route('index')); ?>" class="<?php echo e(request()->routeIs('index') ? 'active' : ''); ?>">Beranda</a></li>
    <li><a href="<?php echo e(route('index')); ?>#cara-kerja">Proses</a></li>
    <li><a href="<?php echo e(route('embedding.index')); ?>" class="<?php echo e(request()->routeIs('embedding.index') ? 'active' : ''); ?>">Embedding</a></li>
    <li><a href="<?php echo e(route('attack.index')); ?>" class="<?php echo e(request()->routeIs('attack.index') ? 'active' : ''); ?>">Attack</a></li>
    <li><a href="<?php echo e(route('extraction.index')); ?>" class="<?php echo e(request()->routeIs('extraction.index') ? 'active' : ''); ?>">Extraction</a></li>
    <li><a href="<?php echo e(route('evaluation.index')); ?>" class="<?php echo e(request()->routeIs('evaluation.index') ? 'active' : ''); ?>">Evaluasi</a></li>
    <li><a href="<?php echo e(route('index')); ?>#edukasi">Edukasi</a></li>
    <li><a href="<?php echo e(route('index')); ?>#tentang">Tentang</a></li>
  </ul>
  <a class="navcta" href="<?php echo e(route('embedding.index')); ?>">Mulai Watermarking</a>
  <button class="burger" id="burgerBtn">☰</button>
</nav>
</header>

<?php if($errors->any()): ?>
    <section class="wrap" style="padding-top:20px; padding-bottom:0;">
        <div class="banner-info" style="border-color: #f2b4a9; background: #fff5f5; color: #7a1f1f;">
            <ul style="margin: 0; padding-left: 18px;">
                <?php $__currentLoopData = $errors->all(); $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $error): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
                    <li><?php echo e($error); ?></li>
                <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
            </ul>
        </div>
    </section>
<?php endif; ?>

<?php if(session('success')): ?>
    <section class="wrap" style="padding-top:20px; padding-bottom:0;">
        <div class="banner-info" style="border-color: #9ad3b1; background: #eefaf2; color: #1c5c3c;">
            <?php echo e(session('success')); ?>

        </div>
    </section>
<?php endif; ?>

<?php echo $__env->yieldContent('content'); ?>

<footer>
  <div class="wrap">
    <span>© 2026 Spectra — Proyek penelitian Keamanan Informasi</span>
    <span class="mono"><?php echo $__env->yieldContent('footer_code', 'DCT · BLIND · PSNR/SSIM/NC/BER'); ?></span>
  </div>
</footer>

<script src="<?php echo e(asset('assets/js/common.js')); ?>"></script>
<?php echo $__env->yieldPushContent('scripts'); ?>
</body>
</html>
<?php /**PATH D:\spectra-watermark-ui\laravel-app\resources\views\layouts\app.blade.php ENDPATH**/ ?>