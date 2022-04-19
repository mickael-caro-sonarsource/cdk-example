from cdkapp.config.schemas_config import EnvironmentConfig


environment_1_config = EnvironmentConfig(
    REGION="eu-central-1",
    SHORT_NAME="ec1",
    EC2_INSTANCE_TYPE="t3.micro",
    DATABASE_INSTANCE_TYPE="t3.medium",
    AWS_ACCOUNT_ID="ACCOUNT_ID_HERE",
    MANUAL_APPROVAL=False,
)
