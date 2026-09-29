#!/usr/bin/env python3
"""JSON subprocess adapter for the existing watermarking pipelines."""
from __future__ import annotations

import json
import math
import os
import sys
from typing import Any

import cv2
import numpy as np

from app.pipeline import (
    ImageLoadError,
    MetadataError,
    PipelineError,
    load_binary_watermark_image,
    load_color_image,
    load_grayscale_image,
    run_embedding_pipeline,
    run_evaluation_pipeline,
    run_extraction_pipeline,
    split_luma_chroma,
)
from app.watermark import CapacityError, DEFAULT_BINARIZE_THRESHOLD
from attack_simulation import attack_crop_resize_back, attack_jpeg, attack_pure_crop, attack_resize


class BridgeInputError(ValueError):
    """Invalid web-bridge payload or unsupported operation."""


def _required(payload: dict[str, Any], field: str) -> Any:
    value = payload.get(field)
    if value is None or value == "":
        raise BridgeInputError(f"Field wajib tidak tersedia: {field}.")
    return value


def _mkdir_for(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def embed(payload: dict[str, Any]) -> dict[str, Any]:
    output_path = str(_required(payload, "watermarked_image_path"))
    metadata_path = str(_required(payload, "metadata_path"))
    _mkdir_for(output_path)
    _mkdir_for(metadata_path)
    result = run_embedding_pipeline(
        original_image_path=str(_required(payload, "original_image_path")),
        watermark_image_path=str(_required(payload, "watermark_image_path")),
        key=str(_required(payload, "secret_key")),
        alpha=float(_required(payload, "alpha")),
        output_watermarked_path=output_path,
        output_metadata_path=metadata_path,
        binarize_threshold=int(_required(payload, "threshold")),
        redundancy=int(_required(payload, "redundancy")),
        preserve_color=bool(payload.get("preserve_color", False)),
    )
    return {
        "ok": True,
        "watermarked_image_path": result["watermarked_image_path"],
        "metadata_path": result["metadata_path"],
        "processed_image_size": result["metadata"]["processed_image_size"],
    }


def attack(payload: dict[str, Any]) -> dict[str, Any]:
    image_path = str(_required(payload, "image_path"))
    attack_type = str(_required(payload, "attack_type"))
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ImageLoadError("Citra watermarked tidak dapat dibaca.")

    if attack_type == "jpeg":
        parameter: int | float = int(_required(payload, "quality"))
        attacked = attack_jpeg(image, int(parameter))
    elif attack_type == "resize":
        parameter = float(_required(payload, "scale"))
        attacked = attack_resize(image, float(parameter))
    elif attack_type == "pure_crop":
        parameter = float(_required(payload, "crop_percent"))
        attacked = attack_pure_crop(image, float(parameter))
    elif attack_type == "crop_resize_back":
        parameter = float(_required(payload, "crop_percent"))
        attacked = attack_crop_resize_back(image, float(parameter))
    elif attack_type == "gaussian_noise":
        sigma = float(_required(payload, "sigma"))
        seed_param = payload.get("seed")
        seed = int(seed_param) if seed_param else None
        parameter = f"sigma={sigma}, seed={seed}"
        from attack_simulation import attack_gaussian_noise
        attacked = attack_gaussian_noise(image, sigma, seed)
    elif attack_type == "brightness_contrast":
        alpha_bc = float(_required(payload, "brightness_alpha"))
        beta_bc = float(_required(payload, "brightness_beta"))
        parameter = f"alpha={alpha_bc}, beta={beta_bc}"
        from attack_simulation import attack_brightness_contrast
        attacked = attack_brightness_contrast(image, alpha_bc, beta_bc)
    else:
        raise BridgeInputError("Jenis attack tidak didukung.")

    if attacked.size == 0:
        raise BridgeInputError("Parameter attack menghasilkan citra kosong.")

    output_path = str(_required(payload, "output_path"))
    _mkdir_for(output_path)
    output = np.clip(attacked, 0, 255).astype(np.uint8)
    if not cv2.imwrite(output_path, output):
        raise PipelineError("Gagal menyimpan citra hasil attack.")

    return {
        "ok": True,
        "attack_type": attack_type,
        "parameter": parameter,
        "output_path": output_path,
    }


def extract(payload: dict[str, Any]) -> dict[str, Any]:
    output_path = str(_required(payload, "extracted_image_path"))
    _mkdir_for(output_path)
    result = run_extraction_pipeline(
        watermarked_image_path=str(_required(payload, "image_path")),
        key=str(_required(payload, "secret_key")),
        metadata_path=str(_required(payload, "metadata_path")),
        output_extracted_watermark_path=output_path,
        on_size_mismatch=str(payload.get("on_size_mismatch", "raise")),
    )
    return {
        "ok": True,
        "extracted_image_path": result["extracted_watermark_path"],
    }


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    metadata_path = str(_required(payload, "metadata_path"))
    try:
        with open(metadata_path, "r", encoding="utf-8") as metadata_file:
            metadata = json.load(metadata_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise MetadataError("Metadata embedding tidak dapat dibaca.") from exc

    is_color = metadata.get("color_mode") == "ycrcb_luma_only"
    if is_color:
        original_color = load_color_image(str(_required(payload, "original_image_path")))
        watermarked_color = load_color_image(str(_required(payload, "watermarked_image_path")))
        original_image, _, _ = split_luma_chroma(original_color)
        watermarked_image, _, _ = split_luma_chroma(watermarked_color)
    else:
        original_image = load_grayscale_image(str(_required(payload, "original_image_path")))
        watermarked_image = load_grayscale_image(str(_required(payload, "watermarked_image_path")))

    threshold = int(metadata.get("binarize_threshold", DEFAULT_BINARIZE_THRESHOLD))
    original_watermark = load_binary_watermark_image(
        str(_required(payload, "watermark_image_path")), threshold=threshold
    )
    extracted_watermark = load_binary_watermark_image(
        str(_required(payload, "extracted_image_path")), threshold=threshold
    )
    processed_height, processed_width = metadata["processed_image_size"]
    original_image = original_image[:processed_height, :processed_width]
    watermarked_image = watermarked_image[:processed_height, :processed_width]
    metrics = run_evaluation_pipeline(
        original_image,
        watermarked_image,
        original_watermark,
        extracted_watermark,
    )

    return {
        "ok": True,
        "metrics": metrics,
        "attack_type": payload.get("attack_type", "none"),
        "parameter": payload.get("parameter"),
    }


def _user_error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, CapacityError):
        message, error_type = str(exc), "CapacityError"
    elif isinstance(exc, ImageLoadError):
        message, error_type = "File gambar tidak dapat dibaca atau formatnya tidak didukung.", "ImageLoadError"
    elif isinstance(exc, MetadataError):
        message, error_type = "Metadata embedding hilang, rusak, atau tidak cocok dengan run ini.", "MetadataError"
    elif isinstance(exc, BridgeInputError):
        message, error_type = str(exc), "ValidationError"
    elif isinstance(exc, PipelineError):
        message, error_type = "Pipeline gagal membaca atau menyimpan artefak. Periksa format input dan penyimpanan.", "PipelineError"
    elif isinstance(exc, (ValueError, TypeError, KeyError)):
        message, error_type = f"Input/parameter tidak valid: {exc}", "ValidationError"
    elif isinstance(exc, RuntimeError):
        message, error_type = "Operasi image gagal. Periksa parameter attack dan format citra.", "PipelineError"
    else:
        message, error_type = "Proses Python gagal. Periksa konfigurasi engine dan log server.", "EngineError"
    return {"ok": False, "error": message, "type": error_type}


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (float, np.floating)):
        number = float(value)
        return number if math.isfinite(number) else ("inf" if number > 0 else "-inf")
    if isinstance(value, np.integer):
        return int(value)
    return value


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
        if not isinstance(payload, dict):
            raise BridgeInputError("Payload bridge harus berupa objek JSON.")
        action = sys.argv[1] if len(sys.argv) > 1 else ""
        actions = {
            "embed": embed,
            "attack": attack,
            "extract": extract,
            "evaluate": evaluate,
        }
        if action not in actions:
            raise BridgeInputError("Jenis operasi bridge tidak didukung.")
        response = actions[action](payload)
    except (
        BridgeInputError,
        CapacityError,
        ImageLoadError,
        MetadataError,
        PipelineError,
        ValueError,
        TypeError,
        KeyError,
        OSError,
        RuntimeError,
    ) as exc:
        response = _user_error(exc)

    print(json.dumps(_json_safe(response), allow_nan=False))
    return 0 if response.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
