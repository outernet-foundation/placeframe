import warnings

from pulumi import Config, get_stack

from stacks.core import create_core_stack
from stacks.dev import create_dev_stack

# Turn pulumi warnings into errors
warnings.simplefilter("error", category=UserWarning)

config = Config()

match get_stack():
    case "core":
        create_core_stack(config)
    case "dev":
        create_dev_stack(config)
    case _:
        raise NotImplementedError("Stack not implemented")
