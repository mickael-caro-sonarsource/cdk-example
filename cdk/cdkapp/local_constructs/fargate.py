from constructs import Construct
from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_ecs as ecs,
    aws_logs as logs,
    aws_elasticloadbalancingv2 as elasticloadbalancingv2,
)


class FargateCluster(Construct):
    """A fargate custom services that uses an existing alb."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        cluster: ecs.Cluster,
        service_name: str,
        role: iam.Role,
        image_name: str,
        container_port: int,
        alb: elasticloadbalancingv2.ApplicationLoadBalancer,
        listner_port: int,
        vpc: ec2.Vpc,
    ) -> None:
        """
        Initialise the fargate service custom construct.

        Args:
            scope: CDK scope
            id: Logical ID
            cluster: The fatgate cluster
            service_name: The name of the service to create
            role: Iam role to use for tasks
            image_name: DockerHub image repository name
            container_port: The port on the container
            alb: The load balancer to use
            listner_port: the port to open on the alb
            vpc: vpc.

        """
        super().__init__(scope, id)

        task_definition = ecs.FargateTaskDefinition(
            self,
            "TaskDefinition",
            task_role=role,
            memory_limit_mib=512,
            cpu=256,
        )

        # Add the definition of the container
        task_definition.add_container(
            "Container",
            image=ecs.ContainerImage.from_registry(image_name),
            memory_limit_mib=512,
            cpu=256,
            logging=ecs.AwsLogDriver(
                stream_prefix=service_name,
                log_retention=logs.RetentionDays.ONE_MONTH,
            ),
            port_mappings=[ecs.PortMapping(container_port=80)],
        )

        self.service = ecs.FargateService(
            self,
            "Service",
            vpc_subnets=ec2.SubnetSelection(subnets=vpc.private_subnets),
            cluster=cluster,
            task_definition=task_definition,
            service_name=service_name,
            desired_count=3,
        )

        self.service.connections.allow_from(alb, ec2.Port.tcp(container_port))
        alb.connections.allow_to(self.service, ec2.Port.tcp(container_port))

        target_group = elasticloadbalancingv2.ApplicationTargetGroup(
            self,
            "TargetGroup",
            targets=[self.service],
            target_type=elasticloadbalancingv2.TargetType.IP,
            port=container_port,
            protocol=elasticloadbalancingv2.ApplicationProtocol.HTTP,
            vpc=vpc,
            health_check=elasticloadbalancingv2.HealthCheck(
                enabled=True,
                path="/",
            ),
        )

        alb.add_listener(
            id + "Listner",
            default_target_groups=[target_group],
            port=listner_port,
            protocol=elasticloadbalancingv2.ApplicationProtocol.HTTP,
        )
