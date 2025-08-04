class ExecutorBase(ABC):
    def __init__(self, vllm_config):
        self.vllm_config = vllm_config
        self._init_executor()
