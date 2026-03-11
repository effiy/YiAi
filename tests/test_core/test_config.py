"""Test configuration loading."""
from core.config import settings


def test_config_loaded():
    """Test that settings can be loaded."""
    assert settings is not None
    assert settings.server_port > 0


def test_cors_origins():
    """Test CORS origins getter."""
    origins = settings.get_cors_origins()
    assert isinstance(origins, list)
