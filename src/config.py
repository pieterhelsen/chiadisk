# std
import logging
import sys
from pathlib import Path
from typing import Optional

# lib
import yaml


class Config:
    def __init__(self, config_path: Path):
        if not config_path.is_file():
            raise ValueError(f"Invalid config.yaml path: {config_path}")

        with open(config_path, "r", encoding="UTF-8") as config_file:
            self._config = yaml.safe_load(config_file)

    def _get_child_config(self, key: str, required: bool = True) -> Optional[dict]:
        if key not in self._config.keys():
            if required:
                raise ValueError(f"Invalid config - cannot find {key} key")
            else:
                return None

        return self._config[key]

    def get_config(self):
        return self._config

    def get_disk_config(self):
        return self._get_child_config("chiadisk")

    def get_health_config(self):
        return self._get_child_config("health")

    def get_log_level(self):
        log_level = self._get_child_config("log_level")

        if log_level == "CRITICAL":
            return logging.CRITICAL
        if log_level == "ERROR":
            return logging.ERROR
        if log_level == "WARNING":
            return logging.WARNING
        if log_level == "INFO":
            return logging.INFO
        if log_level == "DEBUG":
            return logging.DEBUG

        logging.warning(f"Unsupported log level: {log_level}. Fallback to INFO level.")
        return logging.INFO

    @staticmethod
    def check_keys(self, required_keys, config) -> bool:
        for key in required_keys:
            if key not in config.keys():
                logging.error(f"Incompatible configuration. Missing {key} in {config}.")
                return False
        return True

