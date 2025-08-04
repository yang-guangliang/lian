from vllm.executor.executor_base import ExecutorBase

class TPUExecutor(ExecutorBase):
    def _init_executor(self, vllm_config) -> None:
        torch.load(vllm_config.bin_file)