import logging
import subprocess

from abc import ABC
from pathlib import Path
from typing import re
from hurry.filesize import size

from src.config import Config
from src.disk import Disk


class DiskMounter(ABC):

    def __init__(self, config: Config):
        self._config = config
        self._disk = Disk

    def mount(self, disk: Disk):
        self._disk = disk

        # create mount dir
        self._create_dir()

        # update fstab
        self._update_fstab()

        # mount drive
        self._mount_disk()

    def _create_dir(self):
        # create partition folder, including parents
        # skip if the directory exists
        if not self._disk.partition.exists():
            self._disk.partition.mkdir(parents=True)
            logging.debug(f"Creating mount point: {self._disk.partition}")

    def _update_fstab(self):
        fp = Path("/etc/fstab")
        has_duplicates = self._check_fstab_duplicates(fp)
        total, used, free = self._disk.size
        pretty_total = size(total)
        defaults = "defaults,auto,users,rw,nofail,noatime 0 0"

        fstr = (
            "\n"
            f"# {self._disk.model} - {pretty_total}\n"
            f"UUID={self._disk.uuid}\t{self._disk.mount}\t{self._disk.format}\t{defaults}"
        )

        if not has_duplicates:
            fp.write_text(fstr, encoding="utf-8")
            logging.debug(f'Updated /etc/fstab for partition {self._disk.partition}')

    def _mount_disk(self) -> bool:
        try:
            subprocess.check_call(['sudo', 'mount', '-v', self._disk.partition])
            return True
        except subprocess.CalledProcessError as e:
            logging.error(
                f"Could not mount partition ({self._disk.partition}) - returncode: {e.returncode}"
            )
            logging.debug(f"Error: {e.stderr}")

        return False

    def _check_fstab_duplicates(self, fp:Path) -> bool:
        txt = fp.read_text(encoding='utf-8')
        res = False

        if re.search(self._disk.mount, txt):
            logging.debug("Found mount point duplicate in /etc/fstab. Skipping...")
            res = True

        if re.search(self._disk.uuid, txt):
            logging.debug("Found UUID duplicate in /etc/fstab. Skipping...")
            res = True

        return res


