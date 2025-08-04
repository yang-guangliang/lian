class ExecutorBase(ABC):
    def __init__(self, vllm_config):
        self._init_executor(vllm_config)
