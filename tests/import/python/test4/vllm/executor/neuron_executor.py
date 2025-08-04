
from vllm.executor.executor_base import ExecutorBase
class NeuronExecutor(ExecutorBase):
    def _init_executor(self, vllm_config) -> None:
        a = ExecutorBase
        