<?php

declare(strict_types=1);

use App\Http\Controllers\ArtifactController;
use App\Http\Controllers\AttackController;
use App\Http\Controllers\EmbeddingController;
use App\Http\Controllers\EvaluationController;
use App\Http\Controllers\ExtractionController;
use Illuminate\Support\Facades\Route;

Route::get('/', fn () => view('index'))->name('index');

Route::get('/embedding', [EmbeddingController::class, 'index'])->name('embedding.index');
Route::post('/embedding', [EmbeddingController::class, 'store'])->name('embedding.store');

Route::get('/attack', [AttackController::class, 'index'])->name('attack.index');
Route::post('/attack', [AttackController::class, 'run'])->name('attack.run');

Route::get('/extraction', [ExtractionController::class, 'index'])->name('extraction.index');
Route::post('/extraction', [ExtractionController::class, 'run'])->name('extraction.run');

Route::get('/evaluation', [EvaluationController::class, 'index'])->name('evaluation.index');
Route::get('/artifacts/{kind}', [ArtifactController::class, 'show'])->name('artifacts.show');
