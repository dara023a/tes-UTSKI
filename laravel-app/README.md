# Spectra Watermarking — Laravel web layer

Laravel handles uploads, validation, private file storage, routing, and rendering. The sibling `web_bridge.py` process calls the existing Python pipeline; watermark algorithms and metric implementations remain in the parent project's `app/` modules.

## Setup

From this directory:

```powershell
composer install
php artisan key:generate
New-Item -ItemType File -Force database\database.sqlite
php artisan migrate
```

The default `config/watermark.php` expects the project's Python virtual environment at `..\.venv\Scripts\python.exe` and the bridge at `..\web_bridge.py`. Override either path in `.env` if needed:

```dotenv
WATERMARK_PYTHON=D:\path\to\python.exe
WATERMARK_BRIDGE=D:\path\to\web_bridge.py
```

Install the parent project's Python dependencies from the project root with `python -m pip install -r requirements.txt`. For Laravel Herd, configure the site document root to this project's `public/` directory. PHP must allow image uploads of at least 10 MB each and a request body of at least 20 MB (`upload_max_filesize` / `post_max_size`), with a writable `upload_tmp_dir`. The built-in local server can also be used with `php artisan serve`.

## Workflow

1. **Embedding** uploads the original image and watermark, requires an explicit alpha, and stores all input/output files under `storage/app/private/watermark-runs/{uuid}`.
2. **Attack** invokes one single-image helper (`attack_jpeg`, `attack_resize`, `attack_pure_crop`, or `attack_crop_resize_back`). The batch experiment entry point is not used.
3. **Extraction** receives only the attacked image, embedding metadata, secret key, and size-mismatch strategy. The original image is not passed to the extraction call.
4. **Evaluation** is run after extraction by the Python bridge. It reports NC/BER for watermark recovery and PSNR/SSIM separately for embedding imperceptibility.

Files are not placed in Laravel's public directory. Session-scoped artifact routes require the browser session that created the run. Secret keys are sent to Python over subprocess stdin, are not stored in metadata/session state, and are excluded from flashed validation input.

## Parameters and validation

- Alpha has no UI default; enter the value selected for the experiment.
- Redundancy defaults to the engine's documented `1`.
- Watermark binarization threshold defaults to the engine's `127`.
- JPEG quality, resize scale, and crop percentage must be selected for the chosen attack; the UI does not prefill undocumented attack parameter defaults.
- `centered_crop` assumes a symmetric crop. It is most useful when embedding redundancy is greater than one.

## Checks

```powershell
php artisan test
vendor\bin\pint.bat --test app\Http\Controllers app\Services routes config\watermark.php bootstrap\app.php
```

Run the Python engine tests from the parent directory:

```powershell
python -m unittest discover -s tests -v
```
