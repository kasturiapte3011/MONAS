from typing import List
from nasbench301 import api

nb301 = api.NASBench301API()

HARDWARE_PROFILES = {
    "mobile": {
        "max_flops": 100e6,
        "allowed_ops": ["sep_conv_3x3", "avg_pool_3x3", "skip_connect"],
    },
    "cpu": {
        "max_flops": 500e6,
        "allowed_ops": ["conv_1x1", "sep_conv_3x3", "skip_connect"],
    },
    "gpu": {
        "max_flops": 1e9,
        "allowed_ops": [
            "conv_1x1",
            "dil_conv_3x3",
            "sep_conv_3x3",
            "skip_connect",
        ],
    },
    "raspberry_pi": {
        "max_flops": 50e6,
        "allowed_ops": ["sep_conv_3x3", "avg_pool_3x3"],
    },
}


def get_hardware_profile(hardware: str)->dict:
    return HARDWARE_PROFILES.get(hardware)

def sample_architectures(n_samples: int, profile: dict)->List:
    """
    Samples architectures from NAS-Bench-301 search space obeying hardware constraints.
    """
    
    sampled = []
    attempts = 0
    max_attempts = n_samples * 20

    while len(sampled) < n_samples and attempts < max_attempts:
        arch = nb301.sample_random_architecture()

        # simple FLOPs estimation proxy (will use predictor later)
        num_ops = len(arch.get_op_indices())
        flops_est = num_ops * 1e7

        if flops_est < profile["max_flops"]:
            ops = [str(op[0]) for op in arch.get_op_list()]
            if all(any(a in op for a in profile["allowed_ops"]) for op in ops):
                sampled.append(arch)

    return sampled

def initialize_population(hardware: str, n_samples: int = 10)->List:
    """
    Full initialization pipeline wrapper
    """
    profile = get_hardware_profile(hardware)
    archs = sample_architectures(n_samples, profile)
    return archs