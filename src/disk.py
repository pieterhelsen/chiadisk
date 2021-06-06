import logging
import re
import shutil
import subprocess

from abc import ABC
from enum import Enum
from pathlib import Path
from subprocess import CompletedProcess
from typing import Tuple


class DiskError(Exception):
    pass


class Disk(ABC):

    def __init__(self, disk: dict):
        self._device = Path(disk['device'])
        self._partition = Path(f"{disk['device']}1")
        self._mount = Path(disk['mount'])
        self._clear = self._bool(disk['clear'])
        self._format = self._get_format(disk['format'])
        self._sn = disk['sn']
        self._uuid = disk['uuid']
        self._model = disk['model']

        if not self._sn:
            self._sn = self.set_sn()

        if not self._model:
            self._model = self.set_model()

        if self._partition.exists():
            self._uuid = self.set_uuid()
            logging.debug(f'Partition exists. Set UUID to {self._uuid}')

        self._size = shutil.disk_usage(self._device)

    @staticmethod
    def _bool(clear: str) -> bool:
        if clear.lower() in ['yes', 'y']:
            return True

        return False

    @staticmethod
    def _get_format(fmt: str) -> str:
        if fmt in ('ext4', 'ext2', 'ntfs', 'vfat'):
            return fmt

        return 'ext4'

    def set_partition(self, partition_id: int):
        self._partition = f"{self.device}{str(partition_id)}"
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

        except subprocess.CalledProcessError as e:
            logging.error(
                f"Could not read UUID for {self._partition} - returncode: {e.returncode}"
            )
            logging.debug(f"Error: {e.stderr}")

        return uuid

    def set_sn(self) -> str:
        sn = "unknown"

        try:
            result: CompletedProcess = subprocess.run(
                ['udevadm', 'info', '--query=all', f'--name={self._device}', '|', 'grep', 'ID_SERIAL_SHORT'],
                capture_output=True, universal_newlines=True
            )

            res = re.search(r'ID_SERIAL_SHORT=(.*)', result.stdout)
            if res:
                sn = res.group(1)

        except subprocess.CalledProcessError as e:
            logging.error(
                f"Could not read Serial Number for {self._device} - returncode: {e.returncode}"
            )
            logging.debug(f"Error: {e.stderr}")

        return sn

    def set_model(self) -> str:
        model = "unknown"

        try:
            result: CompletedProcess = subprocess.run(
                ['udevadm', 'info', '--query=all', f'--name={self._device}', '|', 'grep', 'ID_MODEL'],
                capture_output=True, universal_newlines=True
            )

            res = re.search(r'ID_MODEL=(.*)', result.stdout)
            if res:
                model = res.group(1)

        except subprocess.CalledProcessError as e:
            logging.error(
                f"Could not read Serial Number for {self._device} - returncode: {e.returncode}"
            )
            logging.debug(f"Error: {e.stderr}")

        return model

    @property
    def device(self) -> Path:
        return self._device

    @property
    def partition(self) -> Path:
        return self._partition

    @property
    def mount(self) -> Path:
        return self._mount

    @property
    def clear(self) -> bool:
        return self._clear

    @property
    def format(self) -> str:
        return self._format

    @property
    def sn(self) -> str:
        return self._sn

    @property
    def uuid(self) -> str:
        return self._uuid

    @property
    def model(self):
        return self._model

    @property
    def size(self) -> Tuple[int, int, int]:
        return self._size
