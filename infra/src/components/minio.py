# import json

# import pulumi
# import pulumi_aws as aws
# import pulumi_awsx as awsx
# from pulumi import Config, Output
# from pulumi_awsx.ecs import FargateService

# from util import ALLOW_ALL_EGRESS, add_security_group_cross_reference


# def create_minio(config: Config, vpc: awsx.ec2.Vpc, s3_bucket: aws.s3.Bucket) -> Output[str]:
#     aws.cloudwatch.LogGroup("minio-log-group", name="/ecs/minio", retention_in_days=7)

#     # Create task role with S3 access for MinIO
#     task_role = aws.iam.Role(
#         "minio-task-role",
#         assume_role_policy="""{
#             "Version": "2012-10-17",
#             "Statement": [
#                 {
#                     "Effect": "Allow",
#                     "Principal": {"Service": "ecs-tasks.amazonaws.com"},
#                     "Action": "sts:AssumeRole"
#                 }
#             ]
#         }""",
#     )

#     # Grant S3 access to MinIO task
#     aws.iam.RolePolicy(
#         "minio-s3-access",
#         role=task_role.id,
#         policy=s3_bucket.arn.apply(
#             lambda arn: json.dumps({
#                 "Version": "2012-10-17",
#                 "Statement": [
#                     {
#                         "Effect": "Allow",
#                         "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"],
#                         "Resource": [arn, f"{arn}/*"],
#                     }
#                 ],
#             })
#         ),
#     )

#     execution_role = aws.iam.Role(
#         "minio-execution-role",
#         assume_role_policy="""{
#             "Version": "2012-10-17",
#             "Statement": [
#                 {
#                     "Effect": "Allow",
#                     "Principal": {"Service": "ecs-tasks.amazonaws.com"},
#                     "Action": "sts:AssumeRole"
#                 }
#             ]
#         }""",
#     )

#     aws.iam.RolePolicyAttachment(
#         "minio-exec-AmazonECSTaskExecutionRolePolicy",
#         role=execution_role.name,
#         policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
#     )

#     # Create load balancer security group
#     lb_security_group = aws.ec2.SecurityGroup(
#         "minio-lb-security-group",
#         vpc_id=vpc.vpc_id,
#         ingress=[
#             {"protocol": "tcp", "from_port": 80, "to_port": 80, "cidr_blocks": ["0.0.0.0/0"]},
#             {"protocol": "tcp", "from_port": 9001, "to_port": 9001, "cidr_blocks": ["0.0.0.0/0"]},
#         ],
#     )

#     # Create ECS security group
#     ecs_security_group = aws.ec2.SecurityGroup("minio-ecs-security-group", vpc_id=vpc.vpc_id, egress=ALLOW_ALL_EGRESS)

#     # Add cross-reference rules between load balancer and ECS
#     add_security_group_cross_reference(
#         source_sg=lb_security_group,
#         target_sg=ecs_security_group,
#         ports=[9000, 9001],
#         source_name="lb",
#         target_name="ecs",
#     )

#     # Create an Application Load Balancer with explicit security groups
#     load_balancer = aws.lb.LoadBalancer(
#         "minio-lb",
#         load_balancer_type="application",
#         security_groups=[lb_security_group.id],
#         subnets=vpc.public_subnet_ids,
#     )

#     # Create target group for MinIO S3 API (port 9000)
#     api_target_group = aws.lb.TargetGroup(
#         "minio-api-tg",
#         port=9000,
#         protocol="HTTP",
#         vpc_id=vpc.vpc_id,
#         target_type="ip",  # Use "ip" for Fargate
#         health_check={"path": "/minio/health/live", "matcher": "200-399"},
#     )

#     # Create target group for MinIO Console (port 9001)
#     console_target_group = aws.lb.TargetGroup(
#         "minio-console-tg",
#         port=9001,
#         protocol="HTTP",
#         vpc_id=vpc.vpc_id,
#         target_type="ip",
#         health_check={"path": "/", "matcher": "200-399"},
#     )

#     # Create listener for MinIO API
#     api_listener = aws.lb.Listener(
#         "minio-api-listener",
#         load_balancer_arn=load_balancer.arn,
#         port=80,
#         protocol="HTTP",
#         default_actions=[{"type": "forward", "target_group_arn": api_target_group.arn}],
#     )

#     # Create listener for MinIO Console
#     console_listener = aws.lb.Listener(
#         "minio-console-listener",
#         load_balancer_arn=load_balancer.arn,
#         port=9001,
#         protocol="HTTP",
#         default_actions=[{"type": "forward", "target_group_arn": console_target_group.arn}],
#     )

#     # Create an ECS cluster for MinIO
#     cluster = aws.ecs.Cluster("minio-cluster")

#     # MinIO Service with automatic load balancer integration
#     minio = FargateService(
#         "minioTool",
#         cluster=cluster.arn,
#         task_definition_args={
#             "task_role": {"role_arn": task_role.arn},
#             "execution_role": {"role_arn": execution_role.arn},
#             "container": {
#                 "name": "minio",
#                 "image": "minio/minio:latest",
#                 "cpu": 256,
#                 "memory": 512,
#                 "command": ["server", "/data", "--address", ":9000", "--console-address", ":9001"],
#                 "environment": [
#                     {"name": "MINIO_ROOT_USER", "value": config.require("minioAccessKey")},
#                     {"name": "MINIO_ROOT_PASSWORD", "value": config.require_secret("minioSecretKey")},
#                 ],
#                 "port_mappings": [
#                     {"container_port": 9000, "target_group": api_target_group},
#                     {"container_port": 9001, "target_group": console_target_group},
#                 ],
#                 "log_configuration": {
#                     "log_driver": "awslogs",
#                     "options": {
#                         "awslogs-group": "/ecs/minio",
#                         "awslogs-region": aws.config.region,
#                         "awslogs-stream-prefix": "ecs",
#                     },
#                 },
#             },
#         },
#         network_configuration={"subnets": vpc.private_subnet_ids, "security_groups": [ecs_security_group.id]},
#         desired_count=1,
#         health_check_grace_period_seconds=60,
#         # Add explicit dependencies to ensure proper creation order
#         opts=pulumi.ResourceOptions(depends_on=[api_listener, console_listener]),
#     )

#     # Get the load balancer URL
#     minio_url = load_balancer.dns_name.apply(lambda dns: f"http://{dns}")

#     # Export URLs and service info
#     pulumi.export("minioServiceName", minio.service.name)
#     pulumi.export("minioApiUrl", minio_url.apply(lambda url: f"{url}"))  # Port 80 maps to 9000
#     pulumi.export("minioConsoleUrl", minio_url.apply(lambda url: f"{url}:9001"))

#     return minio_url
