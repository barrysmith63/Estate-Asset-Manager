"""
Configuration management for Estate Asset Manager
Supports environment-based and file-based configuration
"""
import os
import json
from pathlib import Path


class Config:
    """Base configuration class"""
    
    # Flask settings
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    
    # Upload settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads/images')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
    
    # Database settings
    DB_HOST = os.getenv('DB_HOST', 'dbms.blscomputer.work')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'estate_assets')
    
    # Connection pooling
    DB_POOL_NAME = os.getenv('DB_POOL_NAME', 'estate_pool')
    DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', 5))
    DB_POOL_RESET_SESSION = True
    
    # Pagination
    ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', 20))
    
    # Caching
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'True').lower() == 'true'
    CACHE_TTL = int(os.getenv('CACHE_TTL', 300))  # 5 minutes
    
    @classmethod
    def load_from_file(cls, config_file='project_config.json'):
        """Load configuration from a JSON file
        
        Args:
            config_file: Path to project_config.json
            
        Example project_config.json:
        {
            "database": {
                "host": "dbms.blscomputer.work",
                "port": 3306,
                "user": "your_user",
                "password": "your_password",
                "name": "estate_assets"
            },
            "flask": {
                "debug": false,
                "secret_key": "your-secret-key"
            },
            "upload": {
                "folder": "uploads/images",
                "max_size_mb": 16
            }
        }
        """
        if not os.path.exists(config_file):
            raise FileNotFoundError(
                f"Configuration file not found: {config_file}\n"
                f"Please create {config_file} with your database settings."
            )
        
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        # Database settings
        db_config = config_data.get('database', {})
        cls.DB_HOST = db_config.get('host', cls.DB_HOST)
        cls.DB_PORT = db_config.get('port', cls.DB_PORT)
        cls.DB_USER = db_config.get('user', cls.DB_USER)
        cls.DB_PASSWORD = db_config.get('password', cls.DB_PASSWORD)
        cls.DB_NAME = db_config.get('name', cls.DB_NAME)
        
        # Flask settings
        flask_config = config_data.get('flask', {})
        cls.DEBUG = flask_config.get('debug', cls.DEBUG)
        cls.SECRET_KEY = flask_config.get('secret_key', cls.SECRET_KEY)
        
        # Upload settings
        upload_config = config_data.get('upload', {})
        cls.UPLOAD_FOLDER = upload_config.get('folder', cls.UPLOAD_FOLDER)
        max_size_mb = upload_config.get('max_size_mb', 16)
        cls.MAX_CONTENT_LENGTH = max_size_mb * 1024 * 1024
        
        # Connection pooling
        pool_config = config_data.get('connection_pool', {})
        cls.DB_POOL_SIZE = pool_config.get('size', cls.DB_POOL_SIZE)
        
        # Pagination
        pagination_config = config_data.get('pagination', {})
        cls.ITEMS_PER_PAGE = pagination_config.get('items_per_page', cls.ITEMS_PER_PAGE)
        
        # Caching
        cache_config = config_data.get('cache', {})
        cls.CACHE_ENABLED = cache_config.get('enabled', cls.CACHE_ENABLED)
        cls.CACHE_TTL = cache_config.get('ttl_seconds', cls.CACHE_TTL)
        
        return cls
    
    @classmethod
    def get_db_config(cls):
        """Get database configuration dictionary for mysql.connector"""
        return {
            'host': cls.DB_HOST,
            'port': cls.DB_PORT,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'database': cls.DB_NAME
        }
    
    @classmethod
    def create_example_config_file(cls, filename='project_config.example.json'):
        """Create an example configuration file"""
        example_config = {
            "database": {
                "host": "dbms.blscomputer.work",
                "port": 3306,
                "user": "estate_user",
                "password": "secure_password_here",
                "name": "estate_assets"
            },
            "flask": {
                "debug": False,
                "secret_key": "change-this-to-a-random-secret-key"
            },
            "upload": {
                "folder": "uploads/images",
                "max_size_mb": 16
            },
            "connection_pool": {
                "size": 5
            },
            "pagination": {
                "items_per_page": 20
            },
            "cache": {
                "enabled": True,
                "ttl_seconds": 300
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(example_config, f, indent=2)
        
        return filename


# Load configuration
try:
    Config.load_from_file('project_config.json')
except FileNotFoundError:
    # Fall back to environment variables or defaults
    pass
