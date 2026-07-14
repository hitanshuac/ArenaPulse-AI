import os


class MissingConfigurationError(Exception):
    pass


def load_settings():
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise MissingConfigurationError("API_KEY environment variable is required per 12-factor BYOK rules.")
    return {"api_key": api_key}
