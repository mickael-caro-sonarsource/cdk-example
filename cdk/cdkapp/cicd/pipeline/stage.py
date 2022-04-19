from abc import abstractmethod

import aws_cdk as cdk
from constructs import Construct
from jsii import JSIIAbstractClass

from cdkapp.config.schemas_config import EnvironmentConfig, ProjectConfig


class AbstractStage(cdk.Stage, metaclass=JSIIAbstractClass):
    """
    Abstract Stage to be inherited from in the different repositories.

    The inherited class should be given as an argument to the PipelineStack.
    Only the define_stacks method needs to be overriden.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        env_config: EnvironmentConfig,
        project_config: ProjectConfig,
    ):
        """Initialise CDK stage."""
        super().__init__(scope, id, env=env_config.get_cdk_env())

        self.define_stacks(env_config)

    @abstractmethod
    def define_stacks(self, env_config):
        """Abstract method to add the stacks to the stage."""
        pass
