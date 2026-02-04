from app.api.utils.enums.base import BaseEnum


class EnvEnum(BaseEnum):
    LOCAL = 'LOCAL'
    DEV = 'DEV'
    STAGE = 'STAGE'
    PROD = 'PROD'
    PYTEST = 'PYTEST'
