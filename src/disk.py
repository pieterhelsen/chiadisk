import csv
import logging
import re
import shutil
import subprocess

from abc import ABC
from pathlib import Path
from subprocess import CompletedProcess
from tempfile import NamedTemporaryFile
from typing import Tuple


class DiskError(Exception):
    pass


class Disk(ABC):

    def __init__(self, disk: dict, list: Path):
        self._list = list
        self._device = Path(disk['device'])
        self._partition = Path(f"{disk['device']}1")
        self._mount = Path(disk['mount'])
        self._clear = self._bool(disk['clear'])
        self._format = self._get_format(disk['format'])
        self._sn = disk['sn']
        self._uuid = disk['uuid']
        self._model = disk['model']
        self._size = (0, 0, 0)
        self._changed = False

        self._set_size()

        if not self._sn:
            self._sn = self._get_sn()
            self._changed = True

        if not self._model:
            self._model = self._get_model()
            self._changed = True

        if self._partition.exists():
            self._uuid = self._get_uuid()
            self._changed = True
            logging.debug(f'Partition exists. Set UUID to {self._uuid}')

        if self._changed:
            self._commit()

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

    def _commit(self):
        tmplist = NamedTemporaryFile(mode='w', delete=False)
        with open(self._list, 'r', encoding='utf-8', newline='') as disklist, tmplist:
            reader = csv.DictReader(disklist, delimiter=";")
            names = reader.fieldnames

            # write reader contents to temporary file
            writer = csv.DictWriter(tmplist, fieldnames=names, delimiter=';')
            writer.writeheader()
            for row in reader:
                if row['device'] == str(self._device):
                    logging.debug(f'Updating entry in {str(self._list)}: {str(self._device)}')
                    row['sn'] = self._sn
                    row['model'] = self._model
                    row['uuid'] = self._uuid

                    if self._clear:
                        row['clear'] = 'Y'
                    else:
                        row['clear'] = 'N'

                updated_row = {
                    'device': row['device'],
                    'mount': row['mount'],
                    'clear': row['clear'],
                    'format': row['format'],
                    'sn': row['sn'],
                    'model': row['model'],
                    'uuid': row['uuid'],
                }

                writer.writerow(updated_row)

        # overwrite existing file with updated file
        shutil.move(tmplist.name, disklist.name)

    def _get_uuid(self) -> str:
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

    def _get_sn(self) -> str:
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

    def _get_model(self) -> str:
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

    def _set_size(self) -> Tuple[int, int, int]:
        if self._partition.exists():
            self._size = shutil.disk_usage(self._partition)
            logging.debug(f'Found partition {self._partition} with {self._size} bytes')
        else:
            self._size = shutil.disk_usage(self._device)

        self._changed = True
        return self._size

    def update(self, commit: bool):
        self._set_size()
        self._get_uuid()

        if commit:
            self._commit()

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

    @clear.setter
    def clear(self, value: bool):
        self._clear = value

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
