import aws_cdk as cdk

from dataclasses import dataclass


@dataclass
class EnvironmentConfig:
    """environment configuration."""

    SHORT_NAME: str
    REGION: str
    AWS_ACCOUNT_ID: str
    EC2_INSTANCE_TYPE: str
    DATABASE_INSTANCE_TYPE: str
    MANUAL_APPROVAL: bool

    def get_cdk_env(self):
        """Returns the cdk.Environment object corresponding to this config."""
        return cdk.Environment(account=self.AWS_ACCOUNT_ID, region=self.REGION)
