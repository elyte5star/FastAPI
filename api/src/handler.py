from modules.settings.configuration import ApiConfig
from fastapi.logger import logger

cfg = ApiConfig().from_toml_file().from_env_file()
cfg.logger = logger
