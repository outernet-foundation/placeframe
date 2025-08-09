import pulumi_aws as aws
from pulumi import StackReference
from pulumi_aws.s3 import BucketCorsConfigurationV2


def create_storage(core_stack: StackReference) -> aws.s3.Bucket:
    bucket = aws.s3.Bucket(resource_name="capturesBucket", bucket="dev-captures", acl="private", force_destroy=True)

    api_domain = core_stack.require_output("zone-name").apply(lambda z: f"https://api.{z}")

    BucketCorsConfigurationV2(
        "captures-cors",
        bucket=bucket.id,
        cors_rules=[
            {
                "allowed_methods": ["PUT", "GET", "HEAD"],
                "allowed_origins": [api_domain],  # or ["*"] during dev
                "allowed_headers": ["*"],  # at minimum include "content-type"
                "expose_headers": ["ETag"],
                "max_age_seconds": 3000,
            }
        ],
    )

    return bucket
