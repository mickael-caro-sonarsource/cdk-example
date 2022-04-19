from pathlib import Path

from cdkapp.config.schemas_config import ProjectConfig

project_configuration = ProjectConfig(
    NAME="cdk-assessment",
    CODECOMMIT_REPOSITORY_NAME="CODE_COMMIT_REPO_NAME_HERE",
    ROOT_DIR=Path(__file__).resolve().parents[3].as_posix(),
    AWS_CDK_VERSION="2.13.0",
)
