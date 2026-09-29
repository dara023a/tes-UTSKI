<?php

declare(strict_types=1);

$projectRoot = dirname(base_path());
$defaultPython = $projectRoot.DIRECTORY_SEPARATOR.'.venv'.DIRECTORY_SEPARATOR.'Scripts'.DIRECTORY_SEPARATOR.'python.exe';
$configuredPython = env('WATERMARK_PYTHON');
$configuredBridge = env('WATERMARK_BRIDGE');

return [
    'python_binary' => $configuredPython ?: (is_file($defaultPython) ? $defaultPython : 'python'),
    'bridge_path' => $configuredBridge ?: $projectRoot.DIRECTORY_SEPARATOR.'web_bridge.py',
    'nc_threshold' => [
        // Zero-mean NC (Pearson). Skala: 1.0 = sempurna, ~0 = acak, <0 = inversi.
        // Ambang dikalibrasi dari eksperimen: key-salah ≈ 0.00–0.05.
        'detected' => 0.75,   // NC >= 0.75 -> Terdeteksi
        'weak'     => 0.40,   // NC >= 0.40 -> Melemah; <0.40 -> Gagal
    ],
    'default_params' => [
        'alpha' => 100,
        'redundancy' => 3,
    ],
];
