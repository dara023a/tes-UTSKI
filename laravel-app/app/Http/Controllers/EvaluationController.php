<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\View\View;

final class EvaluationController extends Controller
{
    public function index(Request $request): View
    {
        return view('evaluation', [
            'run' => $request->session()->get('watermark_run'),
            'rows' => $request->session()->get('watermark_metrics', []),
        ]);
    }
}
