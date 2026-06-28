"""Rule-based model advisor for MONAS."""

from __future__ import annotations

from typing import Any, Dict, List


def _priority(payload: Dict[str, Any]) -> Dict[str, float]:
    priority = payload.get("priority") or {}
    accuracy = float(priority.get("accuracy", 0.6) or 0.0)
    latency = float(priority.get("latency", 0.3) or 0.0)
    size = float(priority.get("size", 0.1) or 0.0)
    total = accuracy + latency + size
    if total <= 0:
        return {"accuracy": 0.6, "latency": 0.3, "size": 0.1}
    return {"accuracy": accuracy / total, "latency": latency / total, "size": size / total}


def advisor_suggest(payload: Dict[str, Any]) -> Dict[str, Any]:
    task_type = payload.get("taskType", "Image Classification")
    dataset_size = payload.get("datasetSize", "Medium (10k-100k)")
    target_hardware = payload.get("targetHardware", "Edge   CPU")
    priority = _priority(payload)

    if target_hardware in {"Mobile (ARM)", "Raspberry Pi"}:
        base_architecture = "EfficientNet-lite"
    elif target_hardware == "Edge CPU":
        base_architecture = "MobileNetV3"
    elif task_type == "NLP (text)":
        base_architecture = "BERT-tiny"
    elif task_type == "Object Detection":
        base_architecture = "YOLO-NAS-small"
    elif task_type in {"Tabular", "Time Series"}:
        base_architecture = "Compact MLP-Temporal Hybrid"
    else:
        base_architecture = "ResNet50"

    modifications: List[str] = []
    if priority["accuracy"] >= max(priority["latency"], priority["size"]):
        modifications.extend(
            [
                "Increase depth within the active parameter budget",
                "Prefer conv3x3 or sep_conv5x5 cells in later stages",
                "Keep skip connections on every two to three blocks",
            ]
        )
    if priority["latency"] >= 0.33 or target_hardware != "Cloud GPU":
        modifications.extend(
            [
                "Use depthwise separable convolutions in early high-resolution layers",
                "Add stride-2 downsampling before expensive channel expansion",
                "Avoid repeated conv5x5 blocks on constrained hardware",
            ]
        )
    if priority["size"] >= 0.25:
        modifications.extend(
            [
                "Cap channel width and prefer bottleneck1x1 transitions",
                "Share repeated cell templates across stages",
            ]
        )

    if not modifications:
        modifications.append("Use balanced NSGA-II search across accuracy, latency, and size")

    data_strategy = []
    if dataset_size == "Small (<10k)":
        data_strategy.extend(
            [
                "Use transfer learning with pretrained weights",
                "Apply strong augmentation with mixup or cutmix",
                "Freeze early feature layers for the first training phase",
            ]
        )
    elif dataset_size == "Medium (10k-100k)":
        data_strategy.extend(
            [
                "Fine-tune with moderate augmentation",
                "Use cosine learning-rate decay with warmup",
                "Validate candidate architectures with repeated seeds",
            ]
        )
    else:
        data_strategy.extend(
            [
                "Train top Pareto candidates from scratch",
                "Use progressive resizing for image workloads",
                "Reserve a holdout set for final Pareto-front verification",
            ]
        )

    training_recipe = {
        "epochs": "50-100" if dataset_size == "Small (<10k)" else "30-60" if dataset_size == "Medium (10k-100k)" else "20-40",
        "batchSize": "64-128" if target_hardware == "Cloud GPU" else "16-32",
        "learningRate": "1e-3 with cosine annealing",
        "optimizer": "AdamW",
        "schedule": "Warmup for 5% of steps, then cosine decay",
    }

    compression = []
    if priority["size"] > 0.2 or target_hardware != "Cloud GPU":
        compression.extend(
            [
                {
                    "technique": "Quantization",
                    "description": "INT8 post-training quantization for deployment",
                    "impact": "-50% model size, small accuracy loss, lower latency",
                },
                {
                    "technique": "Structured Pruning",
                    "description": "Remove low-importance channels after search",
                    "impact": "-20-35% parameters with targeted fine-tuning recovery",
                },
            ]
        )
    if dataset_size == "Large (>100k)":
        compression.append(
            {
                "technique": "Knowledge Distillation",
                "description": "Distill the selected Pareto model from a larger teacher",
                "impact": "Improves compact-model accuracy while keeping latency stable",
            }
        )

    latency_hint = "< 40ms" if priority["latency"] > priority["accuracy"] else "40-120ms"
    if target_hardware == "Cloud GPU":
        latency_hint = "< 25ms batch inference" if priority["latency"] > 0.35 else "25-80ms"

    deployment = {
        "runtime": "TorchScript or ONNX Runtime" if target_hardware == "Cloud GPU" else "ONNX Runtime, TFLite, or OpenVINO",
        "batchSize": "32-64" if target_hardware == "Cloud GPU" else "1-8",
        "estimatedLatency": latency_hint,
    }

    confidence = 0.86
    if payload.get("maxParams") or payload.get("maxFlops") or payload.get("maxLatency"):
        confidence += 0.03
    if target_hardware != "Cloud GPU":
        confidence += 0.02

    return {
        "baseArchitecture": base_architecture,
        "modifications": modifications[:5],
        "dataStrategy": data_strategy,
        "trainingRecipe": training_recipe,
        "compression": compression,
        "deployment": deployment,
        "confidence": min(0.96, confidence),
        "justification": (
            f"For {target_hardware} and a {dataset_size} dataset, {base_architecture} gives a strong "
            "starting point. The recommendation biases the NSGA-II search toward the requested "
            "accuracy, latency, and size trade-off while keeping deployment constraints explicit."
        ),
    }
