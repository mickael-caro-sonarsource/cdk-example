from dataclasses import dataclass


@dataclass
class ProjectConfig:
    """environment configuration."""

    NAME: str
    CODECOMMIT_REPOSITORY_NAME: str

    AWS_CDK_VERSION: str
    ROOT_DIR: str
