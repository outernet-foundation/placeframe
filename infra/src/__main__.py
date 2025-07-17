import pulumi
from pulumi import Config

from components.api_gateway import create_http_api
from components.database import create_database
from components.lambdas import create_api_lambda, create_lambda_role
from components.storage import create_captures_bucket

# Stack config (region comes from pulumi config aws:region)
config = Config()

# 1. S3 bucket (captures)
captures_bucket = create_captures_bucket(config=config)

# 2. Postgres database
postgres_instance = create_database(config=config)

# 3. Lambda (container image)
lambda_role = create_lambda_role()
api_lambda = create_api_lambda(
    lambda_role=lambda_role,
    image_context="../api",  # path to FastAPI repo with Dockerfile
    image_tag="latest",
    memory_size=512,
    timeout_seconds=30,
)

# 4. API Gateway → Lambda proxy
api_endpoint_output = create_http_api(api_lambda)

# 5. Stack outputs
pulumi.export("apiUrl", api_endpoint_output)
pulumi.export("capturesBucketId", captures_bucket.id)
pulumi.export("dbEndpointAddress", postgres_instance.address)
