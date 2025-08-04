from vllm.executor.executor_base import ExecutorBase

class TPUExecutor(ExecutorBase):
    def _init_executor(self) -> None:
        torch.load(self.vllm_config.bin_file)