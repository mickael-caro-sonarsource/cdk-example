from cdkapp.cicd.pipeline import AbstractStage
from cdkapp.config.schemas_config import EnvironmentConfig
from cdkapp.stacks import CdkAssessmentStack


class AssessmentPipelineStage(AbstractStage):
    """The CDK assessment pipeline stage."""

    def define_stacks(self, env_config: EnvironmentConfig):
        """Implementation of the abstract method to add the stacks to the stage."""
        CdkAssessmentStack(self, "Assessment", vpc_cidr="192.168.0.0/16", environment_config=env_config)
