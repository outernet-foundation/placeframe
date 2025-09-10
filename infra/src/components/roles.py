import json

from pulumi import Config, Output, ResourceOptions

from components.role import Role


def github_actions_assume_role_policy(
    config: Config, github_oidc_provider_arn: Output[str], environment: str
) -> Output[str]:
    repo = f"{config.require('github-org')}/{config.require('github-repo')}"
    # Use Output.json_dumps so the provider ARN (an Output[str]) can be embedded directly
    return Output.json_dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Federated": github_oidc_provider_arn},
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": [
                            f"repo:{repo}:ref:refs/heads/{config.require('github-branch')}",
                            f"repo:{repo}:pull_request",
                            # f"repo:{repo}:environment:{environment}",
                        ]
                    },
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                        # "token.actions.githubusercontent.com:repository": repo,
                        # "token.actions.githubusercontent.com:environment": environment,
                    },
                },
            }
        ],
    })


def ecs_role(resource_name: str, opts: ResourceOptions | None = None):
    return Role(
        resource_name,
        assume_role_policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Principal": {"Service": "ecs-tasks.amazonaws.com"}, "Action": "sts:AssumeRole"}
            ],
        }),
        opts=opts,
    )


def ecs_execution_role(resource_name: str, opts: ResourceOptions | None = None):
    role = ecs_role(resource_name, opts=opts)
    role.attach_ecs_task_execution_role_policy()
    return role


def ec2_role(resource_name: str, opts: ResourceOptions | None = None):
    role = Role(
        resource_name,
        assume_role_policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole"}
            ],
        }),
        opts=opts,
    )

    role.attach_ec2_instance_role_policy()

    return role


def lambda_role(resource_name: str, opts: ResourceOptions | None = None):
    role = Role(
        resource_name,
        assume_role_policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}
            ],
        }),
        opts=opts,
    )

    role.attach_lambda_basic_execution_role_policy()
    role.attach_lambda_vpc_access_execution_role_policy()

    return role
