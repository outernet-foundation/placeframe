import json

from pulumi import Config, Output


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


def ecs_assume_role_policy() -> str:
    # Static JSON is fine to keep as a plain string
    return json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Principal": {"Service": "ecs-tasks.amazonaws.com"}, "Action": "sts:AssumeRole"}
        ],
    })
