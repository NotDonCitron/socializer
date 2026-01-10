import yaml
from radar.models import StackConfig

def load_stack_config(path: str = "stack.yaml") -> StackConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return StackConfig.model_validate(data)
