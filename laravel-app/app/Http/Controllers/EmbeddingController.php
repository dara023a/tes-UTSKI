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

final class EmbeddingController extends Controller
{
    public function index(Request $request): View
    {
        return view('embedding', [
            'hasRun' => $request->session()->has('watermark_run'),
        ]);
    }

    public function store(
        Request $request,
        PythonWatermarkEngine $engine,
        WatermarkStorageService $storage,
    ): RedirectResponse {
        $validated = $request->validate([
            'original_image' => ['required', 'file', 'image', 'max:10240'],
            'watermark_image' => ['required', 'file', 'image', 'max:10240'],
            'secret_key' => ['required', 'string', 'min:1', 'max:4096'],
            'alpha' => ['required', 'numeric', 'gt:0'],
            'redundancy' => ['nullable', 'integer', 'min:1'],
            'preserve_color' => ['nullable', 'boolean'],
            'threshold' => ['nullable', 'integer', 'min:0', 'max:255'],
        ]);

        $run = $storage->createRun();
        $original = $storage->storeUpload($request->file('original_image'), $run['id'], 'original');
        $watermark = $storage->storeUpload($request->file('watermark_image'), $run['id'], 'watermark');
        $watermarked = 'outputs/watermarked.png';
        $metadata = 'outputs/metadata.json';

        try {
            $engine->call('embed', [
                'original_image_path' => $storage->path($run['id'], $original),
                'watermark_image_path' => $storage->path($run['id'], $watermark),
                'secret_key' => $validated['secret_key'],
                'alpha' => (float) $validated['alpha'],
                'redundancy' => (int) ($validated['redundancy'] ?? 1),
                'preserve_color' => (bool) ($validated['preserve_color'] ?? false),
                'threshold' => (int) ($validated['threshold'] ?? 127),
                'watermarked_image_path' => $storage->path($run['id'], $watermarked),
                'metadata_path' => $storage->path($run['id'], $metadata),
            ]);
        } catch (PythonEngineException $exception) {
            return back()->withErrors(['engine' => $exception->getMessage()]);
        } catch (RuntimeException $exception) {
            return back()->withErrors(['engine' => $exception->getMessage()]);
        }

        $request->session()->put('watermark_run', [
            'id' => $run['id'],
            'original_image' => $original,
            'watermark_image' => $watermark,
            'watermarked_image' => $watermarked,
            'metadata_path' => $metadata,
            'alpha' => (float) $validated['alpha'],
            'preserve_color' => (bool) ($validated['preserve_color'] ?? false),
        ]);
        $request->session()->forget('watermark_metrics');

        return redirect()->route('attack.index')->with('success', 'Embedding selesai. Citra watermarked tersimpan privat di server.');
    }
}
