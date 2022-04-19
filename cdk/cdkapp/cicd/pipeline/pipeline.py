from typing import Type, List, Optional

import aws_cdk as cdk

from aws_cdk import (
    aws_codebuild as codebuild,
    aws_codecommit as codecommit,
    pipelines,
)

from constructs import Construct

from cdkapp.cicd.pipeline import AbstractStage
from cdkapp.config.schemas_config import EnvironmentConfig, ProjectConfig


class PipelineStack(cdk.Stack):
    """Deploy resources for deployment pipeline."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        project_config: ProjectConfig,
        stage_class: Type[AbstractStage],
        workload_configs: List[EnvironmentConfig],
        source_branch: str,
        pipeline_subtitle: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Initialise Pipeline Stack.

        Args:
            scope: CDK Scope
            id: Logical ID withing CFn template
            project_config: project config
            stage_class: the class for the stage
            workload_configs: CDK app config
            source_branch: the repo branch
            pipeline_subtitle: the subtitle for the pipeline. The pipeline name will follow the scheme
            "{project_config.NAME}-{pipeline_subtitle}-pipeline" if the argument is set
            "{project_config.NAME}-pipeline" otherwise.
            **kwargs: other CDK arguments

        """
        super().__init__(scope, id, **kwargs)

        self.project_config = project_config

        repo = codecommit.Repository.from_repository_name(
            self,
            "ImportedRepo",
            repository_name=self.project_config.CODECOMMIT_REPOSITORY_NAME,
        )

        build_image = codebuild.LinuxBuildImage.STANDARD_5_0

        self.build_defaults = pipelines.CodeBuildOptions(
            build_environment=codebuild.BuildEnvironment(
                build_image=build_image,
                privileged=True,
            ),
        )

        # Get the pipeline name
        if pipeline_subtitle is not None:
            pipeline_name = f"{project_config.NAME}-{pipeline_subtitle}-pipeline"
        else:
            pipeline_name = f"{project_config.NAME}-pipeline"

        # Define the new pipeline
        self.pipeline = pipelines.CodePipeline(
            self,
            "Pipeline",
            pipeline_name=pipeline_name,
            cli_version=self.project_config.AWS_CDK_VERSION,
            code_build_defaults=self.build_defaults,
            self_mutation=True,
            cross_account_keys=True,
            synth=pipelines.ShellStep(
                "Synth",
                input=pipelines.CodePipelineSource.code_commit(
                    repository=repo,
                    branch=source_branch,
                ),
                install_commands=self.synth_install_commands,
                commands=["cdk synth --debug"],
                primary_output_directory="cdk/cdk.out",
            ),
        )

        # ######################################################
        # Workload env deployments
        # ######################################################

        for workload_config in workload_configs:
            # We don't use add_application_stage to be able to give the same name to the stack deployed in each env
            app_stage = cdk.Stage(self, workload_config.SHORT_NAME)

            app_stage = self.pipeline.add_stage(
                stage=stage_class(
                    app_stage,
                    project_config.NAME,
                    env_config=workload_config,
                    project_config=project_config,
                )
            )

            if workload_config.MANUAL_APPROVAL:
                app_stage.add_pre(pipelines.ManualApprovalStep("Approve"))

    @property
    def synth_install_commands(self):
        """Install command used by the synth action."""
        return [
            f"npm install -g aws-cdk@{self.project_config.AWS_CDK_VERSION}",
            "git config --global credential.helper '!aws codecommit credential-helper $@'",
            "git config --global credential.UseHttpPath true",
            "cd cdk",
            "pip install -r requirements.txt",
        ]
