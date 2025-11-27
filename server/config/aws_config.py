"""
AWS Secrets Manager configuration
"""
import json
import boto3
from botocore.exceptions import ClientError
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from .settings import settings


class AWSSecretsManager:
    """Manages AWS Secrets Manager interactions"""
    
    _cache = None
    
    @classmethod
    def _get_cache(cls):
        """Get or create secret cache"""
        if cls._cache is None:
            session = boto3.session.Session()
            client = session.client(
                service_name="secretsmanager",
                region_name=settings.aws_region
            )
            cache_config = SecretCacheConfig()
            cls._cache = SecretCache(config=cache_config, client=client)
        return cls._cache
    
    @classmethod
    def get_secret(cls, secret_name: str = None) -> dict:
        """
        Retrieve secret from AWS Secrets Manager
        
        Args:
            secret_name: Name of the secret (defaults to settings.aws_secret_name)
        
        Returns:
            Dictionary containing secret values
        
        Raises:
            ClientError: If secret retrieval fails
        """
        if secret_name is None:
            secret_name = settings.aws_secret_name
        
        try:
            cache = cls._get_cache()
            secret_string = cache.get_secret_string(secret_name)
            return json.loads(secret_string)
        except ClientError as e:
            raise e


class DatabaseConfig:
    """Database configuration from AWS Secrets Manager"""
    
    _secret = None
    
    @classmethod
    def _get_secret(cls) -> dict:
        """Get cached secret"""
        if cls._secret is None:
            cls._secret = AWSSecretsManager.get_secret()
        return cls._secret
    
    @classmethod
    def get_host(cls) -> str:
        return cls._get_secret()["RDS_HOST"]
    
    @classmethod
    def get_port(cls) -> int:
        return cls._get_secret()["RDS_PORT"]
    
    @classmethod
    def get_username(cls) -> str:
        return cls._get_secret()["RDS_USERNAME"]
    
    @classmethod
    def get_password(cls) -> str:
        return cls._get_secret()["RDS_PASSWORD"]
    
    @classmethod
    def get_database(cls) -> str:
        return cls._get_secret()["RDS_DB_NAME_CHATBOX"]
