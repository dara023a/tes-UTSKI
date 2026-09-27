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

final class AttackController extends Controller
{
    public function index(Request $request): View
    {
        return view('attack', [
            'run' => $request->session()->get('watermark_run'),
        ]);
    }

    public function run(
        Request $request,
        PythonWatermarkEngine $engine,
        WatermarkStorageService $storage,
    ): RedirectResponse {
        $run = $request->session()->get('watermark_run');
        if (! is_array($run) || ! isset($run['id'], $run['watermarked_image'])) {
            return redirect()->route('embedding.index')
                ->withErrors(['engine' => 'Jalankan embedding terlebih dahulu.']);
        }

        $validated = $request->validate([
            'attack_type' => ['required', 'in:jpeg,resize,pure_crop,crop_resize_back'],
            'quality' => ['required_if:attack_type,jpeg', 'nullable', 'integer', 'min:1', 'max:100'],
            'scale' => ['required_if:attack_type,resize', 'nullable', 'numeric', 'gt:0'],
            'crop_percent' => ['required_if:attack_type,pure_crop,crop_resize_back', 'nullable', 'numeric', 'between:0,99.99'],
        ]);
        $attackType = $validated['attack_type'];
        $parameter = match ($attackType) {
            'jpeg' => (int) $validated['quality'],
            'resize' => (float) $validated['scale'],
            default => (float) $validated['crop_percent'],
        };
        $attacked = 'outputs/attacked.png';

        try {
            $engine->call('attack', [
                'image_path' => $storage->path($run['id'], $run['watermarked_image']),
                'attack_type' => $attackType,
                'quality' => $attackType === 'jpeg' ? $parameter : null,
                'scale' => $attackType === 'resize' ? $parameter : null,
                'crop_percent' => in_array($attackType, ['pure_crop', 'crop_resize_back'], true) ? $parameter : null,
                'output_path' => $storage->path($run['id'], $attacked),
            ]);
        } catch (PythonEngineException $exception) {
            return back()->withErrors(['engine' => $exception->getMessage()])->withInput();
        } catch (RuntimeException $exception) {
            return back()->withErrors(['engine' => $exception->getMessage()])->withInput();
        }

        $run['attacked_image'] = $attacked;
        $run['attack_type'] = $attackType;
        $run['parameter'] = $parameter;
        unset($run['extracted_image']);
        $request->session()->put('watermark_run', $run);

        return redirect()->route('extraction.index')
            ->with('success', 'Attack selesai. Citra hasilnya siap untuk blind extraction.');
    }
}
