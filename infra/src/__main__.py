import pulumi
from pulumi import Config

from components.api_gateway import create_http_api
from components.database import create_database
from components.lambdas import create_api_lambda, create_lambda_role
from components.storage import create_captures_bucket

# Stack-scoped config
config = Config()

# 1. S3 bucket
captures_bucket = create_captures_bucket(config=config)

# 2. Postgres database
postgres_instance = create_database(config=config)

# 3. Lambda
lambda_role = create_lambda_role()
api_lambda = create_api_lambda(lambda_role=lambda_role, code_path="../api")

# 4. API Gateway
api_endpoint_output = create_http_api(api_lambda)

# 5. Top-level exports for convenience (we also export some inside components)
pulumi.export("apiUrl", api_endpoint_output)
pulumi.export("capturesBucketId", captures_bucket.id)
pulumi.export("dbEndpointAddress", postgres_instance.address)
