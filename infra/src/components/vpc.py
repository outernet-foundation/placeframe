import pulumi_aws.ec2 as ec2
import pulumi_awsx as awsx


def create_vpc() -> tuple[
    awsx.ec2.Vpc,
    ec2.SecurityGroup,
    ec2.SecurityGroup,
]:
    # Create a VPC with default subnet layout (public + private in each AZ)
    vpc = awsx.ec2.Vpc(
        "main-vpc",
        nat_gateways=awsx.ec2.NatGatewayConfigurationArgs(
            strategy=awsx.ec2.NatGatewayStrategy.NONE,
        ),
    )

    # Security group for Lambda functions: no inbound, all outbound
    lambda_sg = ec2.SecurityGroup(
        "lambda-sg",
        description="Security group for Lambda functions",
        vpc_id=vpc.vpc_id,
        egress=[
            ec2.SecurityGroupEgressArgs(
                protocol="-1",
                from_port=0,
                to_port=0,
                cidr_blocks=["0.0.0.0/0"],
            ),
        ],
    )

    # Security group for RDS: allow Lambda SG on port 5432, all outbound
    db_sg = ec2.SecurityGroup(
        "db-sg",
        description="Security group for RDS instances",
        vpc_id=vpc.vpc_id,
        ingress=[
            ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=5432,
                to_port=5432,
                security_groups=[lambda_sg.id],
            ),
        ],
        egress=[
            ec2.SecurityGroupEgressArgs(
                protocol="-1",
                from_port=0,
                to_port=0,
                cidr_blocks=["0.0.0.0/0"],
            ),
        ],
    )

    return (
        vpc,
        lambda_sg,
        db_sg,
    )
