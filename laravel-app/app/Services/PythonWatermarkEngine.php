<?php

declare(strict_types=1);

namespace App\Services;

use RuntimeException;
use Symfony\Component\Process\Process;

final class PythonWatermarkEngine
{
    public function __construct() {}

    public function call(string $action, array $payload): array
    {
        $pythonBinary = (string) config('watermark.python_binary');
        $bridgePath = (string) config('watermark.bridge_path');
        if (! is_file($bridgePath)) {
            throw new RuntimeException('Python bridge tidak ditemukan. Periksa konfigurasi WATERMARK_BRIDGE.');
        }

        $process = new Process([
            $pythonBinary,
            $bridgePath,
            $action,
        ]);
        $process->setEnv([
            'PYTHONUTF8' => '1',
            'PYTHONIOENCODING' => 'utf-8',
        ]);
        $process->setInput(json_encode($payload, JSON_THROW_ON_ERROR));
        $process->setTimeout(60);
        $process->run();

        $decoded = json_decode($process->getOutput(), true);
        if (! is_array($decoded)) {
            throw new RuntimeException(
                $process->isSuccessful()
                    ? 'Python bridge mengembalikan respons yang tidak valid.'
                    : 'Python engine tidak dapat dijalankan. Periksa konfigurasi Python dan dependensinya.',
            );
        }
        if (! ($decoded['ok'] ?? false)) {
            throw new PythonEngineException(
                (string) ($decoded['error'] ?? 'Proses Python gagal.'),
                (string) ($decoded['type'] ?? 'EngineError'),
            );
        }
        if (! $process->isSuccessful()) {
            if ($process->isTimedOut()) {
                throw new RuntimeException('Python engine timeout (lebih dari 60 detik).');
            }
            throw new RuntimeException('Python engine tidak dapat menyelesaikan proses.');
        }

        return $decoded;
    }
}
