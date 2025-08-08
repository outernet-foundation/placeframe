from pulumi_aws import get_region_output
from pulumi_aws.cloudwatch import LogGroup
from pulumi_awsx.ecs._inputs import TaskDefinitionLogConfigurationArgsDict


def log_configuration(log_group: LogGroup) -> TaskDefinitionLogConfigurationArgsDict:
    return {
        "log_driver": "awslogs",
        "options": {
            "awslogs-group": log_group.name,
            "awslogs-region": get_region_output().region,
            "awslogs-stream-prefix": "ecs",
        },
    }
