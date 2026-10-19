"""Compatibility shim for BasicSR 1.4.2 with torchvision 0.20."""

import sys


def install_torchvision_compat() -> None:
    # BasicSR imports rgb_to_grayscale from torchvision's removed module name.
    from torchvision.transforms import functional

    sys.modules.setdefault("torchvision.transforms.functional_tensor", functional)
