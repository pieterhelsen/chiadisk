from abc import ABC
from pathlib import Path

from src.config import Config
from src.disk import Disk


class DiskInfo(ABC):

    def __init__(self, path:Path, config: Config):
        self._config = config
        self._disk = Disk

