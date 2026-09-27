<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Services\PythonEngineException;
use App\Services\PythonWatermarkEngine;
use App\Services\WatermarkStorageService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;
use RuntimeException;

final class ExtractionController extends Controller
{
    public function index(Request $request): View
    {
        $run = $request->session()->get('watermark_run');
        $defaultMismatch = match ($run['attack_type'] ?? null) {
            'resize' => 'resize',
            'pure_crop' => 'centered_crop',
            default => 'raise',
        };

        return view('extraction', compact('run', 'defaultMismatch'));
    }

    public function run(
        Request $request,
        PythonWatermarkEngine $engine,
        WatermarkStorageService $storage,
    ): RedirectResponse {
        $run = $request->session()->get('watermark_run');
        if (! is_array($run)
            || ! isset($run['id'], $run['attacked_image'], $run['metadata_path'], $run['original_image'], $run['watermark_image'], $run['watermarked_image'])) {
            return redirect()->route('embedding.index')
                ->withErrors(['engine' => 'Selesaikan embedding dan attack sebelum extraction.']);
        }

        $validated = $request->validate([
            'secret_key' => ['required', 'string', 'min:1', 'max:4096'],
            'on_size_mismatch' => ['required', 'in:raise,resize,centered_crop'],
        ]);
        $extracted = 'outputs/extracted.png';

        try {
            $engine->call('extract', [
                'image_path' => $storage->path($run['id'], $run['attacked_image']),
                'metadata_path' => $storage->path($run['id'], $run['metadata_path']),
                'secret_key' => $validated['secret_key'],
                'extracted_image_path' => $storage->path($run['id'], $extracted),
                'on_size_mismatch' => $validated['on_size_mismatch'],
            ]);

            $evaluation = $engine->call('evaluate', [
                'original_image_path' => $storage->path($run['id'], $run['original_image']),
                'watermarked_image_path' => $storage->path($run['id'], $run['watermarked_image']),
                'watermark_image_path' => $storage->path($run['id'], $run['watermark_image']),
                'extracted_image_path' => $storage->path($run['id'], $extracted),
                'metadata_path' => $storage->path($run['id'], $run['metadata_path']),
                'threshold' => 127,
                'attack_type' => $run['attack_type'] ?? 'none',
                'parameter' => $run['parameter'] ?? null,
            ]);
        } catch (PythonEngineException $exception) {
            return back()->withErrors(['engine' => $exception->getMessage()]);
        } catch (RuntimeException $exception) {
            return back()->withErrors(['engine' => $exception->getMessage()]);
        }

        $metrics = $evaluation['metrics'];
        $rows = $request->session()->get('watermark_metrics', []);
        $rows[] = [
            'created_at' => now()->toIso8601String(),
            'attack_type' => $run['attack_type'] ?? 'none',
            'parameter' => $run['parameter'] ?? '—',
            'ncc' => $metrics['ncc'],
            'ber' => $metrics['ber'],
            'psnr' => $metrics['psnr'],
            'ssim' => $metrics['ssim'],
        ];

        $run['extracted_image'] = $extracted;
        $request->session()->put('watermark_run', $run);
        $request->session()->put('watermark_metrics', $rows);

        return redirect()->route('evaluation.index')
            ->with('success', 'Blind extraction selesai. NC, BER, PSNR, dan SSIM dihitung oleh engine Python.');
    }
}
