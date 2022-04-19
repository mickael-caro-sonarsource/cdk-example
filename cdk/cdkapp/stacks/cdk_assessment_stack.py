from constructs import Construct
from aws_cdk import (
    aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elasticloadbalancingv2,
    aws_iam as iam,
    aws_rds as rds,
    aws_s3 as s3,
    Duration,
    Stack,
)

from cdkapp.local_constructs import Network
from cdkapp.local_constructs import FargateCluster
from cdkapp.config import project_config
from cdkapp.config.schemas_config import EnvironmentConfig
from cdkapp.utils import PathHelper


class CdkAssessmentStack(Stack):
    """The Assesment stack."""

    def __init__(
        self, scope: Construct, construct_id: str, vpc_cidr: str, environment_config: EnvironmentConfig, **kwargs
    ) -> None:
        """
        Initialise the CdkAssessmentStack.

        Args:
            scope: CDK scope
            construct_id: the construct ID
            vpc_cidr: Vpc CIDR
            environment_config: the environment configuration variables.

        """
        super().__init__(scope, construct_id, **kwargs)

        ##################
        ### Create the s3 bucket
        ##################
        bucket = s3.Bucket(self, "Bucket")

        ##################
        ### Create the network components using a custom construct
        ##################
        network = Network(
            self,
            "Network",
            vpc_cidr=vpc_cidr,
            subnets_mask=24,
        )

        ##################
        ### Create the roles and security groups
        ##################
        asg_ec2_role = iam.Role(
            self,
            "InstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")],
        )

        ecs_task_role = iam.Role(
            self,
            "EcsTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        # Grant read and write access to ecs tasks and ec2 instances
        bucket.grant_read_write(asg_ec2_role)
        bucket.grant_read_write(ecs_task_role)

        # Create the instances (autoscaling) sg
        asg_sg = ec2.SecurityGroup(
            self,
            "AutoScalingSG",
            description="Sonar CDK ASG SG",
            vpc=network.vpc,
            allow_all_outbound=True,
        )

        # Create the load balancer sg
        alb_sg = ec2.SecurityGroup(
            self,
            "LoadBalancerSG",
            description="Sonar CDK ASG SG",
            vpc=network.vpc,
            allow_all_outbound=True,
        )

        # Add ingress rule for the load balancer sg
        alb_sg.add_ingress_rule(peer=ec2.Peer.any_ipv4(), connection=ec2.Port.tcp(80))

        # Only allow the alb to access the asg instances on port 80
        asg_sg.add_ingress_rule(peer=alb_sg, connection=ec2.Port.tcp(80))

        ##################
        ### Create the ALB
        ##################
        alb = elasticloadbalancingv2.ApplicationLoadBalancer(
            self,
            "ApplicationLoadBalancer",
            vpc=network.vpc,
            internet_facing=True,
            vpc_subnets=ec2.SubnetSelection(subnets=network.vpc.public_subnets),
            security_group=alb_sg,
        )

        ##################
        ### Create the  ec2 autoscaling
        ##################
        asg = autoscaling.AutoScalingGroup(
            self,
            "ASG",
            instance_type=ec2.InstanceType(instance_type_identifier=environment_config.EC2_INSTANCE_TYPE),
            machine_image=ec2.MachineImage.latest_amazon_linux(),
            vpc=network.vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=network.vpc.private_subnets),
            role=asg_ec2_role,
            security_group=asg_sg,
            min_capacity=3,
            max_capacity=3,
            desired_capacity=3,
            health_check=autoscaling.HealthCheck.ec2(grace=Duration.seconds(600)),
            update_policy=autoscaling.UpdatePolicy.rolling_update(),
        )

        # Add the userdata
        user_data_file_path = PathHelper(project_config=project_config).get_userdata_path("install_httpd.sh")
        asg.user_data.add_commands(PathHelper.get_file_content(user_data_file_path))

        # Add the application laod balancer listener
        listener = alb.add_listener(
            "TCPListener", protocol=elasticloadbalancingv2.ApplicationProtocol.HTTP, port=80, open=False
        )

        # Add the asg as a target
        listener.add_targets(
            "TargetGroupAsg",
            protocol=elasticloadbalancingv2.ApplicationProtocol.HTTP,
            port=80,
            targets=[asg],
            health_check=elasticloadbalancingv2.HealthCheck(port="80", path="/"),
        )

        ##################
        ### Create the fargate apps infrastructure using a custom construct
        ##################
        # Create the cluster that is shared by the services
        cluster = ecs.Cluster(self, "App", cluster_name=construct_id, vpc=network.vpc)

        # Create the first fargate service
        fargate_app1 = FargateCluster(
            self,
            "app1",
            cluster=cluster,
            service_name="App1Service",
            role=ecs_task_role,
            image_name="httpd",
            container_port=80,
            alb=alb,
            listner_port=8080,
            vpc=network.vpc,
        )

        # Create the second fargate service
        fargate_app2 = FargateCluster(
            self,
            "app2",
            cluster=cluster,
            service_name="App2Service",
            role=ecs_task_role,
            image_name="nginx",
            container_port=80,
            alb=alb,
            listner_port=8081,
            vpc=network.vpc,
        )

        # Add autoscaling for app2
        app2_auto_scaling_target = fargate_app2.service.auto_scale_task_count(
            min_capacity=3,
            max_capacity=12,
        )

        app2_auto_scaling_target.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=50,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60),
        )

        app2_auto_scaling_target.scale_on_memory_utilization(
            "MemoryScaling",
            target_utilization_percent=50,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60),
        )

        ##################
        ### Create the database cluster
        ##################
        db_cluster = rds.DatabaseCluster(
            self,
            "darabase",
            engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_13_4),
            instances=3,
            credentials=rds.Credentials.from_generated_secret(
                "postgres",
                secret_name="my-db-secret",
            ),
            instance_props=rds.InstanceProps(
                vpc=network.vpc,
                vpc_subnets=ec2.SubnetSelection(subnets=network.vpc.isolated_subnets),
                instance_type=ec2.InstanceType(environment_config.DATABASE_INSTANCE_TYPE),
            ),
        )

        # Allow the different applications to access the database.
        db_cluster.connections.allow_default_port_from(asg)
        db_cluster.connections.allow_default_port_from(fargate_app1.service)
        db_cluster.connections.allow_default_port_from(fargate_app2.service)
