<?php

declare(strict_types=1);

$projectRoot = dirname(base_path());
$defaultPython = $projectRoot.DIRECTORY_SEPARATOR.'.venv'.DIRECTORY_SEPARATOR.'Scripts'.DIRECTORY_SEPARATOR.'python.exe';
$configuredPython = env('WATERMARK_PYTHON');
$configuredBridge = env('WATERMARK_BRIDGE');

return [
    'python_binary' => $configuredPython ?: (is_file($defaultPython) ? $defaultPython : 'python'),
    'bridge_path' => $configuredBridge ?: $projectRoot.DIRECTORY_SEPARATOR.'web_bridge.py',
];
