import aws_cdk as cdk

from cdkapp.cicd.pipeline_stages import AssessmentPipelineStage
from cdkapp.cicd.pipeline.pipeline import PipelineStack
from cdkapp.config import env1, project_config


app = cdk.App()

# Deploy the pipeline
PipelineStack(
    app,
    "cdk-assesement",
    project_config=project_config,
    stage_class=AssessmentPipelineStage,
    workload_configs=[
        env1,
    ],
    source_branch="master",
    env=env1.get_cdk_env(),
)

app.synth()
