import pulumi
import pulumi_aws as aws


def create_http_api(lambda_function: aws.lambda_.Function) -> pulumi.Output[str]:
    api = aws.apigatewayv2.Api(
        resource_name="httpApi",
        protocol_type="HTTP",
    )

    integration = aws.apigatewayv2.Integration(
        resource_name="lambdaProxyIntegration",
        api_id=api.id,
        integration_type="AWS_PROXY",
        integration_uri=lambda_function.invoke_arn,
        payload_format_version="2.0",
    )

    aws.apigatewayv2.Route(
        resource_name="catchAllRoute",
        api_id=api.id,
        route_key="$default",
        target=integration.id,
    )

    aws.apigatewayv2.Stage(
        resource_name="defaultStage",
        api_id=api.id,
        name="$default",
        auto_deploy=True,
    )

    # ← NEW: allow API Gateway to invoke the Lambda
    aws.lambda_.Permission(
        resource_name="apiGatewayPermission",
        action="lambda:InvokeFunction",
        function=lambda_function.name,
        principal="apigateway.amazonaws.com",
        source_arn=api.execution_arn.apply(lambda arn: f"{arn}/*/*"),
    )

    return api.api_endpoint
