"""PyTorch code generation for MONAS architectures.

This module avoids loading an LLM at import time. It emits a practical PyTorch
module directly from the architecture dictionary produced by the search engine.
"""

from __future__ import annotations

from typing import Any, Dict, List


def _layer_expression(layer: Dict[str, Any], in_channels: int) -> str:
    op = layer.get("op", "conv3x3")
    out_channels = int(layer.get("channels", in_channels))
    stride = int(layer.get("stride", 1))
    repeat = int(layer.get("repeat", 1))
    activation = {
        "relu": "nn.ReLU(inplace=True)",
        "gelu": "nn.GELU()",
        "swish": "nn.SiLU(inplace=True)",
    }.get(layer.get("activation", "relu"), "nn.ReLU(inplace=True)")

    if op == "skip":
        if in_channels == out_channels and stride == 1:
            return "nn.Identity()"
        return (
            "nn.Sequential("
            f"nn.Conv2d({in_channels}, {out_channels}, kernel_size=1, stride={stride}, bias=False), "
            f"nn.BatchNorm2d({out_channels})"
            ")"
        )

    if op in {"maxpool3x3", "avgpool3x3"}:
        pool = "nn.MaxPool2d" if op == "maxpool3x3" else "nn.AvgPool2d"
        return (
            "nn.Sequential("
            f"{pool}(kernel_size=3, stride={stride}, padding=1), "
            f"nn.Conv2d({in_channels}, {out_channels}, kernel_size=1, bias=False), "
            f"nn.BatchNorm2d({out_channels}), {activation}"
            ")"
        )

    if op in {"sep_conv3x3", "sep_conv5x5"}:
        kernel = 5 if op.endswith("5x5") else 3
        padding = kernel // 2
        return (
            "nn.Sequential("
            f"nn.Conv2d({in_channels}, {in_channels}, kernel_size={kernel}, stride={stride}, "
            f"padding={padding}, groups={in_channels}, bias=False), "
            f"nn.Conv2d({in_channels}, {out_channels}, kernel_size=1, bias=False), "
            f"nn.BatchNorm2d({out_channels}), {activation}"
            ")"
        )

    if op == "bottleneck1x1":
        hidden = max(8, out_channels // 2)
        return (
            "nn.Sequential("
            f"nn.Conv2d({in_channels}, {hidden}, kernel_size=1, bias=False), "
            f"nn.BatchNorm2d({hidden}), {activation}, "
            f"nn.Conv2d({hidden}, {out_channels}, kernel_size=1, stride={stride}, bias=False), "
            f"nn.BatchNorm2d({out_channels}), {activation}"
            ")"
        )

    kernel = 5 if op == "conv5x5" else 3
    dilation = 2 if op == "dil_conv3x3" else 1
    padding = 2 if op in {"conv5x5", "dil_conv3x3"} else 1
    block = (
        "nn.Sequential("
        f"nn.Conv2d({in_channels}, {out_channels}, kernel_size={kernel}, stride={stride}, "
        f"padding={padding}, dilation={dilation}, bias=False), "
        f"nn.BatchNorm2d({out_channels}), {activation}"
        ")"
    )
    if repeat <= 1:
        return block
    repeats = [block]
    for _ in range(repeat - 1):
        repeats.append(
            "nn.Sequential("
            f"nn.Conv2d({out_channels}, {out_channels}, kernel_size={kernel}, padding={padding}, "
            f"dilation={dilation}, bias=False), nn.BatchNorm2d({out_channels}), {activation}"
            ")"
        )
    return "nn.Sequential(" + ", ".join(repeats) + ")"


class ArchitectureCodeGenerator:
    def arch_to_string(self, architecture: Dict[str, Any]) -> str:
        layers = architecture.get("layers", [])
        return "\n".join(
            f"{idx}: {layer.get('op')} channels={layer.get('channels')} stride={layer.get('stride')} "
            f"repeat={layer.get('repeat')}"
            for idx, layer in enumerate(layers)
        )

    def generate_code(self, architecture: Dict[str, Any], class_name: str = "MonasModel") -> str:
        input_channels = int(architecture.get("input_shape", [3, 32, 32])[0])
        num_classes = int(architecture.get("num_classes", 10))
        layers = architecture.get("layers", [])

        lines: List[str] = [
            "import torch",
            "import torch.nn as nn",
            "",
            "",
            f"class {class_name}(nn.Module):",
            "    def __init__(self, num_classes: int = " + str(num_classes) + "):",
            "        super().__init__()",
            "        self.features = nn.Sequential(",
        ]

        in_channels = input_channels
        for layer in layers:
            expression = _layer_expression(layer, in_channels)
            lines.append(f"            {expression},")
            op = layer.get("op", "conv3x3")
            if op not in {"maxpool3x3", "avgpool3x3"} or int(layer.get("channels", in_channels)) != in_channels:
                in_channels = int(layer.get("channels", in_channels))

        lines.extend(
            [
                "        )",
                "        self.pool = nn.AdaptiveAvgPool2d(1)",
                f"        self.classifier = nn.Linear({in_channels}, num_classes)",
                "",
                "    def forward(self, x):",
                "        x = self.features(x)",
                "        x = self.pool(x).flatten(1)",
                "        return self.classifier(x)",
                "",
            ]
        )
        return "\n".join(lines)
