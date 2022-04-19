from constructs import Construct
from aws_cdk import (
    aws_ec2 as ec2,
)


class Network(Construct):
    """A network custom construct."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc_cidr: str,
        subnets_mask: int,
    ) -> None:
        """
        Initialise the Network construct.

        Args:
            scope: CDK scope
            id: Logical ID
            vpc_cidr: Vpc CIDR,
            subnets_mask: subnet mask to use for all subnet types.

        """
        super().__init__(scope, id)

        # Create the VPC
        self.vpc = ec2.Vpc(
            self,
            "vpc",
            cidr=vpc_cidr,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            max_azs=3,
            nat_gateways=3,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=subnets_mask,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,
                    cidr_mask=subnets_mask,
                ),
                ec2.SubnetConfiguration(
                    name="Data",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=subnets_mask,
                ),
            ],
        )

        # Add a gateway endpoint for s3
        self.vpc.add_gateway_endpoint(
            "S3GatewayEndpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
        )

        # TODO. Add NACLs if needed
