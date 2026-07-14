import os

import pytest

from src.capabilities.config import MissingConfigurationError, load_settings


def test_missing_config():
    if "API_KEY" in os.environ:
        del os.environ["API_KEY"]

    with pytest.raises(MissingConfigurationError):
        load_settings()
