from typing import Tuple
from vllm import LLM, SamplingParams

ArchitectureTuple = Tuple[list, list]  # nodes, ops

class ArchitectureCodeGenerator:
    def __init__(self, model_path="meta-llama/Llama-3-7b", device="cuda"):
        """
        model_path: path to LLaMA 3 model
        device: "cuda" or "cpu"
        """
        self.llm = LLM(model=model_path, tensor_parallel_size=1, device=device)

    def arch_to_string(self, arch: ArchitectureTuple) -> str:
        """
        Converts architecture tuple to string description for LLM.
        """
        nodes, ops = arch
        description = "Nodes: {}\nOperations: {}".format(nodes, ops)
        return description

    def generate_code(self, arch: ArchitectureTuple) -> str:
        """
        Calls LLaMA 3 via vLLM to generate PyTorch code.
        """
        arch_desc = self.arch_to_string(arch)
        prompt = f"""
You are a PyTorch expert. Generate a Python class implementing the following architecture:
{arch_desc}

The class should inherit from nn.Module and define the forward pass.
Only return Python code, no explanations.
"""
        sampling_params = SamplingParams(temperature=0.0, max_output_tokens=512)
        outputs = self.llm.generate(prompt, sampling_params=sampling_params)
        code = outputs[0].text
        return code