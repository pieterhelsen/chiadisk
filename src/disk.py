import logging
import re
import shutil
import subprocess

from abc import ABC
from pathlib import Path
from subprocess import CompletedProcess
from typing import Tuple

from pySMART import Device


class DiskError(Exception):
    pass


class Disk(ABC):

    def __init__(self, path: str):
        self._path = Path(path)
        self._smart = Device(path)
        self._fs = None
        self._uuid = None
        self._partition = None
        self._size = (0, 0, 0)
        self.update()

    @staticmethod
    def _bool(clear: str) -> bool:
        if clear.lower() in ['yes', 'y']:
            return True

        return False

    def set_partition(self) -> Path:
        if self._partition is None:
            part = self._path.joinpath('1')
            if part.exists():
                self._partition = part
            else:
                part = self._path.joinpath('p1') # NVMe
                if part.exists():
                    self._partition = part
                else:
                    raise DiskError(f"No partition exists for {self._path}")

        return self._partition

    def set_uuid(self) -> str:

        uuid = "unknown"

        try:
            result: CompletedProcess = subprocess.run(['sudo', 'blkid'], capture_output=True, universal_newlines=True)
            lines = result.stdout.splitlines()

            for line in lines:
                res = re.search(rf'^{re.escape(str(self._partition))}: UUID="(\S*)"', line)
                if res:
                    uuid = res.group(1)
                    logging.error(
                        f"Found UUID for {self._partition}: {uuid}"
                    )

        except subprocess.CalledProcessError as e:
            logging.error(
                f"Could not read UUID for {self._partition} - returncode: {e.returncode}"
            )
            logging.debug(f"Error: {e.stderr}")

        return uuid

    def update(self):
        self._partition = self.set_partition()
        self._uuid = self.set_uuid()
        self._size = self._set_size()

    def _set_size(self) -> Tuple[int, int, int]:
        if self._partition.exists():
            self._size = shutil.disk_usage(self._partition)
            logging.debug(f'Found partition {self._partition} with {self._size} bytes')
        else:
            self._size = shutil.disk_usage(self._path)

        self._changed = True
        return self._size

    @property
    def path(self) -> Path:
        return self._path

    @property
    def partition(self) -> Path:
        if self._partition is None:
            self._partition = self.set_partition()
        return self._partition

    @property
    def smart(self) -> Device:
        return self._smart

    @property
    def uuid(self) -> str:
        if self._uuid is None:
            self._uuid = self.set_uuid()
        return self._uuid

    @property
    def size(self) -> Tuple[int, int, int]:
        return self._size
