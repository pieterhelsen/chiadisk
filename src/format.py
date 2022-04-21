import logging
import subprocess

from abc import ABC
from time import sleep

from src.config import Config
from src.disk import Disk, DiskError

LABEL_TYPES = ("gpt", "bsd", "mac", "msdos")
FILE_SYSTEMS = ("ntfs", "fat32", "ext2", "ext4")


class DiskFormatter(ABC):

    def __init__(self, config: Config):
        self._config = config
        self._disk = None

    def format(self, disk: Disk) -> bool:
        self._disk = disk

        fmt = input(f"Would you like to format the disk at {self._disk.path}? (y/N)")
        if fmt.lower() in ("yes", "y"):
            label = self._get_label()
            fmt_result = self._mklabel(label=label)
            if not fmt_result:
                raise DiskError(f"Could not create label for {self._disk.path}")

            fs = self._get_fs()
            part_result = self._mkpart(fs)
            if not part_result:
                raise DiskError(f"Could not create partition ({fs}) for {self._disk.path}")

            mkfs_result = self._mkfs(fs)
            if not mkfs_result:
                raise DiskError(f"Could not create filesystem ({fs}) for {self._disk.partition}")

            # Waiting for UUID to propagate
            sleep(2)

            # Update UUID and partition size
            self._disk.update()

            return True
        else:
            logging.debug(f"Skipping format for disk {self._disk.path}")

        return False

    def _get_label(self, retry: bool = False) -> str:
        if not retry:
            label = input(f"Select the disk label type (default: gpt):")
        else:
            label = input(f"Invalid disk label type. Choose one of gpt, msdos, bsd or macos (default: gpt):")

        label = "gpt" if label == "" else label
        if label.lower() not in LABEL_TYPES:
            return self._get_label(retry=True)
        else:
            return label.lower()

    def _get_fs(self, retry: bool = False) -> str:
        if not retry:
            fs = input(f"Select the disk filesystem (default: ext4):")
        else:
            fs = input(f"Invalid file system. Choose one of ntfs, fat32, ext2 or ext4 (default: ext4):")

        fs = "ext4" if fs == "" else fs
        if fs.lower() not in FILE_SYSTEMS:
            return self._get_fs(retry=True)
        else:
            return fs.lower()

    def _mklabel(self, label: str = "gpt") -> bool:
        try:
            subprocess.check_call(['sudo', 'parted', '-s', self._disk.path, 'mklabel', label])
            logging.info(f"Creating label for {self._disk.path}: {label}")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Could not create label for {self._disk.path} - returncode: {e.returncode}")
            logging.debug(f"Error: {e.stderr}")

        return False

    def _mkpart(self, fs: str = "ext4") -> bool:
        try:
            subprocess.check_call(['sudo', 'parted', '-s', self._disk.path, 'mkpart', 'primary', fs.lower(),
                                   '0%', '100%'])
            logging.info(f"Creating partition for {self._disk.path}: {fs}")
            self._disk.set_partition()
            return True
        except subprocess.CalledProcessError as e:
            logging.error(
                f"Could not create partition ({fs}) for {self._disk.path} "
                f"- returncode: {e.returncode}"
            )
            logging.debug(f"Error: {e.stderr}")

        return False

    def _mkfs(self, fs: str = "ext4") -> bool:
        try:
            subprocess.check_call(['sudo', f'mkfs.{fs}', '-F', self._disk.partition])
            logging.info(f"Starting filesystem format for {self._disk.partition}")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(
                f"Could not create fs ({fs}) for {self._disk.partition} "
                f"- returncode: {e.returncode}"
            )
            logging.debug(f"Error: {e.stderr}")

        return False

