from pulumi import Output
from pulumi_aws import get_caller_identity, get_region_output
from pulumi_aws.ecr import Repository, get_image_output


def repo_digest(repo: Repository):
    return Output.concat(
        repo.repository_url, "@", get_image_output(repository_name=repo.name, image_tag="latest").image_digest
    )


def pullthrough_repo_digest(repo: Repository):
    return Output.concat(
        get_caller_identity().account_id,
        ".dkr.ecr.",
        get_region_output().region,
        ".amazonaws.com/",
        repo.name,
        ":latest",
    )
