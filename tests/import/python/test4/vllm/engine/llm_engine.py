from vllm.executor.neuron_executor import NeuronExecutor
from vllm.executor.tpu_executor import TPUExecutor

# class ExecutorBase(ABC):
#     def __init__(self, vllm_config):
#         self._init_executor(vllm_config)

# class NeuronExecutor(ExecutorBase):
#     def _init_executor(self, vllm_config) -> None:
#         torch.load(vllm_config.bin_file)

# class TPUExecutor(ExecutorBase):
#     def _init_executor(self, vllm_config) -> None:
#         self.worker()

class LLMEngine: # 污点是vllm_config

    def __init__(self, executor_class, vllm_config):
        self.model_executor = executor_class(vllm_config)
    def from_engine_args(cls, vllm_config):
        executor_class = cls._get_executor_cls(vllm_config)
        engine = cls(executor_class, vllm_config)
    def _get_executor_cls(cls, vllm_config):
        if vllm_config.device_config.device_type == "neuron":
            executor_class = NeuronExecutor
        elif vllm_config.device_config.device_type == "tpu":
            
            executor_class = TPUExecutor
        return executor_class

vllm_config = source()
LLMEngine.from_engine_args(vllm_config)

