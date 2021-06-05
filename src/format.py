import logging
import subprocess

from abc import ABC
from src.config import Config
from src.disk import Disk, DiskError


class DiskFormatter(ABC):

    def __init__(self, config: Config):
        self._config = config
        self._disk = Disk

    def format(self, disk: Disk) -> bool:
        self._disk = disk

        if self._disk.clear:
            fmt_result = self._mklabel()
            if not fmt_result:
                raise DiskError(f"Could not create label for {self._disk.device}")

            part_result = self._mkpart()
            if not part_result:
                raise DiskError(f"Could not create partition ({self._disk.format}) for {self._disk.device}")

            mkfs_result = self._mkfs()
            if not mkfs_result:
                raise DiskError(f"Could not create filesystem ({self._disk.format}) for {disk.partition}")

            return True

    def _mklabel(self) -> bool:
        try:
            subprocess.check_call(['sudo', 'parted', '-s', self._disk.device, 'mklabel', 'gpt'])
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Could not create label for {self._disk.device} - returncode: {e.returncode}")
            logging.debug(f"Error: {e.stderr}")

        return False

    def _mkpart(self) -> bool:
        try:
            subprocess.check_call(['sudo', 'parted', 'mkpart', 'primary', self._disk.format, '0%', '100%'])
            return True
        except subprocess.CalledProcessError as e:
            logging.error(
                f"Could not create partition ({self._disk.format}) for {self._disk.device} "
                f"- returncode: {e.returncode}"
            )
            logging.debug(f"Error: {e.stderr}")

        return False

    def _mkfs(self) -> bool:
        try:
            subprocess.check_call(['sudo', f'mkft.{self._disk.format.value.lower()}', self._disk.partition])
            return True
        except subprocess.CalledProcessError as e:
            logging.error(
                f"Could not create fs ({self._disk.format.value.lower()}) for {self._disk.partition} "
                f"- returncode: {e.returncode}"
            )
            logging.debug(f"Error: {e.stderr}")

        return False

