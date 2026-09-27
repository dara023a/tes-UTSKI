<?php

declare(strict_types=1);

namespace App\Services;

use Illuminate\Http\UploadedFile;
use Illuminate\Support\Str;
use RuntimeException;

final class WatermarkStorageService
{
    public function createRun(): array
    {
        $runId = (string) Str::uuid();
        $directory = $this->directory($runId);
        foreach (['inputs', 'outputs'] as $child) {
            if (! is_dir($directory.DIRECTORY_SEPARATOR.$child)
                && ! mkdir($directory.DIRECTORY_SEPARATOR.$child, 0700, true)
                && ! is_dir($directory.DIRECTORY_SEPARATOR.$child)) {
                throw new RuntimeException('Tidak dapat menyiapkan penyimpanan run watermark.');
            }
        }

        return ['id' => $runId, 'directory' => $directory];
    }

    public function directory(string $runId): string
    {
        if (! Str::isUuid($runId)) {
            throw new RuntimeException('Run watermark tidak valid atau sudah kedaluwarsa.');
        }

        return storage_path('app/private/watermark-runs/'.$runId);
    }

    public function path(string $runId, string $relativePath): string
    {
        if (! preg_match('/\A[a-zA-Z0-9_-]+(?:\/[a-zA-Z0-9_-]+)*\.[a-zA-Z0-9]+\z/', $relativePath)) {
            throw new RuntimeException('Nama artefak watermark tidak valid.');
        }

        return $this->directory($runId).DIRECTORY_SEPARATOR
            .str_replace('/', DIRECTORY_SEPARATOR, $relativePath);
    }

    public function storeUpload(UploadedFile $file, string $runId, string $name): string
    {
        $relativePath = 'inputs/'.$name.'.'.$file->extension();
        $path = $this->path($runId, $relativePath);
        $directory = dirname($path);

        if (! is_dir($directory) && ! mkdir($directory, 0700, true) && ! is_dir($directory)) {
            throw new RuntimeException('Tidak dapat menyimpan file upload secara privat.');
        }

        $file->move($directory, basename($path));

        return $relativePath;
    }
}
