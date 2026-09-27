<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Services\WatermarkStorageService;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\BinaryFileResponse;

final class ArtifactController extends Controller
{
    public function show(
        Request $request,
        WatermarkStorageService $storage,
        string $kind,
    ): BinaryFileResponse {
        $run = $request->session()->get('watermark_run');
        abort_unless(is_array($run) && isset($run['id']), 404);

        $relativePath = match ($kind) {
            'watermarked' => $run['watermarked_image'] ?? null,
            'attacked' => $run['attacked_image'] ?? null,
            'extracted' => $run['extracted_image'] ?? null,
            default => null,
        };
        abort_unless(is_string($relativePath), 404);

        $path = $storage->path($run['id'], $relativePath);
        abort_unless(is_file($path), 404);

        return response()->file($path, [
            'Cache-Control' => 'private, no-store',
            'X-Content-Type-Options' => 'nosniff',
        ]);
    }
}
